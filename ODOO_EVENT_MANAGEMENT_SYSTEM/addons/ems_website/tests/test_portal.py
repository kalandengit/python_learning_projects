from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install", "ems_website")
class TestEmsPortal(HttpCase):
    """End-to-end ownership checks over real HTTP.

    The point of these tests is the negative case: a signed-in portal user must
    never be able to reach another attendee's ticket, by URL or otherwise.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "ems.ticket_qr_secret", "portal-test-secret"
        )
        portal_group = cls.env.ref("base.group_portal")
        cls.alice = cls.env["res.users"].create({
            "name": "Alice Attendee", "login": "alice.attendee",
            "password": "alice.attendee.pw1",
            "email": "alice.attendee@example.com",
            "group_ids": [(6, 0, [portal_group.id])],
        })
        cls.bob = cls.env["res.users"].create({
            "name": "Bob Attendee", "login": "bob.attendee",
            "password": "bob.attendee.pw1",
            "email": "bob.attendee@example.com",
            "group_ids": [(6, 0, [portal_group.id])],
        })
        cls.event = cls.env["event.event"].create({
            "name": "Portal Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
        })
        cls.alice_ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id, "partner_id": cls.alice.partner_id.id,
        })
        cls.bob_ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id, "partner_id": cls.bob.partner_id.id,
        })

    def test_portal_lists_only_own_tickets(self):
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open("/my/ems/tickets")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.alice_ticket.name, response.text)
        self.assertNotIn(self.bob_ticket.name, response.text)

    def test_portal_ticket_detail_is_reachable_by_owner(self):
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open(f"/my/ems/ticket/{self.alice_ticket.public_uid}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.alice_ticket.name, response.text)

    def test_portal_cannot_open_another_users_ticket(self):
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open(f"/my/ems/ticket/{self.bob_ticket.public_uid}")
        self.assertEqual(response.status_code, 404)

    def test_portal_cannot_fetch_another_users_qr(self):
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open(f"/my/ems/ticket/{self.bob_ticket.public_uid}/qr.png")
        self.assertEqual(response.status_code, 404)

    def test_own_qr_is_served_as_uncacheable_png(self):
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open(f"/my/ems/ticket/{self.alice_ticket.public_uid}/qr.png")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "image/png")
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))

    def test_ticket_pages_require_authentication(self):
        response = self.url_open("/my/ems/tickets", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("/web/login", response.headers.get("Location", ""))

    def test_qr_is_not_served_for_revoked_ticket(self):
        self.alice_ticket.action_revoke()
        self.authenticate("alice.attendee", "alice.attendee.pw1")
        response = self.url_open(f"/my/ems/ticket/{self.alice_ticket.public_uid}/qr.png")
        self.assertEqual(response.status_code, 404)


@tagged("post_install", "-at_install", "ems_website")
class TestScannerAccess(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.portal_user = cls.env["res.users"].create({
            "name": "Curious Attendee", "login": "curious.attendee",
            "password": "curious.attendee.pw1",
            "email": "curious.attendee@example.com",
            "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
        })

    def test_scanner_page_is_hidden_from_non_ems_users(self):
        self.authenticate("curious.attendee", "curious.attendee.pw1")
        self.assertEqual(self.url_open("/ems/scanner").status_code, 404)
        self.assertEqual(self.url_open("/ems/scanner/sw.js").status_code, 404)
        self.assertEqual(self.url_open("/ems/scanner/manifest.json").status_code, 404)
