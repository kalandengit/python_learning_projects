from odoo.tests.common import TransactionCase


class TestWaitlist(TransactionCase):
    def test_unique_partner_event(self):
        event = self.env["event.event"].create({
            "name":"Wait","date_begin":"2026-09-01 10:00:00","date_end":"2026-09-01 18:00:00"
        })
        partner = self.env["res.partner"].create({"name":"A"})
        self.env["ems.waitlist.entry"].create({"event_id":event.id,"partner_id":partner.id})
        with self.assertRaises(Exception):
            self.env["ems.waitlist.entry"].create({"event_id":event.id,"partner_id":partner.id})
