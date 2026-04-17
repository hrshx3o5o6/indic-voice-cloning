# Requirements: indic-voice-cli

**Defined:** 2026-04-17
**Core Value:** The easiest open-source way to clone a voice into an Indic language — better quality than ElevenLabs at Indic specifically, free to run, privacy-first.

## v1 Requirements

### Benchmark Harness

- [ ] **BENCH-01**: Developer can run `benchmark/compare_pipelines.py` to generate audio from both pipelines on the same inputs
- [ ] **BENCH-02**: Benchmark test set covers Hindi, Tamil, Telugu (5 sentences each) with 5–8 out-of-distribution reference speakers and transcripts
- [ ] **BENCH-03**: Benchmark measures Speaker Similarity (SIM) via WavLM cosine similarity for each pipeline
- [ ] **BENCH-04**: Benchmark measures WER via `faster-whisper large-v3` (not medium — medium produces Roman transliteration on Indic)
- [ ] **BENCH-05**: Benchmark measures RTF (wall-clock time / audio duration) per pipeline
- [ ] **BENCH-06**: Benchmark outputs a structured results report (JSONL + human-readable summary) that clearly shows which pipeline wins

### IndicF5 Module

- [x] **INDICF5-01**: `pipeline/tts_indicf5.py` exposes `generate_speech(text, ref_audio_path, ref_text, output_path) -> str` as a pure function
- [x] **INDICF5-02**: Module loads IndicF5 from `ai4bharat/IndicF5` with `trust_remote_code=True`; device auto-selects `cuda > cpu` (MPS explicitly excluded — vocos ISTFT crash on Apple M4)
- [ ] **INDICF5-03**: `transformers==4.49.0` pinned in `pyproject.toml` (versions ≥4.51 break model loading with meta tensor error)
- [ ] **INDICF5-04**: `torchaudio>=2.0.0` and `accelerate>=0.33.0` added to `pyproject.toml`
- [ ] **INDICF5-05**: `numpy` upper-bounded to `<=1.26.4` in `pyproject.toml`
- [ ] **INDICF5-06**: Unit tests in `tests/test_tts_indicf5.py` mock the heavy model and cover: happy path, missing ref_audio, empty ref_text, output path creation
- [x] **INDICF5-07**: If output is `int16`, normalize to `float32` before writing with `soundfile`

### CLI Integration

- [ ] **CLI-01**: `clone` command auto-transcribes `--ref-voice` via Whisper if `--ref-text` is not supplied (preserves backward compatibility — no new required flags)
- [ ] **CLI-02**: `translate` command threads Whisper transcript from Step 1 through as `ref_text` to IndicF5 (no extra user input needed)
- [ ] **CLI-03**: Optional `--ref-text` flag added to `clone` command for users who want to supply transcript manually
- [ ] **CLI-04**: Reference audio validation at CLI entry: warns if duration < 5s or > 12s (12s is F5-TTS hard clip limit; < 5s produces poor quality)
- [ ] **CLI-05**: CPU inference warning printed if no CUDA device detected (IndicF5 CPU RTF is 10–50x slower than real-time)
- [ ] **CLI-06**: First-run IndicF5 checkpoint download shows Rich progress bar (1.4 GB download; silence causes users to assume a hang)
- [ ] **CLI-07**: All existing flags unchanged (`--text`, `--ref-voice`, `--audio`, `--target-lang`, `--output`) — zero breaking changes

### Dependency Cleanup

- [ ] **DEPS-01**: `tts_sarvam.py` deleted; `sarvamai` removed from `pyproject.toml`
- [ ] **DEPS-02**: `models/tone_transfer.py` and `models/checkpoint_manager.py` deleted
- [ ] **DEPS-03**: `src/indic_voice/openvoice/` bundle (~3,700 lines) deleted
- [ ] **DEPS-04**: OpenVoice-specific packages removed: `wavmark`, `langid`, `whisper-timestamped`, `inflect`, `unidecode`, `eng-to-ipa`, `pypinyin`, `jieba`, `cn2an`
- [ ] **DEPS-05**: `uv lock` regenerated and verified clean after all removals

### Open Source Polish

- [ ] **POLISH-01**: README updated: HuggingFace login prerequisite (`huggingface-cli login`), reference audio guidance (5–6s optimal, ≤12s), CPU timing expectation, supported languages
- [ ] **POLISH-02**: Clear error messages for all known failure modes: meta tensor (transformers version), HF auth failure (gated model), vocos ISTFT (Apple M4), missing `SARVAM_AI_API` (now obsolete — remove this check)
- [ ] **POLISH-03**: `processed/` temp directory no longer created (was OpenVoice artifact) — verify no residual temp file pollution

## v2 Requirements

### EnCodec Post-processing

- **ENCODEC-01**: `pipeline/encodec_postprocess.py` exposes `postprocess(audio_path, output_path) -> str` using `facebook/encodec_24khz`
- **ENCODEC-02**: `--postprocess` flag added to both `clone` and `translate` commands (default off)
- **ENCODEC-03**: EnCodec input forced to mono 24kHz before encode; stereo silently drops a channel without this guard
- **ENCODEC-04**: Files longer than 30s processed in 10s chunks to avoid VRAM OOM
- **ENCODEC-05**: Output amplitude normalized after decode to prevent clipping

### Language Expansion

- **LANG-01**: Benchmark coverage extended to Kannada, Bengali, Marathi (3 sentences each)
- **LANG-02**: Language code mapping documented for all 11 IndicF5 languages

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web UI or REST API | CLI is the product; simplicity is a feature |
| Real-time / streaming TTS | Batch processing sufficient; diffusion model not suited to streaming |
| English TTS quality improvements | Competing on Indic depth, not language breadth |
| Custom speaker fine-tuning | Zero-shot only; no per-user training pipeline |
| Apple M4 vocos fix | Upstream issue — wait for IndicF5 maintainer fix |
| UTMOS scoring in benchmark | Calibration on Indic languages unverified; WER + SIM are sufficient gates |
| Quantized IndicF5 variant | No confirmed quantized model available; defer to v2 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BENCH-01 | Phase 1 | Pending |
| BENCH-02 | Phase 1 | Pending |
| BENCH-03 | Phase 1 | Pending |
| BENCH-04 | Phase 1 | Pending |
| BENCH-05 | Phase 1 | Pending |
| BENCH-06 | Phase 1 | Pending |
| INDICF5-01 | Phase 2 | Complete |
| INDICF5-02 | Phase 2 | Complete |
| INDICF5-03 | Phase 2 | Pending |
| INDICF5-04 | Phase 2 | Pending |
| INDICF5-05 | Phase 2 | Pending |
| INDICF5-06 | Phase 2 | Pending |
| INDICF5-07 | Phase 2 | Complete |
| CLI-01 | Phase 3 | Pending |
| CLI-02 | Phase 3 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 3 | Pending |
| CLI-05 | Phase 3 | Pending |
| CLI-06 | Phase 3 | Pending |
| CLI-07 | Phase 3 | Pending |
| DEPS-01 | Phase 4 | Pending |
| DEPS-02 | Phase 4 | Pending |
| DEPS-03 | Phase 4 | Pending |
| DEPS-04 | Phase 4 | Pending |
| DEPS-05 | Phase 4 | Pending |
| POLISH-01 | Phase 5 | Pending |
| POLISH-02 | Phase 5 | Pending |
| POLISH-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-17*
*Last updated: 2026-04-15 after roadmap creation (5 phases, 28 requirements mapped)*
