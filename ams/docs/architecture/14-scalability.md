# Section 14 — Scalability Architecture

## 14.1 Capacity model (arithmetic shown)

**Inputs (Future Scale):** 500 sites · 100,000 employees · 250,000 cardholders ·
25,000 visitors/day. Peak-hour multiplier: **20 % of daily volume in the busiest hour**
(Assumption A1, validated against reception logs).

**Visitor flow TPS**

```
Check-ins:  25,000/day × 20% peak hour = 5,000/h ÷ 3600 s ≈ 1.4 TPS peak
Each check-in ≈ 6 API calls (validate QR, docs, check-in, badge issue, notify, print)
→ visitor-path peak ≈ 1.4 × 6 ≈ 8.3 TPS  (round to 10 TPS with headroom)
Check-outs mirror check-ins on the evening shoulder ≈ same order.
```

**Badge validations (dominant load)**

```
Employees on-site/day ≈ 60% of 100,000 = 60,000
Badge presentations/person/day ≈ 8 (entry, exit, zones, canteen, parking)
→ 60,000 × 8 = 480,000 validations/day
Visitors: 25,000 × 4 presentations = 100,000/day
Total ≈ 580,000/day. Morning peak (07:30–09:30 concentrates ~35%):
580,000 × 35% ÷ 7,200 s ≈ 28 TPS sustained peak
Gate bursts (shift change at plants): design for 5× burst = 150 TPS validation target.
At ~40 ms/validation CPU-time, 150 TPS ≈ 6 vCPU busy → 4 pods × 2 vCPU at 75% = fits;
HPA scales access-control 4 → 12 pods for bursts.
```

**Event volume & storage growth**

```
Events/day ≈ validations 580k + visit lifecycle (25k × ~10) 250k + badge lifecycle ~20k
            + approvals ~30k + occupancy/system ~120k ≈ 1.0 M events/day
Audit envelope ≈ 1.5 KB (JSONB + indexes) → 1.0 M × 1.5 KB ≈ 1.5 GB/day
Yearly: 1.5 GB × 365 ≈ 550 GB/yr in PG (13 months hot ≈ 600 GB) — monthly partitions
of ~45 GB each: well inside Flexible Server + partition-prune comfort.
WORM blob (compressed batches, ~0.4 KB/event effective): ≈ 150 GB/yr × 7 y ≈ 1 TB — cheap.
Event Hubs: 1.0 M/day ≈ 12 msg/s average, 150/s burst → 32 partitions on the decision
hub = <5 msg/s/partition at burst: 20× headroom (Section 6.3).
```

**Read load:** SOC dashboards + portals ≈ 100k employees × ~20 API reads/day ≈ 2 M
reads/day ≈ 23 TPS average, 100 TPS peak — served ≥ 80 % from Redis (read models),
so PG read load ≈ 20 TPS peak. Comfortable on 4-vCPU flexible server per hot service DB;
scale up path to 16 vCPU before any re-architecture is needed.

**Conclusion:** the future-scale system peaks in the low hundreds of TPS — engineering
effort goes to **latency, freshness and blast-radius**, not raw throughput. Numbers above
are the HPA and load-test baselines (2× modelled peak per NFR-002).

## 14.2 Growth model: 20 → 500 sites

| Component | Scales by | Mechanism |
|---|---|---|
| access-control | validation TPS | HPA on P95 + RPS, 4→24 pods; Redis snapshot shards by site |
| edge gateways | # sites (1–2/site) | fleet is inherently horizontal; config snapshots per site |
| Event Hubs | partition counts | provisioned per-hub; repartition = new hub + consumer cutover (runbook) |
| PostgreSQL | storage + write TPS | partitioning first, vertical next, per-service DB split to own server last |
| visitor/badge/approval | site-proportional | HPA; stateless |
| occupancy fan-out | concurrent dashboards | SSE nodes scale on connection count; Redis pub/sub |
| Onboarding itself | 30 sites/month peak | site-onboarding runbook + Terraform site module + snapshot bootstrap (the real constraint is people, Section 16) |

