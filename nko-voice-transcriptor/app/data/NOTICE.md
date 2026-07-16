# Dictionary data — attribution & notice

The bundled French–N'Ko lexicon files in this directory
(`lexicon-fr-nko.json`, `lexicon-sample.json`) are derived from:

> **NKo Wuruki / N'Ko Institute** — *Lexique N'Ko–Français*
> <https://www.nkowuruki.net/lexique-nkofr.html>

- `lexicon-fr-nko.json` — the full French→N'Ko lexicon (~47,800 entries),
  included at the repository owner's direction.
- `lexicon-sample.json` — a small subset used as a fallback and in tests.

Each entry is `{ "fr": <French>, "nko": <N'Ko>, "cat": <N'Ko grammatical
category marker> }`.

**Please respect the source.** This data is the work of the N'Ko Institute /
NKo Wuruki. Credit them, and confirm you have the right to redistribute before
reusing this dataset outside this project. To supply your own lexicon instead,
set `NKO_LEXICON_PATH` to a JSON file of the same shape.
