import json
import logging
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

RETENTION_PARAM = "ems.gdpr.scan_log_retention_days"
DEFAULT_RETENTION_DAYS = 730


class ResPartner(models.Model):
    _inherit = "res.partner"

    ems_legal_hold = fields.Boolean(
        string="EMS Legal Hold", copy=False, tracking=True,
        help="Blocks EMS anonymization and retention purging for this contact, "
             "for example while a dispute or investigation is open."
    )
    ems_legal_hold_reason = fields.Char(copy=False)
    ems_anonymized_on = fields.Datetime(readonly=True, copy=False)


class EmsGdprRequest(models.Model):
    _name = "ems.gdpr.request"
    _description = "EMS GDPR Request"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    partner_id = fields.Many2one("res.partner", required=True, index=True)
    request_type = fields.Selection([("export", "Export"), ("anonymize", "Anonymize")],
                                    required=True, default="export")
    state = fields.Selection([("draft", "Draft"), ("done", "Done"), ("rejected", "Rejected")],
                             default="draft", required=True, tracking=True)
    result_json = fields.Text(readonly=True)
    rejection_reason = fields.Char(readonly=True)
    processed_on = fields.Datetime(readonly=True)

    def _ensure_officer(self):
        # env.su covers the superuser and scheduled actions, which legitimately
        # act without holding an EMS group; everyone else must hold one.
        if self.env.su:
            return
        if not self.env.user.has_group("ems_core.group_ems_manager"):
            raise AccessError("Only EMS administrators may process GDPR requests.")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _collect_export(self, partner):
        """Subject-access payload.

        Deliberately excludes EMS security material: QR signing secrets, device
        secrets and scan-log internals are not the data subject's personal data
        and must not leak through an export.
        """
        tickets = self.env["ems.ticket"].search([("partner_id", "=", partner.id)])
        badges = self.env["ems.badge"].search([("partner_id", "=", partner.id)])
        waitlist = self.env["ems.waitlist.entry"].search([("partner_id", "=", partner.id)])
        registrations = self.env["event.registration"].search([("partner_id", "=", partner.id)])
        scans = self.env["ems.scan.log"].search([("ticket_id", "in", tickets.ids)])

        return {
            "partner": {
                "id": partner.id, "name": partner.name,
                "email": partner.email, "phone": partner.phone,
            },
            "registrations": [{
                "event": r.event_id.name, "state": r.state,
                "created": fields.Datetime.to_string(r.create_date),
            } for r in registrations],
            "tickets": [{
                "name": t.name, "event": t.event_id.name, "state": t.state,
                "created": fields.Datetime.to_string(t.create_date),
            } for t in tickets],
            "badges": [{
                "name": b.name, "event": b.event_id.name,
                "zones": b.zone_ids.mapped("name"),
            } for b in badges],
            "waitlist": [{
                "event": w.event_id.name, "state": w.state,
            } for w in waitlist],
            "check_ins": [{
                "event": s.event_id.name, "result": s.result,
                "at": fields.Datetime.to_string(s.server_scanned_at),
            } for s in scans],
        }

    def action_export(self):
        self._ensure_officer()
        self.ensure_one()
        if self.state != "draft":
            raise UserError("This request has already been processed.")
        data = self._collect_export(self.partner_id)
        self.write({
            "state": "done",
            "result_json": json.dumps(data, ensure_ascii=False, indent=2, default=str),
            "processed_on": fields.Datetime.now(),
        })
        return True

    # ------------------------------------------------------------------
    # Anonymization
    # ------------------------------------------------------------------
    def action_anonymize(self):
        self._ensure_officer()
        self.ensure_one()
        if self.state != "draft":
            raise UserError("This request has already been processed.")
        partner = self.partner_id

        if partner.ems_legal_hold:
            # Recorded as a rejection rather than raised: a UserError would roll
            # the transaction back and lose exactly the audit trail a refused
            # erasure request needs to leave behind.
            self.write({
                "state": "rejected",
                "rejection_reason": "Contact is under legal hold: %s"
                                    % (partner.ems_legal_hold_reason or "no reason recorded"),
                "processed_on": fields.Datetime.now(),
            })
            self.message_post(
                body="Anonymization refused: the contact is under legal hold."
            )
            _logger.info("EMS GDPR: anonymization refused for partner %s (legal hold)",
                         partner.id)
            return False
        if partner.is_company:
            raise UserError("Company contacts require manual review.")

        active_tickets = self.env["ems.ticket"].search_count([
            ("partner_id", "=", partner.id), ("state", "=", "active"),
        ])
        if active_tickets:
            raise UserError(
                "This contact still holds %s active ticket(s). Revoke or let them "
                "expire before anonymizing." % active_tickets
            )

        # Scrub direct identifiers while keeping referential integrity, so
        # attendance counts and financial records stay auditable.
        # sudo(): an EMS administrator is not automatically a contacts manager,
        # but erasure is precisely their job. Authorization was already asserted
        # by _ensure_officer above, and the scope is this one partner record.
        partner.sudo().write({
            "name": f"Anonymized Partner {partner.id}",
            "email": False, "phone": False,
            "street": False, "street2": False, "zip": False, "city": False,
            "website": False, "comment": False,
            "ems_anonymized_on": fields.Datetime.now(),
        })
        self.write({
            "state": "done",
            "result_json": json.dumps({"status": "anonymized", "partner_id": partner.id}),
            "processed_on": fields.Datetime.now(),
        })
        return True

    # ------------------------------------------------------------------
    # Retention
    # ------------------------------------------------------------------
    @api.model
    def _retention_days(self):
        raw = self.env["ir.config_parameter"].sudo().get_param(
            RETENTION_PARAM, DEFAULT_RETENTION_DAYS
        )
        try:
            days = int(raw)
        except (TypeError, ValueError):
            _logger.warning("Invalid %s (%r); falling back to %s days",
                            RETENTION_PARAM, raw, DEFAULT_RETENTION_DAYS)
            return DEFAULT_RETENTION_DAYS
        return days if days > 0 else 0

    @api.model
    def _cron_apply_retention(self):
        """Purge check-in telemetry past its retention window.

        Records attached to a contact under legal hold are always kept.
        Retention of 0 disables purging entirely.
        """
        days = self._retention_days()
        if not days:
            return 0
        cutoff = fields.Datetime.now() - timedelta(days=days)
        stale = self.env["ems.scan.log"].sudo().search([
            ("server_scanned_at", "<", cutoff),
        ], limit=5000)
        held = stale.filtered(lambda s: s.ticket_id.partner_id.ems_legal_hold)
        purgeable = stale - held
        count = len(purgeable)
        if count:
            purgeable.unlink()
            _logger.info("EMS GDPR: purged %s scan logs older than %s days", count, days)
        if held:
            _logger.info("EMS GDPR: kept %s scan logs under legal hold", len(held))
        return count
