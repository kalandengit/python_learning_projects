# Master Rebuild Prompt — AI Quran Teacher

> Paste this into a capable coding LLM/agent to reconstruct the project from
> scratch. It is a directly reusable instruction, not a description.

You are a senior engineer. Build **AI Quran Teacher**, an AI-assisted Quran
learning platform, production-grade and secure by default. Deliver a runnable,
tested **NestJS 11 (TypeScript, strict)** REST API and a **Socket.IO signaling
server**, plus **iOS (SwiftUI/MVVM)** and **Android (Jetpack Compose/MVVM)**
client scaffolds, and a **Docker Compose** deploy stack. Work in small steps;
after each module, keep `lint`, `build`, and tests green.

## Product
Learners read the Quran, get **AI tajweed feedback** on their recitation, take
**AI-generated quizzes**, earn **gamification** (points/streaks/badges/leaderboard),
join **WebRTC live classes**, and **subscribe** via Stripe. Admins can grant a
**premium whitelist** (free access for a defined period).

## Stack & conventions
- NestJS 11 modular monolith; DI; feature-per-module; thin controllers, logic in services.
- TypeORM: **SQLite (better-sqlite3) in dev/test, PostgreSQL in prod**, selected by `DB_TYPE`. One config module.
- DTOs validated with `class-validator`; global `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`, `transform`).
- **Secure by default:** global `JwtAuthGuard`; routes opt out with `@Public()`.
- Put every external integration behind an **injectable, mockable service** (no SDK calls in feature code).
- **Never trust external/model input:** sanitise, clamp, length-limit before persistence.
- Global `AllExceptionsFilter` (consistent envelope; internal errors → generic 500).
- Prettier (single quotes, trailing commas), ESLint `--max-warnings 0`.
- Time fields that cross DBs: store **unix seconds as bigint**.

## Config / env (fail-fast validation at boot)
`NODE_ENV, PORT, CORS_ORIGINS`; `DB_TYPE, DATABASE_URL|DB_*, DB_SYNCHRONIZE`;
`JWT_SECRET (>=32 in prod), JWT_EXPIRES_IN, JWT_ISSUER, JWT_AUDIENCE`;
`MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL`; `THROTTLE_TTL_MS, THROTTLE_LIMIT`;
`STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY, STRIPE_PRICE_*`,
success/cancel/portal URLs.

## Auth (users module)
- `User(id uuid, email unique, passwordHash select:false, displayName, role student|teacher|admin, timestamps)`.
- `POST /auth/register` (email, displayName, password ≥10 with upper+lower+digit) → bcrypt(cost 12), returns `{accessToken, expiresIn, user}` (no hash). Reject duplicate email (409).
- `POST /auth/login` → run a bcrypt compare even for unknown users (reduce enumeration); invalid → 401.
- `GET /auth/me`.
- JWT **HS256 pinned** on sign and verify; set/verify `issuer` + `audience`; `ignoreExpiration:false`. (Defeats alg-confusion / `none` forgery — add an e2e test that a forged `alg:none` token → 401.)

## Quran module
- `Surah(id 1..114 PK, nameArabic, nameTransliteration, nameTranslation, revelationPlace, ayahCount)`,
  `Ayah(id uuid, surahId, numberInSurah, textArabic, textTransliteration, translation, unique[surahId,numberInSurah])`.
- Seed **Al-Fatihah (1)** and **Al-Ikhlas (112)** offline on first boot (idempotent).
- Public read: list surahs, get surah with ayahs, get single ayah.

## Mistral integration (common/mistral)
- `MistralService` using global `fetch` to `${apiUrl}/chat/completions`, Bearer key, `AbortController` timeout, `response_format: json_object` option, strips markdown fences, guards JSON.parse. `isConfigured()` → false when no key. On missing key/timeout/upstream error throw `ServiceUnavailableException` (503) — never leak upstream body.

## Tajweed module
- `POST /tajweed/analyze {surahId, ayahNumber, transcript(≤4000)}`: fetch reference ayah, ask Mistral (system prompt: compare recitation to reference, return JSON `{score, feedback, mistakes[]}`), **clamp score 0–100, cap/validate mistakes, coerce severity enum, length-limit strings**, persist `TajweedAnalysis`. `GET /tajweed/history`.

## Quiz module
- `POST /quiz/generate {topic?, difficulty(beginner|intermediate|advanced), numQuestions 1..10}`: Mistral returns `{questions:[{prompt,options[4],correctIndex,explanation}]}`; sanitise (exactly 4 options, valid index); persist; **return questions without correctIndex**.
- `GET /quiz/:id` (owner-only; others → 404). `POST /quiz/:id/submit {answers[]}`: length must match; grade server-side; persist `QuizAttempt`; award points via gamification; return per-question results with explanations.

