# License notes

## Code

The code in this repository is © the repository owner. Choose and commit a
LICENSE file before public distribution (MIT recommended for the code if you
want permissive reuse; the repository currently ships without one so the
choice stays yours).

## French→N'Ko lexicon (`backend/app/data/lexicon-fr-nko.json`)

- Source: **N'Ko Wuruki / N'Ko Institute (Conakry)** —
  <https://www.nkowuruki.net/lexique-nkofr.html> (~47,764 entries,
  extracted 2026-07-14).
- The dataset is redistributed at the repository owner's direction.
  **Verify redistribution rights with N'Ko Wuruki before shipping this file
  in a public release or app store build.** Keep the `_attribution` field
  intact in the JSON.

## Fonts

`Noto Sans NKo` (SIL Open Font License 1.1) should be self-hosted at
`backend/app/static/fonts/NotoSansNKo-Regular.ttf` — fetch it with
`backend/scripts/fetch_fonts.sh`. The OFL permits bundling; keep the license
notice alongside the font file.

## ASR models

- `facebook/mms-1b-all` — CC-BY-NC 4.0. **Non-commercial license**: review
  before commercial deployment; consider the RobotsMali / African Next
  Voices Bambara fine-tunes (612 h open dataset, 2025) as alternatives.
- Mistral Voxtral API usage is governed by Mistral's terms of service.
- Voxtral Realtime open weights are Apache 2.0 if you self-host them later.

## Heritage

This project is a clean-room rebuild of the N'Ko Voice Transcriptor v1.7.0
and reuses the transliteration design of `offline_nko_voice_transcript`
(same owner). The UX draws on FluidVoice's language-first onboarding ideas
without copying its GPLv3 source.
