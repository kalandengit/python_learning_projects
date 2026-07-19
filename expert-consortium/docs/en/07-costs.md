# 7 — Costs (English)

*Prices as of July 2026 — always check <https://mistral.ai/pricing/> for current numbers.*

## Development: $0

Mistral's free **Experiment** tier gives rate-limited access to all API models (≈1B
tokens/month). It covers the entire setup, testing, and light personal use.

## Personal production use — typical monthly estimate

| Item | Price basis | Typical personal usage | Est. cost |
|---|---|---|---|
| OCR (PDFs, images) | ~$1–3 / 1,000 pages | 200 pages/mo | < $1 |
| Audio/video transcription (Voxtral) | $0.003 / minute | 10 hours/mo | ~$1.80 |
| Embeddings (`mistral-embed`) | ~$0.10 / 1M tokens | indexing + queries | < $0.50 |
| Chat (`mistral-large-latest`) | $2 in / $6 out per 1M tokens | ~50 questions/day | $3–8 |
| Chat (`mistral-small-latest`) — cheaper alternative | $0.10 / $0.30 per 1M | same usage | < $1 |
| Fine-tuning job | one-time per run | occasional | $1–10 per run |
| VPS (Hetzner CX22 or similar) | monthly | always on | €5–9 |
| Telegram bot | free | — | $0 |

**Realistic total: €6–18 / month.** Switch `CHAT_MODEL` to `mistral-small-latest` in `.env`
to cut chat costs ~10× (a fine-tuned Small often matches Large on your specific domains —
that is one of the main reasons to fine-tune).

## Cost control tips

1. Start on the free tier; only add a payment method when you hit rate limits.
2. Set a **spending limit** in the Mistral console (Billing → Limits).
3. Ingestion is the expensive step for large archives — OCR of a 5,000-page archive costs
   ~$5–15, but it is paid **once**; questions afterwards are cheap.
4. Watch usage in the Mistral console dashboard (per-endpoint breakdown).
