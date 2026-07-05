# PIDS MVP — Master Prompt (v2)

A research-updated **master prompt** for generating a complete MVP design of a
**Perimeter Intrusion Detection System (PIDS)** — AI perimeter cameras → event ingestion →
rules engine → alerts → notifications, multi-tenant and cloud-native.

## Files

- **[`MASTER_PROMPT.md`](./MASTER_PROMPT.md)** — the improved prompt to paste into any advanced
  LLM (Claude, GPT, Gemini, DeepSeek, Mistral…). Produces a development-ready design dossier.
- **[`RESEARCH_NOTES.md`](./RESEARCH_NOTES.md)** — changelog vs the original prompt + the
  2025‑2026 web research and sources that justify each change.

## What changed vs the original prompt

- Corrected terminology: **Perimeter** (not "Peripheral") Intrusion Detection System.
- Added a **normative/regulatory** section (IEC/EN 62676 incl. 62676‑4:2025, EN 50131, GDPR,
  NIS2, NDAA) with a DPIA and retention policy.
- Quantified targets: **NAR < 5 alarms/day/km**, **detection→alert P95 < 2 s**.
- Modern edge AI (YOLO11/12/26, tracking, MLOps loop) and **multi-sensor fusion** roadmap.
- Layered camera integration (**ONVIF T/M → RTSP/RFC 7826 → vendor SDK**) + media gateway.
- Explicit **Kafka** event backbone with **idempotency + dedup windows**.
- **Rules-engine ADR** (JSON Decision Model vs Drools/CEP), versioned + dry-run.
- Hardened security (Zero-Trust, mTLS, OWASP ASVS, STRIDE, RPO/RTO) and a new
  **observability/SLO** section.

See `RESEARCH_NOTES.md` for the full table and sources.
