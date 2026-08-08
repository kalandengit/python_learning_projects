import secrets
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError


class EmsWaitlistEntry(models.Model):
    _name = "ems.waitlist.entry"
    _description = "EMS Waitlist Entry"
    _order = "priority desc, create_date, id"

    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    priority = fields.Integer(default=0)
    state = fields.Selection([
        ("waiting","Waiting"),("offered","Offered"),("accepted","Accepted"),
        ("expired","Expired"),("cancelled","Cancelled")
    ], default="waiting", required=True, index=True)
    offer_token = fields.Char(copy=False, readonly=True, index=True)
    offer_expires_at = fields.Datetime(index=True)
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)

    _partner_event_unique = models.Constraint(
        "UNIQUE(event_id, partner_id)", "A partner can join an event waitlist only once."
    )

    def action_offer(self, minutes=30):
        for rec in self:
            if rec.state != "waiting":
                raise UserError("Only waiting entries can receive an offer.")
            rec.write({
                "state": "offered",
                "offer_token": secrets.token_urlsafe(24),
                "offer_expires_at": fields.Datetime.now() + timedelta(minutes=max(5, int(minutes))),
            })

    def action_accept(self, token):
        self.ensure_one()
        if self.state != "offered" or not token or token != self.offer_token:
            raise UserError("Invalid waitlist offer.")
        if self.offer_expires_at and self.offer_expires_at < fields.Datetime.now():
            self.state = "expired"
            raise UserError("This waitlist offer has expired.")
        self.state = "accepted"

    @api.model
    def _cron_expire_offers(self):
        expired = self.search([
            ("state","=","offered"),("offer_expires_at","<",fields.Datetime.now())
        ], limit=1000)
        expired.write({"state":"expired"})
