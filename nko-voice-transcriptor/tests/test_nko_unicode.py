"""Validate N'Ko output and the keyboard against the canonical Unicode block."""

import re
import unicodedata
from pathlib import Path

from app.nko import block, transliterate

APP_JS = Path(__file__).resolve().parent.parent / "app" / "static" / "app.js"


class TestCanonicalBlock:
    def test_matches_unicodedata(self):
        # The committed table must exactly match what unicodedata reports for
        # the block — catches edit typos and Unicode-version drift.
        derived = {}
        for cp in range(block.BLOCK_START, block.BLOCK_END + 1):
            try:
                derived[cp] = unicodedata.name(chr(cp))
            except ValueError:
                pass
        table = {cp: name for cp, _, name, _ in block.NKO_CHARACTERS}
        assert table == derived

    def test_char_field_matches_codepoint(self):
        for cp, ch, _, _ in block.NKO_CHARACTERS:
            assert ord(ch) == cp

    def test_helpers_partition(self):
        assert len(block.letters()) == 33
        assert len(block.marks()) == 10
        assert len(block.symbols()) == 9
        assert len(block.NKO_CHARACTERS) == 62

    def test_is_nko(self):
        assert block.is_nko("ߒ")
        assert not block.is_nko("a")
        assert not block.is_nko(chr(0x07FB))  # unassigned in the block


def _keyboard_nko_chars() -> set[str]:
    """Extract every N'Ko-block character used in the app.js KEY_ROWS layout."""
    src = APP_JS.read_text(encoding="utf-8")
    m = re.search(r"const KEY_ROWS = \[(.*?)\];", src, re.S)
    assert m, "KEY_ROWS not found in app.js"
    return {c for c in m.group(1) if block.BLOCK_START <= ord(c) <= block.BLOCK_END}


class TestKeyboardLayout:
    def test_only_assigned_codepoints(self):
        # Every N'Ko glyph on the on-screen keyboard must be a real, assigned
        # character (no unassigned holes, no typos).
        for ch in _keyboard_nko_chars():
            assert block.is_nko(ch), f"keyboard char U+{ord(ch):04X} not assigned"

    def test_covers_all_letters(self):
        keyboard = _keyboard_nko_chars()
        missing = [c for c in block.letters() if c not in keyboard]
        assert not missing, f"letters missing from keyboard: {missing}"

    def test_includes_tone_marks(self):
        keyboard = _keyboard_nko_chars()
        # the seven tone marks U+07EB–U+07F1
        for cp in range(0x07EB, 0x07F2):
            assert chr(cp) in keyboard


class TestRomanization:
    def test_every_letter_has_latin_except_dagbasinna(self):
        for ch in block.letters():
            latin = block.romanize(ch)
            if ord(ch) == 0x07D1:  # dagbasinna: length mark, no phonetic value
                assert latin == ""
            else:
                assert latin, f"letter U+{ord(ch):04X} missing romanization"

    def test_known_values(self):
        assert block.romanize("ߓ") == "b"
        assert block.romanize("ߜ") == "gb"
        assert block.romanize("ߢ") == "ɲ"
        assert block.romanize("߅") == "5"

    def test_alphabet_view(self):
        alpha = block.alphabet()
        assert len(alpha) == 62
        kinds = {e["kind"] for e in alpha}
        assert kinds == {"letter", "digit", "mark", "symbol"}
        ba = next(e for e in alpha if e["char"] == "ߓ")
        assert ba["latin"] == "b" and ba["name"] == "Ba" and ba["cp"] == "U+07D3"


class TestAlphabetEndpoint:
    def test_public_and_complete(self, client):
        r = client.get("/api/alphabet")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) == 62
        assert all(0x07C0 <= int(row["cp"][2:], 16) <= 0x07FF for row in rows)
        # letters carry a Latin value
        letters = [row for row in rows if row["kind"] == "letter"]
        assert len(letters) == 33
        assert any(row["latin"] == "gb" for row in letters)


class TestTransliteratorStaysInBlock:
    def test_output_only_nko_or_ascii_punct(self):
        words = "bamanankan i ni ce mɔgɔ dun nyama an ka kalan 2026 mun?"
        out = transliterate(words)
        for ch in out:
            if ch.isspace() or ch in "?":
                continue
            assert block.is_nko(ch) or ord(ch) == 0x061F, f"{ch!r} outside N'Ko block"
