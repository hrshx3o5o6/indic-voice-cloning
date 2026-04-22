---
phase: 01-benchmark-harness
plan: 02
subsystem: Benchmark Metrics
status: complete
tags: [metrics, wavlm, whisper, rtf, testing]
duration: ~5 minutes
completed_date: 2026-04-17
dependencies:
  requires: []
  provides: [benchmark.metrics.similarity, benchmark.metrics.wer, benchmark.metrics.rtf]
  affects: [01-03-PLAN.md (metric orchestrator)]
tech_stack:
  added:
    - transformers==4.49.0 (WavLM model loading)
    - torchaudio>=2.0.0 (audio processing)
  patterns:
    - Lazy-load model caching (module-level globals)
    - Word-level Levenshtein distance (DP algorithm)
    - Mock-based unit testing for heavy ML models
key_files:
  created:
    - benchmark/metrics/__init__.py
    - benchmark/metrics/similarity.py (68 lines, compute_speaker_similarity)
    - benchmark/metrics/wer.py (72 lines, compute_wer + _word_error_rate)
    - benchmark/metrics/rtf.py (47 lines, compute_rtf + get_audio_duration)
    - tests/benchmark/__init__.py
    - tests/benchmark/test_metrics.py (208 lines, 9 tests)
  modified:
    - pyproject.toml (added transformers + torchaudio dependencies)
decisions: []
metrics:
  tasks_completed: 2
  tests_passing: 9
  test_coverage: compute_speaker_similarity, compute_wer, compute_rtf, get_audio_duration
  commit_count: 2
---

# Phase 01 Plan 02: Benchmark Metrics Summary

Three independently testable metric modules for evaluating Indic voice cloning quality: speaker similarity (WavLM cosine), WER (faster-whisper large-v3), and RTF (wall-clock efficiency).

## One-Liner

**WavLM-based speaker similarity + faster-whisper large-v3 WER + RTF computation — all tested without model downloads, ready for orchestration.**

## What Was Built

### Task 1: Speaker Similarity & RTF Modules ✓

Created two metric modules with lazy-loaded model caching:

**benchmark/metrics/similarity.py (68 lines)**
- `compute_speaker_similarity(ref_wav: str, hyp_wav: str) -> float`
- Uses `microsoft/wavlm-base-plus` via transformers
- Extracts speaker embeddings by mean-pooling last hidden state
- Returns cosine similarity in [-1.0, 1.0] range
- Models cached after first load (module-level globals)

**benchmark/metrics/rtf.py (47 lines)**
- `compute_rtf(audio_path: str, elapsed_seconds: float) -> float`
- Returns wall_clock_seconds / audio_duration as efficiency metric
- `get_audio_duration(audio_path: str) -> float` using soundfile
- Raises ValueError on zero-duration audio, FileNotFoundError if file missing

### Task 2: WER Module & Full Test Suite ✓

**benchmark/metrics/wer.py (72 lines)**
- `compute_wer(ref_text: str, hyp_wav: str) -> float`
- Transcribes hypothesis WAV using `faster-whisper` large-v3 (NOT medium)
- Computes WER via word-level Levenshtein edit distance
- `_word_error_rate(ref_text: str, hyp_text: str) -> float` — DP-based implementation
- Returns 0.0 for exact match, >1.0 possible with insertions

**tests/benchmark/test_metrics.py (208 lines, 9 tests)**
- RTF tests: basic computation (0.5 × 2s elapsed = 1s audio), zero-duration error, missing file error
- Audio duration tests: correct duration read, FileNotFoundError on missing
- WER tests: exact match (0.0), partial match (0.5), complete mismatch (≥1.0), empty ref/hyp
- Similarity tests: mock WavLM return value in [-1.0, 1.0] range

**All 9 tests passing:** ✓ (1.16s total)

## Critical Design Decisions

1. **Lazy-Load Caching:** Module-level globals for WavLM and Whisper to avoid repeated downloads
2. **Large-V3 (Not Medium):** Whisper large-v3 required per BENCH-04 because medium produces Roman transliteration on Indic text
3. **Transformers 4.49.0:** Pinned per CLAUDE.md (>=4.51 breaks model loading with meta tensor errors)
4. **Mock Heavy Models:** Tests mock WavLM + Whisper to eliminate 1.5 GB + 500 MB downloads during CI
5. **Word-Level WER:** Edit distance computed at word granularity (not character), standard for speech metrics

## Deviations from Plan

None — plan executed exactly as written.

## Threat Surface

**T-02-01:** WavLM model cache stored in HuggingFace cache directory (~/.cache/huggingface). No PII in paths; developer-only tool.

**T-02-02:** Whisper large-v3 load is single-invocation; no uptime requirement for benchmark.

**T-02-03:** WAV file paths provided by orchestrator (Plan 03), not external input; no sanitization needed.

## Next Steps

Plan 03 (Benchmark Orchestrator) will wire these three metrics into a unified benchmark harness:
- Accepts ref audio, hypothesis audio, hypothesis text
- Computes all three metrics in parallel
- Returns structured result dict {similarity, wer, rtf}
- Interfaces with existing OpenVoice pipeline from src/indic_voice/

## Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| benchmark/metrics/__init__.py | 5 | Package marker |
| benchmark/metrics/similarity.py | 68 | WavLM speaker similarity |
| benchmark/metrics/wer.py | 72 | Whisper large-v3 WER |
| benchmark/metrics/rtf.py | 47 | Audio duration & RTF |
| tests/benchmark/test_metrics.py | 208 | 9 comprehensive unit tests |
| pyproject.toml | +2 deps | transformers==4.49.0, torchaudio>=2.0.0 |

## Self-Check

✓ All 3 metric modules exist and import without error
✓ All 9 tests pass (test_rtf_basic, test_rtf_zero_duration_raises, test_get_audio_duration_missing_raises, test_get_audio_duration_correct, test_wer_exact_match_is_zero, test_wer_completely_different, test_wer_empty_ref, test_wer_partial_match, test_compute_speaker_similarity_returns_float_in_range)
✓ compute_speaker_similarity returns float in [-1.0, 1.0]
✓ compute_wer uses WhisperModel("large-v3")
✓ compute_rtf raises ValueError on zero duration
✓ Both commits created (a9d6ee7, 211878b)
