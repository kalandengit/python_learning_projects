# Development State — where we are, what's next

_Snapshot of the `claude/mistral-ai-quran-teacher-i36jim` branch (open as PR #4)._

## Completed ✅

**Backend (NestJS 11) — production-grade, tested, runnable**
- Auth: register/login/me, bcrypt(12), JWT (HS256 pinned + issuer/audience), global guard.
- Quran: Surah/Ayah entities + offline seed (Al-Fatihah, Al-Ikhlas), public read API.
- Tajweed: AI analysis vs reference ayah, sanitised/clamped, history.
- Quiz: AI generation (answers hidden), server-side grading, attempts, points.
- Gamification: points, UTC-day streaks, badges, leaderboard.
- Billing: Stripe Checkout + Portal, signed webhook (raw body), idempotent handling.
- Premium whitelist: admin-only, time-boxed, audited; unified entitlement.
- Cross-cutting: ValidationPipe, Helmet, CORS allow-list, throttling, exception filter, Swagger, fail-fast env validation.
- Multi-stage non-root Dockerfile.

**Signaling server (Socket.IO)** — JWT handshake, room capacity/roster, payload validation, pino logs, graceful shutdown, `/health`, Dockerfile.

**Quality gates** — 39 unit + 17 e2e + 3 signaling tests green; `npm audit` clean; `scripts/smoke-test.sh` passes end-to-end; lint/build clean.

**Infra & docs** — Docker Compose (db+backend+signaling+caddy), Caddyfile, `deploy/setup.sh`, `.env.example`; `docs/`: ARCHITECTURE, SECURITY, STRIPE_SECURITY, DEPLOY_LINODE. CI: backend/signaling/iOS/smoke workflows + Dependabot, least-privilege tokens.

**Mobile** — iOS SwiftUI/MVVM and Android Compose/MVVM **scaffolds** (models, QuranReader vertical, API client, hardened Android manifest).

## In progress / current focus
- **Deploying a test instance to a Linode VPS** (IP `172.236.240.38`). App runs; last blocker being resolved is **external access → open 80/443 in the Linode Cloud Firewall** (host `ss` shows Caddy on `0.0.0.0:80/443`, UFW disabled).

## Remaining / not done ⬜
- **Mobile apps are scaffolds** — no committed compilable Xcode/Gradle project; feature screens (LiveClass, Quiz, Gamification) and real STT are stubs.
- **Live classes:** signaling exists; no client UI or deployed STUN/TURN.
- **Quran content:** only 2 surahs seeded — needs full corpus import.
- **DB migrations:** using `DB_SYNCHRONIZE=true`; production needs TypeORM migrations.
- **Auth lifecycle:** no refresh-token rotation / revocation / blacklist.
- **Ops:** no Postgres backups, metrics/tracing/alerting, or secrets manager yet.

## Known issues / risks ⚠️
- **Registration race:** duplicate-email is check-then-insert; under high concurrency a unique-violation could surface as 500 instead of 409. _(Low; add a caught unique-constraint → 409, or DB-level upsert.)_
- **Stripe `current_period_end`** location varies by API version — read defensively (handled) but revisit on SDK upgrades.
- **Single-instance signaling:** `RoomRegistry` is in-process; multi-instance needs the Socket.IO Redis adapter.
- **JWT not revocable** (stateless) until refresh tokens/blacklist exist.
- **`.env` secrets on disk** in the test deploy — move to a secrets manager for prod.

## Suggested next steps (ordered)
1. Finish the Linode test deploy (Cloud Firewall 80/443) and verify from outside.
2. Add TypeORM migrations; set `DB_SYNCHRONIZE=false` for prod.
3. Import the full Quran corpus (surahs/ayahs) via a migration/seed.
4. Build one mobile feature end-to-end (Quran reader → tajweed) against the live API.
5. Add refresh-token rotation + revocation.
6. Add Postgres backups + basic observability (health/metrics/logs shipping).
7. Deploy STUN/TURN and implement the live-class client.

## Unknowns
- Exact product priorities among mobile vs. live-classes vs. web client _(not specified in repo)_.
- Whether a web frontend is planned (only API + native clients exist today).
