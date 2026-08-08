from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EventEvent(models.Model):
    _inherit = "event.event"

    ems_code = fields.Char(copy=False, readonly=True, index=True, tracking=True)
    ems_organizer_id = fields.Many2one(
        "res.users", string="EMS Organizer",
        default=lambda self: self.env.user, required=True, index=True, tracking=True
    )
    ems_company_id = fields.Many2one(
        "res.company", string="EMS Company",
        default=lambda self: self.env.company, required=True, index=True
    )
    ems_high_security = fields.Boolean(tracking=True)
    ems_checkin_open = fields.Boolean(default=False, tracking=True)
    ems_auto_issue_tickets = fields.Boolean(
        string="Auto-issue EMS tickets", default=False, tracking=True,
        help="Issue an EMS ticket automatically as soon as a registration is confirmed. "
             "Leave off for paid events so tickets follow the payment transaction."
    )
    ems_zone_ids = fields.One2many("ems.venue.zone", "event_id", string="Access Zones")
    ems_seats_remaining = fields.Integer(
        string="EMS Seats Remaining", compute="_compute_ems_seats_remaining"
    )

    _ems_code_unique = models.Constraint(
        "UNIQUE(ems_code)",
        "EMS event code must be unique.",
    )

    @api.depends("seats_limited", "seats_max", "seats_available")
    def _compute_ems_seats_remaining(self):
        """Remaining capacity, or -1 when the event is unlimited."""
        for event in self:
            event.ems_seats_remaining = event.seats_available if event.seats_limited else -1

    def ems_has_free_capacity(self, count=1):
        """True when ``count`` more attendees fit. Unlimited events always fit."""
        self.ensure_one()
        if not self.seats_limited:
            return True
        return self.seats_available >= count

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("ems_code"):
                vals["ems_code"] = self.env["ir.sequence"].next_by_code("ems.event") or "/"
        return super().create(vals_list)

    @api.constrains("date_begin", "date_end")
    def _check_ems_dates(self):
        for event in self:
            if event.date_begin and event.date_end and event.date_end < event.date_begin:
                raise ValidationError("Event end date must be after event start date.")

    @api.constrains("ems_checkin_open", "ems_high_security")
    def _check_ems_checkin_window(self):
        """High-security events may not have check-in opened before they exist."""
        for event in self:
            if event.ems_checkin_open and event.ems_high_security and not event.ems_zone_ids:
                raise ValidationError(
                    "A high-security event needs at least one access zone before "
                    "check-in can be opened."
                )
