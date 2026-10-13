# Open Audiobook — CPU-first neural text-to-speech

Clean replacement for the original PDF-to-MP3 Bash script (recoverable from Git history). This is an open-source prototype, not a finished hosted service.

## Architecture

- **GitHub:** application code, configuration, tests and CI. GitHub is not a permanent inference server.
- **Hugging Face:** official pretrained weights, downloaded to local/runner cache (not stored in Git).
- **Streamlit:** web interface; in the present prototype it also calls local inference. The inference component is isolated in `synthesis.py` so it can later move to a dedicated worker.
- **Model:** [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), Apache 2.0, CPU-supported. Original model and authorship remain attributed.

## Start (Ubuntu/Linux, Python 3.11)

```bash
sudo apt-get update && sudo apt-get install -y espeak-ng libsndfile1
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py
streamlit run app.py
```

On Windows, install eSpeak NG separately, then run equivalent venv commands with Python 3.11. The first model download needs an internet connection and disk space; subsequent runs reuse Hugging Face cache. Model weights are **not** committed to this repository.

## Current functionality

PDF/DOCX/TXT import; heuristic PDF table/header/footer skipping; manual text correction; neural English narration; WAV playback/download. The initial implementation loads complete audio in memory; use modest-sized test documents first.

## Planned, not yet delivered

- True document layout reasoning and reliable multi-column parsing
- OCR for scanned PDFs
- EPUB, chapter-based MP3/M4B export, asynchronous jobs, streaming
- Forced alignment, word-by-word highlighting and auto-scroll
- Fine-tuning/checkpoint workflows and performance benchmarks
- External inference worker, persistent hosting and user isolation

## Security and limitations

Do not upload confidential documents to a publicly deployed demo unless its hosting and data-retention policies meet your requirements. Public GitHub Actions logs/artifacts are unsuitable for private content. Do not commit PDF inputs, outputs, model files or credentials. Filtering and reading order are heuristic and should be reviewed before synthesizing. CPU inference speed depends on the machine.
