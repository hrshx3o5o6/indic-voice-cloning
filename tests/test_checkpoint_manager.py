from unittest.mock import patch

from indic_voice.models.checkpoint_manager import ensure_checkpoints


@patch("indic_voice.models.checkpoint_manager.hf_hub_download")
def test_ensure_checkpoints_downloads_openvoice_v2_layout(mock_download, tmp_path):
    """ensure_checkpoints() should fetch checkpoints from OpenVoiceV2 layout."""
    ckpt_dir = ensure_checkpoints(cache_dir=str(tmp_path))

    assert ckpt_dir == str(tmp_path / "checkpoints_v2")
    assert mock_download.call_count == 3
    mock_download.assert_any_call(
        repo_id="myshell-ai/OpenVoiceV2",
        filename="converter/config.json",
        local_dir=str(tmp_path / "checkpoints_v2"),
    )
    mock_download.assert_any_call(
        repo_id="myshell-ai/OpenVoiceV2",
        filename="converter/checkpoint.pth",
        local_dir=str(tmp_path / "checkpoints_v2"),
    )
    mock_download.assert_any_call(
        repo_id="myshell-ai/OpenVoiceV2",
        filename="base_speakers/ses/en-default.pth",
        local_dir=str(tmp_path / "checkpoints_v2"),
    )
