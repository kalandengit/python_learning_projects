import json
from odoo import http
from odoo.http import request


class EmsScannerController(http.Controller):

    @http.route("/ems/scanner", type="http", auth="user", website=True)
    def scanner(self, **kwargs):
        if not request.env.user.has_group("ems_core.group_ems_user"):
            return request.not_found()
        return request.render("ems_scanner_pwa.scanner_page")

    @http.route("/ems/scanner/manifest.json", type="http", auth="user", methods=["GET"])
    def manifest(self, **kwargs):
        payload = {
            "name": "EMS Scanner",
            "short_name": "EMS Scan",
            "start_url": "/ems/scanner",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#111111",
        }
        return request.make_response(
            json.dumps(payload),
            headers=[("Content-Type","application/manifest+json")],
        )

    @http.route("/ems/scanner/sw.js", type="http", auth="user", methods=["GET"])
    def service_worker(self, **kwargs):
        body = '''
const CACHE = "ems-scanner-v2";
self.addEventListener("install", (event) => event.waitUntil(
  caches.open(CACHE).then((c) => c.addAll(["/ems/scanner"]))
));
self.addEventListener("fetch", (event) => {
  if (event.request.method === "GET") {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
  }
});
'''
        return request.make_response(body, headers=[
            ("Content-Type","application/javascript"),
            ("Service-Worker-Allowed","/ems/scanner"),
            ("Cache-Control","no-cache"),
        ])
