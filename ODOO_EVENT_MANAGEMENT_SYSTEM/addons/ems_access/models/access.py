import hashlib
import hmac
import logging
import secrets

import psycopg2

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

MAX_BATCH = 500
PBKDF2_ROUNDS = 200_000


class EmsScannerDevice(models.Model):
    _name = "ems.scanner.device"
    _description = "EMS Scanner Device"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True)
    device_uid = fields.Char(required=True, copy=False, index=True)
    event_ids = fields.Many2many("event.event", string="Authorized Events")
    active = fields.Boolean(default=True, tracking=True)
    last_seen_at = fields.Datetime(readonly=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company,
                                 required=True, index=True)
    # Only the salted hash is stored, and only administrators can read it.
    secret_salt = fields.Char(readonly=True, copy=False, groups="ems_core.group_ems_manager")
    secret_hash = fields.Char(readonly=True, copy=False, groups="ems_core.group_ems_manager")
    secret_set_on = fields.Datetime(readonly=True, copy=False,
                                    groups="ems_core.group_ems_manager")

    _device_uid_unique = models.Constraint("UNIQUE(device_uid)", "Device UID must be unique.")

    @staticmethod
    def _derive(secret, salt):
        return hashlib.pbkdf2_hmac(
            "sha256", secret.encode(), salt.encode(), PBKDF2_ROUNDS
        ).hex()

    def action_enroll(self):
        """Rotate the device secret and return it once, in clear, to the caller.

        The clear value is never stored, never logged and never sent by email;
        the operator copies it into the scanner at enrollment time.
        """
        self.ensure_one()
        if not self.env.user.has_group("ems_core.group_ems_manager"):
            raise AccessError("Only EMS administrators may enroll scanner devices.")
        secret = secrets.token_urlsafe(32)
        salt = secrets.token_urlsafe(16)
        self.sudo().write({
            "secret_salt": salt,
            "secret_hash": self._derive(secret, salt),
            "secret_set_on": fields.Datetime.now(),
        })
        self.message_post(body="Scanner device secret rotated.")
        return {
            "type": "ir.actions.act_window",
            "name": "Device Secret",
            "res_model": "ems.device.secret.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_device_id": self.id, "default_secret": secret},
        }

    def _verify_secret(self, secret):
        """Constant-time check of a presented device secret."""
        self.ensure_one()
        # sudo(): the hash columns are administrator-only by design, but any
        # authorised scan request must still be able to verify against them.
        device = self.sudo()
        if not device.secret_hash or not device.secret_salt or not secret:
            return False
        return hmac.compare_digest(
            device.secret_hash, self._derive(secret, device.secret_salt)
        )


class EmsDeviceSecretWizard(models.TransientModel):
    _name = "ems.device.secret.wizard"
    _description = "EMS Device Secret (shown once)"

    device_id = fields.Many2one("ems.scanner.device", readonly=True)
    secret = fields.Char(readonly=True)


