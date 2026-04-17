"""Unit tests for benchmark.data.loader module."""
from benchmark.data.loader import BenchmarkCase, load_test_cases
from benchmark.data.sentences import SENTENCES
from benchmark.data.speakers import SPEAKERS


def test_loader_returns_nonempty_list() -> None:
    cases = load_test_cases()
    assert isinstance(cases, list)
    assert len(cases) > 0


def test_benchmark_case_fields() -> None:
    cases = load_test_cases()
    case = cases[0]
    assert isinstance(case, BenchmarkCase)
    assert case.text != ""
    assert case.language != ""
    assert case.lang_code != ""
    assert case.ref_audio_path != ""
    assert case.ref_transcript != ""
    assert case.speaker_id != ""


def test_lang_codes_valid() -> None:
    valid_codes = {"hi", "ta", "te"}
    cases = load_test_cases()
    for case in cases:
        assert case.lang_code in valid_codes, f"Unexpected lang_code: {case.lang_code}"


def test_case_count_matches_corpus() -> None:
    cases = load_test_cases()
    expected = sum(len(sents) for sents in SENTENCES.values()) * len(SPEAKERS)
    assert len(cases) == expected, f"Expected {expected} cases, got {len(cases)}"


def test_language_names_populated() -> None:
    cases = load_test_cases()
    hindi_cases = [c for c in cases if c.lang_code == "hi"]
    assert all(c.language == "Hindi" for c in hindi_cases)
    tamil_cases = [c for c in cases if c.lang_code == "ta"]
    assert all(c.language == "Tamil" for c in tamil_cases)
    telugu_cases = [c for c in cases if c.lang_code == "te"]
    assert all(c.language == "Telugu" for c in telugu_cases)
