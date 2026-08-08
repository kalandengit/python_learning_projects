import base64
import hashlib
import hmac
import json
import logging
import secrets
import time

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

QR_SECRET_PARAM = "ems.ticket_qr_secret"
MIN_TTL = 15
MAX_TTL = 300


class EmsTicket(models.Model):
    _name = "ems.ticket"
    _description = "EMS Ticket"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True, readonly=True, copy=False, default="/")
    event_id = fields.Many2one("event.event", required=True, ondelete="restrict", index=True)
    registration_id = fields.Many2one("event.registration", ondelete="set null", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)
    public_uid = fields.Char(required=True, readonly=True, copy=False, index=True,
                             default=lambda self: self._new_uid())
    token_version = fields.Integer(default=1, readonly=True)
    state = fields.Selection(
        [("active", "Active"), ("used", "Used"), ("revoked", "Revoked"),
         ("transferred", "Transferred")],
        required=True, default="active", tracking=True, index=True
    )
    transferred_to_id = fields.Many2one("res.partner", readonly=True)
    transferred_from_id = fields.Many2one("ems.ticket", readonly=True, ondelete="set null")
    used_at = fields.Datetime(readonly=True)
    seat_label = fields.Char(readonly=True)

    _uid_unique = models.Constraint("UNIQUE(public_uid)", "Ticket identifier must be unique.")

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    @staticmethod
    def _new_uid():
        return secrets.token_urlsafe(24)

    def _ems_prepare_create_values(self, vals):
        """Fill EMS defaults for a single create() dict.

        Deliberately *not* named ``_prepare_create_values``: that name belongs to
        ``odoo.orm.models.BaseModel`` (which receives a ``vals_list``), and
        shadowing it breaks every create on this model.
        """
        vals = dict(vals)
        if not vals.get("public_uid"):
            vals["public_uid"] = self._new_uid()
        if not vals.get("name") or vals["name"] == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("ems.ticket") or "/"
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._ems_prepare_create_values(v) for v in vals_list])

    @api.constrains("event_id", "registration_id")
    def _check_registration_event(self):
        for ticket in self:
            registration = ticket.registration_id
            if registration and registration.event_id != ticket.event_id:
                raise ValidationError(
                    "The ticket event must match the event of its registration."
                )

    # ------------------------------------------------------------------
    # Authorization helpers
    # ------------------------------------------------------------------
    def _ensure_manage_rights(self):
        # env.su covers the superuser and scheduled actions, which legitimately
        # act without holding an EMS group; everyone else must hold one.
        if self.env.su:
            return
        if not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("You are not allowed to manage EMS tickets.")

    def _qr_secret(self):
        # sudo(): the signing key is a system parameter that EMS users and the
        # portal must never be able to read directly; only this method may use it.
        secret = self.env["ir.config_parameter"].sudo().get_param(QR_SECRET_PARAM)
        if not secret:
            raise UserError(
                "EMS QR signing secret is not configured. Set the system parameter "
                f"'{QR_SECRET_PARAM}' to a high-entropy random value."
            )
        return secret.encode()

    # ------------------------------------------------------------------
    # Signed QR envelope
    # ------------------------------------------------------------------
    @staticmethod
    def _b64(data):
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    @classmethod
    def _decode_b64(cls, value):
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    def get_qr_envelope(self, ttl=60):
        """Return a short-lived HMAC-signed access credential for this ticket."""
        self.ensure_one()
        self.check_access("read")
        if self.state != "active":
            raise UserError("Only active tickets can generate access credentials.")
        now = int(time.time())
        payload = {
            "uid": self.public_uid,
            "v": self.token_version,
            "iat": now,
            "exp": now + max(MIN_TTL, min(int(ttl), MAX_TTL)),
            "event": self.event_id.id,
            "nonce": secrets.token_urlsafe(8),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        sig = hmac.new(self._qr_secret(), raw, hashlib.sha256).digest()
        return f"{self._b64(raw)}.{self._b64(sig)}"

    def verify_qr_envelope(self, envelope):
        """Verify signature and expiry. Returns ``(ok, reason, payload)``.

        Callable on an empty recordset; it never trusts the payload contents,
        which are re-checked against the stored ticket by the scan validator.
        """
        if not isinstance(envelope, str) or envelope.count(".") != 1:
            return False, "malformed", {}
        try:
            payload_b64, sig_b64 = envelope.split(".", 1)
            raw = self._decode_b64(payload_b64)
            received = self._decode_b64(sig_b64)
        except (ValueError, TypeError, base64.binascii.Error):
            return False, "malformed", {}

        expected = hmac.new(self._qr_secret(), raw, hashlib.sha256).digest()
        if not hmac.compare_digest(received, expected):
            return False, "bad_signature", {}
        try:
            payload = json.loads(raw.decode())
        except (ValueError, UnicodeDecodeError):
            return False, "malformed", {}
        if not isinstance(payload, dict):
            return False, "malformed", {}
        try:
            expires_at = int(payload.get("exp", 0))
        except (TypeError, ValueError):
            return False, "malformed", {}
        if expires_at < int(time.time()):
            return False, "expired", payload
        return True, "ok", payload

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def action_revoke(self):
        self._ensure_manage_rights()
        for ticket in self:
            if ticket.state != "active":
                raise UserError("Only active tickets can be revoked.")
            ticket.write({"state": "revoked", "token_version": ticket.token_version + 1})
        return True

    def action_rotate(self):
        """Invalidate previously issued QR envelopes without revoking the ticket."""
        self._ensure_manage_rights()
        for ticket in self:
            if ticket.state != "active":
                raise UserError("Only active tickets can rotate credentials.")
            ticket.write({"token_version": ticket.token_version + 1})
        return True

    def action_transfer(self, partner):
        """Transfer ownership by issuing a fresh ticket and closing this one."""
        self._ensure_manage_rights()
        self.ensure_one()
        if self.state != "active":
            raise UserError("Only active tickets can be transferred.")
        if not partner or partner == self.partner_id:
            raise UserError("Choose a different partner to transfer this ticket to.")
        new_ticket = self.copy({
            "name": "/",
            "partner_id": partner.id,
            "public_uid": self._new_uid(),
            "token_version": 1,
            "state": "active",
            "transferred_from_id": self.id,
        })
        # Bump the version so any envelope already handed out stops validating.
        self.write({
            "state": "transferred",
            "transferred_to_id": partner.id,
            "token_version": self.token_version + 1,
        })
        self.message_post(body=f"Ticket transferred to {partner.display_name}.")
        return new_ticket

    def action_mark_used(self):
        """Terminal check-in transition; used by the scan validator."""
        for ticket in self:
            if ticket.state != "active":
                raise UserError("Only active tickets can be checked in.")
            ticket.write({"state": "used", "used_at": fields.Datetime.now()})
        return True
