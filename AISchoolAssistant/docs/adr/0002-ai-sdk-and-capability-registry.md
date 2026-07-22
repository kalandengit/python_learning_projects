# ADR-0002: AI SDK + Capability Registry (AI-native core)

- **Status:** Accepted
- **Date:** 2026-07-22
- **Context:** Master Spec improvements #1–#5, #9–#11; Codex AI rules

## Decision
All AI usage flows through two mandatory layers, delivered before any
feature bounded context consumes AI:

1. **AI SDK** — a provider-agnostic port abstracting OpenAI, Anthropic, Google
   Gemini, Mistral, Ollama, and vLLM behind a single interface (chat,
   embeddings, tools, streaming). Business logic **never** imports a vendor SDK.
2. **Capability Registry** — the enterprise catalog of *capabilities* (a named,
   versioned unit: prompt/policy + model routing + input/output schema +
   evaluation suite + governance metadata). Features invoke a **registered
   capability by id/version**, never a raw model call.

Supporting layers (phased): **Agent Registry** + **Multi-Agent Runtime** (#3,#5),
**Native MCP** tool integration (#4), **AI Evaluation** (#9), **AI Observability**
(#10), **AI Governance** (#11).

## Motivation
- **Never bypass the Capability Registry / always use the AI SDK / every
  capability requires evaluation** are constitutional rules (Master Spec).
- Decouples business logic from providers (swap/route models without code
  changes); centralises cost, safety, evaluation, audit, and governance.

## Rules (enforced)
- A feature that calls a model directly (not via a registered capability) fails
  review and CI (lint rule + architectural test).
- Every capability ships with: an input/output schema, an **evaluation suite**
  (accuracy/safety/regression), and governance metadata (data class, PII policy,
  model allow-list, owner). No eval → capability cannot be promoted.
- All capability invocations emit OpenTelemetry traces + standardized events to
  the **Event Catalog** for AI Observability.

## Alternatives considered
- **Direct provider SDK per feature** — rejected: vendor lock-in, no central
  governance/eval, violates the constitution.
- **Thin wrapper only (no registry)** — rejected: loses evaluation, routing,
  governance, and reproducibility guarantees.

## Consequences
- WP-2 delivers the AI SDK + Capability Registry (+ evaluation/governance hooks)
  as foundation. All later AI features (AI Tutor, Teacher/Parent assistants,
  analytics) are *capabilities* registered against it.
- The Learner Digital Twin (#8) and Knowledge Platform (#7) are modeled as
  capability-consuming domains backed by Qdrant/OpenSearch.
