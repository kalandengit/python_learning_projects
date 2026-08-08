from odoo import api, fields, models
from odoo.exceptions import AccessError


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

    _device_uid_unique = models.Constraint("UNIQUE(device_uid)", "Device UID must be unique.")


class EmsScanLog(models.Model):
    _name = "ems.scan.log"
    _description = "EMS Scan Log"
    _order = "server_scanned_at desc, id desc"

    ticket_id = fields.Many2one("ems.ticket", ondelete="restrict", index=True)
    event_id = fields.Many2one(related="ticket_id.event_id", store=True, index=True)
    device_id = fields.Many2one("ems.scanner.device", required=True, ondelete="restrict", index=True)
    client_scan_uid = fields.Char(required=True, index=True)
    client_scanned_at = fields.Datetime()
    server_scanned_at = fields.Datetime(required=True, default=fields.Datetime.now, index=True)
    result = fields.Selection([
        ("accepted","Accepted"),("duplicate","Duplicate"),("revoked","Revoked"),
        ("expired","Expired"),("wrong_event","Wrong Event"),("device_revoked","Device Revoked"),
        ("invalid","Invalid")
    ], required=True, index=True)
    reason = fields.Char()
    company_id = fields.Many2one(related="device_id.company_id", store=True, index=True)

    _client_uid_unique = models.Constraint(
        "UNIQUE(client_scan_uid)", "Client scan UID must be unique."
    )

    @api.model
    def validate_envelope(self, envelope, device_uid, client_scan_uid, client_scanned_at=None):
        if not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("EMS scan permission required.")

        existing = self.search([("client_scan_uid","=",client_scan_uid)], limit=1)
        if existing:
            return existing

        device = self.env["ems.scanner.device"].search(
            [("device_uid","=",device_uid),("company_id","in",self.env.companies.ids)], limit=1
        )
        if not device:
            raise AccessError("Unknown scanner device.")

        ok, reason, payload = self.env["ems.ticket"].verify_qr_envelope(envelope)
        ticket = self.env["ems.ticket"]
        result = "invalid"

        if not device.active:
            result, reason = "device_revoked", "device_revoked"
        elif not ok:
            result = "expired" if reason == "expired" else "invalid"
        else:
            ticket = self.env["ems.ticket"].search([
                ("public_uid","=",payload.get("uid")),
                ("company_id","in",self.env.companies.ids),
            ], limit=1)
            if not ticket or ticket.token_version != int(payload.get("v", -1)):
                result, reason = "invalid", "ticket_or_version"
            elif ticket.event_id.id != int(payload.get("event", 0)) or ticket.event_id not in device.event_ids:
                result, reason = "wrong_event", "wrong_event"
            elif ticket.state == "revoked":
                result, reason = "revoked", "ticket_revoked"
            elif ticket.state == "used":
                result, reason = "duplicate", "already_used"
            elif ticket.state != "active":
                result, reason = "invalid", f"state_{ticket.state}"
            else:
                result, reason = "accepted", "ok"
                ticket.write({"state": "used"})

        device.last_seen_at = fields.Datetime.now()
        return self.create({
            "ticket_id": ticket.id if ticket else False,
            "device_id": device.id,
            "client_scan_uid": client_scan_uid,
            "client_scanned_at": client_scanned_at,
            "result": result,
            "reason": reason,
        })

    @api.model
    def sync_offline_batch(self, device_uid, scans):
        if not isinstance(scans, list) or len(scans) > 500:
            raise AccessError("Invalid offline batch.")
        results = []
        for item in scans:
            log = self.validate_envelope(
                item.get("envelope", ""),
                device_uid,
                item.get("client_scan_uid", ""),
                item.get("client_scanned_at"),
            )
            results.append({
                "client_scan_uid": log.client_scan_uid,
                "result": log.result,
                "reason": log.reason,
                "server_scanned_at": log.server_scanned_at,
            })
        return results
