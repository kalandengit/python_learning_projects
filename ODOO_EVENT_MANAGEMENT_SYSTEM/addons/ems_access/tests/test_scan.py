from odoo.tests.common import TransactionCase


class TestScan(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.user.groups_id += self.env.ref("ems_core.group_ems_user")
        self.env["ir.config_parameter"].sudo().set_param("ems.ticket_qr_secret", "test-secret-not-production")
        self.event = self.env["event.event"].create({
            "name":"Scan Test","date_begin":"2026-09-01 10:00:00","date_end":"2026-09-01 18:00:00"
        })
        p = self.env["res.partner"].create({"name":"A"})
        self.ticket = self.env["ems.ticket"].create({"event_id":self.event.id,"partner_id":p.id})
        self.device = self.env["ems.scanner.device"].create({
            "name":"Gate","device_uid":"gate-1","event_ids":[(6,0,[self.event.id])]
        })

    def test_duplicate_client_uid_is_idempotent(self):
        envelope = self.ticket.get_qr_envelope()
        first = self.env["ems.scan.log"].validate_envelope(envelope,"gate-1","scan-1")
        second = self.env["ems.scan.log"].validate_envelope(envelope,"gate-1","scan-1")
        self.assertEqual(first.id, second.id)
        self.assertEqual(first.result, "accepted")
