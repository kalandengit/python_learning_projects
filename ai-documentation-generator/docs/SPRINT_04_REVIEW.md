# Sprint 04 Review — Background Jobs + Polling UI

## Goal
Move AI documentation generation out of the blocking request/response path and into an asynchronous processing model.

## What changed
- Added BullMQ + Redis queue integration.
- Added DB-only fallback drain script for local development without Redis.
- Added service-role Supabase worker client.
- Added reusable `runAiDocumentationJob` runner.
- Added worker script with graceful shutdown.
- Added job status API endpoint.
- Added client-side polling component.
- Added queue metadata migration.

## Architecture decision
The web app creates the DB job first, then attempts to enqueue it in BullMQ. If Redis is unavailable, the job remains queued in Postgres and can be processed with `npm run jobs:drain`.

This gives two operating modes:

1. **Production mode:** `REDIS_URL` configured + `npm run worker:ai` running.
2. **Local fallback mode:** no Redis + manual `npm run jobs:drain`.

## Tradeoffs
BullMQ requires a separate Redis service and worker runtime, but gives retries, backoff, concurrency, and production-grade queue semantics. The DB fallback is simpler for local development, but should not be the default for high-volume production.

## Security review
- Service role key is isolated to worker/admin scripts.
- User-facing job API still uses normal authenticated Supabase access and RLS.
- Storage files remain private; workers use short-lived signed URLs.

## Known limitations
- Cancel job UI is planned for Sprint 05.
- Worker deployment is documented but not yet containerized.
- No dead-letter dashboard yet.

## Definition of done
- User can queue generation without blocking the browser.
- UI polls job status.
- Completed jobs link to generated documents.
- Failed jobs display errors.
- Worker can process queued jobs.
