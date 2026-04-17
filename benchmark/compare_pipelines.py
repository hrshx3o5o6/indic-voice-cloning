"""Pipeline comparison orchestrator.

Usage:
    uv run python benchmark/compare_pipelines.py \
        --input-audio path/to/english.wav \
        --target-lang hi \
        --output-dir /tmp/bench_out

Runs both the current Sarvam+OpenVoice pipeline and the IndicF5 stub over
every BenchmarkCase for the requested language, then writes:
  - <output-dir>/results.jsonl  — machine-readable per-run results
  - <output-dir>/summary.txt   — human-readable averages and winner

REQUIREMENT: BENCH-01, BENCH-06
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

from rich.console import Console

from benchmark.data.loader import BenchmarkCase, load_test_cases
from benchmark.pipelines.current import run_current_pipeline
from benchmark.pipelines.indicf5_stub import run_indicf5_pipeline
from benchmark.report import BenchmarkResult, write_jsonl, write_summary

console = Console()

_SUPPORTED_LANGS = ("hi", "ta", "te")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare current Sarvam+OpenVoice pipeline against IndicF5 stub."
    )
    parser.add_argument(
        "--input-audio",
        required=True,
        metavar="PATH",
        help="Path to the English input audio file (WAV) for the ASR stage.",
    )
    parser.add_argument(
        "--target-lang",
        required=True,
        choices=list(_SUPPORTED_LANGS),
        metavar="LANG",
        help="Target language code: hi (Hindi), ta (Tamil), te (Telugu).",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        metavar="DIR",
        help="Directory to write synthesized WAVs, results.jsonl, and summary.txt.",
    )
    return parser.parse_args(argv)


def run_benchmark(
    input_audio: str,
    target_lang: str,
    output_dir: str,
) -> List[BenchmarkResult]:
    """Run both pipelines on all BenchmarkCases for target_lang.

    Args:
        input_audio: Path to English WAV for ASR.
        target_lang: BCP-47 code ("hi", "ta", or "te").
        output_dir: Root output directory; sub-dirs created per pipeline.

    Returns:
        Flat list of BenchmarkResult (2 results per BenchmarkCase).
    """
    all_cases = load_test_cases()
    cases = [c for c in all_cases if c.lang_code == target_lang]

    if not cases:
        console.print(
            f"[bold red]No benchmark cases found for lang_code='{target_lang}'.[/bold red]"
        )
        return []

    console.print(
        f"[bold]Running benchmark[/bold]: {len(cases)} cases × 2 pipelines "
        f"= {len(cases) * 2} runs  (lang={target_lang})"
    )

    results: List[BenchmarkResult] = []
    current_dir = os.path.join(output_dir, "current")
    indicf5_dir = os.path.join(output_dir, "indicf5")

    for i, case in enumerate(cases, start=1):
        console.print(
            f"  [dim][{i}/{len(cases)}][/dim] speaker={case.speaker_id}  "
            f"text={case.text[:40]}{'…' if len(case.text) > 40 else ''}"
        )

        r_current = run_current_pipeline(case, input_audio, current_dir)
        if r_current.error:
            console.print(f"    [yellow]current pipeline error:[/yellow] {r_current.error}")
        else:
            console.print(
                f"    current  sim={r_current.similarity:.3f}  "
                f"wer={r_current.wer:.3f}  rtf={r_current.rtf:.3f}"
            )
        results.append(r_current)

        r_indicf5 = run_indicf5_pipeline(case, input_audio, indicf5_dir)
        if r_indicf5.error:
            console.print(f"    [yellow]indicf5 pipeline error:[/yellow] {r_indicf5.error}")
        else:
            console.print(
                f"    indicf5  sim={r_indicf5.similarity:.3f}  "
                f"wer={r_indicf5.wer:.3f}  rtf={r_indicf5.rtf:.3f}"
            )
        results.append(r_indicf5)

    return results


def main(argv: list[str] | None = None) -> int:
    """Entry point for the benchmark orchestrator.

    Args:
        argv: Argument list (defaults to sys.argv[1:] when None).

    Returns:
        Exit code (0 on success).
    """
    args = _parse_args(argv)

    if not os.path.exists(args.input_audio):
        console.print(
            f"[bold red]Input audio file not found:[/bold red] {args.input_audio}"
        )
        return 1

    os.makedirs(args.output_dir, exist_ok=True)

    results = run_benchmark(args.input_audio, args.target_lang, args.output_dir)

    jsonl_path = os.path.join(args.output_dir, "results.jsonl")
    summary_path = os.path.join(args.output_dir, "summary.txt")

    write_jsonl(results, jsonl_path)
    write_summary(results, summary_path)

    console.print(f"\n[bold green]Done.[/bold green]")
    console.print(f"  JSONL   → {jsonl_path}")
    console.print(f"  Summary → {summary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
