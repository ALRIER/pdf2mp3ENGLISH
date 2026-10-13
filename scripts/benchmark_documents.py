"""Two-document extraction and short narration integration benchmark.

Source PDFs are fetched at run time and NEVER committed or uploaded as artifacts.
"""
import json
import re
import time
import urllib.request
from pathlib import Path

import pymupdf
from pipeline import extract_document, split_text
from synthesis import synthesize_wav

CASES = [
    {
        "id": "journal",
        "url": "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0309318&type=printable",
        "max_pages": 30,
    },
    {
        "id": "philosophy",
        "url": "https://cdn.mises.org/For%20a%20New%20Liberty%20The%20Libertarian%20Manifesto_3.pdf",
        "max_pages": 18,
    },
]
OUT = Path("artifacts/document-validation")
OUT.mkdir(parents=True, exist_ok=True)
results = []
for case in CASES:
    req = urllib.request.Request(case["url"], headers={"User-Agent": "AudiobookResearchBenchmark/1.0"})
    with urllib.request.urlopen(req, timeout=90) as response:
        data = response.read(25_000_001)
    if len(data) > 25_000_000:
        raise ValueError("PDF download exceeds test limit")
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        total_pages = len(pdf)
        page_count = min(case["max_pages"], total_pages)
        pdf.select(list(range(page_count)))
        sample_pdf = pdf.tobytes(garbage=3, deflate=True)
    started = time.perf_counter()
    clean = extract_document(sample_pdf, "document.pdf", skip_tables=True, skip_margins=True)
    extraction_seconds = time.perf_counter() - started
    snippet = " ".join(split_text(clean, 650)[:2])
    started = time.perf_counter()
    audio = synthesize_wav(snippet)
    synthesis_seconds = time.perf_counter() - started
    import io
    import soundfile as sf
    info = sf.info(io.BytesIO(audio))
    output = {
        "case": case["id"],
        "source_url": case["url"],
        "total_pdf_pages": total_pages,
        "tested_pages": page_count,
        "extracted_chars": len(clean),
        "audio_input_chars": len(snippet),
        "audio_duration_seconds": round(info.duration, 2),
        "extraction_seconds": round(extraction_seconds, 2),
        "synthesis_seconds": round(synthesis_seconds, 2),
        "real_time_factor": round(synthesis_seconds / info.duration, 3),
        "suspected_page_markers": len(re.findall(r"(?mi)^\\s*page\\s+\\d+\\s*$", clean)),
        "table_heading_mentions": len(re.findall(r"(?i)\\btable\\s+\\d+", clean)),
        "figure_heading_mentions": len(re.findall(r"(?i)\\bfig(?:ure|\\.)?\\s+\\d+", clean)),
    }
    if len(clean) < 600 or info.duration < 3:
        raise ValueError(f"Unusable extraction or speech for {case['id']}")
    results.append(output)
    (OUT / (case["id"] + ".json")).write_text(json.dumps(output, indent=2) + "\n")
    (OUT / (case["id"] + ".preview.txt")).write_text(clean[:1600], encoding="utf-8")
    (OUT / (case["id"] + ".wav")).write_bytes(audio)
    print(json.dumps(output, indent=2), flush=True)
(OUT / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
