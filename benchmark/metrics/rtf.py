"""Real-Time Factor (RTF) metric.

RTF = wall_clock_seconds / audio_duration_seconds.
RTF < 1.0 means the pipeline runs faster than real-time.

REQUIREMENT: BENCH-05
"""
from __future__ import annotations

import os

import soundfile as sf


def get_audio_duration(audio_path: str) -> float:
    """Return the duration of an audio file in seconds.

    Args:
        audio_path: Path to the WAV (or any soundfile-readable) audio file.

    Returns:
        Duration in seconds as a float.

    Raises:
        FileNotFoundError: If audio_path does not exist.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    info = sf.info(audio_path)
    return float(info.duration)


def compute_rtf(audio_path: str, elapsed_seconds: float) -> float:
    """Compute Real-Time Factor for a synthesis run.

    Args:
        audio_path: Path to the output audio file whose duration is the denominator.
        elapsed_seconds: Wall-clock time taken to generate audio_path.

    Returns:
        RTF = elapsed_seconds / audio_duration. Lower is faster.
        RTF < 1.0 means faster than real-time.

    Raises:
        FileNotFoundError: If audio_path does not exist.
        ValueError: If audio_path has zero duration.
    """
    duration = get_audio_duration(audio_path)
    if duration == 0.0:
        raise ValueError(f"Audio file has zero duration: {audio_path}")
    return elapsed_seconds / duration
