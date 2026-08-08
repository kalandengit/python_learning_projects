import base64
import io
import logging

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:  # pragma: no cover - qrcode ships with Odoo's requirements
    qrcode = None


class EmsCustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "ems_ticket_count" in counters:
            values["ems_ticket_count"] = request.env["ems.ticket"].search_count(
                [("partner_id", "=", request.env.user.partner_id.id)]
            )
        return values


class EmsPortalController(http.Controller):
    """Attendee-facing ticket pages.

    Every route re-resolves the ticket through a partner-scoped domain, so
    ownership is enforced by the query itself and not only by the record rule.
    """

    def _own_ticket(self, uid):
        return request.env["ems.ticket"].search([
            ("public_uid", "=", uid),
            ("partner_id", "=", request.env.user.partner_id.id),
        ], limit=1)

    @staticmethod
    def _ticket_values(ticket):
        """Display values for one ticket.

        Portal users have no read access to event.event, so the few event fields
        an attendee needs are read here with an explicitly narrow elevation.
        Ownership was already established by the partner-scoped search above, and
        only these four scalars are ever exposed - never the event record itself.
        """
        event = ticket.event_id.sudo()
        return {
            "name": ticket.name,
            "public_uid": ticket.public_uid,
            "state": ticket.state,
            "seat_label": ticket.seat_label,
            "attendee": ticket.partner_id.name,
            "event_name": event.name,
            "event_date_begin": event.date_begin,
            "event_date_end": event.date_end,
        }

    @http.route("/my/ems/tickets", type="http", auth="user", website=True)
    def my_ems_tickets(self, **kwargs):
        tickets = request.env["ems.ticket"].search(
            [("partner_id", "=", request.env.user.partner_id.id)],
            order="create_date desc",
        )
        return request.render("ems_website.portal_my_ems_tickets", {
            "tickets": [self._ticket_values(ticket) for ticket in tickets],
            "page_name": "ems_tickets",
        })

    @http.route("/my/ems/ticket/<string:uid>", type="http", auth="user", website=True)
    def my_ems_ticket(self, uid, **kwargs):
        ticket = self._own_ticket(uid)
        if not ticket:
            return request.not_found()
        envelope = error = None
        if ticket.state == "active":
            try:
                envelope = ticket.get_qr_envelope()
            except Exception as exc:  # noqa: BLE001 - surfaced as a page notice
                _logger.warning("Could not issue QR envelope for ticket %s: %s", ticket.id, exc)
                error = "The access credential could not be generated. Contact the organizer."
        return request.render("ems_website.portal_ems_ticket", {
            "ticket": self._ticket_values(ticket),
            "has_envelope": bool(envelope),
            "error": error,
            "page_name": "ems_tickets",
        })

    @http.route("/my/ems/ticket/<string:uid>/qr.png", type="http", auth="user")
    def my_ems_ticket_qr(self, uid, **kwargs):
        """Render the credential as an image.

        The signed envelope is never placed in a URL or a query string: it is
        generated here and returned only inside the image body, so it cannot
        leak through browser history, referrers or web-server access logs.
        """
        ticket = self._own_ticket(uid)
        if not ticket or ticket.state != "active" or qrcode is None:
            return request.not_found()
        buffer = io.BytesIO()
        qrcode.make(ticket.get_qr_envelope()).save(buffer, format="PNG")
        return request.make_response(buffer.getvalue(), headers=[
            ("Content-Type", "image/png"),
            # Short-lived credential: never store it in any cache.
            ("Cache-Control", "no-store, max-age=0"),
            ("Pragma", "no-cache"),
        ])
