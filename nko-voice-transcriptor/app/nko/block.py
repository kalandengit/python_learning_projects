"""Canonical N'Ko Unicode block (U+07C0–U+07FF).

Authoritative data: every character assigned in the N'Ko block, generated
from Python's ``unicodedata`` (the Unicode Character Database). Used as the
single source of truth for validating that the app only ever emits real,
assigned N'Ko codepoints. Regenerate if the bundled Unicode version changes;
``tests/test_nko_unicode.py`` re-derives from ``unicodedata`` and asserts
this table matches, so drift or typos are caught.
"""

from __future__ import annotations

BLOCK_START = 0x07C0
BLOCK_END = 0x07FF

# (codepoint, character, unicode_name, category)
NKO_CHARACTERS: tuple[tuple[int, str, str, str], ...] = (
    (0x07C0, "߀", "NKO DIGIT ZERO", "Nd"),
    (0x07C1, "߁", "NKO DIGIT ONE", "Nd"),
    (0x07C2, "߂", "NKO DIGIT TWO", "Nd"),
    (0x07C3, "߃", "NKO DIGIT THREE", "Nd"),
    (0x07C4, "߄", "NKO DIGIT FOUR", "Nd"),
    (0x07C5, "߅", "NKO DIGIT FIVE", "Nd"),
    (0x07C6, "߆", "NKO DIGIT SIX", "Nd"),
    (0x07C7, "߇", "NKO DIGIT SEVEN", "Nd"),
    (0x07C8, "߈", "NKO DIGIT EIGHT", "Nd"),
    (0x07C9, "߉", "NKO DIGIT NINE", "Nd"),
    (0x07CA, "ߊ", "NKO LETTER A", "Lo"),
    (0x07CB, "ߋ", "NKO LETTER EE", "Lo"),
    (0x07CC, "ߌ", "NKO LETTER I", "Lo"),
    (0x07CD, "ߍ", "NKO LETTER E", "Lo"),
    (0x07CE, "ߎ", "NKO LETTER U", "Lo"),
    (0x07CF, "ߏ", "NKO LETTER OO", "Lo"),
    (0x07D0, "ߐ", "NKO LETTER O", "Lo"),
    (0x07D1, "ߑ", "NKO LETTER DAGBASINNA", "Lo"),
    (0x07D2, "ߒ", "NKO LETTER N", "Lo"),
    (0x07D3, "ߓ", "NKO LETTER BA", "Lo"),
    (0x07D4, "ߔ", "NKO LETTER PA", "Lo"),
    (0x07D5, "ߕ", "NKO LETTER TA", "Lo"),
    (0x07D6, "ߖ", "NKO LETTER JA", "Lo"),
    (0x07D7, "ߗ", "NKO LETTER CHA", "Lo"),
    (0x07D8, "ߘ", "NKO LETTER DA", "Lo"),
    (0x07D9, "ߙ", "NKO LETTER RA", "Lo"),
    (0x07DA, "ߚ", "NKO LETTER RRA", "Lo"),
    (0x07DB, "ߛ", "NKO LETTER SA", "Lo"),
    (0x07DC, "ߜ", "NKO LETTER GBA", "Lo"),
    (0x07DD, "ߝ", "NKO LETTER FA", "Lo"),
    (0x07DE, "ߞ", "NKO LETTER KA", "Lo"),
    (0x07DF, "ߟ", "NKO LETTER LA", "Lo"),
    (0x07E0, "ߠ", "NKO LETTER NA WOLOSO", "Lo"),
    (0x07E1, "ߡ", "NKO LETTER MA", "Lo"),
    (0x07E2, "ߢ", "NKO LETTER NYA", "Lo"),
    (0x07E3, "ߣ", "NKO LETTER NA", "Lo"),
    (0x07E4, "ߤ", "NKO LETTER HA", "Lo"),
    (0x07E5, "ߥ", "NKO LETTER WA", "Lo"),
    (0x07E6, "ߦ", "NKO LETTER YA", "Lo"),
    (0x07E7, "ߧ", "NKO LETTER NYA WOLOSO", "Lo"),
    (0x07E8, "ߨ", "NKO LETTER JONA JA", "Lo"),
    (0x07E9, "ߩ", "NKO LETTER JONA CHA", "Lo"),
    (0x07EA, "ߪ", "NKO LETTER JONA RA", "Lo"),
    (0x07EB, "߫", "NKO COMBINING SHORT HIGH TONE", "Mn"),
    (0x07EC, "߬", "NKO COMBINING SHORT LOW TONE", "Mn"),
    (0x07ED, "߭", "NKO COMBINING SHORT RISING TONE", "Mn"),
    (0x07EE, "߮", "NKO COMBINING LONG DESCENDING TONE", "Mn"),
    (0x07EF, "߯", "NKO COMBINING LONG HIGH TONE", "Mn"),
    (0x07F0, "߰", "NKO COMBINING LONG LOW TONE", "Mn"),
    (0x07F1, "߱", "NKO COMBINING LONG RISING TONE", "Mn"),
    (0x07F2, "߲", "NKO COMBINING NASALIZATION MARK", "Mn"),
    (0x07F3, "߳", "NKO COMBINING DOUBLE DOT ABOVE", "Mn"),
    (0x07F4, "ߴ", "NKO HIGH TONE APOSTROPHE", "Lm"),
    (0x07F5, "ߵ", "NKO LOW TONE APOSTROPHE", "Lm"),
    (0x07F6, "߶", "NKO SYMBOL OO DENNEN", "So"),
    (0x07F7, "߷", "NKO SYMBOL GBAKURUNEN", "Po"),
    (0x07F8, "߸", "NKO COMMA", "Po"),
    (0x07F9, "߹", "NKO EXCLAMATION MARK", "Po"),
    (0x07FA, "ߺ", "NKO LAJANYALAN", "Lm"),
    (0x07FD, "߽", "NKO DANTAYALAN", "Mn"),
    (0x07FE, "߾", "NKO DOROME SIGN", "Sc"),
    (0x07FF, "߿", "NKO TAMAN SIGN", "Sc"),
)

