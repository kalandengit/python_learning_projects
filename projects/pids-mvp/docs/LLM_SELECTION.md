# PIDS — LLM Selection (2026)

Where an LLM adds value in a PIDS, which model to use, and how to keep it cheap and safe.
Model facts below are taken from the current Claude API reference (Claude API skill), not memory.

> **Guiding principle:** the LLM is an **assist layer**, never in the safety-critical
> detection→alert path. Intrusion decisions are made by the deterministic rule engine (§8 of
> the master prompt). The LLM summarizes, drafts, and assists — it never decides whether
> something is an intrusion. This keeps latency, cost, and liability bounded.

## Where an LLM helps (and where it must not)

| Use case | LLM? | Why |
|----------|------|-----|
| Alert **summary** ("2 humans crossed North fence at 23:41, high confidence") | ✅ | Cheap NL over structured data; speeds operator triage |
| **Incident report** generation (shift report, PDF) | ✅ | Batchable, non-real-time |
| **Natural-language → rule** authoring assistant ("alert on vehicles in parking at night") → JSON Decision Model | ✅ | Great fit; human reviews before activation |
| **Operator Q&A / RAG** over logs & docs | ✅ | Retrieval + synthesis |
| **False-positive triage** hints (suggest an exclusion mask / threshold) | ✅ | Advisory only; human applies |
| **Object detection** in the camera feed | ❌ | Use YOLO on-edge, not an LLM (latency/cost) |
| **Intrusion decision** | ❌ | Deterministic rule engine only (auditable, sub-second) |

## Model choice — Claude family (2026)

| Model | ID | Input / Output $/1M | Best PIDS use |
|-------|----|--------------------|---------------|
| **Haiku 4.5** | `claude-haiku-4-5` | $1 / $5 | High-volume, low-latency: per-alert **summaries**, classification, short triage hints |
| **Sonnet 5** | `claude-sonnet-5` | $3 / $15 (intro $2 / $10 through 2026-08-31) | **Report generation**, NL→rule assistant, operator RAG Q&A |
| **Opus 4.8** | `claude-opus-4-8` | $5 / $25 | Complex investigation / multi-step agentic analysis (rare, on-demand) |

**Recommendation:**
- **Default runtime model = Haiku 4.5** for the per-alert summary (highest volume, must be cheap
  and fast).
- **Sonnet 5** for report generation and the rule-authoring assistant (quality matters, volume
  is moderate).
- **Opus 4.8** reserved for on-demand deep investigation an operator explicitly triggers.

All are called through the official Anthropic SDK, using **Opus 4.8 as the default** only where
the extra capability is justified — do not silently downgrade a model the user pinned.

## Cost controls

1. **Prompt caching** — cache the stable system prompt + site/zone context so only the volatile
   alert payload is billed at full price (~90% savings on the cached prefix). Verify with
   `usage.cache_read_input_tokens`.
2. **Batch API (50% off)** — generate end-of-shift reports and bulk summaries via
   `messages.batches` rather than real-time calls.
3. **Right-size the model** — Haiku for summaries, Sonnet for reports; reach for Opus only when
   correctness clearly justifies it.
4. **Structured outputs** — use `output_config.format` (JSON schema) for the NL→rule assistant so
   the output is a valid rule object, not free text to re-parse.
5. **Adaptive thinking + effort** — `thinking: {type: "adaptive"}` with `effort: "low"` for
   summaries; raise to `high` only for investigation.

### Illustrative monthly cost (order-of-magnitude)

Assume 500 cameras, ~5 alerts/camera/day after NAR filtering ≈ **75,000 alerts/month**, each
summarized by Haiku 4.5 with prompt caching (≈1.5K cached + 0.3K fresh input, 0.15K output):

```
Fresh input:  75,000 × 300 tok  × $1 /1M  ≈ $22.5
Cached read:  75,000 × 1500 tok × $0.10/1M ≈ $11.3   (cache reads ~0.1× input)
Output:       75,000 × 150 tok  × $5 /1M  ≈ $56.3
                                             --------
                                    ≈ $90 / month for alert summaries
```

Reports (Sonnet 5, batch, ~1,000/month) add roughly **$30–60/month**. Total LLM assist cost is
a rounding error next to camera/compute spend — the value is faster operator triage and lower
mean-time-to-acknowledge (MTTA).

## Safety & governance

- LLM output is **advisory** and clearly labeled as AI-generated in the UI.
- No PII/biometric raw data sent to the LLM — summaries operate on structured metadata
  (class, zone, time, confidence), not raw video frames.
- Handle `stop_reason == "refusal"` gracefully (fall back to the deterministic template summary).
- Log prompts/responses to the audit trail for traceability; respect tenant data-residency.
