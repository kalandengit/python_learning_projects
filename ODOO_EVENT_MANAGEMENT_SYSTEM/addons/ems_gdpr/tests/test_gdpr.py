import json
from datetime import timedelta

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_gdpr")
class TestGdpr(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.officer = cls.env["res.users"].create({
            "name": "Data Protection Officer",
            "login": "ems.dpo@example.com",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_manager").id,
            ])],
        })
        cls.plain_user = cls.env["res.users"].create({
            "name": "EMS Operator",
            "login": "ems.gdpr.operator@example.com",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_user").id,
            ])],
        })
        cls.event = cls.env["event.event"].create({
            "name": "GDPR Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.subject = cls.env["res.partner"].create({
            "name": "Data Subject", "email": "subject@example.com", "phone": "+3212345678",
        })
        cls.ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id, "partner_id": cls.subject.id,
        })

    def _request(self, request_type, partner=None):
        return self.env["ems.gdpr.request"].with_user(self.officer).create({
            "partner_id": (partner or self.subject).id,
            "request_type": request_type,
        })

    # -------------------------------------------------------------- export
    def test_export_includes_tickets_and_registrations(self):
        request = self._request("export")
        request.action_export()
        self.assertEqual(request.state, "done")
        data = json.loads(request.result_json)
        self.assertEqual(data["partner"]["email"], "subject@example.com")
        self.assertEqual(len(data["tickets"]), 1)
        self.assertEqual(data["tickets"][0]["name"], self.ticket.name)

    def test_export_never_contains_signing_material(self):
        request = self._request("export")
        request.action_export()
        blob = request.result_json
        secret = self.env["ir.config_parameter"].sudo().get_param("ems.ticket_qr_secret")
        self.assertTrue(secret)
        self.assertNotIn(secret, blob)
        self.assertNotIn(self.ticket.public_uid, blob)

    def test_export_cannot_be_processed_twice(self):
        request = self._request("export")
        request.action_export()
        with self.assertRaises(UserError):
            request.action_export()

    def test_plain_user_cannot_process_requests(self):
        request = self._request("export")
        with self.assertRaises(AccessError):
            request.with_user(self.plain_user).action_export()

    # --------------------------------------------------------- anonymize
    def test_anonymize_scrubs_direct_identifiers(self):
        self.ticket.action_revoke()
        request = self._request("anonymize")
        request.action_anonymize()
        self.subject.invalidate_recordset()
        self.assertEqual(request.state, "done")
        self.assertFalse(self.subject.email)
        self.assertFalse(self.subject.phone)
        self.assertIn("Anonymized", self.subject.name)
        self.assertTrue(self.subject.ems_anonymized_on)
        # Referential integrity survives: the ticket still points at the record.
        self.assertEqual(self.ticket.partner_id, self.subject)

    def test_anonymize_blocked_by_active_ticket(self):
        request = self._request("anonymize")
        with self.assertRaises(UserError):
            request.action_anonymize()
        self.subject.invalidate_recordset()
        self.assertEqual(self.subject.email, "subject@example.com")

    def test_anonymize_blocked_by_legal_hold(self):
        self.ticket.action_revoke()
        self.subject.write({
            "ems_legal_hold": True, "ems_legal_hold_reason": "Open dispute",
        })
        request = self._request("anonymize")
        # Refusal is recorded, not raised: the audit trail is the point.
        self.assertFalse(request.action_anonymize())
        self.assertEqual(request.state, "rejected")
        self.assertIn("legal hold", request.rejection_reason.lower())
        self.subject.invalidate_recordset()
        self.assertEqual(self.subject.email, "subject@example.com")

    def test_company_contact_requires_manual_review(self):
        company_partner = self.env["res.partner"].create({
            "name": "Acme Corp", "is_company": True,
        })
        request = self._request("anonymize", partner=company_partner)
        with self.assertRaises(UserError):
            request.action_anonymize()

    # --------------------------------------------------------- retention
    def _stale_scan(self, days_old=1000):
        device = self.env["ems.scanner.device"].create({
            "name": "Retention Gate", "device_uid": "retention-gate",
            "event_ids": [(6, 0, [self.event.id])],
        })
        log = self.env["ems.scan.log"].create({
            "ticket_id": self.ticket.id, "device_id": device.id,
            "client_scan_uid": "retention-1", "result": "accepted",
        })
        log.server_scanned_at = fields.Datetime.now() - timedelta(days=days_old)
        return log

    def test_retention_purges_old_scan_logs(self):
        log = self._stale_scan()
        purged = self.env["ems.gdpr.request"]._cron_apply_retention()
        self.assertEqual(purged, 1)
        self.assertFalse(log.exists())

    def test_retention_keeps_recent_scan_logs(self):
        log = self._stale_scan(days_old=10)
        self.env["ems.gdpr.request"]._cron_apply_retention()
        self.assertTrue(log.exists())

    def test_retention_respects_legal_hold(self):
        log = self._stale_scan()
        self.subject.ems_legal_hold = True
        purged = self.env["ems.gdpr.request"]._cron_apply_retention()
        self.assertEqual(purged, 0)
        self.assertTrue(log.exists())

    def test_retention_disabled_when_zero(self):
        log = self._stale_scan()
        self.env["ir.config_parameter"].sudo().set_param(
            "ems.gdpr.scan_log_retention_days", "0"
        )
        self.assertEqual(self.env["ems.gdpr.request"]._cron_apply_retention(), 0)
        self.assertTrue(log.exists())

    def test_invalid_retention_setting_falls_back(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "ems.gdpr.scan_log_retention_days", "not-a-number"
        )
        self.assertEqual(self.env["ems.gdpr.request"]._retention_days(), 730)
