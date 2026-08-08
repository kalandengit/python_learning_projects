import base64
import io
import logging
import secrets

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:  # pragma: no cover - qrcode ships with Odoo's requirements
    qrcode = None


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
    ticket_id = fields.Many2one("ems.ticket", ondelete="set null", index=True)
    zone_ids = fields.Many2many("ems.venue.zone", string="Authorized Zones")
    valid_from = fields.Datetime()
    valid_until = fields.Datetime()
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)
    qr_image = fields.Binary(compute="_compute_qr_image", string="Badge QR")

    _badge_uid_unique = models.Constraint("UNIQUE(badge_uid)", "Badge UID must be unique.")

    @api.depends("badge_uid")
    def _compute_qr_image(self):
        for badge in self:
            badge.qr_image = badge._render_qr(badge.badge_uid) if badge.badge_uid else False

    @staticmethod
    def _render_qr(value):
        if qrcode is None:
            return False
        buffer = io.BytesIO()
        qrcode.make(value).save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    # ------------------------------------------------------------------
    # Zone policy
    # ------------------------------------------------------------------
    @api.constrains("zone_ids", "event_id")
    def _check_zone_event(self):
        """A badge may only grant zones belonging to its own event."""
        for badge in self:
            foreign = badge.zone_ids.filtered(lambda z: z.event_id != badge.event_id)
            if foreign:
                raise ValidationError(
                    "These zones do not belong to the badge's event: %s"
                    % ", ".join(foreign.mapped("name"))
                )

    @api.constrains("valid_from", "valid_until")
    def _check_validity_window(self):
        for badge in self:
            if badge.valid_from and badge.valid_until and badge.valid_until < badge.valid_from:
                raise ValidationError("Badge validity must end after it starts.")

    def is_valid_now(self, when=None):
        """True when the badge is active and inside its validity window."""
        self.ensure_one()
        when = when or fields.Datetime.now()
        if not self.active:
            return False
        if self.valid_from and when < self.valid_from:
            return False
        if self.valid_until and when > self.valid_until:
            return False
        return True

    def allows_zone(self, zone, when=None):
        """Authoritative zone check used by access control."""
        self.ensure_one()
        if not self.is_valid_now(when=when):
            return False
        return zone in self.zone_ids

    def action_print_badge(self):
        if not self:
            raise UserError("Select at least one badge to print.")
        return self.env.ref("ems_badge.action_report_ems_badge").report_action(self)
