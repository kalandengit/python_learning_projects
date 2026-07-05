# PIDS MVP — Perimeter Intrusion Detection System

A research-updated design **and a runnable reference implementation** for a **Perimeter Intrusion
Detection System** (not "Peripheral"): AI perimeter cameras → event ingestion → rule engine →
alerts → notifications, multi-tenant and cloud-native. Built to 2025–2026 best practices.

## What's here

```
pids-mvp/
├── MASTER_PROMPT.md        # v2 master prompt (research-updated)
├── MASTER_PROMPT_V3.md     # v3 — adds diagrams, BOM/cost, LLM selection, code
├── RESEARCH_NOTES.md       # changelog + web-research sources
├── docs/
│   ├── ARCHITECTURE.md     # C4, sequence, class, ER, deployment, network (Mermaid)
│   ├── DATA_MODEL.md       # ER diagram + PostgreSQL DDL + retention/compliance
│   ├── LLM_SELECTION.md    # which Claude model for what, with costs
│   ├── MATERIALS_BOM.md    # bill of materials + cost-efficiency project
│   └── RASPBERRY_PI5_DEPLOYMENT.md  # single Pi 5 + Pi 5 k3s cluster (Chain-of-Thought guide)
├── backend/                # runnable FastAPI reference implementation (tested)
│   ├── app/                # models, rule engine, dedup, notifications, pipeline, API
│   ├── tests/              # 26 tests (rule engine, dedup, end-to-end API)
│   └── Dockerfile
├── frontend/index.html     # lightweight dark-mode SOC console (no build step)
├── simulator/
│   ├── camera_sim.py       # posts synthetic detections to the API
│   └── benchmark.py        # capacity benchmark (rule engine / dedup / pipeline)
└── deploy/
    ├── docker-compose.yml
    ├── k3s/               # Pi 5 cluster: pids.yaml, kube-vip.yaml, metallb.yaml,
    │                      #   observability.yaml, build-and-push.sh
    └── monitoring/grafana-dashboard.json
```

CI: `.github/workflows/build-pids-backend.yml` runs the tests and builds a multi-arch
(amd64 + **arm64**) image to GHCR for the Pi 5 cluster.

## Run it

```bash
cd backend
pip install -r requirements.txt
python -m app.seed                 # create demo tenant + admin + camera + default rules
uvicorn app.main:app --reload      # API at http://localhost:8000 (docs at /docs)

# In another shell — drive the pipeline:
python ../simulator/camera_sim.py --discover --count 20 --night

# Open frontend/index.html in a browser, point it at http://localhost:8000
# Demo login: admin@demo.pids / changeme123
```

Run the tests:

```bash
cd backend && python -m pytest -q      # 28 passed
```

Benchmark capacity (for hardware sizing, e.g. Raspberry Pi 5):

```bash
python simulator/benchmark.py --n 50000
# rule engine ~278K evals/s, dedup ~771K ops/s, pipeline ~149 events/s (x86 dev host, SQLite)
```

### Raspberry Pi 5 deployment

See `docs/RASPBERRY_PI5_DEPLOYMENT.md` for a Chain-of-Thought study of running PIDS on a **single
Pi 5 edge appliance** (small site) and a **Pi 5 k3s cluster** (large site, HA) — with hardware BOM,
step-by-step setup, YOLO/Hailo-8L options, capacity sizing, and a phased roadmap. Cluster manifests
are in `deploy/k3s/`.

## What the reference implementation demonstrates

- **Deterministic rule engine** (JSON Decision Model) — priorities, operators, `dry-run`
  simulation, validation. The LLM is *never* in the intrusion-decision path.
- **Idempotent ingestion** — `idempotency_key` + deduplication window (at-least-once safe).
- **Full pipeline** — detection → dedup → rule eval → alert + immutable audit trail →
  provider-agnostic notification (escalation, quiet hours, channel fallback).
- **RBAC auth** — role hierarchy (viewer→super_admin), stdlib PBKDF2 + HS256 tokens
  (swap for argon2/OIDC in production — noted in code).
- **Multi-tenant** data model with a documented RLS isolation strategy.
- **Observability** — `/metrics` Prometheus endpoint (events/alerts/dedup counters), plus a
  Grafana dashboard (intrusion share, NAR proxy, notification rate) for the edge cluster.

Verified end-to-end: humans at night → `high` intrusion, nuisance classes → `ignore`,
duplicates → deduped, dashboard/alerts reflect the flow.

## Key design choices (2025–2026)

Perimeter terminology fix · IEC/EN 62676 (incl. 62676‑4:2025) + EN 50131 + GDPR/DPIA · quantified
targets (**NAR < 5/day/km**, **detection→alert P95 < 2s**) · edge AI (YOLO11/12/26) + multi-sensor
fusion · layered camera integration (**ONVIF T/M → RTSP RFC 7826 → vendor SDK**) · Kafka event
backbone with idempotency + dedup windows · rules-engine ADR (JSON Decision Model vs Drools/CEP) ·
Zero-Trust/mTLS/OWASP ASVS/STRIDE/RPO-RTO · observability/SLOs. Full rationale + sources in
`RESEARCH_NOTES.md`.