class EmsScanLog(models.Model):
    _name = "ems.scan.log"
    _description = "EMS Scan Log"
    _order = "server_scanned_at desc, id desc"

    ticket_id = fields.Many2one("ems.ticket", ondelete="restrict", index=True)
    event_id = fields.Many2one(related="ticket_id.event_id", store=True, index=True)
    device_id = fields.Many2one("ems.scanner.device", required=True, ondelete="restrict",
                                index=True)
    client_scan_uid = fields.Char(required=True, index=True)
    client_scanned_at = fields.Datetime()
    server_scanned_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    result = fields.Selection([
        ("accepted", "Accepted"), ("duplicate", "Duplicate"), ("revoked", "Revoked"),
        ("expired", "Expired"), ("wrong_event", "Wrong Event"),
        ("device_revoked", "Device Revoked"), ("invalid", "Invalid")
    ], required=True, index=True)
    reason = fields.Char()
    company_id = fields.Many2one(related="device_id.company_id", store=True, index=True)

    # Idempotency is per device: two scanners may legitimately mint the same
    # local counter, so a global unique index would drop real scans.
    _device_client_uid_unique = models.Constraint(
        "UNIQUE(device_id, client_scan_uid)",
        "A scan UID may only be submitted once per device.",
    )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _find_existing(self, device, client_scan_uid):
        return self.search([
            ("device_id", "=", device.id),
            ("client_scan_uid", "=", client_scan_uid),
        ], limit=1)

    @api.model
    def _resolve_device(self, device_uid):
        if not device_uid:
            raise AccessError("A scanner device identifier is required.")
        # active_test=False on purpose: a revoked device must still resolve so the
        # attempt is written to the audit log as 'device_revoked' rather than
        # disappearing behind an "unknown device" error.
        device = self.env["ems.scanner.device"].with_context(active_test=False).search([
            ("device_uid", "=", device_uid),
            ("company_id", "in", self.env.companies.ids),
        ], limit=1)
        if not device:
            raise AccessError("Unknown scanner device.")
        return device

    def _lock_ticket(self, ticket):
        """Serialise concurrent scans of the same ticket.

        Two gates scanning one QR code at the same instant must not both see
        state 'active'; the row lock makes the loser wait and then observe
        'used', which it reports as a duplicate.
        """
        ticket.flush_recordset(["state"])
        self.env.cr.execute("SELECT id FROM ems_ticket WHERE id = %s FOR UPDATE", (ticket.id,))
        ticket.invalidate_recordset(["state"])

    def _evaluate(self, envelope, device):
        """Decide the outcome of one scan. Returns ``(ticket, result, reason)``."""
        Ticket = self.env["ems.ticket"]
        if not device.active:
            return Ticket, "device_revoked", "device_revoked"

        ok, reason, payload = Ticket.verify_qr_envelope(envelope)
        if not ok:
            return Ticket, ("expired" if reason == "expired" else "invalid"), reason

        ticket = Ticket.search([
            ("public_uid", "=", payload.get("uid")),
            ("company_id", "in", self.env.companies.ids),
        ], limit=1)
        if not ticket:
            return Ticket, "invalid", "unknown_ticket"

        # Gate authorization first: a device must never learn anything about a
        # ticket belonging to an event it is not posted at.
        try:
            claimed_event = int(payload.get("event", 0))
        except (TypeError, ValueError):
            return ticket, "invalid", "bad_event"
        if ticket.event_id.id != claimed_event or ticket.event_id not in device.event_ids:
            return ticket, "wrong_event", "wrong_event"

        self._lock_ticket(ticket)

        # Terminal ticket states outrank credential freshness: revoking a ticket
        # also bumps token_version, and "revoked"/"duplicate" tells the operator
        # far more than a generic "invalid" would.
        if ticket.state == "revoked":
            return ticket, "revoked", "ticket_revoked"
        if ticket.state == "used":
            return ticket, "duplicate", "already_used"
        if ticket.state != "active":
            return ticket, "invalid", f"state_{ticket.state}"

        try:
            claimed_version = int(payload.get("v", -1))
        except (TypeError, ValueError):
            return ticket, "invalid", "bad_version"
        if ticket.token_version != claimed_version:
            return ticket, "invalid", "stale_credential"

        if not ticket.event_id.ems_checkin_open:
            return ticket, "invalid", "checkin_closed"

        # sudo(): gate staff hold read-only rights on tickets of events they do
        # not organize; check-in is a controlled state change, not a general
        # write grant, so it is applied here and nowhere else.
        ticket.sudo().action_mark_used()
        return ticket, "accepted", "ok"

    # ------------------------------------------------------------------
    # Public API (re-checks authorization: reachable from controllers)
    # ------------------------------------------------------------------
    @api.model
    def validate_envelope(self, envelope, device_uid, client_scan_uid, client_scanned_at=None):
        if not self.env.su and not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("EMS scan permission required.")
        if not client_scan_uid or not isinstance(client_scan_uid, str):
            raise UserError("A client scan UID is required.")

        device = self._resolve_device(device_uid)

        existing = self._find_existing(device, client_scan_uid)
        if existing:
            return existing

        try:
            with self.env.cr.savepoint():
                ticket, result, reason = self._evaluate(envelope, device)
                log = self.create({
                    "ticket_id": ticket.id if ticket else False,
                    "device_id": device.id,
                    "client_scan_uid": client_scan_uid,
                    "client_scanned_at": client_scanned_at or False,
                    "result": result,
                    "reason": reason,
                })
        except psycopg2.errors.UniqueViolation:
            # A concurrent request for the same (device, client_scan_uid) won the
            # race; its log is the authoritative answer for both callers.
            existing = self._find_existing(device, client_scan_uid)
            if not existing:
                raise
            return existing

        # sudo(): telemetry only. Gate staff have read-only ACL on devices, and
        # widening that ACL to satisfy a heartbeat would grant device tampering.
        device.sudo().last_seen_at = fields.Datetime.now()
        return log

    @api.model
    def sync_offline_batch(self, device_uid, scans):
        """Replay a scanner's offline queue. One bad item never sinks the batch."""
        if not self.env.su and not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("EMS scan permission required.")
        if not isinstance(scans, list) or len(scans) > MAX_BATCH:
            raise UserError(f"Invalid offline batch (maximum {MAX_BATCH} scans).")

        # Resolve once so an unknown device fails the whole batch loudly.
        self._resolve_device(device_uid)

        results = []
        for item in scans:
            if not isinstance(item, dict):
                results.append({"client_scan_uid": None, "result": "invalid",
                                "reason": "malformed_item"})
                continue
            client_scan_uid = item.get("client_scan_uid")
            try:
                log = self.validate_envelope(
                    item.get("envelope", ""),
                    device_uid,
                    client_scan_uid,
                    item.get("client_scanned_at"),
                )
                results.append({
                    "client_scan_uid": log.client_scan_uid,
                    "result": log.result,
                    "reason": log.reason,
                    "server_scanned_at": fields.Datetime.to_string(log.server_scanned_at),
                })
            except (UserError, AccessError) as exc:
                _logger.info("Offline scan %s rejected: %s", client_scan_uid, exc)
                results.append({
                    "client_scan_uid": client_scan_uid,
                    "result": "invalid",
                    "reason": "rejected",
                })
        return results
