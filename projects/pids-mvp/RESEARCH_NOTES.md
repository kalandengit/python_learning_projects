# PIDS Master Prompt — Research Notes & Changelog (2026 update)

This document records **what was improved** in [`MASTER_PROMPT.md`](./MASTER_PROMPT.md) v2
versus the original prompt, and the **web research (2025‑2026)** that justifies each change.
Everything below is traceable to the sources listed at the end.

## Summary of improvements

| # | Change | Why it matters |
|---|--------|----------------|
| 1 | **Terminology fix**: "Peripheral" → **Perimeter** Intrusion Detection System | "PIDS" universally means *Perimeter* IDS in the physical-security industry. Using the wrong term signals non-familiarity and pollutes every downstream artifact. |
| 2 | **New §0 Normative & regulatory framework** | The system processes personal data (and biometric = special-category data). GDPR, **IEC/EN 62676 (incl. the new 62676‑4:2025)**, EN 50131, NIS2 and NDAA §889 shape hard requirements — they cannot be an afterthought. |
| 3 | **Quantified business targets**: NAR **< 5 alarms/day/km**, detection→alert **P95 < 2 s** | Industry-accepted acceptable *Nuisance Alarm Rate* is ~5/day/km in good weather; giving the LLM measurable targets forces a testable design instead of vague "low latency". |
| 4 | **Modernized edge-AI section**: YOLO11 / YOLOv12 / YOLO26, model sizing n/s (edge) vs l/x (server), NMS-free pipeline, ByteTrack tracking, MLOps feedback loop | The original said only "the camera detects". Current SOTA (2025‑2026) is specific and materially changes accuracy/latency and false-positive handling. |
| 5 | **Multi-sensor fusion** (radar / IR / seismic / fence) as roadmap | Real PIDS deployments fuse sensors to cut false alarms; camera-only is a V1 subset. |
| 6 | **Layered camera integration pattern**: ONVIF Profile T/M → RTSP (RFC 7826/SRTP) → vendor SDK, + media gateway (MediaMTX/go2rtc), WebRTC/LL-HLS | This is the accepted 2025‑2026 multi-vendor VMS interoperability pattern; it also flags the real-world gap that many "Profile M" cameras send no bounding boxes. |
| 7 | **Event backbone made explicit**: Kafka/Redpanda, at-least-once + **idempotency keys** + Redis dedup + **deduplication windows** | Original jumped straight from "camera sends event" to "software decides". Reliable, non-duplicating alerting requires an explicit delivery/idempotency model. |
| 8 | **Rules-engine ADR**: JSON Decision Model (GoRules/ZEN) for MVP vs Drools + Fusion CEP for temporal rules; versioned + dry-run/simulation | Original said "extensible rule engine" with no guidance. Gives a concrete, comparable choice and a safe rollout mechanism. |
| 9 | **Notifications hardened**: escalation policies, quiet hours, channel fallback, ack, HMAC-signed webhooks, dedup | Turns "fully configurable" into concrete, anti-alert-fatigue behavior. |
| 10 | **Immutable audit trail** separated from application logs (append-only / hash-chaining) | Compliance and forensics need tamper-evident audit distinct from operational logs. |
| 11 | **Multi-tenant isolation decision** (RLS vs schema-per-tenant vs db-per-tenant) | Original said "multi-tenant" without an isolation strategy — the single biggest data-security decision in a SaaS PIDS. |
| 12 | **Architecture guidance**: start as **modular monolith**, extract microservices only where justified | Avoids premature microservice sprawl while keeping the door open for scale. |
| 13 | **New §23 Observability & reliability**: SLI/SLO, OpenTelemetry, runbooks, chaos/load testing at thousands-of-cameras scale | Makes the "thousands of cameras / low latency" constraint verifiable. |
| 14 | **Security upgraded**: OWASP ASVS, Zero-Trust, mTLS, Vault/KMS, SBOM, STRIDE threat model, RPO/RTO | Moves from a checklist to a design discipline covering both physical (cameras) and software surfaces. |
| 15 | **Deliverables extended** to 35 (adds compliance matrix + DPIA, threat model + SLO/SLA, ADR register) | Closes the governance/decision-record gaps. |

## Key findings from research (2025‑2026)

**PIDS domain & false alarms.** Acceptable Nuisance Alarm Rate ≈ 5 alarms/day/km in good
weather; modern systems combine video analytics, IR, radar and ground sensors; AI-on-the-edge
filtering (object classification + environmental filtering) is the primary lever for reducing
false alarms; "sterile zones" and routine maintenance are core install practices.

**Edge AI detection.** YOLO11 = unified multi-task, strong edge efficiency; YOLOv12 =
attention-centric (Area-Attention + R-ELAN) for higher accuracy at real-time speed; YOLO26 =
NMS-free output that simplifies the pipeline and removes threshold tuning; deploy n/s variants
on edge, l/x server-side.

