"""BenchmarkCase dataclass and test corpus loader for pipeline comparison.

load_test_cases() produces the full cross-product of (sentences × speakers)
for each language, giving the benchmark orchestrator a flat list to iterate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from benchmark.data.sentences import SENTENCES
from benchmark.data.speakers import SPEAKERS

# BCP-47 short code → human readable language name
_LANG_NAMES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
}


@dataclass
class BenchmarkCase:
    """A single (text, speaker) pair to evaluate against both pipelines.

    Attributes:
        text: Indic text to synthesize.
        language: Human-readable language name (e.g. "Hindi").
        lang_code: BCP-47 short code (e.g. "hi").
        ref_audio_path: Path to the reference speaker WAV file.
        ref_transcript: Transcript of the reference audio (used by IndicF5 as ref_text).
        speaker_id: Unique identifier for the reference speaker.
    """
    text: str
    language: str
    lang_code: str
    ref_audio_path: str
    ref_transcript: str
    speaker_id: str


def load_test_cases() -> List[BenchmarkCase]:
    """Return the full benchmark corpus as a flat list of BenchmarkCase objects.

    Produces a cross-product of all sentences × all speakers for each language
    (hi, ta, te).  The ordering is language-major: all Hindi cases come first,
    then Tamil, then Telugu.

    Returns:
        A non-empty list of BenchmarkCase instances.
    """
    cases: List[BenchmarkCase] = []
    for lang_code, sentences in SENTENCES.items():
        lang_name = _LANG_NAMES[lang_code]
        for sentence in sentences:
            for speaker in SPEAKERS:
                cases.append(
                    BenchmarkCase(
                        text=sentence,
                        language=lang_name,
                        lang_code=lang_code,
                        ref_audio_path=speaker.audio_path,
                        ref_transcript=speaker.transcript,
                        speaker_id=speaker.speaker_id,
                    )
                )
    return cases
