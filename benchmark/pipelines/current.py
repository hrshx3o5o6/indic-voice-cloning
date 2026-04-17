"""Current pipeline adapter for benchmark evaluation.

Wraps the existing indic-voice translate pipeline:
  ASR (Whisper) -> Translation (Google) -> TTS (Sarvam) -> Tone Transfer (OpenVoice v2)

Catches all exceptions so the orchestrator never crashes mid-benchmark.

REQUIREMENT: BENCH-01
"""
from __future__ import annotations

import os
import time
import tempfile

from benchmark.data.loader import BenchmarkCase
from benchmark.metrics.rtf import compute_rtf
from benchmark.metrics.similarity import compute_speaker_similarity
from benchmark.metrics.wer import compute_wer
from benchmark.report import BenchmarkResult


def run_current_pipeline(
    case: BenchmarkCase,
    input_audio: str,
    output_dir: str,
) -> BenchmarkResult:
    """Run the current Sarvam+OpenVoice pipeline on a single BenchmarkCase.

    Calls the same pipeline functions used by `indic-voice translate`.
    Wall-clock time covers only synthesis (asr+translate+tts+tone_transfer),
    not metric computation.

    Args:
        case: BenchmarkCase describing text, language, and reference speaker.
        input_audio: Path to English input audio for the ASR stage.
        output_dir: Directory where the synthesized WAV will be written.

    Returns:
        BenchmarkResult with all metrics populated.  On exception, similarity/
        wer/rtf are set to -1.0 and error is set to the exception message.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_wav = os.path.join(
        output_dir,
        f"current_{case.lang_code}_{case.speaker_id}_{abs(hash(case.text)) % 100000:05d}.wav",
    )

    try:
        from indic_voice.pipeline.asr import transcribe_audio
        from indic_voice.pipeline.translator import translate_text
        from indic_voice.pipeline.tts_sarvam import generate_tts
        from indic_voice.models.tone_transfer import apply_tone_transfer
        from indic_voice.models.checkpoint_manager import ensure_checkpoints

        checkpoint_dir = ensure_checkpoints()

        t0 = time.perf_counter()

        # Stage 1: ASR
        english_text = transcribe_audio(input_audio)

        # Stage 2: Translation
        indic_text = translate_text(english_text, target_lang=case.lang_code)

        # Stage 3: TTS — write to a temp file; tone transfer reads it
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tts_path = tmp.name
        try:
            generate_tts(indic_text, output_path=tts_path, lang_code=case.lang_code)

            # Stage 4: Tone transfer
            apply_tone_transfer(
                source_wav=tts_path,
                reference_wav=case.ref_audio_path,
                output_wav=output_wav,
                checkpoint_dir=checkpoint_dir,
            )
        finally:
            if os.path.exists(tts_path):
                os.unlink(tts_path)

        elapsed = time.perf_counter() - t0

        similarity = compute_speaker_similarity(case.ref_audio_path, output_wav)
        wer = compute_wer(case.text, output_wav)
        rtf = compute_rtf(output_wav, elapsed)

        return BenchmarkResult(
            pipeline_name="current",
            case=case,
            output_wav=output_wav,
            elapsed_seconds=elapsed,
            similarity=similarity,
            wer=wer,
            rtf=rtf,
            error=None,
        )

    except Exception as exc:
        return BenchmarkResult(
            pipeline_name="current",
            case=case,
            output_wav=output_wav,
            elapsed_seconds=0.0,
            similarity=-1.0,
            wer=-1.0,
            rtf=-1.0,
            error=str(exc),
        )
