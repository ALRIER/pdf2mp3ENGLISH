"""CPU word timestamps derived from audio transcription (not forced text alignment).

The player displays recognized speech, not necessarily all source text.
"""
from __future__ import annotations
import tempfile
from pathlib import Path


def recognize_word_timestamps(wav: bytes, model_size: str = "tiny.en") -> list[dict]:
    from faster_whisper import WhisperModel
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "speech.wav"
        path.write_bytes(wav)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, _ = model.transcribe(
            str(path), language="en", word_timestamps=True,
            beam_size=3, vad_filter=False)
        words = []
        for segment in segments:
            for word in segment.words or []:
                if word.start is None or word.end is None:
                    continue
                words.append({"text": word.word.strip(), "start": round(word.start, 3),
                              "end": round(word.end, 3)})
        if not words:
            raise ValueError("Speech recognizer returned no word timestamps")
        return words
