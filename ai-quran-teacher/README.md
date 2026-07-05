# AI Quran Teacher

An enterprise-grade, AI-powered Quran learning platform: real-time Tajweed
feedback, an AI Islamic tutor, timed certification exams, live classes,
quizzes, and gamification — designed to scale to millions of users.

**Key docs:**
[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) ·
[Technical Requirements](docs/TECHNICAL_REQUIREMENTS.md) ·
[LLM & Parallel Inference Guide](docs/LLM_GUIDE.md)

## Repository layout

| Directory | What it is | Status |
|---|---|---|
| [`backend/`](backend/) | NestJS API: auth, Tajweed, quizzes, exams/certificates, gamification, AI tutor, health (PostgreSQL + Redis + TypeORM) | ✅ Builds, 28 unit tests, verified end-to-end against live Postgres + Redis |
| [`signaling-server/`](signaling-server/) | Node.js + Socket.IO WebRTC signaling for live classes | ✅ Runs, `/health` endpoint |
| [`ios/`](ios/) | SwiftUI app: reader, AI tutor, exams, quizzes, progress — with a full design system | 🛠️ Sources complete; create the Xcode project ([ios/README.md](ios/README.md)) |
| [`docs/`](docs/) | Implementation guide, technical requirements, LLM guide | — |
| [`docker-compose.yml`](docker-compose.yml) | Full local stack (Postgres + Redis + API + signaling) | ✅ |

CI workflows are at the repo root in [`.github/workflows/`](../.github/workflows/).

## What's included

- **AI Islamic tutor** (`backend/src/tutor` + `llm`) — one question fans out to
  **several Claude calls running simultaneously** (answer, tafsir, Tajweed,
  follow-ups), assembled into a single response. Safe, sourced, never issues
  fatwas. See [LLM_GUIDE.md](docs/LLM_GUIDE.md).
- **Certification exams** (`backend/src/exam`) — timed, auto-graded exams at
  three levels that issue **publicly verifiable certificates**.
- **Tajweed engine** — rule-based detection with word-level recitation
  alignment; on-device Swift fallback for offline use.
- **Enterprise hardening** — JWT + bcrypt auth, Helmet, rate limiting, Redis
  caching, health/readiness probes, graceful shutdown, horizontal scaling.
- **Creative iOS design system** (`ios/DesignSystem`) — an emerald/gold
  "Dark Mode 2.0" theme with gradients, glass cards, and progress rings that
  adapt to light/dark automatically.

## Quick start

### Full stack (Docker)

```bash
docker compose up --build
# API on :3000, signaling on :3001, Postgres on :5432, Redis on :6379
```

### Backend only

```bash
cd backend
cp .env.example .env          # point at your Postgres (Redis + Anthropic optional)
createdb ai_quran_teacher
npm install
npm run start:dev             # http://localhost:3000
npm test                      # 28 unit tests, no DB needed
```

Try the Tajweed engine and the AI tutor:

```bash
curl -X POST http://localhost:3000/tajweed/detect \
  -H "Content-Type: application/json" \
  -d '{"text":"بسم الله الرحيم","ayahId":1,"expectedText":"بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}'

# Requires ANTHROPIC_API_KEY; fans out to parallel Claude calls
curl -X POST http://localhost:3000/tutor/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the rule of Ikhfa and when does it apply?"}'
```

## API overview

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` · `POST /auth/login` | JWT auth (bcrypt) |
| `POST /tajweed/detect` · `/analyze` · `GET /tajweed/rules` | Tajweed engine |
| `POST /quiz/generate` · `/submit` · `GET /quiz/history/:userId` | Quizzes |
| `POST /exams/start` · `/submit` · `GET /exams/certificates/:userId` | Certification exams |
| `GET /exams/verify/:code` | Public certificate verification |
| `POST /tutor/ask` · `GET /tutor/status` | AI Islamic tutor (parallel LLM) |
| `GET /gamification/profile/:userId` · `/leaderboard` · `POST /activity` | Gamification |
| `GET /health` · `GET /ready` | Liveness / readiness probes |
