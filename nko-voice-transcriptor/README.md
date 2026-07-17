# ߒߞߏ N'KO Voice Transcriptor

Speak **Bambara** — read **N'Ko**. A web application that records (or accepts)
audio, transcribes it with a speech-recognition engine, and renders the result
in the N'Ko script (ߒߞߏ), the right-to-left alphabet created by **Solomana
Kanté** in 1949 for the Manding languages.

## Recognition improvement pipeline (1.9)

Uploads are normalized by FFmpeg to 16 kHz mono WAV and split near silence before
ASR. With explicit user consent, normalized audio and later corrections enter a
protected review queue. Only reviewer-approved pairs are used by correction memory
or exported for training.

Reviewer requests use the `X-Review-Key` value stored as `NKO_REVIEW_API_KEY` in
the server environment. Useful endpoints are:

- `GET /api/training/samples?status=pending`
- `PATCH /api/training/samples/{id}`
- `GET /api/training/samples/{id}/audio`
- `GET /api/training/export.csv`

Export an AudioFolder dataset on the backend, then train on a separate GPU machine:

```bash
python scripts/export_training_dataset.py ./approved-dataset
bash scripts/train-mms-adapter.sh ./approved-dataset ./models/bam-adapter-v1
```

Deploy a separately versioned model repository or directory with:

```bash
sudo MMS_MODEL_ID=your-org/bam-mms-adapter MODEL_VERSION=bam-adapter-v1 \
  ASR_ENGINE=mms ./deploy/deploy-ubuntu.sh
```

Compare fixed evaluation hypotheses without changing the production default:

```bash
python scripts/evaluate_pipelines.py evaluation.jsonl
```

Each JSONL row contains `reference`, `mms`, `mms_rag`, `tuned_mms`, and
`tuned_mms_rag_llm`. Promote a pipeline only after it improves held-out WER and
CER and passes human review.

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
pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print('NKO_SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
uvicorn app.main:app --reload
# open http://127.0.0.1:8000  (API docs at /api/docs in development)
```

Register a user in the UI, allow microphone access, record, and read the N'Ko.

### Interface languages

The UI is localized — pick the interface language from the header dropdown:
**French, Bambara, English, Russian, Simplified Chinese, Arabic, and N'Ko**.
French is the canonical source catalog. Arabic and N'Ko render right-to-left
(the whole layout flips), and the choice is remembered across visits. This is
independent of the *source* (spoken) language.

Translation data is isolated in `app/static/languages.js`; the engine in
`app/static/i18n.js` validates each catalog against French and supplies French
fallbacks. The Bambara and N'Ko terminology should receive native-speaker review.

### Copy/paste backend install

```bash
sudo bash -c "$(curl --proto '=https' --tlsv1.2 -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/nko-voice-transcriptor/deploy/install-backend.sh)"
```

### Dictionary

A **N'Ko ↔ French dictionary** search is built in. Type a French word to get
its N'Ko equivalents (accent-insensitive), or switch direction to look up N'Ko;
click **→ ߒߞߏ** on a result to drop it into the editor. The repo bundles the
**full French→N'Ko lexicon** (~47,800 entries) at `app/data/lexicon-fr-nko.json`
and loads it by default; set `NKO_LEXICON_PATH` to substitute your own JSON
(`{"entries": [{"fr","nko","cat"}, …]}`).

Data is derived from the **NKo Wuruki / N'Ko Institute** French–N'Ko lexicon
(<https://www.nkowuruki.net/lexique-nkofr.html>). Verify your redistribution
rights before shipping the full dataset; only the sample is included here.

### History management

The History section supports **search** (matches N'Ko or Latin), a live
**count**, **Load more** pagination, per-entry **edit (✎)** and **delete (✕)**,
and **Clear all** (with confirmation). All scoped to the signed-in user.

### Editing & export

- **Edit the result** — the generated N'Ko is an editable field; correct it and
  **Save** to persist the correction (`PATCH /api/history/{id}`). Any history
  entry can be reopened in the editor with ✎.
- **On-screen N'Ko keyboard** — a ⌨ toggle opens a virtual keyboard (vowels,
  consonants, the seven combining **tone marks** plus nasalization/double-dot,
  N'Ko digits ߀–߉, punctuation, space, backspace) that types into whichever
  N'Ko field is focused. Because standard Latin Manding input carries no tone,
  the tone diacritics let a writer complete the orthography by hand on the
  editable output — the correction path for the transliterator's tone
  limitation.
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

## Deploy on Ubuntu LTS (24.04 / 26.04)

One-shot, idempotent script — installs Python, Nginx, a hardened `systemd`
service (Gunicorn + Uvicorn workers), optional PostgreSQL, UFW, and optional
Let's Encrypt TLS. Copy‑paste on a fresh server (run as root):

```bash
sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/nko-voice-transcriptor-b3u9zg/nko-voice-transcriptor/deploy/deploy-ubuntu.sh)"
```

With a domain, HTTPS and PostgreSQL:

```bash
sudo DOMAIN=nko.example.com ENABLE_TLS=1 [email protected] USE_POSTGRES=1 \
  bash -c "$(curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/claude/nko-voice-transcriptor-b3u9zg/nko-voice-transcriptor/deploy/deploy-ubuntu.sh)"
```

Knobs (all optional env vars): `DOMAIN`, `ENABLE_TLS`, `EMAIL`, `USE_POSTGRES`,
`ASR_ENGINE` (`mock`/`mms`), `APP_PORT`, `WORKERS`, `REPO_REF`. See
`deploy/deploy-ubuntu.sh`. After the PR merges, deploy `main` with
`sudo REPO_REF=main ...`.

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

## Version 1.1.0

- Uploads are read with a strict memory bound and rejected as soon as they exceed
  `NKO_MAX_UPLOAD_BYTES`.
- Malformed JWT subject values now return `401` instead of causing a server error.
- Development-only packages moved to `requirements-dev.txt`, keeping production
  images smaller and reducing their dependency surface.

## API

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | – | liveness + engine info |
| GET | `/api/languages` | – | offered source languages |
| GET | `/api/history/count` | Bearer | number of own transcriptions |
| DELETE | `/api/history` | Bearer | clear all own transcriptions |
| GET | `/api/dictionary` | – | N'Ko ↔ French lexicon lookup (`q`, `dir=fr\|nko`) |
| GET | `/api/alphabet` | – | full N'Ko block: glyph, name, Latin value |
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
For standards, keyboards, learning material, and the transliteration caveat, see
`NKO_RESOURCES.md`.