**Camera interop.** ONVIF Profile T (H.265/H.264 + motion/tamper analytics + richer events)
superseded Profile S for newer hardware; Profile M carries analytics **metadata/bounding boxes**
but adoption is thin and many cameras omit coordinates; recommended pattern = ONVIF first →
RTSP (RFC 7826 / RTSP 2.0, RTP/SRTP) fallback → vendor SDK for advanced features; validate
against exact firmware.

**Event pipeline.** Kafka scales horizontally (partitions, consumer groups, replication) to very
high throughput; assume at-least-once delivery and make consumers idempotent (idempotency key +
Redis dedup set + deduplication window; short 5‑30 min vs long 6‑24 h windows) to prevent alert
fatigue.

**Rules engine.** JSON Decision Model engines (GoRules/ZEN) express rules as versionable data,
start in ms, and are editable by non-developers; Drools (+ Fusion CEP) offers powerful temporal
complex-event-processing but with JVM weight and slower startup — pick per rule complexity.

**Compliance.** CCTV footage of identifiable people = personal data; biometrics = special
category (needs explicit consent / specific legal basis); DPIA generally required; retention must
match purpose (≈30 days common ceiling for general security; keep only the alert event for
biometric matches); **IEC/EN 62676‑4:2025 (OODPCVS)** in force since 2025‑10‑09 sets realistic
minimum pixel densities per object task (Observe/Detect/Recognize/Identify).

## Sources

- [Perimeter Intrusion Detection Systems: Ultimate Guide 2025 — BC Fence](https://bcfenceaustin.com/perimeter-intrusion-detection-systems/)
- [Why AI Cameras are Essential for Perimeter Intrusion Detection — Viact](https://www.viact.ai/post/why-ai-cameras-are-essential-for-perimeter-intrusion-detection)
- [Perimeter Intrusion Detection System PIDS — Sintela](https://sintela.com/pids-perimeter-intrusion-detection/)
- [Physical Intrusion Detection Systems (PIDS): A Complete Guide — Avigilon](https://www.avigilon.com/blog/physical-intrusion-detection-systems)
- [Computer Vision 2026 (Part 1/3): YOLO and Real-Time Object Detection — Flowygo](https://flowygo.com/en/blog/computer-vision-2026-part-1-3-yolo-and-real-time-object-detection-from-zero-to-working-system/)
- [Top Object Detection Models for Edge Devices — Roboflow](https://roboflow.com/models-by-use-case/object-detection-models-for-edge-devices)
- [A Review of YOLOv12: Attention-Based Enhancements — arXiv 2504.11995](https://arxiv.org/pdf/2504.11995)
- [Ultralytics YOLO Evolution: YOLO26, YOLO11, YOLOv8, YOLOv5 — arXiv 2510.09653](https://arxiv.org/html/2510.09653v2)
- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)
- [ONVIF Profiles in 2026: S, T, G, M, A, C, D — Fora Soft](https://www.forasoft.com/blog/article/onvif-profiles-in-security-systems)
- [Retrofit Architecture for AI Physical Security: VMS/ONVIF/RTSP briefing — IntelliSee](https://intellisee.com/intelligence/retrofit-architecture-ai-physical-security-vms-integration-onvif-rtsp-technology-briefing/)
- [Multi-Vendor Camera Integration: The Pattern — Fora Soft](https://www.forasoft.com/learn/video-surveillance/articles-vms/multi-vendor-interoperability-reference-pattern)
- [The Truth About ONVIF: Real Compatibility in 2025 — SmartVision](https://news.smartvision.dev/vms-software/onvif-compatibility)
- [Event-Driven Microservices: Kafka, RabbitMQ, NATS — dasroot.net](https://dasroot.net/posts/2026/01/event-driven-microservices-kafka-rabbitmq-nats/)
- [Event Driven Architecture Done Right (2025) — Growin](https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/)
- [Alert Deduplication — FireHydrant](https://docs.firehydrant.com/docs/alert-deduplication)
- [Alert Deduplication: Architecture & Use Cases (2026) — SRE School](https://sreschool.com/blog/alert-deduplication/)
- [Idempotency & Deduplication — System Design Sandbox](https://www.systemdesignsandbox.com/learn/idempotency-deduplication)
- [GoRules vs Drools (2026)](https://gorules.io/compare/gorules-vs-drools)
- [JSON Rule Engine: Build Decision Models with JSON — Nected](https://www.nected.ai/us/blog-us/json-rules-engine)
- [An Introduction to GDPR Compliance in Video Surveillance — VeraSafe](https://verasafe.com/blog/an-introduction-to-gdpr-compliance-in-video-surveillance/)
- [GDPR Compliance in Video Surveillance Systems — IntechOpen](https://www.intechopen.com/chapters/1204975)
- [IEC 62676 — Video Surveillance — Imatest](https://www.imatest.com/imaging/iec-62676/)
- [IEC/EN 62676-4:2025 (OODPCVS) support — JVSG](https://www.jvsg.com/iec-62676-4-oodpcvs/)
