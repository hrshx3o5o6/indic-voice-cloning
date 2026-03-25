import os

import torch
from rich.console import Console

from indic_voice.models import checkpoint_manager
from indic_voice.openvoice import se_extractor
from indic_voice.openvoice.api import ToneColorConverter

console = Console()


def morph_tone(source_audio: str, ref_audio: str, output_path: str) -> str:
    """Apply tone color from ref_audio onto source_audio using OpenVoice v2.

    Downloads model checkpoints on first run. Extracts the tone color (speaker
    embedding) from ``ref_audio`` and applies it to ``source_audio``, writing
    the result to ``output_path``.

    Args:
        source_audio: Path to the base TTS-generated WAV file whose content is
            kept but whose tone is replaced.
        ref_audio: Path to the reference speaker WAV file whose tone color is
            extracted and applied.
        output_path: Destination path for the tone-morphed WAV output.

    Returns:
        The ``output_path`` string, for easy chaining.

    Raises:
        FileNotFoundError: If ``source_audio`` or ``ref_audio`` do not exist.
    """
    if not os.path.exists(source_audio):
        raise FileNotFoundError(f"Source audio missing: {source_audio}")
    if not os.path.exists(ref_audio):
        raise FileNotFoundError(f"Reference audio missing: {ref_audio}")

    device = (
        "cuda"
        if torch.cuda.is_available()
        else ("mps" if torch.backends.mps.is_available() else "cpu")
    )

    ckpt_dir = checkpoint_manager.ensure_checkpoints()

    console.print(f"[dim]  Initializing OpenVoice ToneColorConverter on {device}...[/dim]")
    converter_ckpt = os.path.join(ckpt_dir, "converter")
    converter = ToneColorConverter(
        os.path.join(converter_ckpt, "config.json"),
        device=device,
    )
    converter.load_ckpt(os.path.join(converter_ckpt, "checkpoint.pth"))

    src_se_path = os.path.join(ckpt_dir, "base_speakers", "ses", "en-default.pth")
    src_se = torch.load(src_se_path, map_location=device)

    console.print(f"[dim]  Extracting tone color from {ref_audio}...[/dim]")
    tgt_se, _ = se_extractor.get_se(ref_audio, converter, vad=True)

    console.print(f"[dim]  Applying tone transfer to {source_audio}...[/dim]")
    converter.convert(
        audio_src_path=source_audio,
        src_se=src_se,
        tgt_se=tgt_se,
        output_path=output_path,
        message="@MyShell",
    )

    return output_path
