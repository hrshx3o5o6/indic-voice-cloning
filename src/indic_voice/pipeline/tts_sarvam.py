import os
import base64
from typing import Any

from dotenv import load_dotenv
from sarvamai import SarvamAI


def _extract_audio_bytes(response: Any) -> bytes:
    """Support both legacy bytes response and newer object response with base64 audios."""
    if isinstance(response, (bytes, bytearray)):
        return bytes(response)

    audios = getattr(response, "audios", None)
    if audios and isinstance(audios, list) and audios[0]:
        return base64.b64decode(audios[0])

    raise ValueError("Sarvam TTS response did not contain audio bytes")


def generate_speech(
    text: str,
    output_path: str,
    lang_code: str = "hi-IN",
    speaker: str = "ritu",
) -> str:
    """Generate Indic speech using Sarvam AI Bulbul TTS.

    Args:
        text: Text to synthesize.
        output_path: File path to write the output WAV audio.
        lang_code: BCP-47 language code for synthesis target.
            Defaults to ``"hi-IN"`` (Hindi).
        speaker: Sarvam speaker voice identifier. Defaults to ``"aditya"``.

    Returns:
        The ``output_path`` string, for easy chaining.

    Raises:
        ValueError: If the ``SARVAM_AI_API`` environment variable is not set.
    """
    load_dotenv()

    api_key = os.getenv("SARVAM_AI_API")
    if not api_key:
        raise ValueError("SARVAM_AI_API environment variable is missing in .env")

    client = SarvamAI(api_subscription_key=api_key)

    response = client.text_to_speech.convert(
        inputs=[text],
        target_language_code=lang_code,
        speaker=speaker,
        model="bulbul:v3",
    )

    with open(output_path, "wb") as f:
        f.write(_extract_audio_bytes(response))

    return output_path
