import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class EventRegistration(models.Model):
    _inherit = "event.registration"

    ems_ticket_ids = fields.One2many("ems.ticket", "registration_id", string="EMS Tickets")
    ems_ticket_count = fields.Integer(compute="_compute_ems_ticket_count")

    @api.depends("ems_ticket_ids")
    def _compute_ems_ticket_count(self):
        for registration in self:
            registration.ems_ticket_count = len(registration.ems_ticket_ids)

    def ems_issue_ticket(self):
        """Issue exactly one active EMS ticket per registration (idempotent)."""
        Ticket = self.env["ems.ticket"]
        issued = Ticket.browse()
        for registration in self:
            if registration.state == "cancel":
                continue
            existing = Ticket.search([
                ("registration_id", "=", registration.id),
                ("state", "in", ("active", "used")),
            ], limit=1)
            if existing:
                issued |= existing
                continue
            partner = registration.partner_id
            if not partner:
                partner = self.env["res.partner"].create({
                    "name": registration.name or registration.email or "Event Attendee",
                    "email": registration.email,
                    "phone": registration.phone,
                })
                registration.partner_id = partner
            issued |= Ticket.create({
                "event_id": registration.event_id.id,
                "registration_id": registration.id,
                "partner_id": partner.id,
            })
        return issued

    def _ems_should_auto_issue(self):
        """Auto-issuance is opt-in per event so paid flows stay payment-driven."""
        self.ensure_one()
        return bool(self.event_id.ems_auto_issue_tickets)

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") in ("open", "done"):
            to_issue = self.filtered(lambda r: r._ems_should_auto_issue())
            if to_issue:
                to_issue.ems_issue_ticket()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        to_issue = registrations.filtered(
            lambda r: r.state in ("open", "done") and r._ems_should_auto_issue()
        )
        if to_issue:
            to_issue.ems_issue_ticket()
        return registrations

    def action_view_ems_tickets(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "EMS Tickets",
            "res_model": "ems.ticket",
            "view_mode": "list,form",
            "domain": [("registration_id", "=", self.id)],
        }
