"""Supported source languages.

All entries are Manding languages/varieties that (a) have an ASR adapter in
Meta MMS (``facebook/mms-1b-all``) and (b) are conventionally writable in the
N'Ko script with the shared Latin→N'Ko rules in :mod:`app.nko` — the Manding
varieties use the same core Latin orthography (vowels ``a e ɛ i o ɔ u``,
nasal codas, ``ɲ``/``ŋ``), so one transliterator serves them all.

Which of these are *offered* by a deployment is controlled by
``NKO_LANGUAGES``; this table only supplies display names.
"""

LANGUAGE_NAMES: dict[str, str] = {
    "bam": "Bambara (Bamanankan)",
    "dyu": "Dyula (Jula)",
    "emk": "Maninka, Eastern (Malinké)",
    "mku": "Maninka, Konyanka",
    "msc": "Maninka, Sankaran",
    "mwk": "Maninkakan, Kita",
}


def display_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)
