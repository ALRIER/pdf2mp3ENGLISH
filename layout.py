"""Auditable, CPU-only PDF narration cleanup.

Heuristics are conservative; audit removed blocks before publishing narration.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
import re
import pymupdf


@dataclass
class Removed:
    page: int
    reason: str
    text: str


def _key(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _is_caption(value: str) -> bool:
    return bool(re.match(r"^\s*(?:fig(?:ure)?\.?|table)\s*\d+\s*[:.\-– ]", value, re.I))


def _column_order(blocks: list[tuple], width: float) -> list[tuple]:
    """Return a narration-friendly reading order for common two-column pages.

    Blocks are classified by geometry rather than exact midpoint boundaries. This
    avoids interleaving left/right columns when blocks slightly cross the page
    midpoint because of indentation, equations, or extraction noise.
    """
    if len(blocks) < 4:
        return sorted(blocks, key=lambda b: (b[1], b[0]))

    mid = width / 2
    max_column_width = width * 0.58

    def block_width(b: tuple) -> float:
        return max(0.0, b[2] - b[0])

    narrow = [b for b in blocks if block_width(b) <= max_column_width]
    left = [b for b in narrow if (b[0] + b[2]) / 2 < mid]
    right = [b for b in narrow if (b[0] + b[2]) / 2 >= mid]

    # Require clear evidence of two columns; otherwise preserve ordinary page flow.
    if len(left) < 2 or len(right) < 2 or len(narrow) < len(blocks) * 0.55:
        return sorted(blocks, key=lambda b: (b[1], b[0]))

    first_column_y = min(b[1] for b in narrow)
    last_column_y = max(b[3] for b in narrow)
    wide = [b for b in blocks if b not in narrow]

    # Full-width title/abstract blocks above the columns are safe to keep first.
    top = [b for b in wide if b[3] <= first_column_y + 6]
    bottom = [b for b in wide if b[1] >= last_column_y - 6]
    middle = [b for b in wide if b not in top and b not in bottom]

    # A full-width block inside the column region is ambiguous (e.g. a large
    # equation/table). Fall back rather than inventing a reading order.
    if middle:
        return sorted(blocks, key=lambda b: (b[1], b[0]))

    return (
        sorted(top, key=lambda b: (b[1], b[0]))
        + sorted(left, key=lambda b: (b[1], b[0]))
        + sorted(right, key=lambda b: (b[1], b[0]))
        + sorted(bottom, key=lambda b: (b[1], b[0]))
    )


def extract_pdf_clean(data: bytes, skip_tables: bool = True,
                      skip_margins: bool = True,
                      skip_captions: bool = True) -> tuple[str, dict]:
    removals: list[Removed] = []
    retained: list[str] = []
    counters = Counter()
    with pymupdf.open(stream=data, filetype="pdf") as doc:
        pages = []
        margins = Counter()
        for page_num, page in enumerate(doc, 1):
            entries = []
            for b in page.get_text("blocks", sort=False):
                if len(b) < 7 or b[6] != 0 or not b[4].strip():
                    continue
                rect = pymupdf.Rect(b[:4])
                top_bottom = rect.y1 < .10 * page.rect.height or rect.y0 > .90 * page.rect.height
                if top_bottom:
                    margins[_key(b[4])] += 1
                entries.append((b, top_bottom))
            pages.append((page, page_num, entries))
        repeated = {k for k, v in margins.items() if v >= 3 and k and len(k) < 140}
        for page, page_num, entries in pages:
            table_rects = []
            if skip_tables:
                try:
                    table_rects = [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
                except Exception:
                    counters["table_detection_errors"] += 1
            chosen = []
            for b, in_margin in entries:
                rect = pymupdf.Rect(b[:4])
                raw = b[4].strip()
                reason = None
                if skip_margins and in_margin and _key(raw) in repeated:
                    reason = "repeated_margin"
                elif skip_margins and in_margin and re.fullmatch(r"(?:page\s*)?\d{1,4}", raw, re.I):
                    reason = "page_number"
                elif skip_tables and rect.get_area() and any(
                    (rect & t).get_area() / rect.get_area() > .20 for t in table_rects):
                    reason = "table"
                elif skip_captions and _is_caption(raw):
                    reason = "caption"
                if reason:
                    removals.append(Removed(page_num, reason, raw[:250]))
                    counters[reason] += 1
                else:
                    chosen.append(b)
            for b in _column_order(chosen, page.rect.width):
                retained.append(b[4].strip())
    text = "\n\n".join(retained)
    audit = {"pages": len(pages), "retained_blocks": len(retained),
             "removed_blocks": len(removals),
             "removed_by_reason": dict(counters),
             "removed_examples": [asdict(x) for x in removals[:150]]}
    return text, audit
