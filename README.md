# EMS — Event Management System (backend)

Production-grade event management: event planning with PostGIS geodata,
PQC-signed QR ticketing (hybrid ML-DSA-65 + HMAC-SHA256), Stripe Checkout
payments, role/zone-based badges, passkey-first auth, GDPR/PCI compliance.

**Source of truth:** [docs/master-prompt-v3.md](docs/master-prompt-v3.md)
(locked decisions §2, domain model §3, API §4). See also
[CLAUDE.md](CLAUDE.md).

## Stack

Python 3.13 · FastAPI · SQLAlchemy 2 async + asyncpg · PostgreSQL 18/PostGIS
3.6 · Valkey 8 · PyJWT RS256 · Argon2id · py_webauthn · liboqs (ML-DSA-65) ·
segno · Stripe · OpenTelemetry. Dependency management with **uv** only.

## Quick start

```bash
docker compose up --build         # API on :8000, docs at /docs (dev only)
```

Local development without Docker:

```bash
uv sync                            # add `--extra pqc` where liboqs is available
cp .env.example .env               # dev keys are generated ephemerally
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Tests & gates

```bash
uv run pytest --cov=app --cov-fail-under=80   # needs PostGIS + Valkey (see tests/conftest.py)
uv run ruff check app tests migrations
uv run mypy app tests                          # strict
```

The suite covers the non-negotiable invariants: overselling under
concurrency, duplicate-scan 409, PQC signature tamper, refresh-token reuse
detection, account lockout and enumeration resistance.

## Load

```bash
EMS_LOAD_TIER_ID=<uuid> uv run locust -f load/locustfile.py --host http://localhost:8000
```

## Security notes

- Card data never touches this server (Stripe Checkout, SAQ-A); webhooks are
  HMAC-verified before parsing.
- No PII in QR codes; ML-DSA-65 signatures are stored server-side (they
  exceed QR capacity) and re-verified on every scan.
- Never commit `.env`, `*.pem`, `*.key` — gitleaks runs in CI.
