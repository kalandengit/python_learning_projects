# CLAUDE.md — Event Management System (EMS)

## Source of truth

Read **[docs/master-prompt-v3.md](docs/master-prompt-v3.md)** before doing anything else.
It is the authoritative, self-contained project brief: locked technical decisions (§2),
domain model (§3), API surface (§4), remaining work plan (§6), and non-negotiable
rules (§7). All decisions in its §2 are LOCKED — do not re-litigate or "improve"
them unless the user explicitly asks.

## Repository status (as of July 2026)

Parts 1–3 (§5) were **regenerated into this repository** in July 2026: schema +
Alembic baseline (`app/models`, `migrations/`), backend core (`app/core`,
`app/services`), all §4 routes (`app/routers`), the pytest suite (`tests/`,
coverage ≥80% against real PostGIS + Valkey), Locust profile (`load/`),
Dockerfile/compose v3 and CI v3 (`.github/workflows/ci.yml`).

**Part 4** (§6, React frontend) was completed in July 2026 under `frontend/`
(Vite 8 / React 19 / TS strict / Tailwind v4; TanStack Query, Zustand, Zod, ky):
API client with refresh-rotation retry, passkey/password+TOTP auth, event
browse + tier purchase, Stripe redirect, My Tickets QR, organizer wizard
(Leaflet map pin), badge admin, and the offline-capable scanner PWA. Two
read-only backend endpoints were added for it (`GET events/{id}/tiers`,
`GET badges?event_id=`). Remaining work starts at §6 **Part 5** (infrastructure:
Terraform plan-only, seed/migration tasks, deploy workflow, Grafana/alarms).

One documented deviation: ML-DSA-65
signatures (3,309 B) exceed QR capacity (2,953 B), so the hybrid PQC signature
is stored on the ticket/badge row and verified server-side on scan; the QR
carries the HMAC envelope `{t,e,u,ts}` exactly as specified (see
`app/core/pqc.py` docstring).

## Quick rules (see master prompt §7 for the full list)

- Python ≥3.13 with **uv** (pyproject.toml + uv.lock) — never pip/requirements.txt.
- Security > convenience: no card data, no secrets/tokens/PII in logs or commits.
- Concurrency invariants (ticket inventory `FOR UPDATE`, atomic scan `UPDATE … RETURNING`) must never be simplified.
- Terraform is plan-only in automation; a human applies.
- CI gates: coverage ≥80%, Trivy CRITICAL blocks, mypy strict, ruff clean.
