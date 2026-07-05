# LLM Selection & Parallel Inference Guide

This platform's AI Islamic tutor is built on **Claude** (Anthropic). This
document explains the model choice, how the parallel-inference design works,
and how to operate it cost-effectively.

> Model IDs, pricing, and API behavior below reflect the Anthropic API as of
> the platform's build. Always confirm current model IDs and pricing at
> [platform.claude.com](https://platform.claude.com/docs/en/about-claude/models/overview)
> before a production launch, and query the Models API for live capability data.

## Why Claude

For a religious-education tutor, three properties matter most, and they rank
above raw benchmark scores:

1. **Faithful, low-hallucination instruction following.** The tutor must stay
   within the sourced scholarship in its system prompt and refuse to
   fabricate rulings. Claude's strong instruction adherence and its tendency
   to say "I'm not certain" rather than invent are a direct fit.
2. **Safety and steerability.** The `SAFETY_PREAMBLE` in
   `backend/src/tutor/tutor.prompts.ts` constrains the model to mainstream,
   attributed sources and forbids issuing fatwas. Claude honors these
   guardrails reliably.
3. **Long context + strong Arabic.** A 1M-token context window lets us pass
   full surah context, tafsir excerpts, and prior conversation without
   truncation; Arabic comprehension is needed for Tajweed and tafsir.

## Recommended models

| Use case | Model | Why |
|---|---|---|
| **Default — tutor answers, tafsir, reasoning** | `claude-opus-4-8` | Most capable Opus-tier model; best judgment on nuanced religious content. This is the platform default (`LlmService.DEFAULT_MODEL`). |
| High-volume, cost-sensitive aspects (follow-up questions, simple rephrasing) | `claude-sonnet-5` | Near-Opus quality at lower cost; good for the lighter fan-out aspects if budget is tight. |
| Latency-critical / cheap classification (e.g. moderation pre-checks) | `claude-haiku-4-5` | Fastest and cheapest; use only where quality tolerance is high. |
| Most demanding long-horizon reasoning | `claude-fable-5` | Anthropic's most capable model; reserve for research or content-generation pipelines where cost is justified. |

**Default policy:** use `claude-opus-4-8` unless you have a measured reason to
downgrade. Don't pick a cheaper model for cost alone without checking answer
quality on a held-out set of real student questions.

### Thinking & effort

The tutor turns on **adaptive thinking** (`thinking: {type: "adaptive"}`) for
the main answer aspect, where multi-step reasoning improves quality, and uses
the **effort** parameter to trade cost against depth:

- Main answer: `effort: "high"` + adaptive thinking.
- Tafsir / Tajweed / follow-ups: `effort: "low"`, no thinking — keeps the
  fan-out fast and cheap.

These are set per-aspect in `TutorService.ask`.

## Parallel / simultaneous inference

The headline design feature: a single student question fans out into **several
independent Claude calls that run concurrently**, then the results are
assembled into one response.

```
                    ┌─────────────────────────────┐
  "Explain Ikhfa    │  TutorService.ask()         │
   in this ayah" ──▶│  builds 4 CompletionRequests│
                    └──────────────┬──────────────┘
                                   │  LlmService.parallel()
             ┌───────────┬─────────┼─────────┬───────────┐
             ▼           ▼         ▼         ▼           
        answer      tafsir    tajweed   followUp     (concurrent Claude calls)
        (opus,      (opus,    (opus,    (opus,
         high)       low)      low)      low)
             └───────────┴─────────┴─────────┴───────────┐
                                   ▼
                    assembled TutorResponse (+ token usage, latency)
```

Because the four aspects are independent, wall-clock latency is roughly that
of the **slowest single call**, not the sum of all four.

### How it's implemented

`LlmService.parallel()` (in `backend/src/llm/llm.service.ts`) is a bounded
worker pool:

- Runs up to `LLM_MAX_CONCURRENCY` (default 8) requests at once, so a large
  fan-out can't exhaust the Anthropic rate limit or the Node event loop.
- Preserves input order in the results.
- Captures per-request failures instead of rejecting the whole batch — if the
  tafsir call fails, the student still gets the answer, tafsir, and Tajweed
  that succeeded.

This same primitive is reusable for other batch/fan-out workloads: generating
a quiz set, pre-computing tafsir for a whole surah, or grading many
recitations in parallel.

### Beyond fan-out: other parallel patterns

- **Map-reduce:** split a long passage into chunks, summarize each chunk in
  parallel (`parallel()`), then a final reduce call composes them.
- **Ensemble / self-consistency:** ask the same question N times and pick the
  most consistent answer for high-stakes content.
- **Batch API:** for non-latency-sensitive bulk jobs (pre-generating tafsir
  for all 6,236 ayahs), use Anthropic's Message Batches API at 50% cost
  instead of the live fan-out.

## Cost controls

- **Per-aspect effort:** only the main answer pays for high effort + thinking.
- **Prompt caching:** the `SAFETY_PREAMBLE` and per-aspect system prompts are
  stable prefixes — enabling prompt caching on them cuts input cost ~90% on
  repeat calls. (Add `cache_control` on the system block in `LlmService`.)
- **Concurrency cap:** `LLM_MAX_CONCURRENCY` bounds spend spikes.
- **Rate limiting:** the `/tutor/ask` route is capped at 10 req/min per client
  (`@Throttle`) so a single user can't run up the bill.
- **Redis cache:** identical questions can be served from Redis
  (`RedisService.remember`) instead of re-calling Claude.

## Safety & compliance notes

- The tutor **never issues fatwas**; the system prompt and the iOS disclaimer
  both direct users to qualified scholars for rulings.
- Responses are labelled AI-generated in the UI.
- No student PII is sent to the model beyond the question text and optional
  ayah context.
- Set `ANTHROPIC_API_KEY` via secrets management (never commit it). The
  service degrades gracefully — `GET /tutor/status` reports `available: false`
  — when no key is configured.

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic credentials | (unset → tutor disabled) |
| `LLM_MAX_CONCURRENCY` | Max simultaneous Claude calls | `8` |

The Anthropic SDK also resolves `ANTHROPIC_AUTH_TOKEN` and `ant auth login`
profiles — see the [SDK docs](https://platform.claude.com/docs).
