"""Document extraction and cleanup. No neural model required."""
from __future__ import annotations

import re
from io import BytesIO

import pymupdf
from docx import Document

MAX_CHARS = 200_000


def _normalize(text: str) -> str:
    text = re.sub(r"(?m)^\s*(?:Page\s+)?\d{1,4}\s*$", "", text)
    text = re.sub(r"(?m)^\s*(?:Figure|Fig\.)\s+\d+[^\n]*$", "", text, flags=re.I)
    text = re.sub(r"(?m)^\s*Table\s+\d+[^\n]*$", "", text, flags=re.I)
    text = re.sub(r"(?m)^[ \t]+", "", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_document(data: bytes, name: str, skip_tables: bool = True,
                     skip_margins: bool = True) -> str:
    suffix = name.lower().rsplit(".", 1)[-1]
    sections: list[str] = []
    if suffix == "pdf":
        from layout import extract_pdf_clean
        extracted, _audit = extract_pdf_clean(
            data, skip_tables=skip_tables, skip_margins=skip_margins)
        sections = [extracted]
    elif suffix == "docx":
        doc = Document(BytesIO(data))
        sections = [p.text for p in doc.paragraphs if p.text.strip()]
        if not skip_tables:
            sections += [cell.text for table in doc.tables
                         for row in table.rows for cell in row.cells]
    elif suffix == "txt":
        sections = [data.decode("utf-8-sig", errors="replace")]
    else:
        raise ValueError("Supported files: PDF, DOCX and TXT")
    result = _normalize("\n\n".join(sections))
    if not result:
        raise ValueError("No readable text found; scanned PDFs require OCR (not implemented).")
    if len(result) > MAX_CHARS:
        raise ValueError(f"Document exceeds initial {MAX_CHARS:,}-character safety limit.")
    return result


def split_text(text: str, max_chars: int = 700) -> list[str]:
    """Split without discarding text, favoring sentence/word boundaries."""
    if max_chars < 100:
        raise ValueError("max_chars must be >= 100")
    chunks = []
    remaining = text.strip()
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        cut = max(remaining.rfind(s, 0, max_chars) for s in (". ", "? ", "! ", "\n", " "))
        if cut < max_chars // 3:
            cut = max_chars
        else:
            cut += 1
        chunks.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    return [c for c in chunks if c]
