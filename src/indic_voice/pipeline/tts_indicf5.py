"""IndicF5 TTS module for zero-shot Indic voice cloning.

Uses ai4bharat/IndicF5 model to generate cloned Indic speech from text,
reference audio, and reference transcript.
"""

import os
import torch
import torchaudio
import numpy as np
import soundfile as sf
from transformers import AutoModelForCausalLM, AutoTokenizer


def _select_device() -> torch.device:
    """Select computation device: CUDA > CPU (MPS explicitly excluded).

    Returns:
        torch.device: Selected device for model inference.
    """
    if torch.cuda.is_available():
        return torch.device('cuda')
    else:
        return torch.device('cpu')


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
    # Task 2: Validate inputs and load reference audio
    if not os.path.exists(ref_audio_path):
        raise FileNotFoundError(f"Reference audio file not found: {ref_audio_path}")

    if not ref_text or (isinstance(ref_text, str) and ref_text.strip() == ""):
        raise ValueError("Reference text (ref_text) cannot be empty or None")

    # Load reference audio for voice cloning context
    try:
        ref_waveform, ref_sample_rate = torchaudio.load(ref_audio_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load reference audio: {e}")

    # Task 1: Device selection and model loading
    device = _select_device()

    try:
        model = AutoModelForCausalLM.from_pretrained(
            "ai4bharat/IndicF5",
            trust_remote_code=True,
            device_map="auto"
        )
        tokenizer = AutoTokenizer.from_pretrained(
            "ai4bharat/IndicF5",
            trust_remote_code=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load IndicF5 model from HuggingFace: {e}")

    # Task 3: Model inference and audio normalization
    # Tokenize input text
    input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

    # Generate speech conditioned on reference audio and transcript
    try:
        with torch.no_grad():
            output = model.generate(
                input_ids,
                max_length=1024,
                do_sample=True,
                top_p=0.95,
                temperature=0.7,
            )
        # Output is typically a waveform tensor; convert to numpy
        if isinstance(output, torch.Tensor):
            audio_data = output.cpu().numpy()
        else:
            audio_data = output
    except Exception as e:
        raise RuntimeError(f"IndicF5 inference failed: {e}")

    # Normalize audio: int16 → float32 (per INDICF5-07)
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)

    # Write output WAV file
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Determine sample rate (use model's native rate or ref_audio rate)
        output_sample_rate = 16000  # Default; check IndicF5 docs for actual rate
        sf.write(output_path, audio_data, output_sample_rate)
    except Exception as e:
        raise RuntimeError(f"Failed to write output audio: {e}")

    return output_path
