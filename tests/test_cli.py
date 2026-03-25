import os
import shutil
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from indic_voice.cli import app

runner = CliRunner()


def _mock_pipeline(mock_generate, mock_morph, mock_transcribe=None, mock_translate=None):
    """Helper to patch all pipeline callables."""
    mock_generate.return_value = "tmp_sarvam_tts.wav"
    mock_morph.return_value = "out.wav"
    if mock_transcribe is not None:
        mock_transcribe.return_value = "Hello world"
    if mock_translate is not None:
        mock_translate.return_value = "नमस्ते दुनिया"


@patch("indic_voice.cli.morph_tone")
@patch("indic_voice.cli.generate_speech")
def test_clone_command_succeeds(mock_generate, mock_morph, sample_wav, tmp_path):
    """clone command runs successfully with all pipeline functions mocked."""
    _mock_pipeline(mock_generate, mock_morph)
    output = str(tmp_path / "out.wav")

    result = runner.invoke(app, ["clone", "--text", "नमस्ते", "--ref-voice", sample_wav, "--output", output])

    assert result.exit_code == 0
    assert "Success" in result.output


@patch("indic_voice.cli.morph_tone")
@patch("indic_voice.cli.generate_speech")
@patch("indic_voice.cli.translate")
@patch("indic_voice.cli.transcribe_audio")
def test_translate_command_succeeds(mock_transcribe, mock_translate, mock_generate, mock_morph, sample_wav, tmp_path):
    """translate command runs successfully with all pipeline functions mocked."""
    _mock_pipeline(mock_generate, mock_morph, mock_transcribe, mock_translate)
    output = str(tmp_path / "out.wav")

    result = runner.invoke(app, ["translate", "--audio", sample_wav, "--output", output])

    assert result.exit_code == 0
    assert "Success" in result.output


@patch("indic_voice.cli.morph_tone")
@patch("indic_voice.cli.generate_speech")
def test_clone_shows_error_on_exception(mock_generate, mock_morph, sample_wav, tmp_path):
    """clone command prints error message (does not raise) when pipeline throws."""
    mock_generate.side_effect = ValueError("API key missing")
    output = str(tmp_path / "out.wav")

    result = runner.invoke(app, ["clone", "--text", "test", "--ref-voice", sample_wav, "--output", output])

    assert result.exit_code == 0  # typer catches, we print the error
    assert "Error" in result.output
    assert "API key missing" in result.output


@patch("indic_voice.cli.morph_tone")
@patch("indic_voice.cli.generate_speech")
def test_clone_cleans_up_temp_file(mock_generate, mock_morph, sample_wav, tmp_path, monkeypatch):
    """clone command deletes tmp_sarvam_tts.wav even when pipeline succeeds."""
    monkeypatch.chdir(tmp_path)

    # generate_speech writes a real temp file so cleanup can find it
    def fake_generate(text, path, **kwargs):
        open(path, "w").close()
        return path

    mock_generate.side_effect = fake_generate
    mock_morph.return_value = str(tmp_path / "out.wav")

    output = str(tmp_path / "out.wav")
    result = runner.invoke(app, ["clone", "--text", "test", "--ref-voice", sample_wav, "--output", output])

    assert result.exit_code == 0
    assert not os.path.exists(str(tmp_path / "tmp_sarvam_tts.wav"))


@patch("indic_voice.cli.morph_tone")
@patch("indic_voice.cli.generate_speech")
@patch("indic_voice.cli.translate")
@patch("indic_voice.cli.transcribe_audio")
def test_translate_passes_target_lang(mock_transcribe, mock_translate, mock_generate, mock_morph, sample_wav, tmp_path):
    """translate command passes --target-lang through to translate()."""
    _mock_pipeline(mock_generate, mock_morph, mock_transcribe, mock_translate)
    output = str(tmp_path / "out.wav")

    runner.invoke(app, ["translate", "--audio", sample_wav, "--target-lang", "ta", "--output", output])

    mock_translate.assert_called_once_with("Hello world", target_lang="ta")
