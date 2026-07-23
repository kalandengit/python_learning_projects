# N'Ko references and project guidance

This shortlist consolidates the most useful material from the three research
files reviewed for version 1.1.0. Standards and specialist references are
preferred over transient social-media posts. The full compiled link sets are
kept for provenance under [`docs/nko-research/`](docs/nko-research/).

## Technical references

- [Unicode chart U+07C0 (PDF)](https://www.unicode.org/charts/PDF/U07C0.pdf) —
  the official N'Ko code chart. See also `docs/NKO_UNICODE_BLOCK.md` for the
  full generated table.
- [UnicodePlus — Nkoo](https://unicodeplus.com/script/Nkoo) and
  [Unicodepedia — N'Ko](https://www.unicodepedia.com/groups/nko) — browsable
  character references.
- [Unicode N'Ko block chart](https://www.unicode.org/charts/PDF/U07C0.pdf) —
  encoded characters in U+07C0–U+07FF.
- [Unicode Core Specification, African scripts](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-19/) —
  normative character behavior.
- [W3C N'Ko layout requirements](https://www.w3.org/TR/nkoo-lreq/) — direction,
  shaping, line breaking, punctuation, and Web layout.
- [Richard Ishida's N'Ko orthography notes](https://r12a.github.io/scripts/nkoo/nqo.html) —
  practical orthographic and browser notes.
- [ScriptSource: Nkoo](https://scriptsource.org/scr/Nkoo) — script, language,
  font, and keyboard metadata.
- [Keyman N'Ko keyboard](https://keyman.com/keyboards/nko) — cross-platform
  N'Ko input.

## Lexicons and dictionaries

- [NKo Wuruki — Lexique N'Ko/Français](https://www.nkowuruki.net/lexique-nkofr.html) —
  a large French↔N'Ko lexicon (≈47,840 entries) with grammatical category
  markers. **Used by this app's dictionary feature** (bundled sample only;
  supply the full data via `NKO_LEXICON_PATH`). Attribution: NKo Wuruki /
  N'Ko Institute, Conakry. Confirm redistribution rights before shipping the
  full dataset.
- [NKo Wuruki — Nkotronic](https://www.nkowuruki.net/nkotronic.html) — an N'Ko
  assistant (ask in French or N'Ko).
- [NKo Wuruki — N'Ko fonts](https://www.nkowuruki.net/nko-fonts.html) —
  downloadable N'Ko fonts (useful for the self-hosted-font improvement below).
- [Vydrine, "Sur le Dictionnaire N'Ko" (Mandenkan)](https://llacan.cnrs.fr/PDF/Mandenkan31/vydrin31.pdf) —
  scholarly analysis of the N'Ko dictionary tradition.

## Learning and community material

- [An ka taa](https://www.ankataa.com/) — Manding and N'Ko lessons from a
  researcher-led project.
- [N'Ko Learner](https://nkolearner.com/) — lessons, practice, and online input.
- [N'Ko Institute](https://www.nkoinstitute.com/) — cultural and educational
  material.
- [N'Ko Wikipedia](https://nqo.wikipedia.org/) — substantial native-script text.
- [CorMand N'Ko library](https://cormand.huma-num.fr/maninkabiblio/) — a digital
  corpus and bibliography.

## NLP research

- [Machine Translation for Nko: Tools, Corpora and Baseline Results](https://aclanthology.org/2023.wmt-1.34/) —
  open tooling and corpora relevant to future language-model features.

## Important product limitation

The app converts Latin Manding output into N'Ko characters; it is not a complete
orthographic transcription system. Standard Latin Bambara input generally does
not contain enough tone and length information to generate fully specified
native N'Ko. The output should therefore remain editable and be presented as a
draft for review by a competent N'Ko writer. This limitation is deliberate and
documented in `app/nko/tables.py`.

## Recommended next improvements

1. Have a native N'Ko writer review the transliteration table and all N'Ko UI
   translations.
2. Build a licensed, versioned evaluation corpus from native N'Ko text and
   aligned Manding audio.
3. Self-host Noto Sans NKo under its license to make rendering consistent.
4. Evaluate direct speech-to-N'Ko or post-editing models against the deterministic
   transliterator; do not silently replace the current auditable path.
