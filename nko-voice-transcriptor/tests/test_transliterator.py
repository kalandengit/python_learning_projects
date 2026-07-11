"""Unit tests for the Bambara Latin → N'Ko transliteration engine."""

from app.nko import tables as t
from app.nko import transliterate


class TestVowels:
    def test_all_seven_vowels(self):
        assert transliterate("a") == t.NKO_A
        assert transliterate("e") == t.NKO_EE
        assert transliterate("ɛ") == t.NKO_E
        assert transliterate("i") == t.NKO_I
        assert transliterate("o") == t.NKO_OO
        assert transliterate("ɔ") == t.NKO_O
        assert transliterate("u") == t.NKO_U

    def test_accent_fallbacks(self):
        # è/ò are common keyboard substitutes for ɛ/ɔ
        assert transliterate("è") == t.NKO_E
        assert transliterate("ò") == t.NKO_O


class TestWords:
    def test_bamanankan(self):
        # ba-ma-nan-kan: two coda nasals → nasalization marks
        expected = (
            t.NKO_BA + t.NKO_A
            + t.NKO_MA + t.NKO_A
            + t.NKO_NA + t.NKO_A + t.NKO_NASAL
            + t.NKO_KA + t.NKO_A + t.NKO_NASAL
        )
        assert transliterate("bamanankan") == expected

    def test_nko_word_itself(self):
        # "n'ko" ("I say"): syllabic-N word is special-cased; here it's n + ' + ko
        # "nko" has n at word start (no preceding vowel) → letter NA
        assert transliterate("nko") == t.NKO_NA + t.NKO_KA + t.NKO_OO

    def test_syllabic_n_pronoun(self):
        # bare "n" = 1sg pronoun → syllabic N ߒ
        assert transliterate("n") == t.NKO_N_SYLLABIC
        assert transliterate("n bɛ taa") == (
            t.NKO_N_SYLLABIC
            + " " + t.NKO_BA + t.NKO_E
            + " " + t.NKO_TA + t.NKO_A + t.NKO_A
        )

    def test_mogo(self):
        assert transliterate("mɔgɔ") == t.NKO_MA + t.NKO_O + t.NKO_GBA + t.NKO_O


class TestNasals:
    def test_word_final_nasal(self):
        assert transliterate("dun") == t.NKO_DA + t.NKO_U + t.NKO_NASAL

    def test_nasal_before_consonant(self):
        # "tinba" → ti + nasal + ba
        assert transliterate("tinba") == (
            t.NKO_TA + t.NKO_I + t.NKO_NASAL + t.NKO_BA + t.NKO_A
        )

    def test_n_before_vowel_is_letter(self):
        # "sini" (tomorrow): n is onset of second syllable
        assert transliterate("sini") == t.NKO_SA + t.NKO_I + t.NKO_NA + t.NKO_I

    def test_word_initial_n_cluster(self):
        # "nsira" — initial n with no preceding vowel stays a letter
        result = transliterate("nsira")
        assert result.startswith(t.NKO_NA)


class TestDigraphs:
    def test_ny_maps_to_nya(self):
        assert transliterate("nyama") == t.NKO_NYA + t.NKO_A + t.NKO_MA + t.NKO_A

    def test_nya_letter_direct(self):
        assert transliterate("ɲama") == t.NKO_NYA + t.NKO_A + t.NKO_MA + t.NKO_A

    def test_ny_after_vowel_still_digraph(self):
        # "kanya": ny between vowels reads as the ɲ digraph, not coda n + y
        assert transliterate("kanya") == (
            t.NKO_KA + t.NKO_A + t.NKO_NYA + t.NKO_A
        )

    def test_gb(self):
        assert transliterate("gba") == t.NKO_GBA + t.NKO_A

    def test_rr(self):
        assert transliterate("burru") == (
            t.NKO_BA + t.NKO_U + t.NKO_RRA + t.NKO_U
        )


class TestDigitsAndPunctuation:
    def test_digits(self):
        assert transliterate("2026") == "߂߀߂߆"

    def test_punctuation(self):
        assert transliterate("a, b!") == t.NKO_A + t.NKO_COMMA + " " + t.NKO_BA + t.NKO_EXCLAMATION
        assert transliterate("mun?") == (
            t.NKO_MA + t.NKO_U + t.NKO_NASAL + t.ARABIC_QUESTION
        )


class TestRobustness:
    def test_empty(self):
        assert transliterate("") == ""

    def test_whitespace_and_lines_preserved(self):
        out = transliterate("aa bb\ncc")
        assert "\n" in out
        assert out.count(" ") == 1

    def test_unknown_chars_pass_through(self):
        assert "x" in transliterate("xylo")  # x not in Bambara alphabet
        assert "." in transliterate("a.")

    def test_uppercase_normalized(self):
        assert transliterate("BAMAKO") == transliterate("bamako")

    def test_output_is_nko_block(self):
        out = transliterate("bamanankan")
        for ch in out:
            assert 0x07C0 <= ord(ch) <= 0x07FF, f"{ch!r} outside N'Ko block"

    def test_idempotent_on_nko_input(self):
        # Already-N'Ko text passes through unchanged
        nko = transliterate("bamanankan")
        assert transliterate(nko) == nko
