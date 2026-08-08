import secrets
from odoo import fields, models


class EmsBadge(models.Model):
    _name = "ems.badge"
    _description = "EMS Badge"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(required=True)
    badge_uid = fields.Char(required=True, default=lambda self: secrets.token_urlsafe(18),
                            readonly=True, copy=False, index=True)
    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    zone_ids = fields.Many2many("ems.venue.zone", string="Authorized Zones")
    valid_from = fields.Datetime()
    valid_until = fields.Datetime()
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)

    _badge_uid_unique = models.Constraint("UNIQUE(badge_uid)", "Badge UID must be unique.")
