import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "ems_badge")
class TestBadge(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.event = cls.env["event.event"].create({
            "name": "Badge Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.other_event = cls.env["event.event"].create({
            "name": "Other Event",
            "date_begin": "2026-09-02 10:00:00",
            "date_end": "2026-09-02 18:00:00",
        })
        cls.zone = cls.env["ems.venue.zone"].create({
            "name": "Backstage", "code": "BACK", "event_id": cls.event.id,
        })
        cls.foreign_zone = cls.env["ems.venue.zone"].create({
            "name": "Foreign", "code": "FOR", "event_id": cls.other_event.id,
        })
        cls.partner = cls.env["res.partner"].create({"name": "Crew Member"})

    def _badge(self, **overrides):
        vals = {
            "name": "Crew Badge",
            "event_id": self.event.id,
            "partner_id": self.partner.id,
            "zone_ids": [(6, 0, [self.zone.id])],
        }
        vals.update(overrides)
        return self.env["ems.badge"].create(vals)

    def test_badge_uid_is_generated_and_unique(self):
        first, second = self._badge(), self._badge()
        self.assertTrue(first.badge_uid)
        self.assertNotEqual(first.badge_uid, second.badge_uid)

    def test_qr_image_is_rendered(self):
        badge = self._badge()
        self.assertTrue(badge.qr_image)
        # Valid base64 PNG magic bytes.
        self.assertTrue(base64.b64decode(badge.qr_image).startswith(b"\x89PNG"))

    def test_zone_must_belong_to_event(self):
        with self.assertRaises(ValidationError):
            self._badge(zone_ids=[(6, 0, [self.foreign_zone.id])])

    def test_validity_window_must_be_ordered(self):
        now = fields.Datetime.now()
        with self.assertRaises(ValidationError):
            self._badge(valid_from=now, valid_until=now - timedelta(hours=1))

    def test_allows_zone_respects_window_and_membership(self):
        now = fields.Datetime.now()
        badge = self._badge(
            valid_from=now - timedelta(hours=1), valid_until=now + timedelta(hours=1),
        )
        self.assertTrue(badge.allows_zone(self.zone))
        self.assertFalse(badge.allows_zone(self.foreign_zone))
        self.assertFalse(badge.allows_zone(self.zone, when=now + timedelta(days=2)))
        self.assertFalse(badge.allows_zone(self.zone, when=now - timedelta(days=2)))

    def test_archived_badge_grants_nothing(self):
        badge = self._badge()
        badge.active = False
        self.assertFalse(badge.is_valid_now())
        self.assertFalse(badge.allows_zone(self.zone))

    def test_badge_report_renders_pdf_template(self):
        badge = self._badge()
        report = self.env.ref("ems_badge.action_report_ems_badge")
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(
            report.report_name, badge.ids
        )
        self.assertIn(b"Badge Event", html)
        self.assertIn(b"Backstage", html)
