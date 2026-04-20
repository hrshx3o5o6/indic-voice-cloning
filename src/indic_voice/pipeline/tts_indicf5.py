"""IndicF5 TTS module for zero-shot Indic voice cloning.

Uses ai4bharat/IndicF5 model to generate cloned Indic speech from text,
reference audio, and reference transcript.
"""

import os
import sys
import torch
import numpy as np
import soundfile as sf
import io
from dotenv import load_dotenv
from pydub import AudioSegment, silence
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file

# Load environment variables from .env file
load_dotenv()

# Import f5_tts modules (installed via pip)
from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
)
from f5_tts.model import DiT


def _get_hf_token() -> str | None:
    """Get HuggingFace token from environment.

    Returns:
        The HF_TOKEN if set, None otherwise.
    """
    return os.getenv("HF_TOKEN")


def _select_device() -> str:
    """Select computation device: CUDA > CPU (MPS explicitly excluded).

    Returns:
        str: Selected device string ("cuda" or "cpu") for f5_tts compatibility.
    """
    if torch.cuda.is_available():
        return "cuda"
    else:
        return "cpu"


def generate_speech(
    text: str,
    ref_audio_path: str,
    ref_text: str,
    output_path: str,
) -> str:
    """Generate cloned Indic speech using IndicF5 TTS model.

    Args:
        text: Indic text to synthesize (e.g., "नमस्ते").
        ref_audio_path: Path to reference audio WAV file (5-12 seconds recommended).
        ref_text: Transcript of the reference audio in the same language.
        output_path: File path to write the output WAV audio.

    Returns:
        The output_path string, for easy chaining.

    Raises:
        FileNotFoundError: If ref_audio_path does not exist.
        ValueError: If ref_text is empty or None.
        RuntimeError: If model loading or inference fails.
    """
    # Validate inputs and load reference audio
    if not os.path.exists(ref_audio_path):
        raise FileNotFoundError(f"Reference audio file not found: {ref_audio_path}")

    if not ref_text or (isinstance(ref_text, str) and ref_text.strip() == ""):
        raise ValueError("Reference text (ref_text) cannot be empty or None")

    # Device selection
    device = _select_device()
    repo_id = "ai4bharat/IndicF5"

    try:
        # Download model checkpoint from HuggingFace
        ckpt_path = hf_hub_download(
            repo_id=repo_id,
            filename="model.safetensors",
            token=_get_hf_token()
        )

        # Download vocab file
        vocab_path = hf_hub_download(
            repo_id=repo_id,
            filename="checkpoints/vocab.txt",
            token=_get_hf_token()
        )

        # Load vocoder
        vocoder = load_vocoder(vocoder_name="vocos", is_local=False, device=device)

        # Load checkpoint and fix key prefixes for torch.compile compatibility
        # IndicF5 checkpoint has "ema_model._orig_mod." prefix that needs stripping
        checkpoint = load_file(ckpt_path, device=device)
        fixed_checkpoint = {}
        for key, value in checkpoint.items():
            # Strip "ema_model._orig_mod." -> ""
            # Also handle "_orig_mod." if present without ema_model
            if key.startswith("ema_model._orig_mod."):
                new_key = key.replace("ema_model._orig_mod.", "")
            elif key.startswith("_orig_mod."):
                new_key = key.replace("_orig_mod.", "")
            elif key.startswith("ema_model."):
                new_key = key.replace("ema_model.", "")
            else:
                new_key = key
            fixed_checkpoint[new_key] = value

        # Save fixed checkpoint to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".safetensors", delete=False) as tmp:
            from safetensors.torch import save_file
            save_file(fixed_checkpoint, tmp.name)
            fixed_ckpt_path = tmp.name

        # Load model with fixed checkpoint path
        # Note: IndicF5 uses DiT architecture with specific config
        ema_model = load_model(
            model_cls=DiT,
            model_cfg=dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
            ckpt_path=fixed_ckpt_path,
            mel_spec_type="vocos",
            vocab_file=vocab_path,
            device=device
        )

        # Clean up temp file
        os.unlink(fixed_ckpt_path)

    except Exception as e:
        raise RuntimeError(f"Failed to load IndicF5 model from HuggingFace: {e}")

    # Model inference
    try:
        # Preprocess reference audio and text
        ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_path, ref_text)

        # Perform inference
        audio, final_sample_rate, _ = infer_process(
            ref_audio,
            ref_text,
            text,
            ema_model,
            vocoder,
            mel_spec_type="vocos",
            speed=1.0,
            device=device,
        )

        # Convert to pydub format and remove silence
        buffer = io.BytesIO()
        sf.write(buffer, audio, samplerate=24000, format="WAV")
        buffer.seek(0)
        audio_segment = AudioSegment.from_file(buffer, format="wav")

        # Remove silence
        non_silent_segs = silence.split_on_silence(
            audio_segment,
            min_silence_len=1000,
            silence_thresh=-50,
            keep_silence=500,
            seek_step=10,
        )
        if non_silent_segs:
            non_silent_wave = sum(non_silent_segs, AudioSegment.silent(duration=0))
            audio_segment = non_silent_wave

        # Normalize loudness
        target_dBFS = -20.0
        change_in_dBFS = target_dBFS - audio_segment.dBFS
        audio_segment = audio_segment.apply_gain(change_in_dBFS)

        # Convert to numpy array
        audio_data = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)

    except Exception as e:
        raise RuntimeError(f"IndicF5 inference failed: {e}")

    # Normalize audio: int16 → float32
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0

    # Write output WAV file
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        output_sample_rate = 24000  # IndicF5 native sample rate
        sf.write(output_path, audio_data, output_sample_rate)
    except Exception as e:
        raise RuntimeError(f"Failed to write output audio: {e}")

    return output_path
