from odoo import fields, models


class EmsPaymentLink(models.Model):
    _name = "ems.payment.link"
    _description = "EMS Payment Link"
    _order = "create_date desc"

    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    registration_id = fields.Many2one("event.registration", ondelete="set null", index=True)
    transaction_id = fields.Many2one("payment.transaction", ondelete="set null", index=True)
    state = fields.Selection([
        ("pending","Pending"),("paid","Paid"),("cancelled","Cancelled"),("refunded","Refunded")
    ], default="pending", required=True, index=True)
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one("res.currency", required=True)
    partner_id = fields.Many2one("res.partner", required=True)
