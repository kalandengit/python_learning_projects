#!/usr/bin/env python3
# ruff: noqa: E501, S603
"""Tiny, dependency-free service dashboard for the N'Ko VPS."""

from __future__ import annotations

import html
import os
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

HOST = os.getenv("ADMIN_BIND", "127.0.0.1")
PORT = int(os.getenv("ADMIN_PORT", "8765"))
CSRF_TOKEN = os.environ["ADMIN_CSRF_TOKEN"]


def configured_services() -> dict[str, tuple[str, str]]:
    """Parse the installer-validated key|label|unit;... service allow-list."""
    raw = os.environ["ADMIN_SERVICES"]
    services: dict[str, tuple[str, str]] = {}
    for entry in raw.split(";"):
        key, label, unit = entry.split("|", 2)
        services[key] = (label, unit)
    if not services:
        raise RuntimeError("ADMIN_SERVICES cannot be empty")
    return services


SERVICES = configured_services()
ALLOWED_ACTIONS = {"start", "stop", "restart"}
SYSTEMCTL = os.getenv("SYSTEMCTL", "/usr/bin/systemctl")
SUDO = os.getenv("SUDO", "/usr/bin/sudo")


def run_systemctl(*args: str, privileged: bool = False) -> subprocess.CompletedProcess[str]:
    command = ([SUDO] if privileged else []) + [SYSTEMCTL, *args]
    return subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)


def service_status(unit: str) -> str:
    result = run_systemctl("is-active", unit)
    value = result.stdout.strip()
    return value if value in {"active", "inactive", "failed", "activating", "deactivating"} else "unknown"


def host_stats() -> tuple[str, str, str]:
    values: dict[str, int] = {}
    try:
        with open("/proc/meminfo", encoding="ascii") as stream:
            for line in stream:
                key, value = line.split(":", 1)
                values[key] = int(value.strip().split()[0])
        total = values["MemTotal"] / 1024
        available = values["MemAvailable"] / 1024
        memory = f"{total - available:.0f} / {total:.0f} MiB"
    except (OSError, KeyError, ValueError):
        memory = "Unavailable"
    try:
        load = f"{os.getloadavg()[0]:.2f}"
    except OSError:
        load = "Unavailable"
    try:
        with open("/proc/uptime", encoding="ascii") as stream:
            days = int(float(stream.read().split()[0]) // 86400)
        uptime = f"{days} day(s)"
    except (OSError, ValueError):
        uptime = "Unavailable"
    return memory, load, uptime


def render_page(message: str = "", error: bool = False) -> bytes:
    memory, load, uptime = host_stats()
    cards = []
    for key, (label, unit) in SERVICES.items():
        status = service_status(unit)
        buttons = "".join(
            f'<button class="{action}" name="action" value="{action}">{action.title()}</button>'
            for action in ("start", "stop", "restart")
        )
        cards.append(f"""
        <section class="card">
          <div><h2>{html.escape(label)}</h2><small>{html.escape(unit)}</small></div>
          <span class="status {status}">{html.escape(status.title())}</span>
          <form method="post" action="action">
            <input type="hidden" name="csrf" value="{html.escape(CSRF_TOKEN)}">
            <input type="hidden" name="service" value="{html.escape(key)}">
            <div class="actions">{buttons}</div>
          </form>
        </section>""")
    notice = f'<p class="notice {"error" if error else ""}">{html.escape(message)}</p>' if message else ""
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VPS application control</title>
<style>
:root{{--bg:#eef3ef;--card:#fff;--ink:#10231d;--green:#16876f;--red:#c74444;--gold:#d99c25}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px system-ui,sans-serif}}
main{{max-width:760px;margin:auto;padding:24px}}header{{display:flex;justify-content:space-between;align-items:center;gap:16px}}
h1{{font-size:1.65rem;margin:.4rem 0}}.refresh{{color:var(--ink);background:white;border:1px solid #ccd8d1;padding:12px 16px;border-radius:10px;text-decoration:none}}
.summary,.card{{background:var(--card);border-radius:16px;padding:20px;margin:16px 0;box-shadow:0 2px 12px #153a2910}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;text-align:center}}.summary b{{display:block;font-size:1.05rem}}
.card{{display:grid;grid-template-columns:1fr auto;gap:14px;align-items:start}}h2{{margin:0 0 4px;font-size:1.25rem}}small{{color:#607169}}
.status{{padding:7px 12px;border-radius:999px;background:#dde3df;font-weight:700}}.status.active{{background:#d5f2e7;color:#08614d}}.status.failed{{background:#ffe1e1;color:#952727}}
form{{grid-column:1/-1}}.actions{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}button{{border:0;border-radius:10px;padding:14px 8px;color:white;font-size:1rem;font-weight:700;cursor:pointer}}
.start{{background:var(--green)}}.stop{{background:var(--red)}}.restart{{background:var(--gold)}}.notice{{background:#dff3ea;padding:12px;border-radius:10px}}.notice.error{{background:#ffe1e1;color:#802020}}
.warning{{font-size:.9rem;color:#5b6962}}@media(max-width:520px){{main{{padding:14px}}.summary{{grid-template-columns:1fr}}.card{{grid-template-columns:1fr}}.status{{justify-self:start}}}}
</style></head><body><main>
<header><div><h1>VPS application control</h1><small>Restricted administrator page</small></div><a class="refresh" href="./">Refresh</a></header>
{notice}<section class="summary"><div><b>{html.escape(memory)}</b>Memory used</div><div><b>{html.escape(load)}</b>1-minute load</div><div><b>{html.escape(uptime)}</b>Uptime</div></section>
{"".join(cards)}
<p class="warning">Stopping an application interrupts its users. This control dashboard remains available because it runs independently.</p>
</main></body></html>"""
    return document.encode()


class Handler(BaseHTTPRequestHandler):
    def send_document(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path in {"/", ""}:
            self.send_document(render_page())
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path != "/action":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not 0 < length <= 4096:
            self.send_error(400)
            return
        form = parse_qs(self.rfile.read(length).decode("utf-8", "strict"))
        csrf = form.get("csrf", [""])[0]
        service = form.get("service", [""])[0]
        action = form.get("action", [""])[0]
        if csrf != CSRF_TOKEN or service not in SERVICES or action not in ALLOWED_ACTIONS:
            self.send_document(render_page("Invalid or expired request.", True), 403)
            return
        label, unit = SERVICES[service]
        result = run_systemctl(action, unit, privileged=True)
        if result.returncode == 0:
            self.send_document(render_page(f"{label}: {action} completed."))
        else:
            detail = (result.stderr or result.stdout or "systemctl failed").strip()[:300]
            self.send_document(render_page(f"{label}: {detail}", True), 500)

    def log_message(self, template: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {template % args}", flush=True)


if __name__ == "__main__":
    HTTPServer((HOST, PORT), Handler).serve_forever()
