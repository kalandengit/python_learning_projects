"""N'Ko Unicode block helpers (U+07C0–U+07FF, stable since Unicode 11.0)."""

NKO_BLOCK_START = 0x07C0
NKO_BLOCK_END = 0x07FF

# Combining tone/length marks used by the on-screen keyboard.
TONE_MARKS = [chr(cp) for cp in range(0x07EB, 0x07F4)]  # ߫ ߬ ߭ ߮ ߯ ߰ ߱ ߲ ߳

DIGITS = [chr(0x07C0 + d) for d in range(10)]

LETTERS = [chr(cp) for cp in range(0x07CA, 0x07EB)]  # ߊ … ߪ


def is_nko_char(char: str) -> bool:
    return NKO_BLOCK_START <= ord(char) <= NKO_BLOCK_END


def contains_nko(text: str) -> bool:
    return any(is_nko_char(char) for char in text)
