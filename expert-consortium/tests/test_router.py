from pathlib import Path

import pytest

from app.ingestion import router


def test_supported_extensions_cover_requirements():
    for ext in (".pdf", ".docx", ".txt", ".md", ".png", ".jpg",
                ".mp3", ".wav", ".mp4", ".mkv"):
        assert ext in router.SUPPORTED_EXTS


def test_unsupported_extension_raises(tmp_path: Path):
    bad = tmp_path / "file.xyz"
    bad.write_text("data")
    with pytest.raises(ValueError, match="Unsupported file type"):
        router.extract(bad)


def test_text_extraction_and_metadata(tmp_path: Path):
    f = tmp_path / "law" / "notes.txt"
    f.parent.mkdir()
    f.write_text("The court ruled in favour of the plaintiff. " * 5, encoding="utf-8")
    doc = router.extract(f)
    assert doc.source_file == "notes.txt"
    assert doc.domain == "law"
    assert doc.language == "latin"
    assert "court" in doc.text


def test_domain_defaults_to_general(tmp_path: Path):
    f = tmp_path / "notes.md"
    f.write_text("# Notes\n\nSome plain content here for testing purposes only.")
    assert router.extract(f).domain == "general"


def test_explicit_domain_overrides_folder(tmp_path: Path):
    f = tmp_path / "cs" / "algo.txt"
    f.parent.mkdir()
    f.write_text("Binary search runs in logarithmic time on sorted arrays always.")
    assert router.extract(f, domain="islamic").domain == "islamic"


def test_empty_file_raises(tmp_path: Path):
    f = tmp_path / "empty.txt"
    f.write_text("   ")
    with pytest.raises(ValueError, match="No text"):
        router.extract(f)


def test_language_detection_arabic_and_nko():
    assert router.guess_language("قال رسول الله صلى الله عليه وسلم " * 5) == "ar"
    assert router.guess_language("ߒߞߏ ߦߋ ߛߓߍߛߎ߲ ߠߋ ߘߌ " * 10) == "nko"
    assert router.guess_language("Plain English text with many letters") == "latin"
