from odoo.tests.common import TransactionCase


class TestSeating(TransactionCase):
    def test_hold(self):
        event = self.env["event.event"].create({
            "name":"Seat","date_begin":"2026-09-01 10:00:00","date_end":"2026-09-01 18:00:00"
        })
        partner = self.env["res.partner"].create({"name":"A"})
        seat = self.env["ems.seat"].create({
            "event_id":event.id,"section":"A","row_label":"1","seat_number":"1"
        })
        hold = self.env["ems.seat.hold"].hold_seat(seat, partner)
        self.assertEqual(hold.state, "held")
