import os
from pathlib import Path

from huggingface_hub import hf_hub_download
from rich.console import Console

_REPO_ID = "myshell-ai/OpenVoiceV2"
_REQUIRED_FILES = [
    "converter/config.json",
    "converter/checkpoint.pth",
    "base_speakers/ses/en-default.pth",
]

console = Console()


def ensure_checkpoints(cache_dir: str | None = None) -> str:
    """Download OpenVoice v2 checkpoints if not cached.

    Downloads required model checkpoint files from the myshell-ai/OpenVoiceV2
    HuggingFace repository on first run. Subsequent calls skip the download
    if all files are already present.

    Args:
        cache_dir: Local directory to store checkpoints. Defaults to
            ``~/.cache/indic-voice/checkpoints_v2``.

    Returns:
        Absolute path to the local ``checkpoints_v2`` directory.
    """
    if cache_dir is None:
        cache_dir = os.path.join(Path.home(), ".cache", "indic-voice")

    ckpt_dir = os.path.join(cache_dir, "checkpoints_v2")

    all_present = all(os.path.exists(os.path.join(ckpt_dir, f)) for f in _REQUIRED_FILES)

    if all_present:
        return ckpt_dir

    console.print("[dim]Downloading OpenVoice v2 checkpoints (first run)...[/dim]")

    for relative_path in _REQUIRED_FILES:
        local_path = os.path.join(ckpt_dir, relative_path)
        if os.path.exists(local_path):
            continue

        console.print(f"[dim]  Fetching {relative_path}...[/dim]")
        hf_hub_download(
            repo_id=_REPO_ID,
            filename=relative_path,
            local_dir=ckpt_dir,
        )

    console.print("[dim]Checkpoints ready.[/dim]")
    return ckpt_dir
