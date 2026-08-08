from odoo import models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    def ems_issue_ticket(self):
        Ticket = self.env["ems.ticket"]
        issued = Ticket.browse()
        for registration in self:
            existing = Ticket.search([("registration_id", "=", registration.id),
                                      ("state", "=", "active")], limit=1)
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
