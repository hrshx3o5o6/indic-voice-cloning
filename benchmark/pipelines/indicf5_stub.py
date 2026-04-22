"""IndicF5 pipeline stub for benchmark evaluation.

IndicF5 is the target replacement TTS (no Sarvam API key required, fully
local, better Indic quality).  Until Phase 2 implements the real IndicF5
integration this stub:
  - Writes a 1-second silent WAV to output_dir
  - Returns a BenchmarkResult with error=None but similarity=0.0, wer=1.0, rtf=1.0

This allows the benchmark harness to run end-to-end without IndicF5 installed
and gives developers a baseline to beat.

REQUIREMENT: BENCH-01
"""
from __future__ import annotations

import os
import time

import numpy as np
import soundfile as sf

from benchmark.data.loader import BenchmarkCase
from benchmark.report import BenchmarkResult

_STUB_DURATION_S = 1.0
_STUB_SR = 22050


def run_indicf5_pipeline(
    case: BenchmarkCase,
    input_audio: str,
    output_dir: str,
) -> BenchmarkResult:
    """No-op stub for the IndicF5 pipeline.

    Writes a silent WAV and returns sentinel metric values (0.0 / 1.0 / 1.0)
    so the harness can produce a complete report before IndicF5 is integrated.

    Args:
        case: BenchmarkCase (used only for output file naming).
        input_audio: Unused in the stub.
        output_dir: Directory where the silent WAV will be written.

    Returns:
        BenchmarkResult with pipeline_name="indicf5", error=None, and
        sentinel metric values.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_wav = os.path.join(
        output_dir,
        f"indicf5_{case.lang_code}_{case.speaker_id}_{abs(hash(case.text)) % 100000:05d}.wav",
    )

    t0 = time.perf_counter()
    n_samples = int(_STUB_DURATION_S * _STUB_SR)
    silent = np.zeros(n_samples, dtype=np.float32)
    sf.write(output_wav, silent, _STUB_SR)
    elapsed = time.perf_counter() - t0

    return BenchmarkResult(
        pipeline_name="indicf5",
        case=case,
        output_wav=output_wav,
        elapsed_seconds=elapsed,
        # Stub sentinel values: similarity 0.0, WER 1.0 (completely wrong), RTF 1.0
        similarity=0.0,
        wer=1.0,
        rtf=elapsed / _STUB_DURATION_S,
        error=None,
    )
