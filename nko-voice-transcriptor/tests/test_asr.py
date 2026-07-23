"""Tests for the ASR layer: validation, sniffing, mock engine, factory."""

import struct

import pytest

from app.asr.base import (
    AudioValidationError,
    get_engine,
    sniff_format,
    validate_audio,
    wav_duration_seconds,
)
from app.asr.mock import MockASREngine
from app.config import Settings


def make_settings(**overrides) -> Settings:
    base = dict(secret_key="x" * 32, asr_engine="mock")
    base.update(overrides)
    return Settings(_env_file=None, **base)


def make_wav(seconds: float = 1.0, sample_rate: int = 16_000) -> bytes:
    """Minimal valid PCM16 mono WAV."""
    n_samples = int(seconds * sample_rate)
    data = b"\x00\x00" * n_samples
    byte_rate = sample_rate * 2
    header = (
        b"RIFF"
        + struct.pack("<I", 36 + len(data))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, byte_rate, 2, 16)
        + b"data"
        + struct.pack("<I", len(data))
    )
    return header + data


class TestSniffing:
    def test_wav(self):
        assert sniff_format(make_wav()) == "wav"

    def test_ogg(self):
        assert sniff_format(b"OggS" + b"\x00" * 64) == "ogg"

    def test_webm(self):
        assert sniff_format(b"\x1a\x45\xdf\xa3" + b"\x00" * 64) == "webm"

    def test_mp3_id3(self):
        assert sniff_format(b"ID3\x04" + b"\x00" * 64) == "mp3"

    def test_garbage(self):
        assert sniff_format(b"not audio at all") is None


class TestValidation:
    def test_valid_wav_passes(self):
        settings = make_settings()
        assert validate_audio(make_wav(), "audio/wav", settings) == "wav"

    def test_empty_rejected(self):
        with pytest.raises(AudioValidationError, match="Empty"):
            validate_audio(b"", "audio/wav", make_settings())

    def test_oversize_rejected(self):
        settings = make_settings(max_upload_bytes=100)
        with pytest.raises(AudioValidationError, match="limit"):
            validate_audio(make_wav(), "audio/wav", settings)

    def test_bad_content_type_rejected(self):
        with pytest.raises(AudioValidationError, match="content type"):
            validate_audio(make_wav(), "application/x-msdownload", make_settings())

    def test_spoofed_mime_rejected_by_magic_bytes(self):
        # Declared audio/wav but the bytes are not audio → rejected
        with pytest.raises(AudioValidationError, match="not look like"):
            validate_audio(b"#!/bin/sh\nrm -rf /", "audio/wav", make_settings())

    def test_content_type_with_codec_params(self):
        # Browsers send e.g. "audio/webm;codecs=opus"
        blob = b"\x1a\x45\xdf\xa3" + b"\x00" * 64
        assert validate_audio(blob, "audio/webm;codecs=opus", make_settings()) == "webm"


class TestWavDuration:
    def test_duration_math(self):
        dur = wav_duration_seconds(make_wav(seconds=2.0))
        assert dur is not None and abs(dur - 2.0) < 0.01

    def test_non_wav_returns_none(self):
        assert wav_duration_seconds(b"OggS" + b"\x00" * 64) is None


class TestMockEngine:
    def test_deterministic(self):
        engine = MockASREngine()
        wav = make_wav()
        assert engine.transcribe(wav, "wav") == engine.transcribe(wav, "wav")

    def test_returns_bambara_latin(self):
        result = MockASREngine().transcribe(make_wav(), "wav")
        assert result.text_latin
        assert result.engine == "mock"
        assert result.language == "bam"


class TestFactory:
    def test_mock_selected(self):
        assert get_engine(make_settings()).name == "mock"

    def test_mms_selected_lazily(self):
        # Constructing the MMS engine must not import torch
        engine = get_engine(make_settings(asr_engine="mms"))
        assert engine.name == "mms"
