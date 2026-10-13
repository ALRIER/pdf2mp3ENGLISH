# PDF to Audiobook — Neural TTS (v1 prototype)

Modernization of the original `pdftomp3` Bash converter. The legacy implementation remains available, unmodified, in [pdftomp3](./pdftomp3) with its original copyright notice and licensing.

## Capabilities

- Upload PDF, DOCX or TXT using Streamlit.
- Skip PDF image blocks, automatically detected tables and optional top/bottom page margins.
- Review extracted text before reading it.
- Use the pretrained Kokoro-82M text-to-speech model (American English voices) on CPU.
- Listen in the browser and download a WAV audiobook.

## Run locally

Python 3.11 is recommended. `kokoro` can require additional operating-system dependencies on some systems.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Model weights are downloaded at runtime to the machine's model cache, **not committed to GitHub**. Ensure that you have reviewed the upstream model's license and that the host has adequate RAM. A WAV audiobook can be very large.

## Scope and known limitations

**This is a prototype, not a production deployment.** Tables and headers are skipped heuristically and may be missed or over-filtered. Multi-column reading order may be incorrect. Image-based scanned PDFs require OCR, which is not implemented. EPUB, MP3 export, streaming chapters, and native multilingual support are not yet implemented. The default app uses American-English Kokoro voices.

**Synchronized word highlighting is planned, not implemented.** It requires accurate word start/end timestamps derived by forced alignment or a TTS engine exposing word timing, followed by a synchronized browser player. Timing cannot be derived reliably from the text alone.

**GitHub Actions are not an always-on app host.** They can run tests and batch inference, but service deployments should use Streamlit hosting or local inference. Public Actions are visible; never submit private documents to public Actions jobs or commit them to this repository.

## Next milestones

1. Benchmark Kokoro vs Piper on CPU, measuring real-time factor, memory and quality.
2. Improve document layout analysis and add chapter handling and EPUB.
3. Add forced word alignment, synchronized text highlighting and auto-scroll.
4. Add chapter-wise downloadable MP3 or M4B generation.
5. Test Streamlit hosting performance and decide on a hybrid local/cloud architecture.
