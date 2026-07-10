# AI Documentation Generator

Sprint 04 starter for an AI SaaS that turns screenshots into editable documentation.

## Current sprint status

Completed through **Sprint 04 — Background Jobs + Polling UI**.

The app now supports:

- Supabase authentication scaffold
- Organizations/workspaces
- Projects
- Screenshot uploads
- Private Supabase Storage
- AI document generation pipeline
- Structured AI output
- Document persistence
- Markdown editing/export
- Share links
- Async generation jobs
- BullMQ worker support
- DB-only local drain fallback
- Job polling UI

## Tech stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Supabase Auth, Postgres, Storage, RLS
- OpenAI Vision API
- BullMQ + Redis for background jobs
- Zod validation

## Quick start

```bash
npm install
cp .env.example .env.local
npm run dev
```

Run Supabase migrations in order:

```bash
supabase db push
```

## Required environment variables

```bash
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENAI_API_KEY=...
OPENAI_VISION_MODEL=gpt-4.1-mini
REDIS_URL=redis://localhost:6379
AI_WORKER_CONCURRENCY=2
AI_JOB_MAX_ATTEMPTS=3
```

## Running background jobs

### Production-style mode

Start Redis, then run the app and worker separately:

```bash
npm run dev
npm run worker:ai
```

### Local fallback mode without Redis

If `REDIS_URL` is empty, generation jobs stay queued in Postgres. Process them manually:

```bash
npm run jobs:drain
```

## Sprint 04 workflow

1. Upload a screenshot.
2. Open the upload detail page.
3. Click **Queue documentation generation**.
4. Keep the page open to watch polling status.
5. When complete, open the generated document.

## Important production notes

- Do not expose `SUPABASE_SERVICE_ROLE_KEY` to the browser.
- Run `npm run worker:ai` in a separate worker service in production.
- Use private storage buckets and signed URLs only.
- Monitor AI job failures and retry rates.
- Add cancellation/dead-letter dashboards in the next sprint.


## Sprint 05 — Editor Hardening and Version History

Sprint 05 adds production-minded document editing foundations:

- Immutable `document_versions` snapshots
- Restore previous versions
- Document word count and excerpt metadata
- Last saved timestamp and last editor tracking
- Autosave-ready API route
- Version listing API route
- Document detail sidebar with metadata and history

Run the new migration after Sprint 04:

```bash
supabase db push
```

Then restart the Next.js app. Manual saves now create restorable snapshots.

## Sprint 07 — Stripe Billing, Plans, and Quotas

Sprint 07 adds SaaS monetization foundations:

- Stripe Checkout for Starter, Pro, and Business subscriptions
- Stripe Customer Portal for subscription and invoice management
- Stripe webhook endpoint with signature verification
- Subscription state synchronized into Supabase
- Billing dashboard at `/billing`
- Public pricing page at `/pricing`
- Monthly upload and AI-generation quota enforcement
- Usage event logging for quota calculations

### Stripe setup

Create three recurring monthly prices in Stripe and add them to `.env.local`:

```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER_MONTHLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_BUSINESS_MONTHLY=price_...
```

For local webhook testing:

```bash
stripe listen --forward-to localhost:3000/api/stripe/webhook
```

