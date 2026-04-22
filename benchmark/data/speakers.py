"""Out-of-distribution reference speaker metadata for benchmark evaluation.

Speakers represent varied demographics (gender, age, accent region) to test
zero-shot voice cloning generalization. Audio files are expected at the paths
defined below; users populate them before running the benchmark.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class SpeakerMeta:
    """Metadata for a single reference speaker used in benchmark evaluation."""
    speaker_id: str
    audio_path: str    # Path relative to project root, e.g. "benchmark/ref_audio/spk_01.wav"
    transcript: str    # Transcript of the reference audio (used by IndicF5 as ref_text)
    language: str      # Primary language spoken in the reference audio


SPEAKERS: List[SpeakerMeta] = [
    SpeakerMeta(
        speaker_id="spk_01",
        audio_path="benchmark/ref_audio/spk_01.wav",
        transcript="Hello, my name is Arjun and I am from Mumbai.",
        language="en",
    ),
    SpeakerMeta(
        speaker_id="spk_02",
        audio_path="benchmark/ref_audio/spk_02.wav",
        transcript="Good morning everyone, today is a beautiful day.",
        language="en",
    ),
    SpeakerMeta(
        speaker_id="spk_03",
        audio_path="benchmark/ref_audio/spk_03.wav",
        transcript="The quick brown fox jumps over the lazy dog.",
        language="en",
    ),
    SpeakerMeta(
        speaker_id="spk_04",
        audio_path="benchmark/ref_audio/spk_04.wav",
        transcript="Please call me back when you get a chance.",
        language="en",
    ),
    SpeakerMeta(
        speaker_id="spk_05",
        audio_path="benchmark/ref_audio/spk_05.wav",
        transcript="I enjoy listening to classical music in the evening.",
        language="en",
    ),
    SpeakerMeta(
        speaker_id="spk_06",
        audio_path="benchmark/ref_audio/spk_06.wav",
        transcript="Technology is changing the world at a rapid pace.",
        language="en",
    ),
]
