import logging

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

_logger = logging.getLogger(__name__)


class EmsApiController(http.Controller):
    """Scanner/mobile API.

    Authentication is two-factor by design:

    * the *operator* is authenticated by Odoo — an API key on the ``/ems/api``
      routes, or the logged-in session on the ``/ems/scanner/api`` routes. There
      is no public, unauthenticated mutation endpoint anywhere.
    * the *device* is authenticated by ``device_secret``, so a stolen operator
      credential on an unenrolled handset still cannot post check-ins.

    Two route families exist because Odoo 19's ``auth='bearer'`` only falls back
    to session authentication for top-level document navigations (it requires
    ``Sec-Fetch-Dest: document`` / ``Sec-Fetch-User: ?1``). A ``fetch()`` call
    from the bundled PWA sends ``Sec-Fetch-Dest: empty`` and would be rejected
    with 401, so the browser client gets its own ``auth='user'`` routes. Both
    families share the identical authorization path below.

    No ``cors`` argument is set on any route: they stay same-origin.
    """

    # ------------------------------------------------------------------
    # Shared implementation
    # ------------------------------------------------------------------
    def _authorize_device(self, device_uid, device_secret):
        if not request.env.user.has_group("ems_core.group_ems_user"):
            raise AccessError("EMS scan permission required.")
        device = request.env["ems.scan.log"]._resolve_device(device_uid)
        if not device._verify_secret(device_secret):
            _logger.warning(
                "Rejected scan API call for device %s: bad device secret", device_uid
            )
            raise AccessError("Device authentication failed.")
        return device

    @staticmethod
    def _serialize(log):
        return {
            "client_scan_uid": log.client_scan_uid,
            "result": log.result,
            "reason": log.reason,
            "server_scanned_at": str(log.server_scanned_at or ""),
            "ticket": log.ticket_id.name if log.ticket_id else None,
            "attendee": log.ticket_id.partner_id.name if log.ticket_id else None,
        }

    def _do_validate(self, envelope, device_uid, client_scan_uid,
                     client_scanned_at=None, device_secret=None):
        self._authorize_device(device_uid, device_secret)
        log = request.env["ems.scan.log"].validate_envelope(
            envelope, device_uid, client_scan_uid, client_scanned_at
        )
        return self._serialize(log)

    def _do_sync(self, device_uid, scans, device_secret=None):
        self._authorize_device(device_uid, device_secret)
        return {"results": request.env["ems.scan.log"].sync_offline_batch(device_uid, scans)}

    def _do_device_events(self, device_uid, device_secret=None):
        device = self._authorize_device(device_uid, device_secret)
        return {
            "device": device.name,
            "active": device.active,
            "events": [
                {"id": event.id, "name": event.name,
                 "checkin_open": event.ems_checkin_open}
                for event in device.event_ids
            ],
        }

    # ------------------------------------------------------------------
    # API-key clients (native scanner apps, integrations)
    # ------------------------------------------------------------------
    @http.route("/ems/api/v1/scan/validate", type="jsonrpc", auth="bearer", methods=["POST"])
    def validate_scan(self, envelope, device_uid, client_scan_uid,
                      client_scanned_at=None, device_secret=None):
        return self._do_validate(envelope, device_uid, client_scan_uid,
                                 client_scanned_at, device_secret)

    @http.route("/ems/api/v1/scan/sync", type="jsonrpc", auth="bearer", methods=["POST"])
    def sync_scan_batch(self, device_uid, scans, device_secret=None):
        return self._do_sync(device_uid, scans, device_secret)

    @http.route("/ems/api/v1/device/events", type="jsonrpc", auth="bearer", methods=["POST"],
                readonly=True)
    def device_events(self, device_uid, device_secret=None):
        return self._do_device_events(device_uid, device_secret)

    # ------------------------------------------------------------------
    # Session clients (the bundled scanner PWA)
    # ------------------------------------------------------------------
    @http.route("/ems/scanner/api/scan/validate", type="jsonrpc", auth="user", methods=["POST"])
    def validate_scan_session(self, envelope, device_uid, client_scan_uid,
                              client_scanned_at=None, device_secret=None):
        return self._do_validate(envelope, device_uid, client_scan_uid,
                                 client_scanned_at, device_secret)

    @http.route("/ems/scanner/api/scan/sync", type="jsonrpc", auth="user", methods=["POST"])
    def sync_scan_batch_session(self, device_uid, scans, device_secret=None):
        return self._do_sync(device_uid, scans, device_secret)

    @http.route("/ems/scanner/api/device/events", type="jsonrpc", auth="user", methods=["POST"],
                readonly=True)
    def device_events_session(self, device_uid, device_secret=None):
        return self._do_device_events(device_uid, device_secret)
