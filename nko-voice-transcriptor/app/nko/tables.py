"""Character tables for Bambara Latin → N'Ko transliteration.

The N'Ko script (ߒߞߏ, Unicode block U+07C0–U+07FF) was devised by Solomana
Kanté in 1949 for the Manding languages. It is written right-to-left.

Orthographic conventions implemented here (documented design choices):

* Source is the official Bambara Latin orthography (Mali, 1982 revision):
  vowels ``a e ɛ i o ɔ u``, consonants ``b c d f g h j k l m n ɲ ŋ p r s t
  w y z``. ASCII fallbacks ``ny → ɲ`` and ``è/ò``-style accents are
  normalized before mapping.
* Syllable-final ``n`` (before a consonant or at word end) marks vowel
  nasality in Bambara and is rendered as the N'Ko combining nasalization
  mark U+07F2 on the preceding vowel — not as the letter NA.
* A word consisting of bare ``n`` (the 1sg pronoun "I/me") is the syllabic
  N letter U+07D2.
* Bambara ``g`` maps to N'Ko GBA (U+07DC), the conventional Manding value.
* ``z`` (loanword-only in Bambara) maps to SA + combining dot above,
  the N'Ko convention for extended/foreign sounds.
* Standard Bambara orthography does not write tone, so no tone marks are
  emitted; long vowels written as doubled Latin vowels come out as doubled
  N'Ko vowel letters. (Documented limitation: native N'Ko text would carry
  tone/length diacritics that plain Latin input cannot supply.)
"""

from __future__ import annotations

# --- N'Ko letters -----------------------------------------------------------

NKO_A = "ߊ"        # ߊ
NKO_EE = "ߋ"       # ߋ  e
NKO_I = "ߌ"        # ߌ
NKO_E = "ߍ"        # ߍ  ɛ
NKO_U = "ߎ"        # ߎ
NKO_OO = "ߏ"       # ߏ  o
NKO_O = "ߐ"        # ߐ  ɔ
NKO_DAGBASINNA = "ߑ"  # ߑ  gemination / elision mark
NKO_N_SYLLABIC = "ߒ"  # ߒ  syllabic N ("I")
NKO_BA = "ߓ"       # ߓ
NKO_PA = "ߔ"       # ߔ
NKO_TA = "ߕ"       # ߕ
NKO_JA = "ߖ"       # ߖ
NKO_CHA = "ߗ"      # ߗ
NKO_DA = "ߘ"       # ߘ
NKO_RA = "ߙ"       # ߙ
NKO_RRA = "ߚ"      # ߚ
NKO_SA = "ߛ"       # ߛ
NKO_GBA = "ߜ"      # ߜ
NKO_FA = "ߝ"       # ߝ
NKO_KA = "ߞ"       # ߞ
NKO_LA = "ߟ"       # ߟ
NKO_MA = "ߡ"       # ߡ
NKO_NYA = "ߢ"      # ߢ  ɲ
NKO_NA = "ߣ"       # ߣ
NKO_HA = "ߤ"       # ߤ
NKO_WA = "ߥ"       # ߥ
NKO_YA = "ߦ"       # ߦ

NKO_NASAL = "߲"    # ߲  combining nasalization mark
NKO_DOT_ABOVE = "߭"  # ߭  combining mark used for extended consonants

NKO_COMMA = "߸"    # ߸
NKO_EXCLAMATION = "߹"  # ߹
ARABIC_QUESTION = "؟"  # ؟  (used in N'Ko text)

# --- Mapping tables ---------------------------------------------------------

VOWELS: dict[str, str] = {
    "a": NKO_A,
    "e": NKO_EE,
    "ɛ": NKO_E,   # ɛ
    "i": NKO_I,
    "o": NKO_OO,
    "ɔ": NKO_O,   # ɔ
    "u": NKO_U,
}

CONSONANTS: dict[str, str] = {
    "b": NKO_BA,
    "c": NKO_CHA,
    "d": NKO_DA,
    "f": NKO_FA,
    "g": NKO_GBA,
    "h": NKO_HA,
    "j": NKO_JA,
    "k": NKO_KA,
    "l": NKO_LA,
    "m": NKO_MA,
    "n": NKO_NA,
    "ɲ": NKO_NYA,          # ɲ
    "ŋ": NKO_NA + NKO_DOT_ABOVE,  # ŋ as onset (rare); coda ŋ nasalizes
    "p": NKO_PA,
    "r": NKO_RA,
    "s": NKO_SA,
    "t": NKO_TA,
    "w": NKO_WA,
    "y": NKO_YA,
    "z": NKO_SA + NKO_DOT_ABOVE,  # loanword z
}

# Multi-character Latin sequences, longest-match-first.
DIGRAPHS: dict[str, str] = {
    "gb": NKO_GBA,
    "ny": NKO_NYA,
    "rr": NKO_RRA,
    "sh": NKO_SA + NKO_DOT_ABOVE,  # loanword ʃ
}

# ASCII/keyboard fallbacks normalized before mapping.
NORMALIZATIONS: dict[str, str] = {
    "è": "ɛ",  # è → ɛ
    "ò": "ɔ",  # ò → ɔ
    "é": "e",       # é → e
    "ó": "o",       # ó → o
}

DIGITS: dict[str, str] = {str(d): chr(0x07C0 + d) for d in range(10)}

PUNCTUATION: dict[str, str] = {
    ",": NKO_COMMA,
    "!": NKO_EXCLAMATION,
    "?": ARABIC_QUESTION,
    "'": NKO_DAGBASINNA,
    "’": NKO_DAGBASINNA,
}

LATIN_VOWELS = frozenset(VOWELS)