## Gamification module
- `GamificationProfile(userId PK, points, currentStreak, longestStreak, lastActivityDate 'YYYY-MM-DD', badges[])`; lazy-created.
- `awardQuizPoints(userId, correct, total)`: points = correct×10 + (perfect?20:0); update streak (same UTC day unchanged / yesterday +1 / else reset 1); grant badges by thresholds (first_steps, century, scholar, consistent, devoted, steadfast).
- `GET /gamification/me | /badges | /leaderboard` (leaderboard joins user displayName, orders by points).

## Billing module (Stripe) + premium whitelist
- `StripeService` wraps SDK; `constructWebhookEvent(rawBody, sig)`; create app with `rawBody: true`.
- Client sends a **plan key** (allow-listed), server maps to a Stripe **price ID** (never trust client amounts).
- `POST /billing/checkout {plan}` → Checkout Session (mode subscription, idempotency key) → `{url}`. `POST /billing/portal` → Billing Portal URL. `GET /billing/config` (publishable key + plans), `GET /billing/me` (entitlement).
- `POST /billing/webhook` (`@Public`): verify signature over raw body (bad/missing → 400); handle `checkout.session.completed`, `customer.subscription.created|updated|deleted` idempotently → upsert `BillingCustomer(status, plan, currentPeriodEnd, cancelAtPeriodEnd)`; unknown events → 200.
- **Whitelist:** `PremiumGrant(userId PK, reason, grantedBy, expiresAt unix nullable)`; admin-only (`RolesGuard` + `@Roles(Admin)`, role read live from DB). `POST /billing/whitelist {userId, durationDays?, reason?}`, `DELETE /billing/whitelist/:userId`, `GET /billing/whitelist`.
- **Entitlement:** `isPremium = subscription active/trialing (not lapsed) OR non-expired grant`; report `source: 'subscription'|'whitelist'|null`.

## Cross-cutting
- Global guards order: `ThrottlerGuard` then `JwtAuthGuard`. Tighter `@Throttle` on auth (10/min) and AI/billing routes.
- `main.ts`: `rawBody:true`, Helmet, CORS allow-list, global prefix `/api`, global ValidationPipe, Swagger at `/api/docs` (non-prod), shutdown hooks.

## Signaling server (separate Node service)
- Express + Socket.IO; JWT-authenticated handshake (verify token, pin trusted `userId`; `ALLOW_ANONYMOUS` only for dev). `RoomRegistry` with capacity limit + roster. Events: `join` (ack roster), `userJoined/Left`, `offer/answer/iceCandidate` (relay; server stamps sender; size-limit payloads; regex-validate roomId), `chat`. `GET /health`. pino logs; graceful shutdown. Tests with `socket.io-client` (node:test).

## Testing
- Unit tests per service with mocked repos + mocked Mistral/Stripe. e2e with in-memory SQLite, overriding MistralService/StripeService with stubs (cover auth, validation, quiz gen/submit hides answers, gamification, billing webhook 400/200, admin whitelist flow via datasource role promotion, forged `none` JWT → 401). Signaling integration tests. A live `scripts/smoke-test.sh` that boots the stack + a mock Mistral and drives every endpoint.

## Deployment
- Multi-stage **non-root Dockerfiles** (backend + signaling). Root `docker-compose.yml`: `db (postgres16)` + `backend` + `signaling` + `caddy`; only Caddy publishes 80/443; app+db use `expose`. Caddy: automatic HTTPS when `SITE_ADDRESS` is a domain, `:80` for IP test; route `/api/*`→backend, `/socket.io/*`→signaling. `deploy/setup.sh` installs Docker + UFW (default-deny, allow 22 rate-limited/80/443). Document that Docker bypasses UFW for published ports and that a **Linode Cloud Firewall** must also allow 80/443.
- GitHub Actions (repo root): backend CI (lint/build/unit/e2e/audit), signaling CI, iOS check, smoke e2e; all with `permissions: contents: read`. Dependabot for npm + github-actions.

## Mobile scaffolds
- iOS SwiftUI/MVVM: models mirroring API JSON, QuranReader view + view model, `APIService` (URLSession) targeting documented routes, `SpeechRecognizer` (SFSpeechRecognizer), Info.plist usage strings.
- Android Compose/MVVM: models, MainActivity, Gradle, hardened manifest (cleartext disabled + dev-only network-security-config).

## Definition of done
`npm run lint/build/test/test:e2e` green in backend; signaling tests green;
`npm audit` clean; `scripts/smoke-test.sh` passes; `docker compose config` valid.
