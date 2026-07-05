# Technical Requirements — AI Quran Teacher Platform

**Status:** Enterprise-grade reference architecture, designed to scale to
millions of users.
**Audience:** Engineers, DevOps, and technical stakeholders.

This document is the single source of truth for what the platform needs to run
in production: functional scope, the technology stack, scalability targets,
security, observability, and the operational requirements to keep it
maintainable and updatable.

---

## 1. Functional Requirements

| # | Capability | Where |
|---|---|---|
| F1 | Quran reader with Arabic text, translation, bookmarks, offline mode | iOS `Views/QuranReader`, Core Data |
| F2 | Real-time Tajweed feedback from recitation (speech → analysis) | `SpeechRecognizer`, `tajweed` module |
| F3 | Rule-based Tajweed engine (izhar/idgham/iqlab/ikhfa/qalqalah/ghunnah/madd) | `backend/src/tajweed` |
| F4 | Quizzes with server-side grading, XP, and badges | `backend/src/quiz` |
| F5 | **Timed certification exams** with verifiable certificates | `backend/src/exam` |
| F6 | Gamification: badges, streaks, XP/levels, leaderboard | `backend/src/gamification` |
| F7 | **AI Islamic tutor** with parallel multi-aspect answers | `backend/src/tutor`, `backend/src/llm` |
| F8 | Authentication (register/login, JWT, bcrypt), role-based access | `backend/src/auth` |
| F9 | Live classes: video, whiteboard, chat over WebRTC | iOS `Views/LiveClass`, `signaling-server` |
| F10 | Multi-role dashboards (student, parent, teacher, org_admin) | `User.role` |
| F11 | Multi-language support | iOS `Localizable.strings`, `User.language` |

## 2. Non-Functional Requirements

| Category | Target |
|---|---|
| **Scale** | 10M+ registered users; 100k+ concurrent; 1k+ req/s steady, 5k+ peak |
| **Availability** | 99.9% (≤ 43 min/month downtime) for the API |
| **Latency** | p95 < 200 ms for CRUD/quiz/gamification; tutor bounded by LLM (streamed) |
| **Durability** | Zero data loss on user progress; PITR backups |
| **Security** | OWASP ASVS L2; encrypted at rest and in transit |
| **Maintainability** | Modular monolith, typed end-to-end, CI on every PR |
| **Portability** | 12-factor; runs identically in Docker, ECS, or Kubernetes |

---

## 3. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| iOS app | Swift 5.9+, SwiftUI, Core Data, AVFoundation, WebRTC | iOS 17+ |
| Backend API | NestJS 10, TypeScript 5, TypeORM | Modular monolith |
| Database | PostgreSQL 16 | Primary store |
| Cache / coordination | Redis 7 | Cache, rate-limit state, Socket.IO adapter |
| Realtime | Node.js + Socket.IO | WebRTC signaling |
| AI | Anthropic Claude (`claude-opus-4-8` default) | See `LLM_GUIDE.md` |
| Auth | JWT (`@nestjs/jwt`), bcrypt, Passport | 7-day access tokens |
| Container | Docker, docker-compose (local), ECS/K8s (prod) | |
| CI/CD | GitHub Actions | Build, test, image, deploy |

**Runtime versions:** Node.js 20 LTS, PostgreSQL 16, Redis 7.

---

## 4. Scalability Architecture (to millions of users)

The design follows the widely-recommended path: **a modular monolith that
scales horizontally behind a load balancer**, with stateless app instances and
all shared state pushed to Postgres and Redis. This avoids premature
microservice complexity while leaving clean seams to split later.

```
                       ┌──────────────┐
        Clients ──────▶│ Load Balancer│  (ALB / Nginx, TLS termination)
   (iOS / web / api)   └──────┬───────┘
                              │  round-robin, health-checked (/health, /ready)
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
        ┌──────────┐    ┌──────────┐     ┌──────────┐
        │ API pod 1│    │ API pod 2│ ... │ API pod N│   (stateless NestJS)
        └────┬─────┘    └────┬─────┘     └────┬─────┘
             └───────────────┼────────────────┘
                     ┌───────┴────────┐
                     ▼                ▼
             ┌───────────────┐  ┌───────────┐
             │ PostgreSQL    │  │  Redis    │
             │ primary +     │  │  cache +  │
             │ read replicas │  │  pub/sub  │
             └───────────────┘  └───────────┘

  Signaling servers scale separately (Socket.IO + Redis adapter, sticky sessions).
```

