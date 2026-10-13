from pipeline import _normalize, split_text


def test_noise_cleanup():
    text = "Page 12\n\nHello world.\nFigure 1. A diagram\nThis is important."
    clean = _normalize(text)
    assert "Page 12" not in clean
    assert "Figure 1" not in clean
    assert "Hello world." in clean


def test_chunks_keep_words():
    text = "A short sentence. " * 120
    chunks = split_text(text, max_chars=200)
    assert all(0 < len(s) <= 200 for s in chunks)
    assert " ".join(chunks).replace("  ", " ") == text.strip()
