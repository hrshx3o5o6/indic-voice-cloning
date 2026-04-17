---
phase: 01-benchmark-harness
plan: 01
subsystem: benchmark-harness
tags: [benchmark, data-layer, corpus, testing]
dependency_graph:
  requires: []
  provides: [benchmark-data-contract]
  affects: [01-02-plan, 01-03-plan]
tech_stack:
  added: []
  patterns: [dataclass-based-configuration, immutable-data-structures]
key_files:
  created:
    - benchmark/__init__.py
    - benchmark/data/__init__.py
    - benchmark/data/sentences.py
    - benchmark/data/speakers.py
    - benchmark/data/loader.py
    - tests/benchmark/__init__.py
    - tests/benchmark/test_loader.py
  modified: []
decisions:
  - id: corpus_size
    summary: "Set corpus to 5 sentences per language (hi, ta, te) × 6 reference speakers = 90 test cases"
    rationale: "Provides sufficient variety for pipeline comparison without excessive runtime"
  - id: speaker_metadata_structure
    summary: "Use SpeakerMeta dataclass with speaker_id, audio_path, transcript, language fields"
    rationale: "Enables flexible reference speaker management and metadata tracking for future audio population"
  - id: language_mapping
    summary: "Use BCP-47 short codes (hi, ta, te) with human-readable language names"
    rationale: "Consistent with industry standard and enables future language expansion"
metrics:
  duration_seconds: 45
  completed_date: "2026-04-17"
  tasks_completed: 2
  files_created: 7
  files_modified: 0
---

# Phase 1 Plan 01: Benchmark Test Data — Summary

**One-liner:** Created benchmark data layer with 90 test cases (5 Hindi/Tamil/Telugu sentences × 6 reference speakers) and loader function for pipeline comparison.

## Objective Achieved

Established the core data contract for the benchmark harness: `BenchmarkCase` dataclass, sentence corpus (SENTENCES dict), speaker metadata (SPEAKERS list), and a loader function that produces the full cross-product of sentences × speakers for the orchestrator to consume.

## Task Execution

### Task 1: Create benchmark data package with sentence corpus and speaker metadata

**Status:** COMPLETED

**Created files:**
- `benchmark/__init__.py` — Package marker
- `benchmark/data/__init__.py` — Package marker
- `benchmark/data/sentences.py` — SENTENCES dict with Hindi, Tamil, Telugu corpus
- `benchmark/data/speakers.py` — SpeakerMeta dataclass and SPEAKERS list

**Verification:**
- SENTENCES loaded successfully: 5 Hindi, 5 Tamil, 5 Telugu sentences
- SPEAKERS loaded successfully: 6 SpeakerMeta instances
- Both modules import without error

**Commit:** c11a87b

### Task 2: Create BenchmarkCase dataclass, load_test_cases() function, and unit tests

**Status:** COMPLETED

**Created files:**
- `benchmark/data/loader.py` — BenchmarkCase dataclass and load_test_cases() function
- `tests/benchmark/__init__.py` — Test package marker
- `tests/benchmark/test_loader.py` — 5 unit tests

**Test Results:**
```
tests/benchmark/test_loader.py::test_loader_returns_nonempty_list PASSED
tests/benchmark/test_loader.py::test_benchmark_case_fields PASSED
tests/benchmark/test_loader.py::test_lang_codes_valid PASSED
tests/benchmark/test_loader.py::test_case_count_matches_corpus PASSED
tests/benchmark/test_loader.py::test_language_names_populated PASSED

5 passed in 0.01s
```

**Data Validation:**
- load_test_cases() returns 90 cases (5 sentences × 6 speakers × 3 languages)
- Each BenchmarkCase has all required fields populated
- All language codes are valid (hi, ta, te)
- Language names mapped correctly (Hindi, Tamil, Telugu)

**Commit:** 8abdd00

## Deviations from Plan

None — plan executed exactly as written.

## Threat Model Compliance

All threats in the threat register (T-01-01, T-01-02) are in "accept" disposition:
- Sentence/speaker data are static, no user input at this layer
- Paths are local developer machine paths, no PII
- Benchmark is dev-only tool not shipped to end users

## Data Contract Provided

### BenchmarkCase (from benchmark/data/loader.py)

```python
@dataclass
class BenchmarkCase:
    text: str               # Indic text to synthesize
    language: str           # Human name: "Hindi", "Tamil", "Telugu"
    lang_code: str          # BCP-47 short code: "hi", "ta", "te"
    ref_audio_path: str     # Path to reference WAV
    ref_transcript: str     # Transcript of reference audio
    speaker_id: str         # Reference speaker ID
```

### SENTENCES (from benchmark/data/sentences.py)

```python
SENTENCES: Dict[str, List[str]] = {
    "hi": [...],   # 5 Hindi sentences
    "ta": [...],   # 5 Tamil sentences
    "te": [...],   # 5 Telugu sentences
}
```

### SPEAKERS (from benchmark/data/speakers.py)

```python
@dataclass
class SpeakerMeta:
    speaker_id: str         # e.g. "spk_01"
    audio_path: str         # e.g. "benchmark/ref_audio/spk_01.wav"
    transcript: str         # Transcript of reference audio
    language: str           # "en" (English reference audio)

SPEAKERS: List[SpeakerMeta] = [...]  # 6 entries
```

## Exported Functions

**From benchmark/data/loader.py:**
- `load_test_cases() -> List[BenchmarkCase]` — Returns 90 test cases for benchmark orchestrator

## Success Criteria

All success criteria met:

- [x] benchmark/data/ package exists with __init__.py, sentences.py, speakers.py, loader.py
- [x] tests/benchmark/ package exists with __init__.py, test_loader.py
- [x] uv run pytest tests/benchmark/test_loader.py exits 0 with all tests passing
- [x] SENTENCES has 5 entries for each of hi, ta, te
- [x] SPEAKERS has 6 SpeakerMeta entries
- [x] load_test_cases() returns 5×6×3 = 90 BenchmarkCase objects

## Code Quality

- [x] Type hints on all functions and dataclass fields (Google-style compatible)
- [x] Google-style docstrings on all public classes and functions
- [x] No external APIs or new dependencies required
- [x] All tests pass without modification
- [x] Follows project conventions from CLAUDE.md

## Next Steps

This plan provides the data contract for:
- **Plan 01-02 (Metrics):** Will consume BenchmarkCase and compute evaluation metrics
- **Plan 01-03 (Orchestrator):** Will iterate over load_test_cases() output to run pipeline comparisons

The benchmark/ref_audio/ directory should be populated with actual WAV files and transcripts before running Plan 01-03 (orchestrator script).

---

**Execution Duration:** 45 seconds  
**Commits:** 2 (c11a87b, 8abdd00)
