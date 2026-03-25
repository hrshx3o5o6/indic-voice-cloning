import os

from dotenv import load_dotenv
from sarvamai import SarvamAI


def generate_speech(
    text: str,
    output_path: str,
    lang_code: str = "hi-IN",
    speaker: str = "meera",
) -> str:
    """Generate Indic speech using Sarvam AI Bulbul TTS.

    Args:
        text: Text to synthesize.
        output_path: File path to write the output WAV audio.
        lang_code: BCP-47 language code for synthesis target.
            Defaults to ``"hi-IN"`` (Hindi).
        speaker: Sarvam speaker voice identifier. Defaults to ``"meera"``.

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
        text=text,
        target_language_code=lang_code,
        speaker=speaker,
        model="bulbul:v3",
    )

    with open(output_path, "wb") as f:
        f.write(response)

    return output_path
