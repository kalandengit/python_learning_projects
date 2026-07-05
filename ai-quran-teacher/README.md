# AI Quran Teacher

An AI-powered Quran learning platform with real-time Tajweed feedback, live
classes, quizzes, and gamification.

**Full guide:** [docs/IMPLEMENTATION_GUIDE.md](docs/IMPLEMENTATION_GUIDE.md)

## Repository layout

| Directory | What it is | Status |
|---|---|---|
| [`backend/`](backend/) | NestJS API: Tajweed engine, quizzes, gamification, users (PostgreSQL + TypeORM) | ✅ Builds, 17 unit tests passing |
| [`signaling-server/`](signaling-server/) | Node.js + Socket.IO WebRTC signaling for live classes | ✅ Runs, `/health` endpoint |
| [`ios/`](ios/) | SwiftUI iPhone/iPad app: Quran reader, live classes, quizzes, progress | 🛠️ Sources complete; create the Xcode project (see [ios/README.md](ios/README.md)) |
| [`docs/`](docs/) | Master implementation guide | — |

CI workflows live at the repo root in [`.github/workflows/`](../.github/workflows/).

## Quick start

### Backend

```bash
cd backend
cp .env.example .env         # point at your PostgreSQL
createdb ai_quran_teacher
npm install
npm run start:dev            # http://localhost:3000
npm test                     # unit tests (no DB needed)
```

Try the Tajweed engine:

```bash
curl -X POST http://localhost:3000/tajweed/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "بسم الله الرحيم", "ayahId": 1, "expectedText": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"}'
```

It responds with word-level mistakes (here: the skipped word الرحمن), an
accuracy score, and the Tajweed rules present in the ayah.

### Signaling server

```bash
cd signaling-server
npm install
npm start                    # http://localhost:3001/health
```

### iOS app

Follow [ios/README.md](ios/README.md) — the Swift sources are complete; you
create the Xcode project shell, the Core Data model, and add two Swift
package dependencies.

## API overview

| Endpoint | Purpose |
|---|---|
| `POST /tajweed/detect` | Compare a recitation transcript to the expected ayah text |
| `POST /tajweed/analyze` | List Tajweed rule occurrences in a vocalized text |
| `GET /tajweed/rules` | Rule catalog with descriptions |
| `GET /tajweed/mistakes/:userId` | A user's mistake history |
| `POST /quiz/generate` · `POST /quiz/submit` · `GET /quiz/history/:userId` | Tajweed quizzes |
| `GET /gamification/profile/:userId` | XP, level, streak, badges |
| `GET /gamification/leaderboard` | Top users by XP |
| `POST /gamification/activity` | Record a practice day (streaks) |
| `POST /users` · `GET /users/:id` … | User CRUD (student/parent/teacher/org roles) |
