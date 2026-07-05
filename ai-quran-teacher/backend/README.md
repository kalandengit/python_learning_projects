# AI Quran Teacher — Backend

NestJS + TypeORM + PostgreSQL API providing the Tajweed engine, quiz engine,
gamification engine, and user management.

## Modules

- **`src/auth/`** — Register/login with JWT access tokens and bcrypt password
  hashing (cost 12). Credentials live in a separate `auth_credentials` table
  from the `User` profile. `JwtAuthGuard` protects routes; roles come from the
  token.
- **`src/tutor/` + `src/llm/`** — The AI Islamic tutor. `LlmService` wraps the
  Anthropic SDK (default `claude-opus-4-8`) and exposes `parallel()`, a bounded
  worker pool that runs many Claude calls **concurrently**. `TutorService`
  fans one question out to four aspects (answer, tafsir, Tajweed, follow-ups)
  simultaneously. Safe, sourced, never issues fatwas. See
  [`../docs/LLM_GUIDE.md`](../docs/LLM_GUIDE.md).
- **`src/exam/`** — Timed certification exams (foundation/intermediate/advanced)
  with auto-grading, pass thresholds, expiry, and **verifiable certificates**
  (`GET /exams/verify/:code`).
- **`src/common/`** — `RedisService`: shared cache and cross-instance
  coordination; degrades to a no-op when `REDIS_URL` is unset.
- **`src/health/`** — `GET /health` (liveness) and `GET /ready` (readiness +
  subsystem status) for load-balancer probes.
- **`src/tajweed/`** — Rule-based Tajweed analysis (`tajweed.rules.ts`) and
  recitation checking. `detectMistakes` aligns the recited transcript against
  the expected mushaf text with word-level Levenshtein alignment, so one
  skipped word doesn't cascade into errors for the rest of the ayah. Detected
  rules: izhar, idgham (±ghunnah), iqlab, ikhfa, qalqalah, ghunnah, and
  natural/extended madd. Mistakes are persisted per user for the Hifz
  spaced-repetition roadmap.
- **`src/quiz/`** — Serves quizzes from a curated question bank
  (`question-bank.ts`, easy/medium/hard). Correct answers never leave the
  server until submission; grading awards XP and badges.
- **`src/gamification/`** — Badges (`badges.catalog.ts`), daily streaks with
  idempotent same-day updates, XP/levels, and a leaderboard.
- **`src/users/`** — User CRUD with roles: student, parent, teacher, org_admin.

## Running

```bash
cp .env.example .env
npm install
npm run start:dev
```

Requires PostgreSQL (`createdb ai_quran_teacher`). Redis and Anthropic are
optional in development — the app runs single-node without them and reports
their status at `GET /ready`. Schema sync is enabled via `DB_SYNCHRONIZE=true`
for development; switch to TypeORM migrations for production.

### Enterprise features

- **Auth:** JWT (`JWT_SECRET`, `JWT_EXPIRES_IN`) + bcrypt.
- **Rate limiting:** global `RATE_LIMIT`/min, tighter on `/auth` and `/tutor`.
- **Security headers:** Helmet; CORS locked to `ALLOWED_ORIGINS` in prod.
- **Scaling:** stateless instances + Redis (`REDIS_URL`) + Postgres read
  replicas; see [`../docs/TECHNICAL_REQUIREMENTS.md`](../docs/TECHNICAL_REQUIREMENTS.md).
- **AI tutor:** set `ANTHROPIC_API_KEY`; tune `LLM_MAX_CONCURRENCY`.

## Testing

```bash
npm test
```

Unit tests mock the repositories, so no database is needed. Coverage:
Tajweed rule detection and transcript alignment, quiz generation/grading/
anti-resubmission, badge idempotency, streak transitions, level math.

## Extending the Tajweed engine with ML

`TajweedService.analyze`/`detectMistakes` are the seams: keep the response
shapes and swap the text-rule implementation for calls to an audio model
(e.g. a wav2vec2 fine-tune served from Python) when it's ready.
