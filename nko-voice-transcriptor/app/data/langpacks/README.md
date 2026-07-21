# Language packs

Each `*.json` file here is a **language pack** consumed by the `app.langpack`
module: it maps terms in one language to N'Ko.

```json
{
  "_language": "en",
  "_name": "English",
  "_partial": true,
  "entries": [ { "term": "water", "nko": "ߓߊߟߋ߲", "cat": "ߕ." }, ... ]
}
```

- **French** (`fr`) is **not** stored here — it is served from the full
  reference lexicon (`app/data/lexicon-fr-nko.json`, ~47,800 entries).
- **`en`, `ru`, `zh`, `ar`** are **curated seed packs** (`_partial: true`):
  common vocabulary, translated by hand and attached to the authentic N'Ko
  from the French lexicon. They are **not** full translations of all ~47,800
  entries — that requires a translation source this build could not reach, and
  auto-generating it would fabricate data.

## Add or complete a pack

- **Add a language:** drop a `<code>.json` file here with the shape above. The
  `app.langpack` registry discovers it automatically; no code change, and it
  appears in `GET /api/langpack/languages` and the dictionary's language menu.
- **Regenerate the seeds:** `python scripts/build_seed_langpacks.py`.
- **Complete a pack from a translation source:** produce a JSON of the same
  shape (e.g. by translating the French headwords with a service you have
  rights to use) and replace the seed file, keeping `_partial: false` once it
  is comprehensive.

## Attribution

N'Ko values come from the **NKo Wuruki / N'Ko Institute** lexicon
(see `../NOTICE.md`). Translations in the seed packs are hand-curated.
