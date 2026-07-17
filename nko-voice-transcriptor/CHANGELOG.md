# Changelog

## 1.10.0 - 2026-07-17

- Added rotating refresh sessions in HttpOnly cookies, logout revocation, complete account/data
  deletion, personal history export, Android Keystore and iOS Keychain token protection.
- Added queued transcription jobs with provider/progress states and backward-compatible results.
- Added waveform preview, duration, pause/resume, playback, client-side trimming and retry-ready jobs.
- Added timestamp segment storage/editing, tap-to-replay and N'Ko SRT/VTT downloads.
- Added online/offline and active-provider disclosure plus explicit contribution controls.
- Added optional biometric/device-credential locks to both mobile wrappers.
- Hardened trusted-origin navigation and file access, upgraded Android to API 36 and iOS to 1.10.

## 1.9.0 - 2026-07-17

- Added FFmpeg audio/video normalization and silence-aware long-audio segmentation.
- Added explicit opt-in recording retention, correction submission, protected review,
  approved dataset export, and deletion of contributed audio with user history.
- Added conservative retrieval from approved Bambara corrections before optional LLM cleanup.
- Added fixed WER/CER metrics, four-pipeline comparison tooling, speaker-disjoint dataset
  export, and a reproducible MMS adapter-training wrapper.
- Added separately versioned MMS model deployment settings and health reporting.

## 1.8.1 - 2026-07-17

- Fixed Android WebView microphone access by waiting for the runtime
  `RECORD_AUDIO` result before granting audio capture to the web page.
- Restricted the WebView bridge to microphone capture instead of granting every
  requested browser resource.
- Added Android's document picker bridge for importing audio files without
  requesting broad storage access.
- Clarified that registration automatically signs the new account in.
- Added an explicit translated Edit result button and accidental-edit protection
  for generated N'Ko text.
- Added Share transcript with Android's native app chooser, Web Share API, and
  clipboard fallback.

## 1.8.0 - 2026-07-16

### Languages and clients

- Split the browser language catalogs from the i18n engine and made French the
  canonical reference catalog with runtime/test parity validation.
- Added complete Bambara, Russian, Simplified Chinese, English, Arabic, and
  N'Ko interface catalogs. Bambara terminology is derived from the French source.
- Localized dynamic recorder, clipboard, authentication, and error messages.
- Aligned Android at 1.8.0 and added an iOS SwiftUI/WKWebView client.

### Deployment and tests

- Added a copy/paste backend installer and generated-WAV transcription smoke test.

## 1.7.0 - 2026-07-14

### Dictionary

- **Populated the dictionary with the full French→N'Ko lexicon** (~47,800
  entries) from NKo Wuruki / N'Ko Institute, bundled as
  `app/data/lexicon-fr-nko.json`. The loader now defaults to it (override with
  `NKO_LEXICON_PATH`; the small sample is the last-resort fallback).
- Added `app/data/NOTICE.md` crediting the source and stating the
  redistribution caveat.

### Tests

- Assert the bundled full lexicon (>10k entries) is the default and that
  common words (maison, eau, paix, bonjour) resolve.

## 1.6.0 - 2026-07-14

### Learning aid

- Add standard **Latin/phonetic values** for every N'Ko letter and digit in
  `app/nko/block.py` (`romanize()`), plus an ordered `alphabet()` teaching view
  (glyph, name, Latin, kind).
- New public `GET /api/alphabet` returns the full block as a teaching table.
- On-screen keyboard keys now show a **tooltip** with each character's Latin
  value and name (e.g. "b · Ba", "gb · Gba", "ɲ · Nya"), loaded once from
  `/api/alphabet` — the keyboard doubles as an alphabet reference.

### Tests

- Romanization covers all 33 letters (dagbasinna intentionally blank);
  `/api/alphabet` returns 62 entries with Latin values for letters.

## 1.5.0 - 2026-07-14

### N'Ko Unicode completeness

- Add `app/nko/block.py`: the canonical N'Ko Unicode block (U+07C0–U+07FF),
  62 assigned characters generated from the Unicode Character Database, as the
  single source of truth for what counts as valid N'Ko.
- Extend the on-screen keyboard to full block coverage: the previously missing
  letters (NA WOLOSO ߠ, NYA WOLOSO ߧ, JONA JA/CHA/RA ߨߩߪ), the DANTAYALAN
  combining mark, the high/low tone apostrophes (ߴ ߵ), and the N'Ko symbols
  and punctuation. All 33 letters are now typeable.
- Add `docs/NKO_UNICODE_BLOCK.md` — the full reference table, with links to
  the authoritative Unicode chart and specialist references.

### Tests

- `tests/test_nko_unicode.py`: the committed block table must match
  `unicodedata` exactly; every keyboard glyph must be an assigned N'Ko
  codepoint; the keyboard must cover all 33 letters and the 7 tone marks; the
  transliterator must only emit assigned N'Ko (or ASCII punctuation).

## 1.4.0 - 2026-07-14

### Features

- **N'Ko ↔ French dictionary lookup.** New `GET /api/dictionary` endpoint and
  a UI section search the lexicon in either direction (French headword,
  accent-insensitive, or the N'Ko side), ranked exact → prefix → substring. A
  result can be inserted straight into the N'Ko editor, so the dictionary
  doubles as a spelling aid for corrections.
- Lexicon data is loaded once at startup from `NKO_LEXICON_PATH`, defaulting
  to a bundled **attributed sample** (`app/data/lexicon-sample.json`).

### Attribution

- Dictionary data is derived from the NKo Wuruki / N'Ko Institute
  French–N'Ko lexicon (https://www.nkowuruki.net/lexique-nkofr.html). Only a
  sample ships in-repo; supply the full dataset you are licensed to use via
  `NKO_LEXICON_PATH`. See `NKO_RESOURCES.md`.

## 1.3.0 - 2026-07-13

### Features

- On-screen N'Ko keyboard now includes the combining **tone diacritics**
  (short high/low/rising, long descending/high/low/rising) plus the
  nasalization and double-dot marks. These carry the tone and length that
  Latin ASR cannot supply, so users can complete the orthography by hand on
  the editable output.

### Security

- Login now performs a dummy Argon2 verification for unknown usernames, so
  the failure path takes the same time as a real wrong password (removes the
  timing side-channel for user enumeration). Addresses a 1.2.0 audit finding.
- `scripts/publish-claude-skills.sh` no longer force-pushes by default: it
  prints the resolved remote, requires `CONFIRM_FORCE_PUSH=1`, and uses
  `--force-with-lease`. Addresses the audit's highest operational finding.

### Documentation

- Added the full compiled N'Ko research link sets under `docs/nko-research/`
  for provenance, referenced from `NKO_RESOURCES.md`.

## 1.2.0 - 2026-07-13

### Interface

- Refresh visual hierarchy, responsive behavior, focus states, and RTL-friendly
  workspace sections.
- Add a keyboard-accessible skip link, reduced-motion handling, and sign-out action.

### Security review

- Add a repository-wide security assessment with prioritized open risks.

## 1.1.0 - 2026-07-13

### Security

- Bound multipart audio reads to the configured maximum upload size plus one byte.
- Treat non-numeric JWT subjects as invalid credentials.
- Handle concurrent duplicate registrations without leaking a database error.
- Disable caching on sensitive API routes and add browser isolation, microphone,
  and production HSTS headers.

### Packaging

- Separate test and lint tools into `requirements-dev.txt`.
- Add a curated N'Ko technical and learning resource guide.

### Tests

- Add regression coverage for malformed JWT subjects.

## 1.0.0 - 2026-07-11

- Initial release.
