from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_notifications")
class TestNotificationQueue(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create({
            "name": "Notified Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Notified Attendee", "email": "notified@example.com",
        })
        cls.ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id, "partner_id": cls.partner.id,
        })

    def _queue(self, **overrides):
        vals = {"channel": "email", "recipient": "notified@example.com",
                "subject": "Hello", "body": "<p>Hi</p>"}
        vals.update(overrides)
        return self.env["ems.notification"].create(vals)

    def test_email_is_sent_and_marked(self):
        notification = self._queue()
        self.env["ems.notification"]._cron_process()
        self.assertEqual(notification.state, "sent")
        self.assertTrue(notification.sent_at)
        self.assertFalse(notification.last_error)

    def test_failure_backs_off_then_gives_up(self):
        notification = self._queue()
        with patch.object(
            type(self.env["ems.notification"]), "_send_one",
            side_effect=RuntimeError("smtp down"),
        ):
            for _ in range(5):
                notification.next_attempt_at = False
                self.env["ems.notification"]._cron_process()
        self.assertEqual(notification.state, "failed")
        self.assertEqual(notification.attempt_count, 5)
        self.assertIn("smtp down", notification.last_error)

    def test_backoff_defers_next_attempt(self):
        notification = self._queue()
        with patch.object(
            type(self.env["ems.notification"]), "_send_one",
            side_effect=RuntimeError("smtp down"),
        ):
            self.env["ems.notification"]._cron_process()
        self.assertEqual(notification.state, "pending")
        self.assertGreater(notification.next_attempt_at, fields.Datetime.now())

    def test_future_attempts_are_not_picked_up(self):
        notification = self._queue()
        notification.next_attempt_at = fields.Datetime.now() + timedelta(hours=1)
        self.assertEqual(self.env["ems.notification"]._cron_process(), 0)
        self.assertEqual(notification.state, "pending")

    def test_unconfigured_channel_fails_fast(self):
        notification = self._queue(channel="sms", recipient="+3212345678")
        self.env["ems.notification"]._cron_process()
        self.assertEqual(notification.state, "failed")
        # Fails immediately instead of consuming the retry budget.
        self.assertEqual(notification.attempt_count, 0)
        self.assertIn("No provider configured", notification.last_error)

    def test_retry_requeues_failed_notification(self):
        notification = self._queue(channel="sms", recipient="+3212345678")
        self.env["ems.notification"]._cron_process()
        notification.action_retry()
        self.assertEqual(notification.state, "pending")
        self.assertEqual(notification.attempt_count, 0)

    def test_one_bad_recipient_does_not_sink_the_batch(self):
        good = self._queue()
        bad = self._queue(recipient="also@example.com")
        original = type(self.env["ems.notification"])._send_one

        def selective(self_rec):
            if self_rec.id == bad.id:
                raise RuntimeError("bounced")
            return original(self_rec)

        with patch.object(type(self.env["ems.notification"]), "_send_one", selective):
            self.env["ems.notification"]._cron_process()
        self.assertEqual(good.state, "sent")
        self.assertEqual(bad.state, "pending")

    def test_enqueue_template_renders_and_links_record(self):
        notification = self.env["ems.notification"].ems_enqueue_template(
            "ems_notifications.mail_template_ticket_issued", self.ticket
        )
        self.assertTrue(notification)
        self.assertEqual(notification.recipient, "notified@example.com")
        self.assertIn(self.ticket.name, notification.body)
        self.assertIn("Notified Event", notification.subject)
        self.assertEqual(notification.res_model, "ems.ticket")
        self.assertEqual(notification.res_id, self.ticket.id)

    def test_enqueue_template_skips_recipientless_records(self):
        partner = self.env["res.partner"].create({"name": "No Email"})
        ticket = self.env["ems.ticket"].create({
            "event_id": self.event.id, "partner_id": partner.id,
        })
        self.assertFalse(self.env["ems.notification"].ems_enqueue_template(
            "ems_notifications.mail_template_ticket_issued", ticket
        ))
