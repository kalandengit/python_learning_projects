from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_seating")
class TestSeating(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create({
            "name": "Seated Show",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.other_event = cls.env["event.event"].create({
            "name": "Other Show",
            "date_begin": "2026-09-02 10:00:00",
            "date_end": "2026-09-02 18:00:00",
        })
        cls.buyer = cls.env["res.partner"].create({"name": "Buyer One"})
        cls.rival = cls.env["res.partner"].create({"name": "Buyer Two"})
        cls.seat = cls.env["ems.seat"].create({
            "event_id": cls.event.id, "section": "A", "row_label": "1", "seat_number": "1",
        })

    def _hold(self, partner=None, minutes=10):
        return self.env["ems.seat.hold"].hold_seat(self.seat, partner or self.buyer, minutes)

    def test_hold_marks_seat_held(self):
        hold = self._hold()
        self.assertEqual(hold.state, "held")
        self.seat.invalidate_recordset(["state"])
        self.assertEqual(self.seat.state, "held")

    def test_second_hold_on_live_hold_is_refused(self):
        self._hold()
        with self.assertRaises(UserError):
            self._hold(partner=self.rival)

    def test_hold_after_expiry_is_allowed(self):
        first = self._hold()
        first.expires_at = fields.Datetime.now() - timedelta(minutes=1)
        second = self._hold(partner=self.rival)
        self.assertEqual(second.state, "held")

    def test_hold_duration_is_clamped(self):
        hold = self._hold(minutes=9999)
        span = hold.expires_at - fields.Datetime.now()
        self.assertLessEqual(span, timedelta(minutes=30, seconds=5))

    def test_assign_to_ticket_sets_seat_label(self):
        ticket = self.env["ems.ticket"].create({
            "event_id": self.event.id, "partner_id": self.buyer.id,
        })
        hold = self._hold()
        hold.assign_to_ticket(ticket)
        self.assertEqual(hold.state, "assigned")
        self.assertEqual(hold.ticket_id, ticket)
        self.assertEqual(ticket.seat_label, self.seat.display_label)
        self.seat.invalidate_recordset(["state"])
        self.assertEqual(self.seat.state, "assigned")

    def test_seat_cannot_be_assigned_twice(self):
        first_ticket = self.env["ems.ticket"].create({
            "event_id": self.event.id, "partner_id": self.buyer.id,
        })
        second_ticket = self.env["ems.ticket"].create({
            "event_id": self.event.id, "partner_id": self.rival.id,
        })
        first_hold = self._hold()
        first_hold.assign_to_ticket(first_ticket)

        # A stale hold record must not be able to steal an assigned seat.
        stale = self.env["ems.seat.hold"].create({
            "seat_id": self.seat.id,
            "partner_id": self.rival.id,
            "expires_at": fields.Datetime.now() + timedelta(minutes=5),
        })
        with self.assertRaises(UserError):
            stale.assign_to_ticket(second_ticket)

    def test_expired_hold_cannot_be_assigned(self):
        ticket = self.env["ems.ticket"].create({
            "event_id": self.event.id, "partner_id": self.buyer.id,
        })
        hold = self._hold()
        hold.expires_at = fields.Datetime.now() - timedelta(minutes=1)
        with self.assertRaises(UserError):
            hold.assign_to_ticket(ticket)
        self.assertFalse(hold.ticket_id)
        # The refusal rolls back, so the cron is what records the expiry.
        self.env["ems.seat.hold"]._cron_expire_holds()
        self.assertEqual(hold.state, "expired")

    def test_cross_event_assignment_is_refused(self):
        foreign_ticket = self.env["ems.ticket"].create({
            "event_id": self.other_event.id, "partner_id": self.buyer.id,
        })
        hold = self._hold()
        with self.assertRaises(UserError):
            hold.assign_to_ticket(foreign_ticket)

    def test_cron_expires_stale_holds(self):
        hold = self._hold()
        hold.expires_at = fields.Datetime.now() - timedelta(minutes=1)
        self.env["ems.seat.hold"]._cron_expire_holds()
        self.assertEqual(hold.state, "expired")
        self.seat.invalidate_recordset(["state"])
        self.assertEqual(self.seat.state, "available")

    def test_zone_must_belong_to_event(self):
        foreign_zone = self.env["ems.venue.zone"].create({
            "name": "VIP", "code": "VIP", "event_id": self.other_event.id,
        })
        with self.assertRaises(ValidationError):
            self.seat.zone_id = foreign_zone

    def test_seat_availability_search(self):
        available = self.env["ems.seat"].search([("state", "=", "available")])
        self.assertIn(self.seat, available)
        self._hold()
        held = self.env["ems.seat"].search([("state", "=", "held")])
        self.assertIn(self.seat, held)
        available = self.env["ems.seat"].search([("state", "=", "available")])
        self.assertNotIn(self.seat, available)
