import logging
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

_logger = logging.getLogger(__name__)

MIN_OFFER_MINUTES = 5
DEFAULT_OFFER_MINUTES = 30


class EmsWaitlistEntry(models.Model):
    _name = "ems.waitlist.entry"
    _description = "EMS Waitlist Entry"
    _order = "priority desc, create_date, id"

    event_id = fields.Many2one("event.event", required=True, ondelete="cascade", index=True)
    partner_id = fields.Many2one("res.partner", required=True, index=True)
    priority = fields.Integer(default=0)
    state = fields.Selection([
        ("waiting", "Waiting"), ("offered", "Offered"), ("accepted", "Accepted"),
        ("expired", "Expired"), ("cancelled", "Cancelled")
    ], default="waiting", required=True, index=True)
    offer_token = fields.Char(copy=False, readonly=True, index=True, groups="ems_core.group_ems_user")
    offer_expires_at = fields.Datetime(index=True, readonly=True)
    offered_at = fields.Datetime(readonly=True)
    registration_id = fields.Many2one("event.registration", readonly=True, ondelete="set null")
    company_id = fields.Many2one(related="event_id.ems_company_id", store=True, index=True)

    _partner_event_unique = models.Constraint(
        "UNIQUE(event_id, partner_id)", "A partner can join an event waitlist only once."
    )

    def _ensure_manage_rights(self):
        # env.su covers the superuser and scheduled actions, which legitimately
        # act without holding an EMS group; everyone else must hold one.
        if self.env.su:
            return
        if not self.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("You are not allowed to manage the EMS waitlist.")

    def action_offer(self, minutes=DEFAULT_OFFER_MINUTES):
        """Offer a released seat to waiting entries with a time-boxed token."""
        self._ensure_manage_rights()
        now = fields.Datetime.now()
        for rec in self:
            if rec.state != "waiting":
                raise UserError("Only waiting entries can receive an offer.")
            rec.write({
                "state": "offered",
                "offer_token": secrets.token_urlsafe(24),
                "offered_at": now,
                "offer_expires_at": now + timedelta(
                    minutes=max(MIN_OFFER_MINUTES, int(minutes))
                ),
            })
        return True

    def action_accept(self, token):
        """Accept an offer and convert it into a real event registration."""
        self.ensure_one()
        # Serialise against the expiry cron and a second acceptance.
        self.env.cr.execute(
            "SELECT id FROM ems_waitlist_entry WHERE id = %s FOR UPDATE", (self.id,)
        )
        self.invalidate_recordset(["state", "offer_expires_at"])

        stored_token = self.sudo().offer_token
        if self.state != "offered" or not token or not stored_token:
            raise UserError("Invalid waitlist offer.")
        # Constant-time comparison: the token is a bearer credential.
        if not secrets.compare_digest(str(token), str(stored_token)):
            raise UserError("Invalid waitlist offer.")
        if self.offer_expires_at and self.offer_expires_at < fields.Datetime.now():
            # Refuse without writing: raising rolls the transaction back, so a
            # state change made here would be lost anyway. _cron_expire_offers
            # is what actually moves the entry to 'expired'.
            raise UserError("This waitlist offer has expired.")
        if not self.event_id.ems_has_free_capacity():
            raise UserError("The event is full again; the offer can no longer be accepted.")

        registration = self.env["event.registration"].sudo().create({
            "event_id": self.event_id.id,
            "partner_id": self.partner_id.id,
        })
        # The token is single-use: clear it as soon as it is spent.
        self.write({"state": "accepted", "registration_id": registration.id,
                    "offer_token": False})
        return registration

    def action_cancel(self):
        self._ensure_manage_rights()
        self.write({"state": "cancelled", "offer_token": False})
        return True

    # ------------------------------------------------------------------
    # Automation
    # ------------------------------------------------------------------
    @api.model
    def _cron_expire_offers(self):
        expired = self.search([
            ("state", "=", "offered"), ("offer_expires_at", "<", fields.Datetime.now())
        ], limit=1000)
        if expired:
            expired.write({"state": "expired", "offer_token": False})
            _logger.info("EMS: expired %s waitlist offers", len(expired))
        return len(expired)

    @api.model
    def _cron_promote(self):
        """Offer freed capacity to the head of each event's queue."""
        promoted = 0
        events = self.search([("state", "=", "waiting")]).event_id
        for event in events:
            if not event.seats_limited:
                free = self.search_count([("event_id", "=", event.id), ("state", "=", "waiting")])
            else:
                outstanding = self.search_count([
                    ("event_id", "=", event.id), ("state", "=", "offered"),
                ])
                free = event.seats_available - outstanding
            if free <= 0:
                continue
            candidates = self.search(
                [("event_id", "=", event.id), ("state", "=", "waiting")], limit=free
            )
            if candidates:
                candidates.sudo().action_offer()
                promoted += len(candidates)
        if promoted:
            _logger.info("EMS: promoted %s waitlist entries", promoted)
        return promoted
