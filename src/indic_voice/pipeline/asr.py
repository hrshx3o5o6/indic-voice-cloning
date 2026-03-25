from faster_whisper import WhisperModel
import os

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe the given audio using a lightweight medium Whisper model.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Source audio {audio_path} not found.")
        
    # Try to load the local model you downloaded earlier to skip the 1.5GB wait time!
    model_path = "../faster_whisper_medium" if os.path.exists("../faster_whisper_medium") else "medium"
    model = WhisperModel(model_path, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5)
    
    return " ".join([segment.text for segment in segments])
