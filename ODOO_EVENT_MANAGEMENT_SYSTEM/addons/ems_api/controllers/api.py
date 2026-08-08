from odoo import http
from odoo.http import request


class EmsApiController(http.Controller):

    @http.route("/ems/api/v1/scan/validate", type="jsonrpc", auth="bearer", methods=["POST"])
    def validate_scan(self, envelope, device_uid, client_scan_uid, client_scanned_at=None):
        log = request.env["ems.scan.log"].validate_envelope(
            envelope, device_uid, client_scan_uid, client_scanned_at
        )
        return {
            "client_scan_uid": log.client_scan_uid,
            "result": log.result,
            "reason": log.reason,
            "server_scanned_at": log.server_scanned_at,
            "ticket": log.ticket_id.name if log.ticket_id else None,
        }

    @http.route("/ems/api/v1/scan/sync", type="jsonrpc", auth="bearer", methods=["POST"])
    def sync_scan_batch(self, device_uid, scans):
        rows = request.env["ems.scan.log"].sync_offline_batch(device_uid, scans)
        return {"results": rows}