ASSIGNED_CODEPOINTS = frozenset(cp for cp, _, _, _ in NKO_CHARACTERS)


def is_nko(ch: str) -> bool:
    """True if ``ch`` is an assigned character in the N'Ko block."""
    return ord(ch) in ASSIGNED_CODEPOINTS


def letters() -> list[str]:
    """Assigned N'Ko letters (Lo), in code order."""
    return [c for _, c, n, cat in NKO_CHARACTERS if "LETTER" in n]


def marks() -> list[str]:
    """Combining marks (tone, nasalization, …), in code order."""
    return [c for _, c, n, cat in NKO_CHARACTERS if cat.startswith("M")]


def symbols() -> list[str]:
    """Punctuation and symbols (non-letter, non-mark, non-digit)."""
    out = []
    for _, c, n, cat in NKO_CHARACTERS:
        if "DIGIT" not in n and "LETTER" not in n and not cat.startswith("M"):
            out.append(c)
    return out


# --- Romanization (standard N'Ko Latin/phonetic values, for learning) --------
# Latin/phonetic value of each N'Ko letter, keyed by codepoint. Matches the
# Manding Latin orthography used by the transliterator (ɛ ɔ ɲ). ``dagbasinna``
# has no phonetic value of its own (it marks length/gemination).
LATIN_VALUES: dict[int, str] = {
    0x07CA: "a", 0x07CB: "e", 0x07CC: "i", 0x07CD: "ɛ", 0x07CE: "u",
    0x07CF: "o", 0x07D0: "ɔ", 0x07D1: "", 0x07D2: "n", 0x07D3: "b",
    0x07D4: "p", 0x07D5: "t", 0x07D6: "j", 0x07D7: "c", 0x07D8: "d",
    0x07D9: "r", 0x07DA: "rr", 0x07DB: "s", 0x07DC: "gb", 0x07DD: "f",
    0x07DE: "k", 0x07DF: "l", 0x07E0: "n", 0x07E1: "m", 0x07E2: "ɲ",
    0x07E3: "n", 0x07E4: "h", 0x07E5: "w", 0x07E6: "y", 0x07E7: "ɲ",
    0x07E8: "j", 0x07E9: "c", 0x07EA: "r",
}
# Digits romanize to their Western value.
LATIN_VALUES.update({0x07C0 + d: str(d) for d in range(10)})


def romanize(ch: str) -> str:
    """Latin/phonetic value of a N'Ko character, or '' if it has none."""
    return LATIN_VALUES.get(ord(ch), "")


def _kind(name: str, cat: str) -> str:
    if "DIGIT" in name:
        return "digit"
    if cat.startswith("M"):
        return "mark"
    if "LETTER" in name:
        return "letter"
    return "symbol"


def short_name(name: str) -> str:
    """The letter/character name without the ``NKO`` / ``LETTER`` prefixes."""
    return name.replace("NKO ", "").replace("LETTER ", "").title()


def alphabet() -> list[dict]:
    """Ordered teaching view of the whole block: glyph, name, Latin, kind."""
    return [
        {
            "cp": f"U+{cp:04X}",
            "char": ch,
            "name": short_name(name),
            "latin": romanize(ch),
            "kind": _kind(name, cat),
        }
        for cp, ch, name, cat in NKO_CHARACTERS
    ]

