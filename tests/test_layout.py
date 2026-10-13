"""Synthetic layout checks for Stage 3B; no external PDFs needed."""
import pymupdf
from layout import extract_pdf_clean, _column_order


def test_column_order():
    blocks = [
        (320, 200, 540, 230, "right second", 0, 0),
        (40, 90, 260, 120, "left first", 0, 0),
        (320, 90, 540, 120, "right first", 0, 0),
        (40, 200, 260, 230, "left second", 0, 0),
    ]
    assert [b[4] for b in _column_order(blocks, 580)] == [
        "left first", "left second", "right first", "right second"]


def test_repeated_headers_and_numbers():
    doc = pymupdf.open()
    for i in range(4):
        p = doc.new_page(width=595, height=842)
        p.insert_text((60, 35), "Journal of Sample Studies")
        p.insert_text((60, 160), f"Important scientific paragraph number {i}.")
        p.insert_text((290, 810), str(i + 1))
    content = doc.tobytes()
    text, audit = extract_pdf_clean(content)
    assert "Important scientific paragraph number 0" in text
    assert "Journal of Sample Studies" not in text
    assert audit["removed_by_reason"]["repeated_margin"] >= 4
    assert audit["removed_by_reason"]["page_number"] == 4


def test_caption_filter_preserves_body_reference():
    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((50, 150), "Figure 2. Example chart")
    p.insert_text((50, 220), "The results in Figure 2 support the hypothesis.")
    text, audit = extract_pdf_clean(doc.tobytes())
    assert "Figure 2. Example chart" not in text
    assert "The results in Figure 2 support the hypothesis." in text
    assert audit["removed_by_reason"]["caption"] == 1
