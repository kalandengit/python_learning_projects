# Security design & threat model

Scope: backend API + web UI, mobile clients, ASR integrations, data at rest.
This rebuild bakes in fixes for **all eight open findings** of the
N'Ko Voice Transcriptor v1.2.0 audit.

## Controls by audit finding

| Audit finding (severity) | Rebuild control |
|---|---|
| Dependency reproducibility (Medium) | `requirements-lock.txt` committed; Dockerfile installs from the lock file; base image digest pinning documented |
| Proxy-aware rate limiting (Medium) | `app/limits.py` trusts `X-Forwarded-For` **only** from `NKO_TRUSTED_PROXIES`; falls back to peer address otherwise; nginx sample adds a second layer |
| Multipart parsing limit (Medium) | `BodySizeLimitMiddleware` rejects by `Content-Length` and by counted stream bytes **before** the multipart parser consumes the body |
| Mutable MMS model revision (Medium) | `NKO_MMS_REVISION` pins the Hugging Face revision; `local_files_only` supported for air-gapped deployments |
| CSP inline styles (Low) | No inline styles or scripts anywhere in the web UI; `style-src 'self'`; font self-hosted |
| Health endpoint exposure (Low) | `/api/health` returns `{"status":"ok"}` only; `/api/health/detailed` requires the `NKO_INTERNAL_HEALTH_TOKEN` header |
| Timing side-channel on login (Low, fixed in 1.3.0) | Kept: dummy Argon2id verification for unknown users |
| Force-push risk in publish script (High, fixed in 1.3.0) | No publish script in this repo; CI deploys, protected branches documented |

## Authentication & sessions

- Argon2id (argon2-cffi defaults) for password hashing.
- Login always performs one Argon2 verification (real or dummy) — constant
  work whether or not the account exists.
- Access tokens: HS256 JWT, **15 min** lifetime, `type=access`.
- Refresh tokens: 7 days, stored server-side as SHA-256 hashes, **rotated on
  every use**. Presenting an already-rotated token is treated as theft:
  the whole token family for that user is revoked.
- Secret key must be ≥ 32 characters — enforced at startup by config
  validation; the app refuses to boot otherwise.
- Web UI keeps tokens in `sessionStorage` (never cookies → no CSRF surface);
  mobile apps use Keychain (iOS) / EncryptedSharedPreferences (Android).

## Input handling

- Upload cap (`NKO_MAX_UPLOAD_BYTES`, default 10 MiB) enforced pre-parse.
- Content sniffing: declared MIME must be in the allowlist **and** the magic
  bytes must match (RIFF/WAVE, OggS, fLaC, MP3, M4A `ftyp`, WebM EBML).
- All request bodies validated with Pydantic; all SQL through SQLAlchemy
  bound parameters; all dynamic DOM writes in the web UI use `textContent`.

## Privacy

- Audio is never written to disk and never retained after the response.
- History storage is **opt-in per request** and stores text only.
- Logs are structured and contain identifiers, never audio or transcripts.
- The Mistral API key lives only in server config; requests to Mistral send
  audio for transcription only — document this in your user-facing privacy
  policy if you enable the Voxtral engine.

## Transport & headers

Responses carry: strict CSP (`default-src 'self'`; no inline), `X-Frame-Options:
DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
`Permissions-Policy: microphone=(self), camera=()`. Enable HSTS at the TLS
terminator. A hardened nginx sample lives in `backend/deploy/nginx.conf`.

## Secrets management

- `.env` is git-ignored; `.env.example` documents every variable.
- Production: use a secrets manager (or Docker/K8s secrets); rotate
  `NKO_SECRET_KEY` and the Mistral key on a schedule; rotating the JWT secret
  invalidates outstanding tokens by design.

## CI security gates

`bandit` (SAST), `pip-audit` (known CVEs against the lock file), `ruff`,
and the full test suite — including the security regression tests in
`backend/tests/test_security.py` (headers, body limit, rate limit, IDOR,
refresh reuse) — run on every PR.
