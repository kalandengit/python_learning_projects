from odoo import http
from odoo.http import request


class EmsPortalController(http.Controller):

    @http.route("/my/ems/tickets", type="http", auth="user", website=True)
    def my_ems_tickets(self, **kwargs):
        tickets = request.env["ems.ticket"].search([
            ("partner_id","=",request.env.user.partner_id.id)
        ], order="create_date desc")
        return request.render("ems_website.portal_my_ems_tickets", {"tickets": tickets})

    @http.route("/my/ems/ticket/<string:uid>", type="http", auth="user", website=True)
    def my_ems_ticket(self, uid, **kwargs):
        ticket = request.env["ems.ticket"].search([
            ("public_uid","=",uid),
            ("partner_id","=",request.env.user.partner_id.id),
        ], limit=1)
        if not ticket:
            return request.not_found()
        envelope = ticket.get_qr_envelope()
        return request.render("ems_website.portal_ems_ticket", {
            "ticket": ticket, "envelope": envelope
        })
