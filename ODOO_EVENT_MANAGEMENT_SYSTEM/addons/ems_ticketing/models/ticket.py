import base64
import hashlib
import hmac
import json
import secrets
import time

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


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
    public_uid = fields.Char(required=True, readonly=True, copy=False, index=True)
    token_version = fields.Integer(default=1, readonly=True)
    state = fields.Selection(
        [("active","Active"),("used","Used"),("revoked","Revoked"),("transferred","Transferred")],
        required=True, default="active", tracking=True, index=True
    )
    transferred_to_id = fields.Many2one("res.partner", readonly=True)

    _uid_unique = models.Constraint("UNIQUE(public_uid)", "Ticket identifier must be unique.")

    def _qr_secret(self):
        secret = self.env["ir.config_parameter"].sudo().get_param("ems.ticket_qr_secret")
        if not secret:
            raise UserError("EMS QR signing secret is not configured.")
        return secret.encode()

    def _ensure_manage_rights(self):
        if not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("You are not allowed to manage EMS tickets.")

    @staticmethod
    def _b64(data):
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    def get_qr_envelope(self, ttl=60):
        self.ensure_one()
        self.check_access("read")
        if self.state != "active":
            raise UserError("Only active tickets can generate access credentials.")
        now = int(time.time())
        payload = {
            "uid": self.public_uid,
            "v": self.token_version,
            "iat": now,
            "exp": now + max(15, min(int(ttl), 300)),
            "event": self.event_id.id,
            "nonce": secrets.token_urlsafe(8),
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        sig = hmac.new(self._qr_secret(), raw, hashlib.sha256).digest()
        return f"{self._b64(raw)}.{self._b64(sig)}"

    @classmethod
    def _decode_b64(cls, value):
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

    def verify_qr_envelope(self, envelope):
        try:
            payload_b64, sig_b64 = envelope.split(".", 1)
            raw = self._decode_b64(payload_b64)
            received = self._decode_b64(sig_b64)
            expected = hmac.new(self._qr_secret(), raw, hashlib.sha256).digest()
            if not hmac.compare_digest(received, expected):
                return False, "bad_signature", {}
            payload = json.loads(raw.decode())
            if int(payload.get("exp", 0)) < int(time.time()):
                return False, "expired", payload
            return True, "ok", payload
        except (ValueError, TypeError, json.JSONDecodeError):
            return False, "malformed", {}

    def action_revoke(self):
        self._ensure_manage_rights()
        for ticket in self:
            if ticket.state != "active":
                raise UserError("Only active tickets can be revoked.")
            ticket.write({"state": "revoked", "token_version": ticket.token_version + 1})

    def action_rotate(self):
        self._ensure_manage_rights()
        for ticket in self:
            if ticket.state != "active":
                raise UserError("Only active tickets can rotate credentials.")
            ticket.write({"token_version": ticket.token_version + 1})

    def action_transfer(self, partner):
        self._ensure_manage_rights()
        self.ensure_one()
        if self.state != "active":
            raise UserError("Only active tickets can be transferred.")
        new_ticket = self.copy({
            "name": "/",
            "partner_id": partner.id,
            "public_uid": secrets.token_urlsafe(24),
            "token_version": 1,
            "state": "active",
        })
        self.write({"state": "transferred", "transferred_to_id": partner.id,
                    "token_version": self.token_version + 1})
        return new_ticket

    @classmethod
    def _new_uid(cls):
        return secrets.token_urlsafe(24)

    def _prepare_create_values(self, vals):
        vals = dict(vals)
        if not vals.get("public_uid"):
            vals["public_uid"] = self._new_uid()
        if not vals.get("name") or vals.get("name") == "/":
            vals["name"] = self.env["ir.sequence"].next_by_code("ems.ticket") or "/"
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._prepare_create_values(v) for v in vals_list])
