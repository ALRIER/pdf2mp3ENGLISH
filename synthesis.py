"""CPU-compatible Kokoro synthesis with process-level model reuse."""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Callable

import numpy as np
import soundfile as sf

from pipeline import split_text

SAMPLE_RATE = 24_000
MODEL_ID = "hexgrad/Kokoro-82M"


@lru_cache(maxsize=1)
def get_pipeline():
    """Load once per Python process; Hugging Face caches downloaded weights on disk."""
    from kokoro import KPipeline
    return KPipeline(lang_code="a", repo_id=MODEL_ID, device="cpu")


def synthesize_wav(text: str, voice: str = "af_heart", speed: float = 1.0,
                   on_progress: Callable[[int, int], None] | None = None) -> bytes:
    chunks = split_text(text)
    if not chunks:
        raise ValueError("There is no text to narrate.")
    pipeline = get_pipeline()
    pieces = []
    for index, chunk in enumerate(chunks, start=1):
        for _, _, audio in pipeline(chunk, voice=voice, speed=speed, split_pattern=r"\n+"):
            if audio is not None:
                pieces.append(np.asarray(audio, dtype=np.float32))
                pieces.append(np.zeros(int(0.22 * SAMPLE_RATE), dtype=np.float32))
        if on_progress is not None:
            on_progress(index, len(chunks))
    if not pieces:
        raise ValueError("The model produced no audio.")
    buffer = BytesIO()
    sf.write(buffer, np.concatenate(pieces), SAMPLE_RATE, format="WAV", subtype="PCM_16")
    return buffer.getvalue()
