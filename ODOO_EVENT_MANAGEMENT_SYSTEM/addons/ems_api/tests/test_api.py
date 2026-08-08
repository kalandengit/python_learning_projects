import json

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install", "ems_api")
class TestScanApi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "ems.ticket_qr_secret", "api-test-secret"
        )
        cls.operator = cls.env["res.users"].create({
            "name": "API Operator",
            "login": "api.operator",
            "password": "api.operator.pw1",
            "email": "api.operator@example.com",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_user").id,
            ])],
        })
        cls.outsider = cls.env["res.users"].create({
            "name": "API Outsider",
            "login": "api.outsider",
            "password": "api.outsider.pw1",
            "email": "api.outsider@example.com",
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        cls.event = cls.env["event.event"].create({
            "name": "API Event",
            "date_begin": "2026-09-01 10:00:00",
            "date_end": "2026-09-01 18:00:00",
            "ems_checkin_open": True,
        })
        cls.ticket = cls.env["ems.ticket"].create({
            "event_id": cls.event.id,
            "partner_id": cls.env["res.partner"].create({"name": "API Attendee"}).id,
        })
        cls.device = cls.env["ems.scanner.device"].create({
            "name": "API Gate", "device_uid": "api-gate",
            "event_ids": [(6, 0, [cls.event.id])],
        })
        manager = cls.env["res.users"].create({
            "name": "API Manager", "login": "api.manager",
            "email": "api.manager@example.com",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ems_core.group_ems_manager").id,
            ])],
        })
        cls.device_secret = cls.device.with_user(manager).action_enroll()[
            "context"]["default_secret"]

    def _call(self, route, params):
        response = self.url_open(
            route,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_validate_requires_authentication(self):
        payload = self._call("/ems/scanner/api/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "anon-1",
            "device_secret": self.device_secret,
        })
        self.assertIn("error", payload)
        self.assertEqual(
            self.env["ems.scan.log"].search_count([("client_scan_uid", "=", "anon-1")]), 0
        )

    def test_validate_requires_device_secret(self):
        self.authenticate("api.operator", "api.operator.pw1")
        payload = self._call("/ems/scanner/api/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "no-secret-1",
        })
        self.assertIn("error", payload)
        self.assertEqual(self.ticket.state, "active")

    def test_validate_rejects_wrong_device_secret(self):
        self.authenticate("api.operator", "api.operator.pw1")
        payload = self._call("/ems/scanner/api/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "bad-secret-1",
            "device_secret": "not-the-secret",
        })
        self.assertIn("error", payload)

    def test_validate_rejects_non_ems_user(self):
        self.authenticate("api.outsider", "api.outsider.pw1")
        payload = self._call("/ems/scanner/api/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "outsider-1",
            "device_secret": self.device_secret,
        })
        self.assertIn("error", payload)

    def test_validate_accepts_authorized_scan(self):
        self.authenticate("api.operator", "api.operator.pw1")
        payload = self._call("/ems/scanner/api/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "ok-1",
            "device_secret": self.device_secret,
        })
        self.assertNotIn("error", payload)
        self.assertEqual(payload["result"]["result"], "accepted")
        self.ticket.invalidate_recordset(["state"])
        self.assertEqual(self.ticket.state, "used")

    def test_sync_endpoint_replays_queue(self):
        self.authenticate("api.operator", "api.operator.pw1")
        envelope = self.ticket.get_qr_envelope()
        params = {
            "device_uid": "api-gate",
            "device_secret": self.device_secret,
            "scans": [
                {"envelope": envelope, "client_scan_uid": "sync-1"},
                {"envelope": envelope, "client_scan_uid": "sync-2"},
            ],
        }
        payload = self._call("/ems/scanner/api/scan/sync", params)
        results = payload["result"]["results"]
        self.assertEqual(results[0]["result"], "accepted")
        self.assertEqual(results[1]["result"], "duplicate")

        replay = self._call("/ems/scanner/api/scan/sync", params)
        self.assertEqual(replay["result"]["results"][0]["result"], "accepted")
        self.assertEqual(
            self.env["ems.scan.log"].search_count([
                ("client_scan_uid", "in", ["sync-1", "sync-2"]),
            ]), 2
        )

    def test_device_events_endpoint(self):
        self.authenticate("api.operator", "api.operator.pw1")
        payload = self._call("/ems/scanner/api/device/events", {
            "device_uid": "api-gate",
            "device_secret": self.device_secret,
        })
        result = payload["result"]
        self.assertEqual(result["device"], "API Gate")
        self.assertEqual(result["events"][0]["name"], "API Event")
        self.assertTrue(result["events"][0]["checkin_open"])

    def test_bearer_route_rejects_a_plain_session_fetch(self):
        """Odoo 19 only accepts a session on auth='bearer' for document
        navigations (Sec-Fetch-Dest: document). An XHR from the PWA does not
        qualify, which is why the session route family exists."""
        self.authenticate("api.operator", "api.operator.pw1")
        payload = self._call("/ems/api/v1/scan/validate", {
            "envelope": self.ticket.get_qr_envelope(),
            "device_uid": "api-gate",
            "client_scan_uid": "bearer-session-1",
            "device_secret": self.device_secret,
        })
        self.assertIn("error", payload)
        self.assertIn("Unauthorized", payload["error"]["data"]["name"])

    def test_bearer_route_accepts_an_api_key(self):
        api_key = self.env["res.users.apikeys"].with_user(self.operator).sudo()._generate(
            None, "EMS scanner test key", False
        )
        response = self.url_open(
            "/ems/api/v1/scan/validate",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                "envelope": self.ticket.get_qr_envelope(),
                "device_uid": "api-gate",
                "client_scan_uid": "bearer-key-1",
                "device_secret": self.device_secret,
            }}),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        payload = response.json()
        self.assertNotIn("error", payload)
        self.assertEqual(payload["result"]["result"], "accepted")

    def test_no_wildcard_cors_header(self):
        self.authenticate("api.operator", "api.operator.pw1")
        response = self.url_open(
            "/ems/scanner/api/device/events",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                "device_uid": "api-gate", "device_secret": self.device_secret,
            }}),
            headers={"Content-Type": "application/json"},
        )
        self.assertNotEqual(response.headers.get("Access-Control-Allow-Origin"), "*")
