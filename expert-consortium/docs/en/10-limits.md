# 10 — Limits & scaling behavior (English)

What happens when you push the system hard, and which knobs exist (all in `.env`).

## Automatic protections (nothing to configure)

| Situation | What the system does |
|---|---|
| Audio/video longer than ~100 min | Automatically split into segments, transcribed one by one, merged — a 5-hour lecture just works |
| Very large document to embed | Embedding requests are batched by size so the API never rejects them |
| PDF/image over 45 MB | Refused with a clear message and advice to split the PDF first |
| Web upload over 500 MB | Refused (413); files are streamed to disk, so big uploads never fill the RAM |
| More than 30 questions/minute | Refused (429) — protects your Mistral budget if the password leaks |
| 10 wrong passwords in 5 min | Login blocked for 5 minutes (brute-force protection) |
| File still being copied into uploads/ | The watcher waits until the size is stable before ingesting |
| Telegram file over 20 MB | Politely refused (hard Telegram bot limit) with a redirect to web/folder upload |
| One file fails during batch ingest | The others continue; the error is printed and logged |
| Log file growth | `logs/app.log` rotates at 5 MB, keeping 3 old files |

## The one real constraint: two processes, one local database

Embedded storage (`QDRANT_URL` empty) allows **one process at a time**. Running the web app
AND the Telegram bot together needs a Qdrant server:

- **With Docker (recommended, what the VPS uses):** `docker compose up -d` — Qdrant runs as
  a service and both app and bot connect to it. Nothing to configure.
- **Without Docker:** run only one process at a time, or install a local Qdrant server and
  set `QDRANT_URL=http://localhost:6333`.

If you hit it, the error message tells you exactly this.

## Tuning knobs (`.env`)

```
MAX_UPLOAD_MB=500            # web upload cap
MAX_OCR_MB=45                # OCR file-size guard
AUDIO_SEGMENT_MINUTES=100    # split threshold for long recordings
CHAT_RATE_PER_MIN=30         # questions per minute
EMBED_BATCH_CHAR_BUDGET=40000
```

## Realistic capacity (personal use, €5 VPS)

- **Knowledge base:** tens of thousands of chunks (≈ thousands of documents) are fine for
  Qdrant on 4 GB RAM; retrieval stays fast.
- **Ingestion throughput:** limited by the Mistral free/paid tier rate limits, not by the
  machine — big archives simply take a while (the retry/backoff handles rate limits
  automatically).
- **Users:** this is a single-user system by design (one shared password, one Telegram ID).
  Multi-user is out of scope for v1 (see PRD §3).
