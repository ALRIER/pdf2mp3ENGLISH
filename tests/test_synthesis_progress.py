from unittest.mock import patch
import numpy as np
from synthesis import synthesize_wav


def test_synthesis_reports_completed_chunks():
    events = []

    def fake_pipeline(chunk, **kwargs):
        yield None, None, np.ones(2400, dtype=np.float32)

    with patch("synthesis.get_pipeline", return_value=fake_pipeline):
        wav = synthesize_wav("A sentence. " * 150, on_progress=lambda i, n: events.append((i, n)))
    assert wav.startswith(b"RIFF")
    assert len(events) > 1
    assert events == [(i, len(events)) for i in range(1, len(events) + 1)]
