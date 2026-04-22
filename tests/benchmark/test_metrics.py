"""Unit tests for benchmark.metrics modules (similarity, wer, rtf).

Heavy models (WavLM, faster-whisper) are mocked so tests run without
downloading any model weights.
"""
from __future__ import annotations

import io
import os
import struct
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import soundfile as sf

from benchmark.metrics.rtf import compute_rtf, get_audio_duration
from benchmark.metrics.wer import _word_error_rate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_wav(path: str, duration_s: float = 1.0, sr: int = 16000) -> None:
    """Write a minimal valid mono WAV file to path."""
    n_samples = int(sr * duration_s)
    audio = np.zeros(n_samples, dtype=np.float32)
    sf.write(path, audio, sr)


# ---------------------------------------------------------------------------
# RTF tests
# ---------------------------------------------------------------------------

def test_rtf_basic() -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        _write_wav(tmp, duration_s=2.0)
        rtf = compute_rtf(tmp, elapsed_seconds=1.0)
        assert abs(rtf - 0.5) < 0.05, f"Expected ~0.5, got {rtf}"
    finally:
        os.unlink(tmp)


def test_rtf_zero_duration_raises() -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        import pytest
        with patch("benchmark.metrics.rtf.get_audio_duration", return_value=0.0):
            with pytest.raises(ValueError, match="zero duration"):
                compute_rtf(tmp, elapsed_seconds=1.0)
    finally:
        os.unlink(tmp)


def test_get_audio_duration_missing_raises() -> None:
    import pytest
    with pytest.raises(FileNotFoundError):
        get_audio_duration("/nonexistent/path/audio.wav")


def test_get_audio_duration_correct() -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    try:
        _write_wav(tmp, duration_s=3.0)
        dur = get_audio_duration(tmp)
        assert abs(dur - 3.0) < 0.1, f"Expected ~3.0s, got {dur}"
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# WER (_word_error_rate) tests — no model needed
# ---------------------------------------------------------------------------

def test_wer_exact_match_is_zero() -> None:
    assert _word_error_rate("hello world", "hello world") == 0.0


def test_wer_completely_different() -> None:
    wer = _word_error_rate("hello world", "foo bar baz")
    # 2 substitutions / 2 ref words = 1.0  (but baz is an insertion -> WER > 1)
    assert wer >= 1.0


def test_wer_empty_ref() -> None:
    assert _word_error_rate("", "") == 0.0


def test_wer_partial_match() -> None:
    # "hello world" vs "hello earth" -> 1 substitution / 2 words = 0.5
    wer = _word_error_rate("hello world", "hello earth")
    assert abs(wer - 0.5) < 0.01


# ---------------------------------------------------------------------------
# Similarity tests — mock WavLM to avoid model download
# ---------------------------------------------------------------------------

def test_compute_speaker_similarity_returns_float_in_range() -> None:
    """compute_speaker_similarity returns a float in [-1, 1] given two WAV files."""
    import torch
    from benchmark.metrics import similarity as sim_module

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f1, \
         tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f2:
        p1, p2 = f1.name, f2.name
    try:
        _write_wav(p1, duration_s=1.0)
        _write_wav(p2, duration_s=1.0)

        # Mock the lazy-loaded model cache
        mock_extractor = MagicMock()
        mock_model = MagicMock()
        # Return a fixed embedding tensor
        fixed_emb = torch.ones(1, 768)
        mock_outputs = MagicMock()
        mock_outputs.last_hidden_state = fixed_emb.unsqueeze(1)  # (1, 1, 768)
        mock_model.return_value = mock_outputs
        mock_extractor.return_value = {"input_values": torch.zeros(1, 16000)}

        with patch.object(sim_module, "_load_model", return_value=(mock_extractor, mock_model)):
            with patch.object(sim_module, "_load_audio", return_value=torch.zeros(16000)):
                with patch.object(sim_module, "_embed", return_value=fixed_emb):
                    result = sim_module.compute_speaker_similarity(p1, p2)

        assert isinstance(result, float), f"Expected float, got {type(result)}"
        assert -1.0 <= result <= 1.0, f"Similarity out of range: {result}"
    finally:
        os.unlink(p1)
        os.unlink(p2)
