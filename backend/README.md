# StaffHub Backend (MVP)

FastAPI backend for **StaffHub**, an employee self-service & shift-planning
portal. This is the MVP backend slice described in the v1.2 Master Prompt: the
multi-tenant domain, authentication, the request lifecycle, planning, the ICS
feed, notifications, timeline, attachments, auditing, feature flags and rate
limiting — all covered by an automated test suite.

## Quick start

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the API (SQLite by default — no external services needed)
uvicorn app.main:app --reload
# Interactive docs at http://127.0.0.1:8000/docs

# Run the tests
pytest
```

Configuration is environment-driven (prefix `STAFFHUB_`); see `.env.example`.

## Docker

```bash
docker build -t staffhub-backend .
docker run -p 8000:8000 staffhub-backend
```

## Architecture

- **FastAPI** application factory in `app/main.py`.
- **SQLAlchemy 2.0** models in `app/models/`. SQLite is the default so the app
  runs and tests without a server; production targets **PostgreSQL** using the
  same `DATABASE_URL`. PostgreSQL **row-level security** is the production
  tenant-isolation mechanism; the service layer mirrors that filtering (by
  `tenant_id`) so isolation also holds on SQLite and as defence in depth.
- **Layering**: routers (`app/routers/`) handle HTTP; services
  (`app/services/`) hold business logic (state machine, audit, ICS rendering,
  rate limiting, storage/scan); schemas (`app/schemas/`) are the Pydantic I/O
  contracts.

### First-run flow

The API bootstraps without seed data:

1. `POST /auth/bootstrap-tenant` — create a tenant (platform-admin op).
2. `POST /auth/tenants/{id}/first-admin` — seed the first admin (allowed only
   while the tenant has no users).
3. `POST /auth/accept-invite` — the admin sets a password and is activated.
4. `POST /auth/login` — obtain a JWT, then invite the rest of the team via
   `POST /auth/tenants/{id}/invite`.

## Master Prompt coverage

| Master Prompt requirement | Status | Where |
|---|---|---|
| Multi-tenant isolation (`tenant_id`, RLS) | ✅ service-layer + RLS-ready | `models/base.py` (`TenantMixin`), all routers |
| Auth: email invitation | ✅ | `routers/auth.py` |
| Auth: forced password reset | ✅ (`must_reset_password`, reset flow) | `models/user.py`, `routers/auth.py` |
| Auth: MFA-ready architecture | ✅ (schema field; enrolment TODO) | `models/user.py` (`mfa_secret`) |
| Requests: desiderata / leave / absence | ✅ | `models/request.py` |
| Requests: full state machine | ✅ validated transitions | `models/request.py`, `services/requests.py` |
| Requests: status history | ✅ one row per transition | `models/request.py` (`RequestStatusHistory`) |
| Requests: online drafts | ✅ create/edit while `draft` | `routers/requests.py` |
| Planning: shifts + bulk actions | ✅ publish/archive/delete | `routers/planning.py` |
| Planning: PDF export | ✅ planner + self-service schedule PDF | `routers/planning.py`, `services/pdf.py` |
| Audit log query API | ✅ admin/HR, filter + pagination | `routers/admin.py` |
| Soft-delete retention purge | ✅ scheduled/on-demand hard purge | `services/purge.py`, `routers/admin.py` |
| ICS feed (Must Have) | ✅ hashed token, revoke, annual expiry | `routers/ics.py`, `services/ics.py` |
| Attachments: type/size limits | ✅ JPEG/PNG/PDF, 10 MB | `routers/attachments.py`, `config.py` |
| Attachments: malware scan before availability | ✅ scan gates `is_available` | `services/storage.py`, `models/attachment.py` |
| Attachments: medical = HR-only | ✅ access-controlled | `routers/attachments.py` |
| Notification centre: read/unread, archive, deep links | ✅ | `routers/notifications.py` |
| Timeline: unified chronological stream | ✅ shifts + requests + notifications | `routers/timeline.py` |
| Audit log: actor/ip/device/reason/before/after | ✅ | `models/audit.py`, `services/audit.py` |
| Soft delete + retention | ✅ (`deleted_at`/`deleted_by` + purge) | `models/base.py`, `services/purge.py` |
| Tenant feature flags | ✅ | `models/tenant.py`, `routers/admin.py` |
| Rate limiting (login, uploads, requests, ICS) | ✅ tenant-aware, Redis-ready | `services/rate_limit.py`, `deps.py` |

### Deliberately out of scope for this slice

- **React + TypeScript frontend** — the Master Prompt's client. This repository
  is Python-focused; the backend exposes the full API (`/docs`) the frontend
  would consume.
- **Client-side image compression, Background Sync, push/email delivery** —
  client- and infra-side concerns. The notification *model* supports push/email
  channels; actual delivery adapters are not implemented here.
- **Terraform / GitHub Actions / blue-green / PITR backups** — deployment
  infrastructure.
- **Real object storage + at-rest encryption + async ClamAV** — abstracted
  behind `services/storage.py` stubs (`store_blob`, `scan_blob`) with the
  correct interfaces and availability gating; swap in real implementations
  without touching the routers.
- **PostgreSQL RLS policies + Alembic migrations** — production uses migrations
  instead of `create_all`; RLS policies enforce `tenant_id` at the database.

## Request state machine

```
Draft → Submitted → Under Review → Needs Information → Resubmitted
                         ↓                                   ↓
              Approved / Rejected / Cancelled  ← ← ← ← ← ← ← ←
```

Allowed transitions live in `ALLOWED_TRANSITIONS` (`models/request.py`).
Transition validity (409 on an illegal jump) is checked before authorization
(403 for the wrong role): employees may submit/resubmit/cancel; planners/admins
may review/approve/reject. Every transition writes history, an audit entry, and
a notification to the requester.

## Continuous integration

`.github/workflows/ci.yml` installs the backend dependencies and runs the full
`pytest` suite on every push and pull request (Python 3.11).

## Tests

47 tests in `tests/` cover auth flows, the request lifecycle and RBAC, planning
and bulk actions, PDF export, the ICS feed end-to-end, notifications, the
timeline, attachments (clean/infected/medical), tenant isolation, feature flags,
rate limiting, the audit-log query API, and retention purge. Run with `pytest`.
