"""Word Error Rate (WER) metric using faster-whisper large-v3.

WER = edit_distance(ref_words, hyp_words) / len(ref_words)

Uses faster-whisper large-v3 for transcription. Per BENCH-04: large-v3 is
required (not medium) because medium produces Roman transliteration on Indic
text, corrupting WER calculation.

REQUIREMENT: BENCH-04
"""
from __future__ import annotations

from faster_whisper import WhisperModel


_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    """Lazy-load faster-whisper large-v3 (cached after first call)."""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    return _whisper_model


def _word_error_rate(ref_text: str, hyp_text: str) -> float:
    """Compute WER using word-level Levenshtein distance.

    Args:
        ref_text: Ground-truth reference text.
        hyp_text: Hypothesis text from ASR transcription.

    Returns:
        WER as float. 0.0 = perfect match. Can exceed 1.0 with many insertions.
    """
    ref_words = ref_text.strip().split()
    hyp_words = hyp_text.strip().split()
    n = len(ref_words)
    m = len(hyp_words)

    if n == 0:
        return 0.0 if m == 0 else float(m)

    # Build DP table for Levenshtein distance at word level
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j - 1], prev[j], dp[j - 1])
    return dp[m] / n


def compute_wer(ref_text: str, hyp_wav: str) -> float:
    """Compute WER by transcribing hyp_wav with faster-whisper large-v3.

    The hypothesis WAV is transcribed; its transcript is compared against
    ref_text using word-level Levenshtein edit distance.

    Args:
        ref_text: Ground-truth text (the original Indic sentence that was synthesized).
        hyp_wav: Path to the synthesized audio file to transcribe and evaluate.

    Returns:
        WER as float. 0.0 = perfect, 1.0 = completely different.
    """
    model = _get_whisper_model()
    segments, _ = model.transcribe(hyp_wav, beam_size=5)
    hyp_text = " ".join(seg.text.strip() for seg in segments)
    return _word_error_rate(ref_text, hyp_text)
