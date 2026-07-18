from app.config import settings
from app.ingestion.chunker import chunk_text


def test_short_text_single_chunk():
    assert chunk_text("Hello world.") == ["Hello world."]


def test_empty_text():
    assert chunk_text("   \n\n  ") == []


def test_respects_size_limit():
    text = "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(30))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    # +1 char slack for joins
    assert all(len(c) <= settings.chunk_chars + 1 for c in chunks)


def test_overlap_between_chunks():
    text = "\n\n".join("Sentence %d. " % i + "filler " * 50 for i in range(20))
    chunks = chunk_text(text)
    assert len(chunks) >= 2
    # The tail of chunk N should reappear at the head of chunk N+1.
    tail = chunks[0][-50:]
    assert tail in chunks[1]


def test_heading_sections_kept_together_when_small():
    text = "# Title A\n\nShort body.\n\n# Title B\n\nAnother short body."
    chunks = chunk_text(text)
    assert len(chunks) == 1  # both fit in one chunk


def test_very_long_unbroken_block_is_split():
    text = "One sentence. " * 1000  # single paragraph, no headings
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= settings.chunk_chars + 1 for c in chunks)


def test_arabic_text_survives_chunking():
    text = ("بسم الله الرحمن الرحيم۔ " * 200).strip()
    chunks = chunk_text(text)
    assert chunks
    assert all("الله" in c for c in chunks)