### 4.1 Stateless application tier

- **No in-process session state.** Auth is stateless JWT; nothing is pinned to
  a specific instance, so any pod can serve any request and the tier scales by
  adding pods (`docker compose up --scale backend=N`, or an ECS/K8s replica
  count).
- **Graceful shutdown** (`enableShutdownHooks`, listen on `0.0.0.0`) drains
  in-flight requests on `SIGTERM` for zero-downtime rolling deploys.
- Practical limit per Node instance is ~10k–30k concurrent connections; scale
  out horizontally well before that.

### 4.2 Database scaling

- **Connection pooling** via PgBouncer in front of Postgres (thousands of app
  connections → a bounded pool).
- **Read replicas** for read-heavy endpoints (leaderboard, surah content,
  certificate verification). TypeORM supports replica routing.
- **Indexing:** hot columns are indexed (`@Index` on `userId`, `ayahId`,
  `email`, `verificationCode`, leaderboard `xp`).
- **Migrations, not `synchronize`:** `DB_SYNCHRONIZE=false` in production; use
  TypeORM migrations for controlled schema evolution.
- **Partitioning / archival** for high-volume tables (`tajweed_mistakes`,
  `recitation sessions`) once they grow large.

### 4.3 Caching (Redis)

- `RedisService.remember()` caches expensive/hot reads (surah content,
  leaderboard, certificate lookups, repeated tutor questions).
- Redis also backs **cross-instance rate limiting** and, for the signaling
  tier, the **Socket.IO Redis adapter** so a message published on one node
  reaches clients connected to another.

### 4.4 Realtime tier (live classes)

- Socket.IO scales across nodes with the **Redis adapter** for pub/sub
  broadcast, plus **sticky sessions** at the load balancer (or disable HTTP
  long-polling and use WebSocket-only transport to avoid the sticky-session
  requirement).
- A dedicated STUN/TURN service (e.g. coturn) is required for WebRTC NAT
  traversal at scale; the signaling server only brokers SDP/ICE.

### 4.5 AI tier (Claude)

- The tutor's **parallel fan-out** (`LlmService.parallel`) is bounded by
  `LLM_MAX_CONCURRENCY` per instance to respect Anthropic rate limits.
- Heavy bulk generation (pre-computing tafsir for all ayahs) should use the
  **Message Batches API** (50% cost), not the live path.
- See [`LLM_GUIDE.md`](LLM_GUIDE.md) for model choice, cost controls, and
  prompt caching.

### 4.6 Async & heavy work

- Long-running or spiky work (notifications, batch AI jobs, analytics
  roll-ups) belongs on a **queue** (BullMQ on Redis, or SQS/Kafka) processed
  by workers, so it never blocks a user's API request.
- Audio recitation ML (future custom Tajweed model) runs as a separate
  inference service, called async.

---

## 5. Security Requirements

| Area | Requirement | Status in repo |
|---|---|---|
| Transport | TLS everywhere; HSTS | `helmet()` sets security headers |
| Auth | JWT access tokens, bcrypt (cost 12) password hashing | `auth` module |
| Passwords | Never stored plaintext; separate `auth_credentials` table | ✅ |
| Input validation | DTO validation, whitelist + reject unknown fields | global `ValidationPipe` |
| Rate limiting | Global + tighter per-route (auth, tutor) | `@nestjs/throttler` |
| CORS | Locked to `ALLOWED_ORIGINS` in production | `main.ts` |
| Secrets | Env vars / secrets manager; never committed | `.env` gitignored |
| Least privilege | DB user scoped; API keys per environment | ops |
| PII | Minimize; the tutor sends only question + ayah context to Claude | ✅ |
| Dependency hygiene | `npm audit` in CI; Dependabot | recommended |

Production hardening checklist: enable WAF, secrets rotation, audit logging on
auth events, and per-tenant data isolation for the org/school role.

---

## 6. Observability

| Concern | Approach |
|---|---|
| Health/readiness | `GET /health` (liveness), `GET /ready` (readiness + subsystem status) |
| Structured logging | Winston/Pino with request IDs and levels (add in production) |
| Error tracking | Sentry (backend + iOS Crashlytics) |
| Metrics | Prometheus (req rate, latency, DB pool, Redis hit rate, LLM tokens/cost) |
| Tracing | OpenTelemetry across API → DB → Claude |
| Dashboards & alerts | Grafana; alert on p95 latency, error rate, LLM spend |