Subscribe production webhooks to:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`

### Current plan limits

| Plan | Price | AI documents/month | Uploads/month | Storage | Seats |
| --- | ---: | ---: | ---: | ---: | ---: |
| Free | $0 | 5 | 10 | 100MB | 1 |
| Starter | $19 | 50 | 100 | 1GB | 3 |
| Pro | $49 | 250 | 500 | 10GB | 10 |
| Business | $149 | 1,000 | 2,000 | 100GB | 25 |

Webhook updates, not checkout redirects, are treated as the source of truth for paid entitlements.


## Sprint 08 — Analytics and Admin Visibility

Sprint 08 adds a durable analytics foundation:

- `analytics_events` stores first-party product events in Supabase.
- Optional PostHog client/server capture is enabled with env vars.
- `/analytics` shows workspace activation, exports, AI jobs, costs, top events, and recent event stream.
- `/admin` gives early operator visibility for workspace health.
- `feature_flags` provides the database foundation for safer feature rollouts.

### Analytics environment variables

```bash
NEXT_PUBLIC_POSTHOG_KEY=phc_placeholder
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
POSTHOG_API_KEY=phx_placeholder
```

PostHog is optional. If these values are empty, the app still records first-party analytics in Supabase.

### Sprint 08 migration

Apply:

```bash
supabase/migrations/008_sprint08_analytics_admin.sql
```

### Review notes

See `docs/SPRINT_08_REVIEW.md` for architecture decisions, tradeoffs, and the next sprint recommendation.


## Sprint 09 additions

Team collaboration is now scaffolded with role-based workspace access.

### Added

- `/team` dashboard route for members and pending invitations
- Organization invitations with secure acceptance tokens
- Owner/admin/member role model
- Server-action authorization helpers
- Organization-scoped RLS helper functions
- Collaboration policies for projects, uploads, documents, exports, versions, AI jobs, and usage events

### Local acceptance flow

1. Sign in as an owner.
2. Open `/team`.
3. Invite a second account by email.
4. Copy the token URL shown under pending invitations.
5. Sign in as the invited email.
6. Visit `/api/invitations/<token>`.

Sprint 10 should replace manual token copy with transactional email delivery.

## Sprint 10 — Profiles, emails, audit logs, notifications

Apply the new migration:

```bash
supabase migration up
```

Add email configuration:

```env
RESEND_API_KEY=re_placeholder
EMAIL_FROM="DocuPilot AI <onboarding@resend.dev>"
```

If `RESEND_API_KEY` is not configured, the app logs invitation links to the server console so local development still works.

New routes:

- `/settings` — profile settings
- `/notifications` — user notification center
- `/admin/audit-logs` — workspace audit history

Sprint 10 intentionally keeps notifications database-backed. Realtime delivery, email digests, and Slack notifications are planned for a later collaboration sprint.

## Sprint 11 — Tests, CI/CD, security checks, production readiness

Sprint 11 adds production-readiness guardrails so the codebase can be changed safely.

### Added

- Vitest unit test configuration
- Playwright E2E smoke test configuration
- Unit tests for Markdown rendering, slugging, and security header policy
- Public page smoke tests
- GitHub Actions CI workflow
- Supabase migration validation workflow
- Dependabot configuration
- Security headers in `next.config.ts`
- Security header CI check script
- Production readiness checklist

### New commands

```bash
npm run ci
npm run test
npm run test:coverage
npm run test:e2e
npm run security:headers
npm run security:audit
npm run predeploy
```

### CI secrets

Add these GitHub repository secrets before enabling required CI checks:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

### Sprint 11 docs

- `docs/SPRINT_11_REVIEW.md`
- `docs/CI_CD.md`
- `docs/PRODUCTION_READINESS.md`

Sprint 12 should focus on launch assets, legal pages, final onboarding, and a beta release checklist.

## Sprint 12: Beta Launch Package

Sprint 12 adds the launch-readiness layer:

- Public Privacy, Terms, Security, Beta, and Contact pages
- Dashboard onboarding checklist
- Feedback capture API and database migration
- `robots.ts` and `sitemap.ts` metadata routes
- Product Hunt launch kit
- Beta testing guide
- Launch plan
- Legal review notes
- Demo guide sample data

### Sprint 12 environment reminder

Set `NEXT_PUBLIC_APP_URL` in Vercel for correct sitemap URLs and redirects. Vercel keeps environment variables per environment, so configure Development, Preview, and Production separately.

### Before public traffic

Add rate limiting and spam protection to `/api/feedback` before a large Product Hunt or paid campaign launch.


## Sprint 13: Browser extension

A Manifest V3 extension now lives in `browser-extension/`. Apply migration 013, generate a scoped token under Settings, then build and load the extension. See `browser-extension/README.md`.
