# ߒߞߏ N'KO Voice Transcriptor

Speak **Bambara** — read **N'Ko**. A web application that records (or accepts)
audio, transcribes it with a speech-recognition engine, and renders the result
in the N'Ko script (ߒߞߏ), the right-to-left alphabet created by **Solomana
Kanté** in 1949 for the Manding languages.

## How it works

```
mic / upload → validation → ASR engine → Bambara (Latin) → transliteration → N'Ko (RTL)
```

Two ASR engines ship behind one interface (`NKO_ASR_ENGINE`):

| Engine | What it is | When to use |
|---|---|---|
| `mock` (default) | Deterministic, zero ML dependencies | tests, CI, demos, development |
| `mms` | Meta **MMS** (`facebook/mms-1b-all`) with the Bambara `bam` adapter | production — real speech recognition |

The Latin→N'Ko **transliteration engine** (`app/nko/`) is deterministic and
fully unit-tested: the seven Bambara vowels, coda-nasal → nasalization mark
(߲), the syllabic-N pronoun (ߒ), digraphs (`ny`, `gb`, `rr`), N'Ko digits and
punctuation. Design choices and known limitations are documented in
`app/nko/tables.py`.

## Quick start (development)

```bash
cd nko-voice-transcriptor
pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print('NKO_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
uvicorn app.main:app --reload
# open http://127.0.0.1:8000  (API docs at /api/docs in development)
```

Register a user in the UI, allow microphone access, record, and read the N'Ko.

## Real speech recognition (MMS)

```bash
pip install torch torchaudio transformers   # ~2 GB+
echo "NKO_ASR_ENGINE=mms" >> .env
```

First transcription downloads the model (~4 GB, cached). MMS quality for
Bambara is usable but far from perfect — low-resource ASR is an open research
problem; treat output as a draft to correct, not ground truth.

## Production (Docker)

```bash
export NKO_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
export POSTGRES_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(24))")
docker compose up --build
```

Runs the API (non-root container, healthcheck) against PostgreSQL 16.
Put a TLS-terminating reverse proxy (Caddy/Traefik/nginx) in front.

## Tests & lint

```bash
python -m pytest tests/ -v   # 61 tests: transliteration, ASR, API, auth, security
ruff check app tests
```

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | – | liveness + engine info |
| POST | `/api/auth/register` | – | create account |
| POST | `/api/auth/login` | – | get JWT access token |
| POST | `/api/transcribe` | Bearer | audio → `{text_latin, text_nko}` (stored) |
| POST | `/api/transliterate` | – | text-only Latin → N'Ko (stateless) |
| GET | `/api/history` | Bearer | own transcriptions (paginated) |
| DELETE | `/api/history/{id}` | Bearer | delete own transcription |

## Display

The UI renders N'Ko RTL with `Noto Sans NKo` / `Ebrima` if installed on the
client. For guaranteed rendering everywhere, self-host
[Noto Sans NKo](https://fonts.google.com/noto/specimen/Noto+Sans+NKo) (SIL OFL)
in `app/static/fonts/` and add an `@font-face` rule in `styles.css`.

See `ARCHITECTURE.md` for design details and `SECURITY.md` for the threat model.
