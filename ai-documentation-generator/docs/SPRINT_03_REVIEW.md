# Sprint 03 Review — AI Pipeline Hardening

## Goal
Move from a direct single-call AI generation action to a safer MVP AI pipeline with structured outputs, provider abstraction, job tracking, usage telemetry, and better generation observability.

## Current research alignment
- Next.js App Router Route Handlers remain the correct mechanism for machine/API-style endpoints.
- OpenAI Structured Outputs are used because they constrain model responses to a JSON Schema instead of relying on loose JSON mode.
- Supabase SSR/Auth and RLS remain the authorization foundation.
- Zod remains the runtime validation layer for untrusted AI/API payloads.

## Implemented
- `lib/ai/schemas.ts` for Zod + JSON Schema generated-document contracts.
- `lib/ai/providers/openai.ts` for OpenAI Vision structured-output generation.
- `lib/ai/pipeline.ts` as the orchestration entry point.
- `lib/ai/jobs.ts` for job creation, processing, telemetry, and document persistence.
- `supabase/migrations/003_sprint03_ai_pipeline.sql` for `ai_jobs`, indexes, RLS, triggers, and usage view.
- Upload detail page now shows AI job history.
- `GET /api/ai/jobs/[id]` provides job-status lookup.
- Markdown generation now includes detected UI, confidence score, expected results, tips, warnings, FAQ, and model metadata.

## Tradeoffs
- Jobs are still processed synchronously inside the Server Action for MVP simplicity. This avoids Redis/BullMQ setup in early development.
- The database model is designed so Sprint 04 can move the same processing logic into a background worker without changing the user-facing schema.
- Cost estimation is intentionally conservative and should be replaced with exact model-pricing configuration before production billing.

## Risks
- Long AI calls can hit serverless timeout limits on large images or slow providers.
- Signed URLs expire, so background processing will need service-role storage access or freshly generated signed URLs.
- Vision output quality depends strongly on screenshot clarity and context.

## Definition of done check
- Structured schema exists: yes.
- AI response is validated server-side: yes.
- Job telemetry exists: yes.
- RLS policies exist: yes.
- User can see generation history: yes.
- Background queue exists: not yet; scheduled for Sprint 04.
