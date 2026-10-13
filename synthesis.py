"""CPU-compatible Kokoro synthesis; weights are downloaded at runtime."""
from __future__ import annotations

from io import BytesIO

import numpy as np
import soundfile as sf

from pipeline import split_text

SAMPLE_RATE = 24_000


def synthesize_wav(text: str, voice: str = "af_heart", speed: float = 1.0) -> bytes:
    # Import lazily so text extraction and the interface work without model weights.
    from kokoro import KPipeline

    pipeline = KPipeline(lang_code="a")
    pieces = []
    for chunk in split_text(text):
        for _, _, audio in pipeline(chunk, voice=voice, speed=speed, split_pattern=r"\n+"):
            if audio is not None:
                pieces.append(np.asarray(audio, dtype=np.float32))
                pieces.append(np.zeros(int(0.22 * SAMPLE_RATE), dtype=np.float32))
    if not pieces:
        raise ValueError("The model produced no audio.")
    buffer = BytesIO()
    sf.write(buffer, np.concatenate(pieces), SAMPLE_RATE, format="WAV", subtype="PCM_16")
    return buffer.getvalue()
