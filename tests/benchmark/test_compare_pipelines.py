"""Unit tests for benchmark orchestrator and report writer.

All pipeline functions and metric functions are mocked so no model downloads
or real audio synthesis occur during CI.
"""
from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import soundfile

from benchmark.data.loader import BenchmarkCase
from benchmark.pipelines.indicf5_stub import run_indicf5_pipeline
from benchmark.report import BenchmarkResult, write_jsonl, write_summary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_case(lang_code: str = "hi", speaker_id: str = "spk_01") -> BenchmarkCase:
    return BenchmarkCase(
        text="नमस्ते दुनिया",
        language="Hindi",
        lang_code=lang_code,
        ref_audio_path="benchmark/ref_audio/spk_01.wav",
        ref_transcript="Hello world",
        speaker_id=speaker_id,
    )


def _make_result(pipeline_name: str = "current", error: str | None = None) -> BenchmarkResult:
    return BenchmarkResult(
        pipeline_name=pipeline_name,
        case=_make_case(),
        output_wav="/tmp/out.wav",
        elapsed_seconds=1.5,
        similarity=0.85 if error is None else -1.0,
        wer=0.12 if error is None else -1.0,
        rtf=0.75 if error is None else -1.0,
        error=error,
    )


# ---------------------------------------------------------------------------
# Report writer tests
# ---------------------------------------------------------------------------

def test_write_jsonl_produces_valid_jsonl() -> None:
    results = [_make_result("current"), _make_result("indicf5")]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "results.jsonl")
        write_jsonl(results, path)
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as fh:
            lines = [json.loads(line) for line in fh if line.strip()]
    assert len(lines) == 2
    assert lines[0]["pipeline"] == "current"
    assert lines[1]["pipeline"] == "indicf5"
    # All required fields present
    required = {"pipeline", "text", "language", "lang_code", "speaker_id",
                "output_wav", "elapsed_seconds", "similarity", "wer", "rtf", "error"}
    assert required.issubset(set(lines[0].keys()))


def test_write_summary_contains_winner_line() -> None:
    results = [_make_result("current"), _make_result("indicf5")]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "summary.txt")
        write_summary(results, path)
        assert os.path.exists(path)
        content = open(path, encoding="utf-8").read()
    assert "Winner" in content


def test_write_summary_contains_both_pipeline_names() -> None:
    results = [_make_result("current"), _make_result("indicf5")]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "summary.txt")
        write_summary(results, path)
        content = open(path, encoding="utf-8").read()
    assert "current" in content
    assert "indicf5" in content


def test_write_summary_winner_is_higher_similarity() -> None:
    """current has sim=0.85, indicf5 has sim=0.0 -> current should win."""
    results = [_make_result("current"), _make_result("indicf5")]
    # Override indicf5 similarity to 0.0 (default stub value)
    results[1] = BenchmarkResult(
        pipeline_name="indicf5",
        case=_make_case(),
        output_wav="/tmp/indicf5.wav",
        elapsed_seconds=0.05,
        similarity=0.0,
        wer=1.0,
        rtf=1.0,
        error=None,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "summary.txt")
        write_summary(results, path)
        content = open(path, encoding="utf-8").read()
    # The winner line should name "current"
    winner_line = [l for l in content.splitlines() if "Winner" in l][0]
    assert "current" in winner_line


# ---------------------------------------------------------------------------
# IndicF5 stub tests
# ---------------------------------------------------------------------------

def test_indicf5_stub_returns_result_with_no_error() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_indicf5_pipeline(_make_case(), "/dev/null", tmp)
    assert isinstance(result, BenchmarkResult)
    assert result.pipeline_name == "indicf5"
    assert result.error is None


def test_indicf5_stub_writes_valid_wav() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_indicf5_pipeline(_make_case(), "/dev/null", tmp)
        assert os.path.exists(result.output_wav)
        info = soundfile.info(result.output_wav)
        assert info.duration > 0.0


def test_indicf5_stub_sentinel_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_indicf5_pipeline(_make_case(), "/dev/null", tmp)
    assert result.similarity == 0.0
    assert result.wer == 1.0


# ---------------------------------------------------------------------------
# Orchestrator (run_benchmark) tests — mock both pipeline runners
# ---------------------------------------------------------------------------

def test_orchestrator_filters_by_lang() -> None:
    """Only cases matching target_lang are processed."""
    from benchmark.compare_pipelines import run_benchmark

    hi_case = _make_case(lang_code="hi")
    ta_case = _make_case(lang_code="ta")

    mock_result = _make_result("current")

    with patch("benchmark.compare_pipelines.load_test_cases", return_value=[hi_case, ta_case]):
        with patch("benchmark.compare_pipelines.run_current_pipeline", return_value=mock_result):
            with patch("benchmark.compare_pipelines.run_indicf5_pipeline", return_value=mock_result):
                with tempfile.TemporaryDirectory() as tmp:
                    results = run_benchmark("/dev/null", "hi", tmp)

    # Only 1 hi case × 2 pipelines = 2 results
    assert len(results) == 2


def test_orchestrator_writes_output_files() -> None:
    """main() writes results.jsonl and summary.txt to output_dir."""
    from benchmark.compare_pipelines import main

    # Create a minimal valid WAV as input_audio
    with tempfile.TemporaryDirectory() as tmp:
        input_wav = os.path.join(tmp, "input.wav")
        soundfile.write(input_wav, np.zeros(16000, dtype=np.float32), 16000)
        output_dir = os.path.join(tmp, "out")

        mock_result = _make_result("current")

        with patch("benchmark.compare_pipelines.load_test_cases", return_value=[_make_case("hi")]):
            with patch("benchmark.compare_pipelines.run_current_pipeline", return_value=mock_result):
                with patch("benchmark.compare_pipelines.run_indicf5_pipeline", return_value=mock_result):
                    exit_code = main([
                        "--input-audio", input_wav,
                        "--target-lang", "hi",
                        "--output-dir", output_dir,
                    ])

        assert exit_code == 0
        assert os.path.exists(os.path.join(output_dir, "results.jsonl"))
        assert os.path.exists(os.path.join(output_dir, "summary.txt"))
