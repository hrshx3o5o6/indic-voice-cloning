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

        # Initialize model architecture
        model_cfg = dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4)
        
        # We need the vocab size to initialize the model
        from f5_tts.infer.utils_infer import get_tokenizer
        vocab_char_map, vocab_size = get_tokenizer(vocab_path, "custom")
        
        from f5_tts.model.cfm import CFM
        ema_model = CFM(
            transformer=DiT(**model_cfg, text_num_embeds=vocab_size, mel_dim=100),
            mel_spec_kwargs=dict(
                n_fft=1024,
                hop_length=256,
                win_length=1024,
                n_mel_channels=100,
                target_sample_rate=24000,
                mel_spec_type="vocos",
            ),
            odeint_kwargs=dict(method="euler"),
            vocab_char_map=vocab_char_map,
        ).to(device)

        # Load and fix checkpoint keys
        checkpoint = load_file(ckpt_path, device=device)
        
        # The goal is to map checkpoint keys (ema_model._orig_mod.transformer.xxx) 
        # to our model keys (transformer.xxx)
        state_dict = {}
        for key, value in checkpoint.items():
            if key.startswith("vocoder"):
                continue
            
            # Strip all common prefixes to get to the core layer names
            new_key = key
            for prefix in ["ema_model._orig_mod.", "ema_model.", "_orig_mod."]:
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix):]
                    break
            
            state_dict[new_key] = value

        # Load state dict into the CFM model
        # CFM has a 'transformer' attribute, so keys starting with 'transformer.' will match
        ema_model.load_state_dict(state_dict, strict=True)
        ema_model.eval()

    except Exception as e:
        raise RuntimeError(f"Failed to load IndicF5 model: {e}")

    # Model inference
    try:
        # Preprocess reference audio and text
        ref_audio, ref_text = preprocess_ref_audio_text(ref_audio_path, ref_text)

        # Perform inference
        # Use a slightly higher cfg_strength for better articulation if it was sounding like gibberish
        audio, final_sample_rate, _ = infer_process(
            ref_audio,
            ref_text,
            text,
            ema_model,
            vocoder,
            mel_spec_type="vocos",
            speed=1.0,
            cfg_strength=2.0,
            device=device,
        )
    except Exception as e:
        raise RuntimeError(f"IndicF5 inference failed: {e}")

    # Write output WAV file
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Normalization to prevent clipping and resolve "garbage" sound if it was related to range
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * 0.95  # Normalize to -0.95 to 0.95

        output_sample_rate = 24000  # IndicF5 native sample rate
        sf.write(output_path, audio.astype(np.float32), output_sample_rate)
    except Exception as e:
        raise RuntimeError(f"Failed to write output audio: {e}")

    return output_path
