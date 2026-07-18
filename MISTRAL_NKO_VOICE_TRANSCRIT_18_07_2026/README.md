# MISTRAL_NKO_VOICE_TRANSCRIT_18_07_2026

**N'Ko Voice Transcriptor — rebuilt.** Transcribes Manding-language speech
(Bambara, Dyula, Maninka) to N'Ko script (ߒߞߏ, Unicode U+07C0–U+07FF) through a
two-stage pipeline — ASR → Latin Bambara orthography → deterministic N'Ko
transliteration — with a hybrid ASR strategy:

- **Local MMS Bambara engine** (pinned model revision, offline-capable) for
  Manding languages, which Mistral's models do not natively support.
- **Mistral Voxtral Transcribe 2** (batch + realtime) for French and other
  supported languages, via the Mistral API — key held server-side only.

This is a ground-up rebuild of the N'Ko Voice Transcriptor v1.7.0 in which
every finding of the v1.2.0 security audit is fixed **by design**, not patched
after the fact.

## Repository layout (branch-per-component)

| Branch | Contents |
|---|---|
| `main` | Documentation, CI workflows, governance files |
| `backend` | `backend/` — FastAPI service, N'Ko core, web UI, Docker |
| `android` | `android-app/` — native Kotlin / Jetpack Compose app |
| `ios` | `ios-app/` — native Swift / SwiftUI app |

Component branches merge into `main` through pull requests; CI is
path-filtered so each component builds independently. See
`docs/BRANCHING.md`.

## Quickstart (backend)

```bash
git checkout backend
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env            # then set NKO_SECRET_KEY (>=32 chars)
uvicorn app.main:app --reload   # http://127.0.0.1:8000
pytest                          # run the test suite
```

By default the **mock ASR engine** is active so the whole stack runs with no
model download and no API key. Set `NKO_ASR_ENGINE=mms` (plus a local model)
or configure `NKO_MISTRAL_API_KEY` for Voxtral.

## Security posture (summary)

- Argon2id password hashing with timing-safe dummy verification
- Short-lived access tokens + **rotating refresh tokens with reuse detection**
- Strict CSP (no `unsafe-inline`), full security-header set
- Proxy-aware rate limiting (trusted `X-Forwarded-For` only)
- Upload cap enforced **before** multipart parsing; MIME + magic-byte checks
- Audio processed in memory and discarded — text only is stored, opt-in
- Pinned dependencies (lock file), pinned ASR model revision
- Multi-stage, non-root Docker image

Details and threat model: `docs/SECURITY.md`.

## License notes

The bundled French→N'Ko lexicon (~47.8k entries) originates from the
N'Ko Wuruki lexicon — see `docs/LICENSE-NOTES.md` and verify redistribution
rights before shipping it publicly.
