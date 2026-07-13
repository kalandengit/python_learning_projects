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
fully unit-tested: the seven Manding vowels, coda-nasal → nasalization mark
(߲), the syllabic-N pronoun (ߒ), digraphs (`ny`, `gb`, `rr`), N'Ko digits and
punctuation. Design choices and known limitations are documented in
`app/nko/tables.py`.

### Source languages

Not only Bambara — pick a source language per recording from the UI. Offered
languages are configurable via `NKO_LANGUAGES` (default: all six Manding
varieties with MMS adapters, Bambara first):

| Code | Language |
|---|---|
| `bam` | Bambara (Bamanankan) — default |
| `dyu` | Dyula (Jula) |
| `emk` | Maninka, Eastern (Malinké) |
| `mku` | Maninka, Konyanka |
| `msc` | Maninka, Sankaran |
| `mwk` | Maninkakan, Kita |

The MMS engine hot-swaps the per-language adapter; the same N'Ko
transliteration rules apply across the Manding varieties.

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

### Editing & export

- **Edit the result** — the generated N'Ko is an editable field; correct it and
  **Save** to persist the correction (`PATCH /api/history/{id}`). Any history
  entry can be reopened in the editor with ✎.
- **On-screen N'Ko keyboard** — a ⌨ toggle opens a virtual keyboard (vowels,
  consonants, combining nasal/tone marks, N'Ko digits ߀–߉, punctuation, space,
  backspace) that types into whichever N'Ko field is focused — handy for
  corrections without an N'Ko system keyboard.
- **Download** the generated text as **TXT**, **PNG** (canvas-rendered N'Ko,
  RTL, with a Latin caption), or **PDF** (via the browser's Save-as-PDF print
  dialog, using the system N'Ko font). All client-side — no external libraries,
  CSP-safe.

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
| GET | `/api/languages` | – | offered source languages |
| POST | `/api/auth/register` | – | create account |
| POST | `/api/auth/login` | – | get JWT access token |
| POST | `/api/transcribe` | Bearer | audio → `{text_latin, text_nko}` (stored) |
| POST | `/api/transliterate` | – | text-only Latin → N'Ko (stateless) |
| GET | `/api/history` | Bearer | own transcriptions (paginated) |
| PATCH | `/api/history/{id}` | Bearer | edit/save the N'Ko text of own transcription |
| DELETE | `/api/history/{id}` | Bearer | delete own transcription |

## Display

The UI renders N'Ko RTL with `Noto Sans NKo` / `Ebrima` if installed on the
client. For guaranteed rendering everywhere, self-host
[Noto Sans NKo](https://fonts.google.com/noto/specimen/Noto+Sans+NKo) (SIL OFL)
in `app/static/fonts/` and add an `@font-face` rule in `styles.css`.

See `ARCHITECTURE.md` for design details and `SECURITY.md` for the threat model.
