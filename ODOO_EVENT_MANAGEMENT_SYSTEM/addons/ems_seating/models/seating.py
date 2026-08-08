import secrets
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError


class EmsSeat(models.Model):
    _name = "ems.seat"
    _description = "EMS Seat"
    _order = "event_id, section, row_label, seat_number"

    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    section = fields.Char(required=True)
    row_label = fields.Char(required=True)
    seat_number = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)

    _seat_unique = models.Constraint(
        "UNIQUE(event_id, section, row_label, seat_number)",
        "Seat coordinates must be unique per event."
    )


class EmsSeatHold(models.Model):
    _name = "ems.seat.hold"
    _description = "EMS Seat Hold"

    seat_id = fields.Many2one("ems.seat", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    token = fields.Char(required=True, default=lambda self: secrets.token_urlsafe(24),
                        copy=False, readonly=True, index=True)
    expires_at = fields.Datetime(required=True, index=True)
    state = fields.Selection([
        ("held","Held"),("assigned","Assigned"),("released","Released"),("expired","Expired")
    ], default="held", required=True, index=True)
    ticket_id = fields.Many2one("ems.ticket", ondelete="set null")

    _token_unique = models.Constraint("UNIQUE(token)", "Seat hold token must be unique.")

    @api.model
    def hold_seat(self, seat, partner, minutes=10):
        now = fields.Datetime.now()
        active = self.search([
            ("seat_id","=",seat.id),("state","=","held"),("expires_at",">",now)
        ], limit=1)
        if active:
            raise UserError("Seat is temporarily held.")
        return self.create({
            "seat_id": seat.id,
            "partner_id": partner.id,
            "expires_at": now + timedelta(minutes=max(2, min(int(minutes), 30))),
        })

    def assign_to_ticket(self, ticket):
        self.ensure_one()
        if self.state != "held" or self.expires_at < fields.Datetime.now():
            raise UserError("Seat hold is not valid.")
        if ticket.event_id != self.seat_id.event_id:
            raise UserError("Seat and ticket belong to different events.")
        self.write({"state":"assigned","ticket_id":ticket.id})

    @api.model
    def _cron_expire_holds(self):
        self.search([
            ("state","=","held"),("expires_at","<",fields.Datetime.now())
        ], limit=2000).write({"state":"expired"})
