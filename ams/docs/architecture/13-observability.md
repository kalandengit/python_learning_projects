# Section 13 — Observability

Stack: OTel SDK in every service → OTel Collector (daemonset) → Prometheus (metrics),
Loki (logs), Tempo (traces), Azure Monitor exporter (platform + Sentinel correlation).
Alert rules as code: `observability/prometheus-alerts.yaml`.

## 13.1 Metrics catalog

**Business**

| Metric | Type | Labels |
|---|---|---|
| `ams_visits_registered_total` | counter | site, channel (portal/walkin/group) |
| `ams_checkins_total` / `ams_checkouts_total` | counter | site, method |
| `ams_checkin_duration_seconds` | histogram | site, method |
| `ams_badges_issued_total` / `ams_badges_revoked_total` | counter | type, reason |
| `ams_revocation_propagation_seconds` | histogram | region |
| `ams_validations_total` | counter | site, decision, reason_code, offline |
| `ams_occupancy_current` | gauge | site, zone |
| `ams_approval_completion_seconds` | histogram | escalated (bool) |
| `ams_muster_generation_seconds` | histogram | site |
| `ams_audit_ingest_lag_seconds` | gauge | source_topic |

**Technical (per service, OTel semconv + custom)**

| Metric | Type | Purpose |
|---|---|---|
| `http_server_request_duration_seconds` | histogram | API SLIs (route, method, status) |
| `ams_outbox_lag_seconds` / `ams_outbox_pending_rows` | gauge | ADR-019 health, HPA input |
| `eventhubs_consumer_lag` | gauge | KEDA scaler + freshness SLI |
| `ams_snapshot_staleness_seconds` | gauge | edge cache freshness (per site) |
| `ams_idempotency_replays_total` | counter | client retry health |
| `db_pool_connections_in_use` / Npgsql histograms | gauge/hist | saturation |
| `ams_edge_gateways_offline` | gauge | fleet health (SOC tile) |

## 13.2 Structured log schema (JSON, one event per line)

```json
{
  "timestamp": "2026-07-04T07:58:12.412Z",
  "severity": "Information",
  "service": "badge-service",
  "environment": "prod-weu",
  "traceId": "7c3f1a2b9d4e5f60a1b2c3d4e5f6a7b8",
  "spanId": "9d4e5f60a1b2c3d4",
  "tenantId": "contoso",
  "siteId": "0197a1b2-9999-7aaa-8bbb-0ccc1ddd2eee",
  "category": "Ams.Badge.Application.IssueBadgeHandler",
  "message": "Badge issued",
  "eventId": "BadgeIssued",
  "data": { "badgeId": "0197b0c1-...", "cardholderId": "0197a1b2-...", "badgeType": "RFID" }
}
```

**PII-masking rules (enforced by a logging enricher + CI log-audit test):**
names/emails/phones never logged — IDs only; QR tokens and RFID values logged as SHA-256
prefixes (`a3f9c2…`, 8 chars); free-text fields (justification, comments) never logged;
the enricher redacts configured JSON paths defensively (`*.email`, `*.fullName`,
`*.qrToken`) and a scheduled Loki query alerts on residual PII patterns (regex for email
shapes) — target: zero findings (NFR-014).

## 13.3 Tracing strategy

- OTel auto-instrumentation (ASP.NET Core, HttpClient, Npgsql, StackExchange.Redis,
  Azure SDK) + manual spans around the decision pipeline stages.
- **Context across Event Hubs:** W3C `traceparent`/`tracestate` copied into event
  headers by the outbox dispatcher; consumers start a new trace **linked** to the
  producer span (span links, not parent-child — a 3-day-later projection rebuild must not
  extend a request trace).
- **Sampling:** head sampling 10 % baseline; **100 %** for: badge-validation denies,
  evacuation flows, any request > 1 s, and all errors (tail-based rules in the
  collector). Trace retention 14 days (Tempo), errors 30 days.

## 13.4 Grafana dashboards (specs)

1. **Executive health:** availability per SLO (30-day), error-budget remaining gauges,
   visits/check-ins today vs baseline, sites onboarded, DORA tiles. Audience: leadership;
   no per-pod noise.
2. **Service SLO (one per service, templated):** SLI vs objective, multi-window burn
   rate (5m/1h/6h/3d), latency heatmap, top RFC 7807 error types, outbox/consumer lag,
   saturation (CPU/mem/pool), deploy annotations from ArgoCD.
3. **Security events:** deny-rate by reason and site, alarm feed (FR-035), offline-edge
   fleet map, revocation-propagation histogram, watchlist hits, Sentinel incident links,
   audit ingest lag.

## 13.5 Alerting (rules in `observability/prometheus-alerts.yaml`)

Multi-window multi-burn-rate pattern per SLO: page at 14.4× burn over 5m∧1h; ticket at
6× over 30m∧6h; plus cause-based alerts (outbox stall, consumer lag, edge fleet offline,
audit-lag, cert expiry, Pod crash-loops).

## 13.6 SLOs, error budgets, burn-rate alerts (mirrors Section-0 targets)

| SLO | SLI definition | Objective | 30-day error budget | Alert |
|---|---|---|---|---|
| Badge validation latency | share of `/v1/badge-validations` (+gRPC) server-side < 200 ms (P95 proxy: good-event ratio) | 95 % < 200 ms; 99 % < 400 ms | 5 % / 1 % slow events | `AmsValidationLatencyBurnFast/Slow` |
| API latency (all endpoints) | share of requests < 200 ms (P95) / < 600 ms (P99), per service | 95 % / 99 % | 5 % / 1 % | `AmsApiLatencyBurn*` |
| Authentication latency | token-acquisition spans < 300 ms (P95) / < 500 ms (P99) | 95 % / 99 % | 5 % / 1 % | `AmsAuthLatencyBurn*` |
| Approval completion | approvals completed < 2 h (P95) / < 4 h (P99) | 95 % / 99 % | 5 % / 1 % of approvals | `AmsApprovalSlaBurn` (6h/3d windows — hours-scale SLI) |
| Platform availability | good requests / total, all services | 99.95 % monthly | 21.9 min | `AmsAvailabilityBurn*` |
| Critical-path availability | validation + evacuation endpoints good/total | 99.99 % monthly | 4.4 min | `AmsCriticalAvailabilityBurn*` (paging at lowest thresholds) |
| Revocation propagation | propagation events ≤ 5 s / total | 99 % | 1 % | `AmsRevocationPropagationBurn` |
| Audit ingest freshness | envelopes appended ≤ 60 s of source event | 99 % | 1 % | `AmsAuditLagBurn` |

**Error-budget policy (governance, CSF 2.0 "Govern"):** budget < 50 % → releases to that
service require SRE review; budget exhausted → feature freeze, reliability-only changes
until 7-day burn < 1×. Reviewed weekly in the ops forum; every Section-0 target above has
a live alert — no decorative targets.

<!-- SECTION 13 COMPLETE -->
