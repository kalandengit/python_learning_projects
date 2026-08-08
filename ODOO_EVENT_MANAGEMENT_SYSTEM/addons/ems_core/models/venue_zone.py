from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EmsVenueZone(models.Model):
    _name = "ems.venue.zone"
    _description = "EMS Venue Zone"
    _order = "event_id, sequence, id"

    name = fields.Char(required=True, index=True)
    code = fields.Char(required=True, index=True)
    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)
    sequence = fields.Integer(default=10)
    capacity = fields.Integer(default=0)
    active = fields.Boolean(default=True)

    _event_code_unique = models.Constraint(
        "UNIQUE(event_id, code)",
        "Zone code must be unique per event.",
    )

    @api.constrains("capacity")
    def _check_capacity(self):
        for rec in self:
            if rec.capacity < 0:
                raise ValidationError("Zone capacity cannot be negative.")
