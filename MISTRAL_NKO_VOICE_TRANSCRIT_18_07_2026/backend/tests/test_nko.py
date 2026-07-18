"""Golden tests for the deterministic Latin → N'Ko transliterator."""

from app.nko import transliterate
from app.nko.block import contains_nko, is_nko_char


def test_syllabic_n_pronoun():
    assert transliterate("n") == "ߒ"


def test_greeting_golden():
    # i → ߌ ; ni → ߣߌ (onset n) ; ce → ߗߋ
    assert transliterate("i ni ce") == "ߌ ߣߌ ߗߋ"


def test_coda_nasalization():
    # kan → KA + A + combining nasalization mark (not letter NA)
    assert transliterate("kan") == "ߞߊ߲"


def test_ny_digraph():
    assert transliterate("nya") == "ߢߊ"


def test_digits():
    assert transliterate("2026") == "߂߀߂߆"


def test_punctuation():
    assert transliterate("a?") == "ߊ؟"


def test_unknown_passthrough():
    assert "q" in transliterate("q")


def test_whitespace_preserved():
    result = transliterate("i ni\nce")
    assert "\n" in result and result.count(" ") == 1


def test_empty():
    assert transliterate("") == ""


def test_output_is_nko():
    assert contains_nko(transliterate("i ni ce"))
    assert is_nko_char("ߒ")
    assert not is_nko_char("a")
