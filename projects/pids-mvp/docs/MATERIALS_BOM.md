# PIDS — Materials List (BOM) & Cost-Efficiency Project

Hardware, software, and cloud materials required to deploy the PIDS, with a cost-efficiency
analysis. Prices are **2026 order-of-magnitude USD** for planning only — confirm with vendors and
adjust per region/volume. Two reference designs: a **small site** (residential/commercial,
~8 cameras) and a **large site** (industrial/critical, ~64 cameras). Cloud costs scale with the
whole fleet, not per site.

---

## A. Edge materials (per site)

| # | Item | Purpose | Small (8 cam) | Large (64 cam) | Unit $ (est.) |
|---|------|---------|--------------:|---------------:|--------------:|
| 1 | **AI perimeter camera** (on-board detector, e.g. Hailo/Ambarella SoC; ONVIF Profile T) | Detect + classify objects at the fence | 8 | 64 | $250–$700 |
| 2 | Mounting poles / brackets / housings (IP66, IR) | Physical install above fence line | 8 | 64 | $40–$120 |
| 3 | **PoE+ switch** (managed, VLAN-capable) | Power + isolate cameras | 1×16-port | 4×24-port | $150–$900 |
| 4 | **Edge gateway / mini-NVR** (8-core, 16–32 GB RAM, NVMe, optional NPU) | Media gateway (MediaMTX), store-and-forward, sensor fusion | 1 | 2 (HA) | $600–$2,500 |
| 5 | UPS (battery backup) | Ride through power blips | 1 | 2 | $150–$600 |
| 6 | Industrial cellular/5G failover router | WAN redundancy | 1 | 1 | $200–$500 |
| 7 | Cabling (Cat6 outdoor, conduit, connectors) | Wiring | lot | lot | $300–$2,000 |
| 8 | **Aux sensors (roadmap V2):** radar unit, IR beam pair, fence/seismic sensor | Multi-sensor fusion → lower NAR | opt. | opt. | $500–$5,000 |

**Selection guidance (cost-efficiency):**
- Prefer **ONVIF Profile T** cameras with a documented **edge NPU** — pushing detection to the
  edge slashes uplink bandwidth and cloud GPU cost (you send events, not 24×7 video).
- Buy **one mid-range camera tier** rather than mixing many models — reduces integration/testing
  cost (each firmware must be validated per the layered ONVIF→RTSP→SDK pattern).
- Size the gateway NPU to also run **fusion + fallback server-side re-inference** (YOLO l/x) so a
  cheaper camera tier is viable.

---

## B. Cloud / platform materials (whole fleet)

| Item | Purpose | Small fleet | Large fleet |
|------|---------|-------------|-------------|
| Kubernetes cluster (managed, multi-AZ) | Run microservices | 3× small nodes | 6–12× medium nodes |
| Managed PostgreSQL (HA + replica) + Timescale | Core data | 1 small instance | 1 large + replica |
| Redis (managed) | Cache / dedup / rate-limit | 1 small | 1 medium |
| Kafka / Redpanda (managed) | Event bus | 3 brokers (shared) | 3–5 brokers |
| Object storage (S3/MinIO) | Media (30-day retention) | ~1 TB | ~20 TB |
| OpenSearch/ELK | Logs / search | 1 small | 3-node |
| Observability (Prometheus/Grafana/Loki/Tempo) | SLOs, tracing | shared | dedicated |
| LLM assist (Claude API) | Summaries/reports | ~$90–150/mo | ~$150–400/mo (see LLM_SELECTION.md) |
| Notification providers (Twilio/SMTP/FCM) | Alerts | usage | usage |

---

## C. Software / licensing materials

| Item | Type | Cost model |
|------|------|-----------|
| PIDS application (this project) | In-house | Dev + maintenance |
| Object-detection models (Ultralytics YOLO11/12/26) | OSS (check license for commercial use) | Free / AGPL or enterprise license |
| MediaMTX / go2rtc (media gateway) | OSS (MIT/Apache) | Free |
| PostgreSQL, Redis, Kafka/Redpanda, MinIO, OpenSearch | OSS | Free (or managed-service fee) |
| Prometheus/Grafana/Loki/Tempo, OpenTelemetry | OSS | Free (or Grafana Cloud) |
| Identity (Keycloak) or managed OIDC | OSS / SaaS | Free / per-MAU |

> ⚠️ **License note:** Ultralytics YOLO is **AGPL-3.0** — for a closed-source commercial product
> you need either an Ultralytics enterprise license or a permissively-licensed detector
> (e.g. an Apache-2.0 model export). Budget for this; it is a real cost-efficiency lever.

---

## D. Cost-efficiency analysis

### D.1 Rough CapEx per reference site

| | Small (8 cam) | Large (64 cam) |
|-|--------------:|---------------:|
| Cameras (mid tier ~$450) | $3,600 | $28,800 |
| Mounts/housings (~$80) | $640 | $5,120 |
| Switch(es) | $300 | $2,400 |
| Gateway(s) + UPS + WAN | $1,200 | $6,000 |
| Cabling/install | $1,000 | $6,000 |
| **Edge CapEx (excl. aux sensors)** | **≈ $6,740** | **≈ $48,320** |

### D.2 Cost levers (highest impact first)

1. **Edge-first detection** — on-camera/on-gateway inference avoids per-camera cloud GPU. A
   cloud-only VMS re-analyzing 64 RTSP streams needs multiple GPUs (**$1–3k/mo each**); edge
   inference removes almost all of it. *Biggest single lever.*
2. **Event-driven, not stream-driven cloud** — send detection events + short clips, not 24×7
   video. Cuts egress and object-storage cost by 1–2 orders of magnitude.
3. **NAR reduction (fusion + tracking + zone masks)** — every false alarm eliminated saves
   operator time *and* downstream LLM/notification spend. Targeting **< 5 alarms/day/km** is a
   cost target, not just a quality one.
4. **Right-sized LLM + caching + batch** — see `LLM_SELECTION.md`; keeps assist cost < $500/mo
   even at large scale.
5. **Modular monolith first** — run the platform as one deployable until load justifies
   splitting services; avoids premature per-service infra overhead.
6. **Storage lifecycle** — 30-day media retention with object-store lifecycle rules; downsample
   events after 90 days (Timescale continuous aggregates).
7. **Single camera tier** — fewer firmware variants = lower integration/QA cost.

### D.3 Illustrative monthly OpEx (large fleet, ~500 cameras across sites)

| Line | Est. $/mo |
|------|----------:|
| Kubernetes + DB + Redis + Kafka + storage + observability | $2,500–$6,000 |
| LLM assist (Claude) | $150–$400 |
| Notifications (SMS/voice usage) | $100–$1,000 (volume-driven) |
| **Cloud OpEx total** | **≈ $3k–$7k/mo** |

**Takeaway:** the dominant cost is **edge CapEx** (cameras) and **cloud infra**; the LLM assist
layer is negligible. The three levers that move the budget most are (1) edge-first detection,
(2) event-driven cloud, and (3) aggressive NAR reduction. Design decisions in the master prompt
(YOLO on edge, Kafka event backbone, fusion, dedup) are all chosen with these levers in mind.