## 14.3 Multi-region active-active (WEU primary / NEU secondary)

- **Traffic:** Front Door latency-routes to both regions; APIM + AKS active in each;
  health-probe failover < 60 s.
- **Data:** PG Flexible Server — zone-redundant HA in WEU + geo replica in NEU
  (read-only). Writes are **single-region-at-a-time per service** ("active-active
  platform, active-passive data"): NEU serves reads/validation from replicas + Redis;
  on failover the replica promotes (RTO ≤ 30 min critical path, Section 7.5).
  Honest trade-off: true multi-master SQL is out (ADR-006).
- **Why this still meets 99.99 % on the critical path:** validation reads at the edge
  never require the primary — edge gateways + regional Redis snapshots keep permits
  flowing during a regional DB failover; only *mutations* (issue/revoke) queue briefly.
- **Conflict/idempotency handling:** uuidv7 IDs mint conflict-free in any region;
  all writes carry Idempotency-Keys so retried cross-region requests are safe;
  Event Hubs geo-paired namespaces + capture replay recover in-flight events; consumer
  inbox dedupe (`processed_events`) makes replays harmless; revocation events are
  tombstones that always win merges (deny-precedence rule).

## 14.4 HA per tier

| Tier | Redundancy |
|---|---|
| Edge | ≥ 2 gateways at large sites; local snapshot + offline queue (24 h autonomy) |
| Global entry | Front Door (inherently multi-POP) + WAF |
| Compute | AKS across 3 AZs, PodDisruptionBudgets, topology-spread, cluster autoscaler |
| Messaging | Event Hubs Premium (AZ-redundant), geo-paired secondary |
| Cache | Redis zone-redundant, replicas; cache-miss tolerant clients |
| DB | Zone-redundant HA (sync standby) + geo replica + PITR |
| Audit | PG + RA-GZRS immutable blob (two independent persistence paths) |

## 14.5 Cache strategy (Redis)

| Cache | Pattern | TTL | Invalidation |
|---|---|---|---|
| Credential/validation snapshot | replicated read-through per region; edge pulls signed deltas | 24 h (edge), continuous delta | **event-driven:** badge/policy events bump `snapshot_seq`; tombstones (revocations) pushed immediately (≤ 5 s NFR-013) |
| API read models (visits, badges, occupancy boards) | cache-aside keyed by resource+etag | 60 s | write-through bump on outbox publish; ETag re-validation |
| Policy decisions (ABAC partial results) | per cardholder+zone memo | 300 s | version-keyed: key embeds `policyVersion` — publish = natural invalidation, no scans |
| Idempotency keys | write-once | 24 h | TTL only |
| Anti-passback state | per zone hash | rolling | decision events update; zone-empty resets |

**Stampede protection:** (1) per-key singleflight lock (`SET NX PX` 2 s — one loader,
others wait on pub/sub notify); (2) TTL jitter ±10 %; (3) stale-while-revalidate: serve
expired value ≤ 30 s while refresh runs; (4) negative caching (5 s) for unknown
credentials to blunt scan attacks (pairs with FR-035 alarms).

## 14.6 Performance budgets

| Budget | Target |
|---|---|
| SPA initial load (operator app) | ≤ 300 KB gz critical path, TTI ≤ 3 s on mid-range hardware; route-level code splitting |
| Kiosk screen transitions | ≤ 150 ms perceived; assets pre-cached (service worker) |
| API server processing | ≤ 120 ms P95 in-service (leaves 80 ms for network+gateways within the 200 ms SLO) |
| Decision pipeline internal | ≤ 40 ms P95 (cache-hit path), ≤ 150 ms cold |
| DB query ceiling | any query > 50 ms P95 needs an index review; > 250 ms fails PR perf test |
| Event publish (outbox commit→hub) | ≤ 1 s P95 |
| Page weight regression gate | CI Lighthouse budget file; fail on +10 % |

<!-- SECTION 14 COMPLETE -->
