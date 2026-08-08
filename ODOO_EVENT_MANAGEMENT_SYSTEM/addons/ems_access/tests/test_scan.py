from odoo.exceptions import AccessError, UserError
from odoo.tests.common import tagged

from .common import EmsAccessCommon


@tagged("post_install", "-at_install", "ems_access")
class TestScan(EmsAccessCommon):

    def test_accepted_scan_marks_ticket_used(self):
        envelope = self.ticket.get_qr_envelope()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "accepted")
        self.assertEqual(self.ticket.state, "used")
        self.assertTrue(self.ticket.used_at)

    def test_duplicate_client_uid_is_idempotent(self):
        envelope = self.ticket.get_qr_envelope()
        first = self.scan(envelope, "gate-1", "scan-1")
        second = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(first.id, second.id)
        self.assertEqual(first.result, "accepted")
        self.assertEqual(
            self.env["ems.scan.log"].search_count([("client_scan_uid", "=", "scan-1")]), 1
        )

    def test_same_client_uid_on_two_devices_is_not_collapsed(self):
        """Scanners mint their own UIDs; a collision across devices is legitimate."""
        envelope = self.ticket.get_qr_envelope()
        first = self.scan(envelope, "gate-1", "shared-uid")
        second = self.scan(envelope, "gate-2", "shared-uid")
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.result, "accepted")
        self.assertEqual(second.result, "duplicate")

    def test_replayed_envelope_on_second_gate_is_duplicate(self):
        envelope = self.ticket.get_qr_envelope()
        self.scan(envelope, "gate-1", "scan-1")
        replay = self.scan(envelope, "gate-2", "scan-2")
        self.assertEqual(replay.result, "duplicate")
        self.assertEqual(replay.reason, "already_used")

    def test_revoked_ticket_is_refused(self):
        envelope = self.ticket.get_qr_envelope()
        self.ticket.with_user(self.ems_manager).action_revoke()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "revoked")
        self.assertEqual(self.ticket.state, "revoked")

    def test_rotated_credential_invalidates_old_envelope(self):
        envelope = self.ticket.get_qr_envelope()
        self.ticket.with_user(self.ems_manager).action_rotate()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "invalid")
        self.assertEqual(log.reason, "stale_credential")
        self.assertEqual(self.ticket.state, "active")

    def test_device_not_authorized_for_event(self):
        self.device.event_ids = [(5, 0, 0)]
        envelope = self.ticket.get_qr_envelope()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "wrong_event")
        self.assertEqual(self.ticket.state, "active")

    def test_inactive_device_is_refused(self):
        self.device.active = False
        envelope = self.ticket.get_qr_envelope()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "device_revoked")

    def test_tampered_envelope_is_refused(self):
        envelope = self.ticket.get_qr_envelope()
        payload, signature = envelope.split(".")
        tampered = f"{payload}.{'A' * len(signature)}"
        log = self.scan(tampered, "gate-1", "scan-1")
        self.assertEqual(log.result, "invalid")
        self.assertEqual(log.reason, "bad_signature")

    def test_malformed_envelope_is_refused(self):
        log = self.scan("not-an-envelope", "gate-1", "scan-1")
        self.assertEqual(log.result, "invalid")
        self.assertEqual(log.reason, "malformed")

    def test_scan_refused_when_checkin_closed(self):
        self.event.ems_checkin_open = False
        envelope = self.ticket.get_qr_envelope()
        log = self.scan(envelope, "gate-1", "scan-1")
        self.assertEqual(log.result, "invalid")
        self.assertEqual(log.reason, "checkin_closed")

    def test_unknown_device_is_refused(self):
        envelope = self.ticket.get_qr_envelope()
        with self.assertRaises(AccessError):
            self.scan(envelope, "does-not-exist", "scan-1")

    def test_non_ems_user_cannot_scan(self):
        outsider = self.env["res.users"].create({
            "name": "Plain Employee",
            "login": "plain.employee@example.com",
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        envelope = self.ticket.get_qr_envelope()
        with self.assertRaises(AccessError):
            self.scan(envelope, "gate-1", "scan-1", user=outsider)

    def test_gate_operator_cannot_write_devices_directly(self):
        """The heartbeat is applied server-side; operators keep read-only ACL."""
        with self.assertRaises(AccessError):
            self.device.with_user(self.ems_user).write({"name": "Tampered"})

    def test_last_seen_is_updated_by_scan(self):
        self.assertFalse(self.device.last_seen_at)
        self.scan(self.ticket.get_qr_envelope(), "gate-1", "scan-1")
        self.device.invalidate_recordset(["last_seen_at"])
        self.assertTrue(self.device.last_seen_at)


@tagged("post_install", "-at_install", "ems_access")
class TestOfflineSync(EmsAccessCommon):

    def test_offline_batch_is_idempotent_and_partial_safe(self):
        envelope = self.ticket.get_qr_envelope()
        batch = [
            {"envelope": envelope, "client_scan_uid": "off-1"},
            {"envelope": envelope, "client_scan_uid": "off-2"},
            "not-a-dict",
            {"envelope": envelope},
        ]
        env = self.env(user=self.ems_user)
        results = env["ems.scan.log"].sync_offline_batch("gate-1", batch)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]["result"], "accepted")
        self.assertEqual(results[1]["result"], "duplicate")
        self.assertEqual(results[2]["reason"], "malformed_item")
        self.assertEqual(results[3]["result"], "invalid")

        # Replaying the whole queue must not create new logs or new outcomes.
        replay = env["ems.scan.log"].sync_offline_batch("gate-1", batch)
        self.assertEqual(replay[0]["result"], "accepted")
        self.assertEqual(
            env["ems.scan.log"].search_count([("client_scan_uid", "in", ["off-1", "off-2"])]), 2
        )

    def test_oversized_batch_is_refused(self):
        env = self.env(user=self.ems_user)
        with self.assertRaises(UserError):
            env["ems.scan.log"].sync_offline_batch("gate-1", [{}] * 501)


@tagged("post_install", "-at_install", "ems_access")
class TestDeviceEnrollment(EmsAccessCommon):

    def test_enroll_stores_only_a_hash(self):
        action = self.device.with_user(self.ems_manager).action_enroll()
        secret = action["context"]["default_secret"]
        self.assertTrue(secret)
        self.device.invalidate_recordset()
        stored = self.device.with_user(self.ems_manager).secret_hash
        self.assertTrue(stored)
        self.assertNotIn(secret, stored)
        self.assertTrue(self.device._verify_secret(secret))
        self.assertFalse(self.device._verify_secret("wrong-secret"))

    def test_plain_user_cannot_enroll(self):
        with self.assertRaises(AccessError):
            self.device.with_user(self.ems_user).action_enroll()
