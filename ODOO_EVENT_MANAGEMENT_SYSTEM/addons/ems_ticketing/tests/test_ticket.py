import time
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_ticketing")
class TestTicket(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "ems.ticket_qr_secret", "test-secret-not-production"
        )
        cls.event = cls.env["event.event"].create({
            "name": "Ticket Test",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.partner = cls.env["res.partner"].create({"name": "Attendee"})
        cls.other_partner = cls.env["res.partner"].create({"name": "New Owner"})

    def _ticket(self, partner=None):
        return self.env["ems.ticket"].create({
            "event_id": self.event.id,
            "partner_id": (partner or self.partner).id,
        })

    def test_create_assigns_sequence_and_uid(self):
        ticket = self._ticket()
        self.assertNotEqual(ticket.name, "/")
        self.assertTrue(ticket.name.startswith("TKT/"))
        self.assertTrue(ticket.public_uid)
        self.assertEqual(ticket.state, "active")

    def test_public_uid_is_unique_across_tickets(self):
        first, second = self._ticket(), self._ticket()
        self.assertNotEqual(first.public_uid, second.public_uid)

    def test_qr_envelope_roundtrip(self):
        ticket = self._ticket()
        envelope = ticket.get_qr_envelope()
        ok, reason, payload = ticket.verify_qr_envelope(envelope)
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")
        self.assertEqual(payload["uid"], ticket.public_uid)
        self.assertEqual(payload["event"], self.event.id)

    def test_envelope_expires(self):
        ticket = self._ticket()
        envelope = ticket.get_qr_envelope(ttl=15)
        with patch.object(time, "time", return_value=time.time() + 3600):
            ok, reason, _payload = ticket.verify_qr_envelope(envelope)
        self.assertFalse(ok)
        self.assertEqual(reason, "expired")

    def test_tampered_payload_fails_signature(self):
        ticket = self._ticket()
        payload_b64, signature = ticket.get_qr_envelope().split(".")
        other = self._ticket()
        other_payload = other.get_qr_envelope().split(".")[0]
        ok, reason, _payload = ticket.verify_qr_envelope(f"{other_payload}.{signature}")
        self.assertFalse(ok)
        self.assertEqual(reason, "bad_signature")
        self.assertNotEqual(payload_b64, other_payload)

    def test_missing_secret_is_refused(self):
        self.env["ir.config_parameter"].sudo().set_param("ems.ticket_qr_secret", "")
        ticket = self._ticket()
        with self.assertRaises(UserError):
            ticket.get_qr_envelope()

    def test_revoke_bumps_version_and_blocks_issuance(self):
        ticket = self._ticket()
        version = ticket.token_version
        ticket.action_revoke()
        self.assertEqual(ticket.state, "revoked")
        self.assertEqual(ticket.token_version, version + 1)
        with self.assertRaises(UserError):
            ticket.get_qr_envelope()
        with self.assertRaises(UserError):
            ticket.action_revoke()

    def test_rotate_keeps_ticket_active(self):
        ticket = self._ticket()
        version = ticket.token_version
        ticket.action_rotate()
        self.assertEqual(ticket.state, "active")
        self.assertEqual(ticket.token_version, version + 1)

    def test_transfer_issues_new_ticket_and_closes_old(self):
        ticket = self._ticket()
        new_ticket = ticket.action_transfer(self.other_partner)
        self.assertEqual(ticket.state, "transferred")
        self.assertEqual(ticket.transferred_to_id, self.other_partner)
        self.assertEqual(new_ticket.partner_id, self.other_partner)
        self.assertEqual(new_ticket.state, "active")
        self.assertEqual(new_ticket.token_version, 1)
        self.assertEqual(new_ticket.transferred_from_id, ticket)
        self.assertNotEqual(new_ticket.public_uid, ticket.public_uid)
        self.assertNotEqual(new_ticket.name, ticket.name)

    def test_transfer_to_same_partner_is_refused(self):
        ticket = self._ticket()
        with self.assertRaises(UserError):
            ticket.action_transfer(self.partner)

    def test_transfer_of_used_ticket_is_refused(self):
        ticket = self._ticket()
        ticket.action_mark_used()
        with self.assertRaises(UserError):
            ticket.action_transfer(self.other_partner)

    def test_registration_event_mismatch_is_refused(self):
        other_event = self.env["event.event"].create({
            "name": "Other", "date_begin": "2026-10-01 10:00:00",
            "date_end": "2026-10-01 18:00:00",
        })
        registration = self.env["event.registration"].create({
            "event_id": other_event.id, "partner_id": self.partner.id,
        })
        with self.assertRaises(ValidationError):
            self.env["ems.ticket"].create({
                "event_id": self.event.id,
                "registration_id": registration.id,
                "partner_id": self.partner.id,
            })

    def test_non_ems_user_cannot_manage_tickets(self):
        outsider = self.env["res.users"].create({
            "name": "Outsider", "login": "ticket.outsider@example.com",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        ticket = self._ticket()
        with self.assertRaises(AccessError):
            ticket.with_user(outsider).action_revoke()


@tagged("post_install", "-at_install", "ems_ticketing")
class TestRegistrationIssuance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create({
            "name": "Issuance Test",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
            "ems_auto_issue_tickets": True,
        })
        cls.partner = cls.env["res.partner"].create({"name": "Auto Attendee"})

    def test_confirmed_registration_issues_one_ticket(self):
        registration = self.env["event.registration"].create({
            "event_id": self.event.id, "partner_id": self.partner.id,
        })
        self.assertEqual(registration.ems_ticket_count, 1)

    def test_issuance_is_idempotent(self):
        registration = self.env["event.registration"].create({
            "event_id": self.event.id, "partner_id": self.partner.id,
        })
        registration.ems_issue_ticket()
        registration.ems_issue_ticket()
        self.assertEqual(registration.ems_ticket_count, 1)

    def test_no_auto_issue_when_disabled(self):
        self.event.ems_auto_issue_tickets = False
        registration = self.env["event.registration"].create({
            "event_id": self.event.id,
            "partner_id": self.env["res.partner"].create({"name": "Paid"}).id,
        })
        self.assertEqual(registration.ems_ticket_count, 0)

    def test_issuance_creates_partner_when_missing(self):
        registration = self.env["event.registration"].create({
            "event_id": self.event.id,
            "name": "Walk In",
            "email": "walk.in@example.com",
        })
        tickets = registration.ems_issue_ticket()
        self.assertTrue(tickets)
        self.assertTrue(registration.partner_id)
        self.assertEqual(tickets.partner_id, registration.partner_id)

    def test_cancelled_registration_is_not_issued(self):
        registration = self.env["event.registration"].create({
            "event_id": self.event.id,
            "partner_id": self.env["res.partner"].create({"name": "Cancelled"}).id,
        })
        registration.ems_ticket_ids.action_revoke()
        registration.action_cancel()
        issued_before = self.env["ems.ticket"].search_count([
            ("registration_id", "=", registration.id),
        ])
        registration.ems_issue_ticket()
        self.assertEqual(
            self.env["ems.ticket"].search_count([("registration_id", "=", registration.id)]),
            issued_before,
        )
