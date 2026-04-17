# Roadmap: indic-voice-cli

## Overview

The existing Sarvam+OpenVoice pipeline produces noticeably synthetic clones because the two-stage TTS-then-tone-transfer architecture compounds quality loss at every handoff. This roadmap replaces that pipeline with IndicF5 — a single model trained natively on 1,417 hours of Indic audio that performs voice cloning in one pass. The work is gated: Phase 1 benchmarks the two pipelines before a single line of production code changes. If IndicF5 wins (expected), Phases 2-5 build, integrate, clean up, and polish the replacement. The CLI surface stays identical throughout.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Benchmark Harness** - Build the evaluation harness that proves IndicF5 beats the current pipeline before any production code changes
- [ ] **Phase 2: IndicF5 Module** - Build and test the IndicF5 TTS module in complete isolation — no CLI changes yet
- [ ] **Phase 3: CLI Integration** - Wire IndicF5 into the `clone` and `translate` commands with ref_text auto-fill and new UX guardrails
- [ ] **Phase 4: Dependency Cleanup** - Remove Sarvam, OpenVoice, and the 10 packages that supported them
- [ ] **Phase 5: Open-Source Polish** - README, error messages, temp-file hygiene — everything a new contributor needs

## Phase Details

### Phase 1: Benchmark Harness
**Goal**: Developer can quantitatively compare the current Sarvam+OpenVoice pipeline against IndicF5 before touching production code
**Depends on**: Nothing (first phase)
**Requirements**: BENCH-01, BENCH-02, BENCH-03, BENCH-04, BENCH-05, BENCH-06
**Success Criteria** (what must be TRUE):
  1. Developer can run `python benchmark/compare_pipelines.py` against both pipelines on the same input audio and text without error
  2. The test set covers Hindi, Tamil, and Telugu with at least 5 sentences each and 5-8 out-of-distribution reference speakers
  3. The report shows Speaker Similarity (WavLM cosine), WER (faster-whisper large-v3), and RTF for each pipeline side-by-side
  4. A structured JSONL + human-readable summary file is written to disk; a reader can tell at a glance which pipeline wins
  5. Benchmark completes in a single command invocation with no manual steps between pipelines
**Plans**: TBD

### Phase 2: IndicF5 Module
**Goal**: `pipeline/tts_indicf5.py` is a fully tested, dependency-pinned module that generates cloned Indic speech — the CLI is not yet changed
**Depends on**: Phase 1
**Requirements**: INDICF5-01, INDICF5-02, INDICF5-03, INDICF5-04, INDICF5-05, INDICF5-06, INDICF5-07
**Success Criteria** (what must be TRUE):
  1. `from indic_voice.pipeline.tts_indicf5 import generate_speech` imports without error in a clean environment
  2. `generate_speech(text, ref_audio_path, ref_text, output_path)` produces a `.wav` file at the specified path
  3. Device auto-selects CUDA over CPU; MPS is explicitly excluded (no vocos ISTFT crash on Apple M4)
  4. `uv run pytest tests/test_tts_indicf5.py` passes — happy path, missing ref_audio, empty ref_text, and output path creation are all covered
  5. `transformers==4.49.0`, `numpy<=1.26.4`, `torchaudio>=2.0.0`, and `accelerate>=0.33.0` are pinned in `pyproject.toml`
**Plans**: TBD

### Phase 3: CLI Integration
**Goal**: Both `indic-voice clone` and `indic-voice translate` use IndicF5 end-to-end, with ref_text auto-filled and new UX guardrails in place — zero breaking changes
**Depends on**: Phase 2
**Requirements**: CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-07
**Success Criteria** (what must be TRUE):
  1. `indic-voice clone --text "नमस्ते" --ref-voice ref.wav` produces cloned audio via IndicF5 without requiring a `--ref-text` flag
  2. `indic-voice translate --audio input.wav --target-lang hi` completes the full S2ST pipeline using IndicF5, with Whisper's Step-1 transcript automatically forwarded as `ref_text`
  3. All existing flags (`--text`, `--ref-voice`, `--audio`, `--target-lang`, `--output`) work identically to before — existing scripts are not broken
  4. Running either command with a reference audio shorter than 5s or longer than 12s prints a clear warning before proceeding
  5. Running on a machine without CUDA prints a CPU-speed warning; the first run shows a Rich progress bar during the 1.4 GB checkpoint download
**Plans**: TBD
**UI hint**: yes

### Phase 4: Dependency Cleanup
**Goal**: All Sarvam AI and OpenVoice code and packages are removed; `uv sync` resolves a clean, minimal dependency set
**Depends on**: Phase 3
**Requirements**: DEPS-01, DEPS-02, DEPS-03, DEPS-04, DEPS-05
**Success Criteria** (what must be TRUE):
  1. `uv sync` completes with no `sarvamai`, `wavmark`, `langid`, `whisper-timestamped`, `inflect`, `unidecode`, `eng-to-ipa`, `pypinyin`, `jieba`, or `cn2an` packages installed
  2. `src/indic_voice/openvoice/` directory no longer exists in the repository
  3. `tts_sarvam.py`, `models/tone_transfer.py`, and `models/checkpoint_manager.py` no longer exist
  4. `uv run indic-voice clone --text "नमस्ते" --ref-voice ref.wav` still succeeds after all removals
  5. `uv lock` is regenerated and committed; lockfile contains no removed packages
**Plans**: TBD

### Phase 5: Open-Source Polish
**Goal**: A developer who has never seen this project can clone the repo, follow the README, and produce cloned Indic speech in under 5 minutes
**Depends on**: Phase 4
**Requirements**: POLISH-01, POLISH-02, POLISH-03
**Success Criteria** (what must be TRUE):
  1. README documents: `huggingface-cli login` prerequisite, optimal reference audio length (5-6s, hard max 12s), CPU timing expectations, and all 11 supported IndicF5 languages
  2. Every known failure mode (meta tensor / transformers version, HF auth failure, vocos ISTFT on Apple M4) produces a clear, actionable error message — no raw Python traceback reaches the user
  3. Running either CLI command leaves no `processed/` directory or other temp files behind after completion
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Benchmark Harness | 0/TBD | Not started | - |
| 2. IndicF5 Module | 0/TBD | Not started | - |
| 3. CLI Integration | 0/TBD | Not started | - |
| 4. Dependency Cleanup | 0/TBD | Not started | - |
| 5. Open-Source Polish | 0/TBD | Not started | - |
