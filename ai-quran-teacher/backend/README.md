# AI Quran Teacher — Backend

NestJS + TypeORM + PostgreSQL API providing the Tajweed engine, quiz engine,
gamification engine, and user management.

## Modules

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

Requires PostgreSQL (`createdb ai_quran_teacher`). Schema sync is enabled via
`DB_SYNCHRONIZE=true` for development; switch to TypeORM migrations for
production.

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
