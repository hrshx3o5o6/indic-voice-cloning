import os
from unittest.mock import MagicMock, patch, call

import pytest


@patch("indic_voice.models.tone_transfer.checkpoint_manager.ensure_checkpoints")
@patch("indic_voice.models.tone_transfer.ToneColorConverter")
@patch("indic_voice.models.tone_transfer.se_extractor.get_se")
@patch("indic_voice.models.tone_transfer.torch.load")
def test_morph_tone_calls_converter_convert(
    mock_torch_load,
    mock_get_se,
    mock_converter_cls,
    mock_ensure_ckpts,
    sample_wav,
    tmp_path,
):
    """morph_tone() calls converter.convert() with the correct arguments."""
    mock_ensure_ckpts.return_value = str(tmp_path / "checkpoints_v2")

    mock_converter = MagicMock()
    mock_converter_cls.return_value = mock_converter

    src_se = MagicMock()
    tgt_se = MagicMock()
    mock_torch_load.return_value = src_se
    mock_get_se.return_value = (tgt_se, "audio_name")

    output = str(tmp_path / "out.wav")

    # Need a second wav as ref audio
    import shutil
    ref_wav = str(tmp_path / "ref.wav")
    shutil.copy(sample_wav, ref_wav)

    from indic_voice.models.tone_transfer import morph_tone
    result = morph_tone(sample_wav, ref_wav, output)

    assert result == output
    mock_converter.convert.assert_called_once_with(
        audio_src_path=sample_wav,
        src_se=src_se,
        tgt_se=tgt_se,
        output_path=output,
        message="@MyShell",
    )


def test_morph_tone_raises_for_missing_source(tmp_path):
    """morph_tone() raises FileNotFoundError when source_audio is missing."""
    from indic_voice.models.tone_transfer import morph_tone

    with pytest.raises(FileNotFoundError, match="Source audio missing"):
        morph_tone(
            str(tmp_path / "nonexistent.wav"),
            str(tmp_path / "ref.wav"),
            str(tmp_path / "out.wav"),
        )


def test_morph_tone_raises_for_missing_ref(sample_wav, tmp_path):
    """morph_tone() raises FileNotFoundError when ref_audio is missing."""
    from indic_voice.models.tone_transfer import morph_tone

    with pytest.raises(FileNotFoundError, match="Reference audio missing"):
        morph_tone(
            sample_wav,
            str(tmp_path / "nonexistent_ref.wav"),
            str(tmp_path / "out.wav"),
        )
