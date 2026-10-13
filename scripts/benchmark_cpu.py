"""Reproducible CPU inference smoke test with timing and memory metrics."""
import json
import os
import platform
import resource
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from kokoro import KPipeline

OUT = Path("artifacts/cpu-smoke")
OUT.mkdir(parents=True, exist_ok=True)
TEXT = (
    "This is a reproducible CPU audiobook test. "
    "A scientific article may contain figures, tables, page numbers, and references. "
    "The narration system should prioritize coherent paragraphs and natural speech."
)
VOICE = os.getenv("TTS_VOICE", "af_heart")

start = time.perf_counter()
model = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device="cpu")
load_seconds = time.perf_counter() - start
start = time.perf_counter()
audio_parts = [np.asarray(audio, dtype=np.float32) for _, _, audio
               in model(TEXT, voice=VOICE, speed=1.0) if audio is not None]
infer_seconds = time.perf_counter() - start
if not audio_parts:
    raise RuntimeError("Kokoro returned no samples")
samples = np.concatenate(audio_parts)
if not np.isfinite(samples).all():
    raise RuntimeError("Kokoro returned non-finite audio samples")
sample_rate = 24000
audio_seconds = len(samples) / sample_rate
if audio_seconds <= 1 or not np.max(np.abs(samples)) > 0.001:
    raise RuntimeError("Generated audio is empty or abnormally quiet")
sf.write(OUT / "sample.wav", samples, sample_rate, subtype="PCM_16")
metrics = {
    "model": "hexgrad/Kokoro-82M", "voice": VOICE,
    "platform": platform.platform(), "python": platform.python_version(),
    "cpu_count": os.cpu_count(), "sample_rate": sample_rate,
    "text_chars": len(TEXT), "model_load_seconds": round(load_seconds, 3),
    "inference_seconds": round(infer_seconds, 3),
    "audio_seconds": round(audio_seconds, 3),
    "real_time_factor": round(infer_seconds / audio_seconds, 4),
    "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
}
(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
