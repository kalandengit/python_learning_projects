# 06 — LLM Selection (research as of July 2026)

## 1. What the education workload actually needs

Before comparing models, the task profile — different features stress different capabilities:

| Feature | Dominant needs | Volume | Latency-sensitive? |
|---------|----------------|--------|--------------------|
| Student tutor chat | Pedagogy/instruction-following, safety, grounded reasoning, warmth | **Very high** | Yes (streaming) |
| Draft grading | Rubric adherence, consistency, evidence extraction | High (batchable) | No |
| Lesson/content generation | Structured long-form quality, curriculum alignment | Medium | Somewhat |
| Moderation & classification | Cheap, fast, reliable classification | Very high | Yes |
| Insight clustering/summaries | Summarization at scale | Medium (nightly) | No |

Conclusion up front: **no single model is optimal for all five** — the July-2026 consensus in
model-selection guides is that a **routing strategy beats any single-model bet**
([iternal.ai LLM selection guide](https://iternal.ai/llm-selection-guide),
[BenchLM 2026 comparison](https://benchlm.ai/blog/posts/chatgpt-vs-claude-vs-gemini-2026)).

## 2. Frontier landscape (July 2026)

From current benchmark aggregators ([LM Council](https://lmcouncil.ai/benchmarks),
[BenchLM](https://benchlm.ai/blog/posts/chatgpt-vs-claude-vs-gemini-2026),
[tech-insider comparison](https://tech-insider.org/claude-vs-chatgpt-vs-gemini-2026/)):

| Family | Standout strengths | Watch-outs for our use case |
|--------|--------------------|------------------------------|
| **Anthropic Claude** (Fable 5 / Opus 4.8 / Sonnet 5 / Haiku 4.5) | Tops overall aggregate rankings (Mythos/Fable 5 lead; Opus 4.8 leads SWE-bench Pro 69.2% vs GPT-5.5 58.6% / Gemini 3.1 Pro 54.2%); strongest instruction-following & long-horizon consistency — exactly what an *enforced Socratic policy* depends on; 1M context; mature safety posture | Premium pricing at the top tier (mitigated by routing to Sonnet/Haiku) |
| **Google Gemini** (3.x Pro / 3.5 Flash) | Best abstract reasoning (ARC-AGI-2) and science benchmarks (GPQA ~94%); excellent multimodal; Flash is very cheap; NotebookLM shows Google's strength in *study-material* UX ([XDA study-tools test](https://www.xda-developers.com/tested-notebooklm-gemini-claude-and-chatgpt-for-studying/)) | Instruction-following on strict persona policies historically less steerable; ecosystem lock-in |
| **OpenAI GPT-5.x** | Strong structured reasoning and computer-use; large ecosystem | Middle of pack on the agentic/consistency benchmarks we care most about |
| **Open-weight (Llama 4, DeepSeek)** | Self-hosting = maximal data control; no per-token cost at scale | Real gap to frontier on pedagogy-critical instruction following; we'd own safety fine-tuning, evals, and GPU ops — wrong trade for a small team in v1 |

Note: classic benchmarks (MMLU, GSM8K, HumanEval) are saturated in 2026 and no longer
discriminate between frontier models; the meaningful education-adjacent signals are
instruction-following/steerability, refusal quality, long-conversation consistency, and cost.
**Public benchmarks are a prior, not a verdict — our own eval suite (grounding, answer-leak,
rubric agreement; see 03_MVP §4) is the final selector.**

## 3. Pricing snapshot (per 1M tokens, July 2026)

Sources: [TLDL pricing table](https://www.tldl.io/resources/llm-api-pricing),
[BenchLM pricing](https://benchlm.ai/llm-pricing), [PricePerToken](https://pricepertoken.com/),
Anthropic official pricing.

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| Claude Fable 5 | $10.00 | $50.00 | Frontier tier — overkill for v1 |
| Claude Opus 4.8 | $5.00 | $25.00 | 1M ctx, top agentic quality |
| **Claude Sonnet 5** | **$3.00 ($2.00 intro to 2026-08-31)** | **$15.00 ($10.00 intro)** | Near-Opus quality on our tasks |
| Claude Haiku 4.5 | $1.00 | $5.00 | Fast classification tier |
| GPT-5.4 (ref.) | ~$2.50 | ~$10 | Comparable mid-tier |
| Gemini 3.5 Flash (ref.) | <$1 | <$3 | Cheapest capable tier |

**Cost levers that matter more than sticker price:**
- **Prompt caching** — cached reads ≈ 0.1× input price. Tutor sessions re-send the same class
  persona/policy/context every turn → ~90% savings on that prefix.
- **Batch API** — 50% off everything; grading and nightly digests are batch-perfect.
- **Routing** — sending moderation/classification (the highest-volume calls) to Haiku instead
  of Sonnet is an ~70% cut on that traffic.

### Cost model vs. target (≤ $1.50 / student-month)

Assume an active student: 40 tutor turns/mo (avg 3K cached + 700 fresh input, 350 output),
plus moderation on every turn, plus amortized grading/digests:
- Tutor (Sonnet 5): ≈ $0.45 · Moderation+summaries (Haiku): ≈ $0.08
- Grading share (Opus 4.8, batch): ≈ $0.15 · Digests (batch, Sonnet): ≈ $0.05
- **≈ $0.75/student-month** → comfortable 2× headroom under the $1.50 target.

## 4. Recommendation

**Primary provider: Anthropic Claude, with a routing table and a thin provider-abstraction
layer (`LLMGateway`) keeping Gemini as tested fallback/secondary.**

| Task class | Model | Rationale |
|------------|-------|-----------|
| Tutor conversation | **Claude Sonnet 5** | Best steerability-per-dollar; the Socratic policy holding up under 40-turn adversarial chats is the product; near-Opus quality at 1/3 the price |
| Lesson plans, quizzes, re-teach content | **Claude Opus 4.8** | Highest structured long-form quality; low volume so premium is affordable |
| Draft grading | **Claude Opus 4.8 via Batch API** | Consistency across a batch is the requirement; batch −50% makes it cheap |
| Moderation, classification, session tagging, routing | **Claude Haiku 4.5** | Fast + cheap at the highest call volume |
| Fallback (provider outage) | **Gemini 3.x** (Flash for tutor, Pro for generation) | Independent infrastructure; kept warm by running 5% of eval traffic through it |
| Embeddings | Provider embedding API (benchmark Voyage vs. Gemini embedding at build time) | Decided by retrieval eval, not brand |

**Why not…**
- *Single cheap model everywhere:* answer-leak and jailbreak-resistance evals are exactly
  where cheap tiers degrade; the tutor is student-facing and minor-facing — quality floor is a
  safety property.
- *Self-hosted open weights in v1:* data-control appeal is real, but we'd trade a provider
  contract clause ("no training on inputs", available today) for owning GPU ops, safety
  tuning, and red-teaming with a small team. Revisit at scale or for on-prem district deals.
- *Heavy framework (LangChain) instead of thin gateway:* our routing/caching/audit needs are
  simple and stability-critical; plain official SDKs + ~300 lines of gateway code.

## 5. Decision review triggers

Re-run this analysis when any of: Sonnet 5 intro pricing ends (2026-08-31); a provider ships
an education-tuned tier; our eval suite shows a rival model ≥5 pts better on grounding or
leak-resistance; monthly LLM spend > 25% of revenue; a district requires on-prem.

## Sources

- [LM Council — AI model benchmarks (July 2026)](https://lmcouncil.ai/benchmarks)
- [BenchLM — ChatGPT vs Claude vs Gemini 2026](https://benchlm.ai/blog/posts/chatgpt-vs-claude-vs-gemini-2026) · [BenchLM pricing](https://benchlm.ai/llm-pricing)
- [Tech-Insider — Claude vs ChatGPT vs Gemini 2026](https://tech-insider.org/claude-vs-chatgpt-vs-gemini-2026/)
- [Iternal — LLM selection guide (30+ models)](https://iternal.ai/llm-selection-guide)
- [TLDL — LLM API pricing (July 2026)](https://www.tldl.io/resources/llm-api-pricing) · [PricePerToken](https://pricepertoken.com/)
- [XDA — NotebookLM vs Gemini vs Claude vs ChatGPT for studying](https://www.xda-developers.com/tested-notebooklm-gemini-claude-and-chatgpt-for-studying/)
- Anthropic official model & pricing documentation (platform.claude.com)
