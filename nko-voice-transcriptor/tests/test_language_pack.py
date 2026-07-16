"""Static checks for the separately maintained browser language pack."""

import re
from pathlib import Path

STATIC = Path(__file__).parents[1] / "app" / "static"
EXPECTED_LANGUAGES = {"fr", "bm", "en", "ru", "zh", "ar", "nqo"}


def _catalogs() -> dict[str, str]:
    source = (STATIC / "languages.js").read_text(encoding="utf-8")
    starts = list(re.finditer(r"^  ([a-z]{2,3}): \{$", source, re.MULTILINE))
    catalogs = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(source)
        catalogs[match.group(1)] = source[match.end() : end]
    return catalogs


def _keys(catalog: str) -> set[str]:
    return set(re.findall(r"(?:^|,\s*)([a-z][a-z0-9_]*):\s*", catalog, re.MULTILINE))


def test_french_is_reference_language():
    engine = (STATIC / "i18n.js").read_text(encoding="utf-8")
    assert 'REFERENCE_LANGUAGE = "fr"' in engine


def test_all_requested_languages_are_present_and_complete():
    catalogs = _catalogs()
    assert set(catalogs) == EXPECTED_LANGUAGES
    reference_keys = _keys(catalogs["fr"])
    assert len(reference_keys) >= 45
    for language, catalog in catalogs.items():
        assert _keys(catalog) == reference_keys, language


def test_language_module_loads_before_engine():
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert html.index("/static/languages.js") < html.index("/static/i18n.js")


def test_bambara_catalog_uses_standard_language_tag():
    catalog = _catalogs()["bm"]
    assert 'Bamanankan' in catalog
    assert "Daɲɛgafe" in catalog
