# AI Quran Teacher 📖

An **AI-powered Quran learning platform** — real-time tajweed feedback,
AI-generated quizzes, live classes over WebRTC, and gamification — built with a
**Mistral AI**-powered NestJS backend and native **iOS** and **Android** clients.

[![Backend CI](../../actions/workflows/backend-ci.yml/badge.svg)](../../actions/workflows/backend-ci.yml)
[![Signaling CI](../../actions/workflows/signaling-ci.yml/badge.svg)](../../actions/workflows/signaling-ci.yml)

---

## ✨ Features

| Feature | Description |
| --- | --- |
| 📖 **Quran Reader** | Arabic text, transliteration, translation, bookmarks |
| 🎙️ **AI Tajweed feedback** | Compares a recitation transcript to the reference ayah via Mistral AI and returns scored, explained mistakes |
| 🧠 **AI Quizzes** | Auto-generated tajweed quizzes with server-side grading |
| 🏆 **Gamification** | Points, daily streaks, badges, and a leaderboard |
| 👥 **Live Classes** | Peer-to-peer video/audio with chat via WebRTC + signaling server |
| 💳 **Payments** | Stripe Checkout subscriptions + billing portal (PCI SAQ-A), signature-verified webhooks |
| 🎟️ **Premium whitelist** | Admins grant free premium access to users for a defined period |

## 🧱 Architecture

```
┌──────────────┐     ┌──────────────┐
│   iOS App    │     │ Android App  │   SwiftUI / Compose (MVVM)
└──────┬───────┘     └──────┬───────┘
       │  HTTPS/JSON + WSS  │
       ▼                    ▼
┌────────────────────────────────────┐
│  NestJS REST API  │  Signaling srv  │
│  (auth, tajweed,  │  (Socket.IO,    │
│   quiz, gamif.,   │   WebRTC        │
│   quran)          │   handshake)    │
└─────────┬─────────┴────────┬────────┘
          │                  │
     ┌────▼────┐        ┌────▼────┐
     │Postgres │        │  Redis  │      Mistral AI (chat completions)
     └─────────┘        └─────────┘
```

Full diagrams (system context, module graph, sequence, ERD, deployment) are in
**[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)**. Security controls are in
**[`docs/SECURITY.md`](./docs/SECURITY.md)**.

## 📁 Project structure

```
AIQuranTeacherProject/
├── ios/                # SwiftUI client (MVVM) — scaffold
├── android/            # Jetpack Compose client (MVVM) — scaffold
├── backend/            # NestJS API (Mistral AI, JWT, TypeORM) — production-grade
├── signaling-server/   # Socket.IO WebRTC signaling — production-grade
└── docs/               # Architecture & security documentation
```

CI workflows live at the repository root under
[`.github/workflows/`](../.github/workflows).

## 🚀 Quick start (backend + signaling)

Both services run locally with no external dependencies (backend uses embedded
SQLite; set a Mistral key to enable the AI features).

```bash
# 1) Backend API — http://localhost:3000/api  (docs at /api/docs)
cd backend
cp .env.example .env          # set JWT_SECRET (>=32 chars) and MISTRAL_API_KEY
npm install
npm run start:dev

# 2) Signaling server — ws://localhost:3001
cd ../signaling-server
cp .env.example .env          # set JWT_SECRET to match the backend
npm install
npm start
```

Then run the iOS or Android app (see their READMEs) and point the API base URL
at your backend.

## ✅ Testing

```bash
cd backend && npm test && npm run test:e2e   # 26 unit + 8 e2e
cd ../signaling-server && npm test           # integration tests

# Full live end-to-end smoke test (boots both services + a mock Mistral and
# exercises every module over real HTTP):
bash scripts/smoke-test.sh
```

Dependencies are audited in CI (`npm audit`); an npm `overrides` entry pins
Multer to a patched release. All test suites and the smoke test run in GitHub
Actions on every PR.

## 🔐 Security highlights

Global JWT auth (secure by default), bcrypt hashing, strict input validation,
rate limiting, Helmet headers, explicit CORS, validated/clamped AI output, and
non-root Docker images. See [`docs/SECURITY.md`](./docs/SECURITY.md).

## 🛠️ Tech stack

- **Backend:** NestJS 11, TypeScript, TypeORM, PostgreSQL/SQLite, Passport JWT, Mistral AI
- **Signaling:** Node.js, Socket.IO, JWT, pino
- **iOS:** Swift, SwiftUI, Combine, AVFoundation, Speech
- **Android:** Kotlin, Jetpack Compose, Retrofit, Room, Coroutines
- **DevOps:** Docker (multi-stage, non-root), GitHub Actions

## 📈 Status

- **Backend & signaling server:** implemented, tested, and runnable.
- **iOS & Android:** architectural scaffolds (models, key views/services) —
  see each platform's README for the roadmap to a buildable app.

## 📄 License

Released under the terms of the repository [`LICENSE`](../LICENSE).
