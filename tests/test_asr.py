import os
from unittest.mock import MagicMock, patch

import pytest

from indic_voice.pipeline.asr import transcribe_audio


def _make_segment(text):
    seg = MagicMock()
    seg.text = text
    return seg


@patch("indic_voice.pipeline.asr.WhisperModel")
def test_transcribe_returns_joined_text(mock_model_cls, sample_wav):
    """transcribe_audio() joins segment texts with spaces."""
    mock_instance = MagicMock()
    mock_instance.transcribe.return_value = (
        [_make_segment("Hello"), _make_segment("world")],
        MagicMock(language="en"),
    )
    mock_model_cls.return_value = mock_instance

    result = transcribe_audio(sample_wav)

    assert result == "Hello world"
    mock_instance.transcribe.assert_called_once_with(sample_wav, beam_size=5)


def test_transcribe_raises_for_missing_file():
    """transcribe_audio() raises FileNotFoundError for non-existent file."""
    with pytest.raises(FileNotFoundError):
        transcribe_audio("/nonexistent/audio.wav")


@patch("indic_voice.pipeline.asr.WhisperModel")
def test_transcribe_uses_local_model_when_available(mock_model_cls, sample_wav, tmp_path, monkeypatch):
    """transcribe_audio() uses local model path when ../faster_whisper_medium exists."""
    # The ASR code checks os.path.exists("../faster_whisper_medium") relative to cwd.
    # Put cwd inside a subdirectory so that ../faster_whisper_medium resolves.
    subdir = tmp_path / "project"
    subdir.mkdir()
    local_model = tmp_path / "faster_whisper_medium"
    local_model.mkdir()
    monkeypatch.chdir(subdir)

    mock_instance = MagicMock()
    mock_instance.transcribe.return_value = ([_make_segment("test")], MagicMock(language="en"))
    mock_model_cls.return_value = mock_instance

    transcribe_audio(sample_wav)

    call_args = mock_model_cls.call_args
    assert "faster_whisper_medium" in call_args[0][0]
