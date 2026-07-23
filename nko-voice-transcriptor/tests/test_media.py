import struct

from app.media import normalize_media, segment_wav
from tests.test_asr import make_wav


def voiced_wav(seconds=3):
    wav = make_wav(seconds=seconds)
    samples = (len(wav) - 44) // 2
    return wav[:44] + struct.pack("<h", 1000) * samples


def test_normalized_wav_passes_without_ffmpeg():
    wav = voiced_wav(1)
    assert normalize_media(wav, "wav") == wav


def test_long_wav_is_segmented():
    chunks = segment_wav(voiced_wav(3), max_seconds=1, silence_db=-40)
    assert len(chunks) == 3
    assert all(chunk.startswith(b"RIFF") for chunk in chunks)
