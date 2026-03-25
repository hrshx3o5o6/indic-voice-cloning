import os
from sarvamai import SarvamAI
from dotenv import load_dotenv

load_dotenv()

def generate_hindi_speech(text: str, output_path: str):
    """
    Generate generic Hindi speech using Sarvam Bulbul.
    """
    api_key = os.getenv("SARVAM_AI_API")
    if not api_key:
        raise ValueError("SARVAM_AI_API environment variable is missing in .env")

    client = SarvamAI(api_subscription_key=api_key)
    
    response = client.text_to_speech.convert(
        text=text,
        target_language_code="hi-IN",
        speaker="meera", # Bulbul defaults
        model="bulbul:v3"
    )
    
    # Save the bytes to audio file
    with open(output_path, "wb") as f:
        f.write(response)
        
    return output_path
