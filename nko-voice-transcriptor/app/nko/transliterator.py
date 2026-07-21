"""Deterministic Bambara Latin → N'Ko transliteration engine.

Algorithm, per word:

1. Unicode-normalize (NFC), lowercase, apply keyboard fallbacks
   (see :mod:`app.nko.tables`).
2. A word that is exactly ``n`` becomes the syllabic N letter ߒ.
3. Scan left to right with longest-match tokenization (digraphs first).
4. ``n`` or ``ŋ`` in syllable coda (immediately after a vowel and followed
   by a consonant or word end) becomes the combining nasalization mark ߲
   on that vowel, matching Bambara phonology.
5. Everything unmapped (Latin text left as-is by design, e.g. foreign
   words) passes through unchanged.

The output is logically ordered N'Ko; right-to-left rendering is the job
of the display layer (Unicode bidi).
"""

from __future__ import annotations

import unicodedata

from app.nko import tables


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text).lower()
    for src, dst in tables.NORMALIZATIONS.items():
        text = text.replace(src, dst)
    return text


def _is_vowel(ch: str) -> bool:
    return ch in tables.LATIN_VOWELS


def _coda_nasal(word: str, i: int) -> bool:
    """True if word[i] is ``n``/``ŋ`` acting as a syllable-final nasal."""
    if word[i] not in ("n", "ŋ"):
        return False
    if i == 0 or not _is_vowel(word[i - 1]):
        return False  # no preceding vowel to nasalize
    nxt = word[i + 1] if i + 1 < len(word) else None
    if nxt is None:
        return True  # word-final nasal
    if _is_vowel(nxt):
        return False  # onset of next syllable: keep as letter
    if word[i] == "n" and nxt == "y":
        return False  # part of the "ny" digraph
    return True


def _transliterate_word(word: str) -> str:
    if word == "n":
        return tables.NKO_N_SYLLABIC

    out: list[str] = []
    i = 0
    while i < len(word):
        # Longest match first: digraphs
        matched_digraph = False
        for seq, nko in tables.DIGRAPHS.items():
            if word.startswith(seq, i):
                # "ny"/"rr"/... but never steal a coda nasal from its vowel
                if not _coda_nasal(word, i):
                    out.append(nko)
                    i += len(seq)
                    matched_digraph = True
                break
        if matched_digraph:
            continue

        ch = word[i]
        if _coda_nasal(word, i):
            out.append(tables.NKO_NASAL)
        elif ch in tables.VOWELS:
            out.append(tables.VOWELS[ch])
        elif ch in tables.CONSONANTS:
            out.append(tables.CONSONANTS[ch])
        elif ch in tables.DIGITS:
            out.append(tables.DIGITS[ch])
        elif ch in tables.PUNCTUATION:
            out.append(tables.PUNCTUATION[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def transliterate(text: str) -> str:
    """Convert Bambara text in Latin orthography to N'Ko script.

    Whitespace and line structure are preserved. Unknown characters pass
    through unchanged, so mixed-language input degrades gracefully.
    """
    if not text:
        return ""
    normalized = _normalize(text)
    lines = []
    for line in normalized.split("\n"):
        lines.append(" ".join(_transliterate_word(w) for w in line.split(" ")))
    return "\n".join(lines)
