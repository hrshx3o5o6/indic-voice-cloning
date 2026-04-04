import os
import base64
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

from indic_voice.pipeline.tts_sarvam import generate_speech


@patch("indic_voice.pipeline.tts_sarvam.load_dotenv")
@patch("indic_voice.pipeline.tts_sarvam.SarvamAI")
def test_generate_speech_supports_sarvamai_v010_response_shape(
    mock_sarvam_cls, mock_dotenv, mock_sarvam_response, tmp_path
):
    """generate_speech() decodes base64 audio from newer Sarvam SDK response."""
    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = SimpleNamespace(
        audios=[base64.b64encode(mock_sarvam_response).decode("ascii")]
    )
    mock_sarvam_cls.return_value = mock_client

    output = str(tmp_path / "out.wav")

    with patch.dict(os.environ, {"SARVAM_AI_API": "test-key"}):
        generate_speech("नमस्ते", output)

    mock_client.text_to_speech.convert.assert_called_once_with(
        inputs=["नमस्ते"],
        target_language_code="hi-IN",
        speaker="aditya",
        model="bulbul:v3",
    )
    with open(output, "rb") as f:
        assert f.read() == mock_sarvam_response


@patch("indic_voice.pipeline.tts_sarvam.load_dotenv")
@patch("indic_voice.pipeline.tts_sarvam.SarvamAI")
def test_generate_speech_writes_audio_bytes(mock_sarvam_cls, mock_dotenv, mock_sarvam_response, tmp_path):
    """generate_speech() writes the API response bytes to the output file."""
    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = mock_sarvam_response
    mock_sarvam_cls.return_value = mock_client

    output = str(tmp_path / "out.wav")

    with patch.dict(os.environ, {"SARVAM_AI_API": "test-key"}):
        result = generate_speech("नमस्ते", output)

    assert result == output
    assert os.path.exists(output)
    with open(output, "rb") as f:
        assert f.read() == mock_sarvam_response


@patch("indic_voice.pipeline.tts_sarvam.load_dotenv")
def test_generate_speech_raises_without_api_key(mock_dotenv, tmp_path):
    """generate_speech() raises ValueError when SARVAM_AI_API is absent."""
    env = {k: v for k, v in os.environ.items() if k != "SARVAM_AI_API"}
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ValueError, match="SARVAM_AI_API"):
            generate_speech("test", str(tmp_path / "out.wav"))


@patch("indic_voice.pipeline.tts_sarvam.load_dotenv")
@patch("indic_voice.pipeline.tts_sarvam.SarvamAI")
def test_generate_speech_passes_lang_code_and_speaker(mock_sarvam_cls, mock_dotenv, mock_sarvam_response, tmp_path):
    """generate_speech() passes lang_code and speaker through to the API."""
    mock_client = MagicMock()
    mock_client.text_to_speech.convert.return_value = mock_sarvam_response
    mock_sarvam_cls.return_value = mock_client

    output = str(tmp_path / "out.wav")

    with patch.dict(os.environ, {"SARVAM_AI_API": "test-key"}):
        generate_speech("hello", output, lang_code="ta-IN", speaker="arvind")

    mock_client.text_to_speech.convert.assert_called_once_with(
        inputs=["hello"],
        target_language_code="ta-IN",
        speaker="arvind",
        model="bulbul:v3",
    )
