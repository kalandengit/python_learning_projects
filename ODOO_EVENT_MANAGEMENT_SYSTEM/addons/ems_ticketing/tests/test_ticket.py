from odoo.tests.common import TransactionCase


class TestTicket(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param("ems.ticket_qr_secret", "test-secret-not-production")
        self.event = self.env["event.event"].create({
            "name":"Ticket Test","date_begin":"2026-09-01 10:00:00","date_end":"2026-09-01 18:00:00"
        })
        self.partner = self.env["res.partner"].create({"name":"Attendee"})

    def test_qr_envelope_roundtrip(self):
        ticket = self.env["ems.ticket"].create({"event_id":self.event.id,"partner_id":self.partner.id})
        env = ticket.get_qr_envelope()
        ok, reason, payload = ticket.verify_qr_envelope(env)
        self.assertTrue(ok)
        self.assertEqual(reason, "ok")
        self.assertEqual(payload["uid"], ticket.public_uid)
