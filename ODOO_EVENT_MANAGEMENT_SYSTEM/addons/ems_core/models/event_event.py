from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EventEvent(models.Model):
    _inherit = "event.event"

    ems_code = fields.Char(copy=False, readonly=True, index=True, tracking=True)
    ems_organizer_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, required=True, index=True, tracking=True
    )
    ems_company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True, index=True
    )
    ems_high_security = fields.Boolean(tracking=True)
    ems_checkin_open = fields.Boolean(default=False, tracking=True)
    ems_zone_ids = fields.One2many("ems.venue.zone", "event_id", string="Access Zones")

    _ems_code_unique = models.Constraint(
        "UNIQUE(ems_code)",
        "EMS event code must be unique.",
    )

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
