"""BenchmarkResult dataclass and report writers for pipeline comparison.

write_jsonl() produces a machine-readable JSONL file (one result per line).
write_summary() produces a human-readable text summary with per-pipeline
averages and a winner declaration based on mean speaker similarity.

REQUIREMENT: BENCH-06
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import List, Optional

from benchmark.data.loader import BenchmarkCase


@dataclass
class BenchmarkResult:
    """Outcome of running one pipeline on one BenchmarkCase.

    Attributes:
        pipeline_name: Identifier string — "current" or "indicf5".
        case: The BenchmarkCase that was evaluated.
        output_wav: Absolute path to the synthesized audio file.
        elapsed_seconds: Wall-clock synthesis time in seconds.
        similarity: WavLM cosine similarity (ref vs. output). -1.0 on error.
        wer: Word Error Rate of the output audio. -1.0 on error.
        rtf: Real-Time Factor (elapsed / audio duration). -1.0 on error.
        error: Exception message if the pipeline failed; None on success.
    """

    pipeline_name: str
    case: BenchmarkCase
    output_wav: str
    elapsed_seconds: float
    similarity: float
    wer: float
    rtf: float
    error: Optional[str]


def write_jsonl(results: List[BenchmarkResult], path: str) -> None:
    """Write benchmark results to a JSONL file (one JSON object per line).

    BenchmarkCase fields are inlined into each record for easy downstream
    processing without a join.

    Args:
        results: List of BenchmarkResult objects to serialise.
        path: Destination file path (created or overwritten).
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for r in results:
            record = {
                "pipeline": r.pipeline_name,
                "text": r.case.text,
                "language": r.case.language,
                "lang_code": r.case.lang_code,
                "speaker_id": r.case.speaker_id,
                "ref_audio_path": r.case.ref_audio_path,
                "output_wav": r.output_wav,
                "elapsed_seconds": r.elapsed_seconds,
                "similarity": r.similarity,
                "wer": r.wer,
                "rtf": r.rtf,
                "error": r.error,
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_summary(results: List[BenchmarkResult], path: str) -> None:
    """Write a human-readable summary of benchmark results.

    Computes per-pipeline mean similarity, WER, and RTF (excluding error
    results where similarity == -1.0).  Declares a winner based on higher
    mean similarity.

    Args:
        results: List of BenchmarkResult objects.
        path: Destination file path (created or overwritten).
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    # Group results by pipeline name
    pipelines: dict[str, List[BenchmarkResult]] = {}
    for r in results:
        pipelines.setdefault(r.pipeline_name, []).append(r)

    def _mean(values: List[float]) -> float:
        valid = [v for v in values if v >= 0.0]
        return sum(valid) / len(valid) if valid else float("nan")

    stats: dict[str, dict[str, float]] = {}
    for name, res in pipelines.items():
        stats[name] = {
            "mean_similarity": _mean([r.similarity for r in res]),
            "mean_wer": _mean([r.wer for r in res]),
            "mean_rtf": _mean([r.rtf for r in res]),
            "n_ok": sum(1 for r in res if r.error is None),
            "n_error": sum(1 for r in res if r.error is not None),
            "n_total": len(res),
        }

    # Determine winner by highest mean similarity (nan loses)
    def _sim(name: str) -> float:
        v = stats[name]["mean_similarity"]
        return v if v == v else -999.0  # NaN check

    winner = max(stats.keys(), key=_sim) if stats else "N/A"

    lines: List[str] = [
        "=" * 60,
        "  BENCHMARK SUMMARY",
        "=" * 60,
        "",
    ]
    for name, s in sorted(stats.items()):
        lines += [
            f"Pipeline: {name}",
            f"  Runs:             {s['n_ok']} ok / {s['n_error']} errors / {s['n_total']} total",
            f"  Mean Similarity:  {s['mean_similarity']:.4f}  (higher is better)",
            f"  Mean WER:         {s['mean_wer']:.4f}  (lower is better)",
            f"  Mean RTF:         {s['mean_rtf']:.4f}  (lower is better)",
            "",
        ]
    lines += [
        "=" * 60,
        f"  Winner (by speaker similarity): {winner}",
        "=" * 60,
    ]

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
