import logging
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

MIN_HOLD_MINUTES = 2
MAX_HOLD_MINUTES = 30


class EmsSeat(models.Model):
    _name = "ems.seat"
    _description = "EMS Seat"
    _order = "event_id, section, row_label, seat_number"
    _rec_name = "display_label"

    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    section = fields.Char(required=True)
    row_label = fields.Char(required=True)
    seat_number = fields.Char(required=True)
    display_label = fields.Char(compute="_compute_display_label", store=True)
    zone_id = fields.Many2one("ems.venue.zone", ondelete="set null", index=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)

    state = fields.Selection(
        [("available", "Available"), ("held", "Held"), ("assigned", "Assigned")],
        compute="_compute_state", search="_search_state", string="Availability"
    )
    hold_ids = fields.One2many("ems.seat.hold", "seat_id")

    _seat_unique = models.Constraint(
        "UNIQUE(event_id, section, row_label, seat_number)",
        "Seat coordinates must be unique per event."
    )

    @api.depends("section", "row_label", "seat_number")
    def _compute_display_label(self):
        for seat in self:
            seat.display_label = f"{seat.section or ''}-{seat.row_label or ''}-{seat.seat_number or ''}"

    @api.depends("hold_ids.state", "hold_ids.expires_at")
    def _compute_state(self):
        now = fields.Datetime.now()
        for seat in self:
            holds = seat.hold_ids
            if any(h.state == "assigned" for h in holds):
                seat.state = "assigned"
            elif any(h.state == "held" and h.expires_at and h.expires_at > now for h in holds):
                seat.state = "held"
            else:
                seat.state = "available"

    def _search_state(self, operator, value):
        if operator not in ("=", "!=") or value not in ("available", "held", "assigned"):
            raise UserError("Unsupported seat availability search.")
        now = fields.Datetime.now()
        assigned = self.env["ems.seat.hold"].search([("state", "=", "assigned")]).seat_id.ids
        held = [
            seat_id
            for seat_id in self.env["ems.seat.hold"].search([
                ("state", "=", "held"), ("expires_at", ">", now),
            ]).seat_id.ids
            if seat_id not in assigned
        ]
        if value == "assigned":
            positive = ("id", "in", assigned)
        elif value == "held":
            positive = ("id", "in", held)
        else:
            positive = ("id", "not in", assigned + held)

        if operator == "=":
            return [positive]
        inverted = "not in" if positive[1] == "in" else "in"
        return [(positive[0], inverted, positive[2])]

    @api.constrains("zone_id", "event_id")
    def _check_zone_event(self):
        for seat in self:
            if seat.zone_id and seat.zone_id.event_id != seat.event_id:
                raise ValidationError("A seat zone must belong to the seat's event.")


class EmsSeatHold(models.Model):
    _name = "ems.seat.hold"
    _description = "EMS Seat Hold"
    _order = "create_date desc, id desc"

    seat_id = fields.Many2one("ems.seat", required=True, ondelete="cascade", index=True)
    event_id = fields.Many2one(related="seat_id.event_id", store=True, index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    token = fields.Char(required=True, default=lambda self: secrets.token_urlsafe(24),
                        copy=False, readonly=True, index=True)
    expires_at = fields.Datetime(required=True, index=True)
    state = fields.Selection([
        ("held", "Held"), ("assigned", "Assigned"), ("released", "Released"), ("expired", "Expired")
    ], default="held", required=True, index=True)
    ticket_id = fields.Many2one("ems.ticket", ondelete="set null")
    company_id = fields.Many2one(related="seat_id.company_id", store=True, index=True)

    _token_unique = models.Constraint("UNIQUE(token)", "Seat hold token must be unique.")

    @api.model
    def hold_seat(self, seat, partner, minutes=10):
        """Take an exclusive temporary hold on a seat.

        The seat row is locked first, so two concurrent buyers cannot both pass
        the "is it free?" check and end up holding the same seat.
        """
        if not seat or not partner:
            raise UserError("A seat and a partner are required to hold a seat.")
        seat.ensure_one()
        # Raw SQL bypasses the ORM cache: flush pending writes first so the lock
        # and the checks below see the same state the database does.
        self.env.flush_all()
        self.env.cr.execute("SELECT id FROM ems_seat WHERE id = %s FOR UPDATE", (seat.id,))

        now = fields.Datetime.now()
        blocking = self.search([
            ("seat_id", "=", seat.id),
            "|",
                ("state", "=", "assigned"),
                "&", ("state", "=", "held"), ("expires_at", ">", now),
        ], limit=1)
        if blocking:
            raise UserError("Seat is already held or assigned.")

        return self.create({
            "seat_id": seat.id,
            "partner_id": partner.id,
            "expires_at": now + timedelta(
                minutes=max(MIN_HOLD_MINUTES, min(int(minutes), MAX_HOLD_MINUTES))
            ),
        })

    def assign_to_ticket(self, ticket):
        """Convert a live hold into a permanent seat assignment."""
        self.ensure_one()
        self.env.flush_all()
        self.env.cr.execute("SELECT id FROM ems_seat_hold WHERE id = %s FOR UPDATE", (self.id,))
        self.invalidate_recordset(["state", "expires_at"])

        if self.state != "held":
            raise UserError("Seat hold is not valid.")
        if self.expires_at and self.expires_at < fields.Datetime.now():
            # Refuse without writing: raising rolls the transaction back, so the
            # state change would be lost. _cron_expire_holds owns that transition.
            raise UserError("Seat hold has expired.")
        if ticket.event_id != self.seat_id.event_id:
            raise UserError("Seat and ticket belong to different events.")
        if self.search_count([("seat_id", "=", self.seat_id.id), ("state", "=", "assigned")]):
            raise UserError("Seat has already been assigned.")

        self.write({"state": "assigned", "ticket_id": ticket.id})
        ticket.sudo().write({"seat_label": self.seat_id.display_label})
        return True

    def action_release(self):
        for hold in self:
            if hold.state == "assigned":
                raise UserError("Assigned seats must be released by cancelling the ticket.")
            hold.state = "released"
        return True

    @api.model
    def _cron_expire_holds(self):
        expired = self.search([
            ("state", "=", "held"), ("expires_at", "<", fields.Datetime.now())
        ], limit=2000)
        if expired:
            expired.write({"state": "expired"})
            _logger.info("EMS: expired %s seat holds", len(expired))
        return len(expired)