The readiness endpoint already reports Redis and LLM availability and the
serving instance ID — wire it to the load balancer's health check.

---

## 7. Maintainability & Updatability

This is a first-class requirement, not an afterthought.

- **Modular monolith.** Each domain (auth, tajweed, quiz, exam, gamification,
  tutor, llm, health) is a self-contained NestJS module with clear service
  boundaries and dependency injection — no shared mutable state, no hidden
  coupling. Modules can be extracted into services later without rewrites.
- **Typed end-to-end.** TypeScript on the backend; the iOS `Codable` models
  mirror the API response shapes exactly, so a contract change surfaces at
  compile time on both sides.
- **Tests as a safety net.** 28 backend unit tests cover Tajweed detection,
  quiz/exam grading, gamification, and the parallel tutor fan-out. CI runs
  build + test on every push and PR (`.github/workflows`).
- **Seams for the future.** `LlmService` isolates the AI provider behind one
  interface (swap models or providers in one file); `TajweedService.analyze`
  is the seam where a trained ML model replaces the rule engine; the on-device
  `TajweedEngine.swift` mirrors the backend rules and is documented to stay in
  sync.
- **Config over code.** All environment-specific behavior (DB, Redis, JWT,
  CORS, rate limits, LLM concurrency) is env-driven (12-factor), so the same
  build promotes across dev/staging/prod.
- **Schema evolution.** Adopt TypeORM migrations before production; never run
  `synchronize` against real data.
- **Documentation.** This doc, `LLM_GUIDE.md`, `IMPLEMENTATION_GUIDE.md`, and
  per-component READMEs are kept in-repo alongside the code they describe.
- **Dependency updates.** Pin runtime versions; use Dependabot/Renovate for
  controlled upgrades; `npm ci` for reproducible installs.

---

## 8. Environments & Deployment

| Environment | Purpose | Notes |
|---|---|---|
| Local | Development | `docker compose up` (Postgres + Redis + API + signaling) |
| Staging | Pre-prod validation | Mirror of prod, seeded data |
| Production | Live | Autoscaling API tier, managed Postgres (RDS) + Redis (ElastiCache) |

**Deploy flow:** GitHub Actions → build → test → Docker image → registry →
rolling deploy (ECS service or K8s Deployment) behind the load balancer.
Blue/green or canary recommended for zero-downtime releases.

**Capacity planning (order-of-magnitude for ~1M DAU):**
- API: 10–30 pods (2 vCPU / 2 GB each) behind an ALB, autoscaled on CPU + req rate.
- Postgres: 1 primary (managed, multi-AZ) + 2 read replicas; PgBouncer.
- Redis: clustered/HA managed instance.
- Signaling: 3+ nodes with Redis adapter + coturn TURN cluster.

---

## 9. Data Model (core entities)

| Entity | Table | Key fields |
|---|---|---|
| User | `users` | id, email (unique), name, role, language |
| AuthCredential | `auth_credentials` | userId (unique), passwordHash |
| TajweedMistake | `tajweed_mistakes` | userId, ayahId, type, severity, wordIndex |
| Quiz | `quizzes` | userId, difficulty, questions (jsonb), score |
| Exam | `exams` | userId, level, questions (jsonb), score, passed, certificateId |
| Certificate | `certificates` | userId, examId, level, verificationCode (unique) |
| UserBadge | `user_badges` | userId + badgeCode (unique) |
| Streak | `streaks` | userId (unique), current, longest, lastActivityDate |
| LeaderboardEntry | `leaderboard_entries` | userId (unique), xp, level |

---

## 10. Compliance & Content Integrity

- **Quran text** sourced from Tanzil under its terms of use; Tajweed
  annotations under CC-BY where applicable (see `ios/README.md`).
- **AI answers** are labelled AI-generated and never issue religious rulings
  (see `LLM_GUIDE.md` §Safety).
- **Privacy:** GDPR/CCPA — support data export and deletion; minimize PII;
  document data flows (student question + ayah context are the only data sent
  to the LLM provider).
- **Children:** if targeting under-13 users, COPPA obligations apply (parental
  consent via the parent role).
