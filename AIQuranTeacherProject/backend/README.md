# AI Quran Teacher — Backend (NestJS)

Production-grade REST API providing Mistral-AI-powered tajweed correction,
AI-generated quizzes, gamification, user auth, and Quran content.

## Stack

- **NestJS 11** + TypeScript (strict)
- **TypeORM** — SQLite out of the box, PostgreSQL for production
- **JWT** auth (`@nestjs/jwt` + Passport) with bcrypt password hashing
- **Mistral AI** for tajweed analysis and quiz generation
- **class-validator** DTOs, **Helmet**, **@nestjs/throttler** rate limiting
- **Swagger** API docs, **Jest** unit + e2e tests

## Quick start

```bash
cp .env.example .env          # then set JWT_SECRET and MISTRAL_API_KEY
npm install
npm run start:dev             # http://localhost:3000/api
```

Interactive API docs (non-production): `http://localhost:3000/api/docs`.

With the default `DB_TYPE=sqlite`, the app runs with **zero external
dependencies** and seeds two surahs (Al-Fatihah, Al-Ikhlas) on first boot.

> Without a `MISTRAL_API_KEY`, the AI endpoints return `503`; everything else
> (auth, Quran, gamification) works fully.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run build` | Compile to `dist/` |
| `npm run start:dev` | Watch-mode dev server |
| `npm test` | Unit tests |
| `npm run test:e2e` | End-to-end tests (in-memory SQLite, mocked AI) |
| `npm run lint` | ESLint |

## API overview

All routes are prefixed with `/api`. Protected routes require
`Authorization: Bearer <token>`.

| Method | Route | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/health` | public | Liveness probe |
| `POST` | `/auth/register` | public | Create account, returns JWT |
| `POST` | `/auth/login` | public | Exchange credentials for JWT |
| `GET` | `/auth/me` | ✅ | Current user |
| `GET` | `/quran/surahs` | public | List surahs |
| `GET` | `/quran/surahs/:id` | public | Surah with ayahs |
| `GET` | `/quran/surahs/:surahId/ayahs/:ayah` | public | Single ayah |
| `POST` | `/tajweed/analyze` | ✅ | AI tajweed analysis of a recitation |
| `GET` | `/tajweed/history` | ✅ | Past analyses |
| `POST` | `/quiz/generate` | ✅ | Generate an AI quiz |
| `GET` | `/quiz/:id` | ✅ | Fetch a quiz (answers hidden) |
| `POST` | `/quiz/:id/submit` | ✅ | Grade a submission, award points |
| `GET` | `/gamification/me` | ✅ | Points, streak, badges |
| `GET` | `/gamification/badges` | ✅ | Badge catalogue |
| `GET` | `/gamification/leaderboard` | ✅ | Top users |

### Example

```bash
# Register
curl -s localhost:3000/api/auth/register -H 'content-type: application/json' \
  -d '{"email":"a@b.com","displayName":"Aisha","password":"StrongPass123"}'

# Analyse a recitation (use the returned token)
curl -s localhost:3000/api/tajweed/analyze -H "authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"surahId":1,"ayahNumber":1,"transcript":"bismillah ar rahman ar rahim"}'
```

## Configuration

See [`.env.example`](./.env.example). Notable variables:

- `DB_TYPE` — `sqlite` (default) or `postgres` (set `DATABASE_URL` or discrete vars)
- `JWT_SECRET` — **required, ≥ 32 chars in production**
- `MISTRAL_API_KEY`, `MISTRAL_MODEL` (default `mistral-large-latest`)
- `CORS_ORIGINS`, `THROTTLE_TTL_MS`, `THROTTLE_LIMIT`

## Production notes

- Set `DB_TYPE=postgres`, `DB_SYNCHRONIZE=false`, and use **migrations**.
- Run behind a TLS-terminating reverse proxy; keep Swagger disabled (default in prod).
- Build the container with the provided multi-stage [`Dockerfile`](./Dockerfile) (runs as non-root).

See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) and
[`../docs/SECURITY.md`](../docs/SECURITY.md).
