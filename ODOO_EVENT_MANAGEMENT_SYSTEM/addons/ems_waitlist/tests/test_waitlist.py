from datetime import timedelta

import psycopg2

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install", "ems_waitlist")
class TestWaitlist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create({
            "name": "Sold Out Show",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
            "seats_limited": True,
            "seats_max": 1,
        })
        cls.first = cls.env["res.partner"].create({"name": "First In Line"})
        cls.second = cls.env["res.partner"].create({"name": "Second In Line"})

    def _entry(self, partner=None, priority=0):
        return self.env["ems.waitlist.entry"].create({
            "event_id": self.event.id,
            "partner_id": (partner or self.first).id,
            "priority": priority,
        })

    @mute_logger("odoo.sql_db")
    def test_unique_partner_event(self):
        self._entry()
        with self.assertRaises(psycopg2.errors.UniqueViolation), self.cr.savepoint():
            self._entry()

    def test_offer_sets_token_and_deadline(self):
        entry = self._entry()
        entry.action_offer(minutes=45)
        self.assertEqual(entry.state, "offered")
        self.assertTrue(entry.offer_token)
        self.assertTrue(entry.offer_expires_at > fields.Datetime.now())

    def test_offer_minimum_window_is_enforced(self):
        entry = self._entry()
        entry.action_offer(minutes=1)
        span = entry.offer_expires_at - fields.Datetime.now()
        self.assertGreater(span, timedelta(minutes=4))

    def test_accept_creates_registration_and_burns_token(self):
        entry = self._entry()
        entry.action_offer()
        token = entry.offer_token
        registration = entry.action_accept(token)
        self.assertEqual(entry.state, "accepted")
        self.assertEqual(registration.partner_id, self.first)
        self.assertEqual(entry.registration_id, registration)
        self.assertFalse(entry.offer_token)
        # The spent token cannot be replayed.
        with self.assertRaises(UserError):
            entry.action_accept(token)

    def test_wrong_token_is_refused(self):
        entry = self._entry()
        entry.action_offer()
        with self.assertRaises(UserError):
            entry.action_accept("not-the-token")
        self.assertEqual(entry.state, "offered")

    def test_empty_token_is_refused(self):
        entry = self._entry()
        entry.action_offer()
        with self.assertRaises(UserError):
            entry.action_accept(False)

    def test_accept_after_deadline_is_refused(self):
        entry = self._entry()
        entry.action_offer()
        token = entry.offer_token
        entry.offer_expires_at = fields.Datetime.now() - timedelta(minutes=1)
        with self.assertRaises(UserError):
            entry.action_accept(token)
        # The refusal rolls back, so the cron is what records the expiry.
        self.env["ems.waitlist.entry"]._cron_expire_offers()
        self.assertEqual(entry.state, "expired")
        self.assertFalse(entry.registration_id)

    def test_accept_is_refused_when_event_refilled(self):
        entry = self._entry()
        entry.action_offer()
        token = entry.offer_token
        # Somebody else takes the last seat before the offer is accepted.
        self.env["event.registration"].create({
            "event_id": self.event.id, "partner_id": self.second.id,
        })
        self.event.invalidate_recordset()
        with self.assertRaises(UserError):
            entry.action_accept(token)

    def test_cron_expires_stale_offers(self):
        entry = self._entry()
        entry.action_offer()
        entry.offer_expires_at = fields.Datetime.now() - timedelta(minutes=1)
        self.env["ems.waitlist.entry"]._cron_expire_offers()
        self.assertEqual(entry.state, "expired")
        self.assertFalse(entry.sudo().offer_token)

    def test_cron_promotes_only_available_capacity(self):
        first = self._entry(self.first, priority=10)
        second = self._entry(self.second)
        promoted = self.env["ems.waitlist.entry"]._cron_promote()
        self.assertEqual(promoted, 1)
        self.assertEqual(first.state, "offered")
        self.assertEqual(second.state, "waiting")

    def test_cron_promote_respects_outstanding_offers(self):
        self._entry(self.first, priority=10).action_offer()
        self._entry(self.second)
        self.assertEqual(self.env["ems.waitlist.entry"]._cron_promote(), 0)

    def test_cancel_clears_token(self):
        entry = self._entry()
        entry.action_offer()
        entry.action_cancel()
        self.assertEqual(entry.state, "cancelled")
        self.assertFalse(entry.sudo().offer_token)
