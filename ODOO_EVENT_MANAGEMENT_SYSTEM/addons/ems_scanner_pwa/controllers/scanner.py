import json

from odoo import http
from odoo.http import request

# The service worker deliberately caches only the shell. Scan results are never
# cached: a stale "accepted" shown offline would be worse than no answer.
SERVICE_WORKER = """
const CACHE = "ems-scanner-v3";
const SHELL = ["/ems/scanner"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") {
    return;  // never intercept scan submissions
  }
  const url = new URL(request.url);
  if (url.pathname.startsWith("/ems/api/")) {
    return;
  }
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok && url.origin === self.location.origin) {
          const copy = response.clone();
          caches.open(CACHE).then((c) => c.put(request, copy));
        }
        return response;
      })
      .catch(() => caches.match(request))
  );
});
"""


class EmsScannerController(http.Controller):

    @http.route("/ems/scanner", type="http", auth="user", website=True)
    def scanner(self, **kwargs):
        if not request.env.user.has_group("ems_core.group_ems_user"):
            return request.not_found()
        return request.render("ems_scanner_pwa.scanner_page")

    @http.route("/ems/scanner/manifest.json", type="http", auth="user", methods=["GET"])
    def manifest(self, **kwargs):
        if not request.env.user.has_group("ems_core.group_ems_user"):
            return request.not_found()
        payload = {
            "name": "EMS Scanner",
            "short_name": "EMS Scan",
            "start_url": "/ems/scanner",
            "scope": "/ems/scanner",
            "display": "standalone",
            "orientation": "portrait",
            "background_color": "#ffffff",
            "theme_color": "#111111",
            "description": "Event check-in scanner with offline queueing.",
        }
        return request.make_response(json.dumps(payload), headers=[
            ("Content-Type", "application/manifest+json"),
        ])

    @http.route("/ems/scanner/sw.js", type="http", auth="user", methods=["GET"])
    def service_worker(self, **kwargs):
        if not request.env.user.has_group("ems_core.group_ems_user"):
            return request.not_found()
        return request.make_response(SERVICE_WORKER, headers=[
            ("Content-Type", "application/javascript"),
            ("Service-Worker-Allowed", "/ems/scanner"),
            ("Cache-Control", "no-cache"),
        ])
