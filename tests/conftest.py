import wave
import struct
import pytest
import numpy as np
import torch


@pytest.fixture
def sample_wav(tmp_path):
    """Generate a minimal valid 1-second silent 16kHz mono WAV file."""
    wav_path = tmp_path / "sample.wav"
    sample_rate = 16000
    n_frames = sample_rate  # 1 second

    with wave.open(str(wav_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_frames, *([0] * n_frames)))

    return str(wav_path)


@pytest.fixture
def mock_sarvam_response():
    """Return minimal valid WAV bytes to simulate Sarvam API response."""
    import io

    buf = io.BytesIO()
    sample_rate = 22050
    n_frames = sample_rate

    with wave.open(buf, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_frames, *([0] * n_frames)))

    return buf.getvalue()


@pytest.fixture
def mock_indicf5_audio_output():
    """Synthetic audio output from IndicF5 model (int16 numpy array, 1 second at 16kHz)."""
    return np.array([0, 100, 200, 300, -100, -200] * 2667, dtype=np.int16)[:16000]


@pytest.fixture
def mock_indicf5_ref_audio():
    """Synthetic reference audio for IndicF5 input (float32 tensor, 16kHz, 1 second)."""
    return torch.randn(1, 16000).float()  # [channels=1, samples=16000]
