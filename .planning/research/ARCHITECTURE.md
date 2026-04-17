# Architecture: IndicF5 Integration

**Research Date:** 2026-04-15
**Domain:** Indic TTS / Voice Cloning pipeline
**Confidence:** MEDIUM — IndicF5 public model card verified; `model.py` internals gated behind HF auth; garbled-output issues noted from community

---

## Research Sources

- HuggingFace model card: `ai4bharat/IndicF5` (verified, HIGH confidence)
- HF discussions #2, #20, #22, #25, #33 (MEDIUM confidence — community reports)
- HuggingFace model card: `facebook/encodec_24khz` (verified, HIGH confidence)
- Existing codebase: `src/indic_voice/` (HIGH confidence — read directly)

---

## IndicF5 Exact Inputs

IndicF5's `__call__` signature (from public model card + discussion corroboration):

```python
audio = model(
    text,                          # str — target text in any of 11 supported scripts
    ref_audio_path="ref.wav",      # str — path to reference speaker audio
    ref_text="...",                # str — verbatim transcript of ref_audio_path
)
```

**No `language_code` parameter exists in the public API.** Language is inferred implicitly from the script of the input `text`. The supported languages — Assamese (`as`), Bengali (`bn`), Gujarati (`gu`), Hindi (`hi`), Kannada (`kn`), Malayalam (`ml`), Marathi (`mr`), Odia (`or`), Punjabi (`pa`), Tamil (`ta`), Telugu (`te`) — all use distinct Unicode scripts, so the model auto-routes to the correct language model branch based on the script of the input text. No explicit mapping layer is needed in the wrapper.

**Reference audio requirements:** No explicit minimum duration is documented. Community usage shows 5–10 second clips work well (consistent with general voice cloning literature). The reference audio should contain clear speech with minimal background noise.

**Transformers version pin:** Community confirmed `transformers==4.49.0` is required. Transformers 5.0.0 has a breaking change (PR #33 exists but had not merged as of research date).

---

## IndicF5 Output Format

- **Type:** `numpy.ndarray`, dtype `int16` or `float32` depending on run
- **Sample rate:** 24,000 Hz
- **Normalization required:** If `audio.dtype == np.int16`, divide by 32768.0 before writing
- **Write format:** WAV via `soundfile.write(..., samplerate=24000)`

This matches the EnCodec 24kHz model's native sample rate exactly — no resampling is needed if EnCodec post-processing is applied.

---

## Language Code Mapping

The existing pipeline uses BCP-47 short codes (`hi`, `ta`, `te`) for `target_lang` in the translator and `lang_code` in Sarvam TTS (`hi-IN` format). IndicF5 uses the same ISO 639-1 two-letter codes in its README but does NOT accept them as an explicit parameter. The `target_lang` code that flows through the translator stage is sufficient to identify which script to use — no new mapping table is required. The CLI `--target-lang` flag stays unchanged.

---

## Component Boundary Decision

**IndicF5 replaces BOTH `tts_sarvam.py` AND `tone_transfer.py` with a single new module.**

Rationale:
- `tts_sarvam.py` produces neutral Sarvam speech; `tone_transfer.py` grafts voice characteristics on top. This two-stage handoff is the source of prosody loss.
- IndicF5 performs TTS and speaker embedding simultaneously inside one model. The reference audio is conditioned at generation time, not post-processed on top.
- Splitting IndicF5 across two files would be artificial — there is no intermediate "neutral TTS" output to expose.
- The OpenVoice bundled library (`src/indic_voice/openvoice/`) can be deleted once IndicF5 is confirmed superior in benchmarks.

**What stays untouched:**
- `pipeline/asr.py` — no change
- `pipeline/translator.py` — no change
- `cli.py` — interface unchanged; only the internal import and call site changes
- `models/checkpoint_manager.py` — adapt to download IndicF5 weights instead of OpenVoice; or use HF `AutoModel` auto-download (preferred — no custom checkpoint manager needed)

---

## New Module: `pipeline/tts_indicf5.py`

**Interface contract — pure function, matches the style of every other pipeline stage:**

```python
def generate_speech(
    text: str,
    ref_audio_path: str,
    ref_text: str,
    output_path: str,
) -> str:
    """Generate Indic speech cloned to the speaker in ref_audio_path using IndicF5.

    Args:
        text: Indic-language text to synthesize. Language is auto-detected
            from the Unicode script of the input text.
        ref_audio_path: Path to a reference speaker WAV file (5–10 seconds,
            clean speech recommended).
        ref_text: Verbatim transcript of ref_audio_path in the same language
            and script as that audio. Required by IndicF5 for speaker
            conditioning.
        output_path: Destination path for the output WAV file.

    Returns:
        The output_path string, for easy chaining.

    Raises:
        FileNotFoundError: If ref_audio_path does not exist.
        RuntimeError: If IndicF5 model loading or inference fails.
    """
```

**Key implementation notes:**
1. Model is loaded via `AutoModel.from_pretrained("ai4bharat/IndicF5", trust_remote_code=True)`.
2. Weights auto-download to HF cache on first run (~1.4 GB safetensors). No custom checkpoint manager needed.
3. Output requires dtype check before `soundfile.write` — normalize int16 → float32 if needed.
4. Output sample rate is always 24000 Hz.
5. Pin `transformers==4.49.0` in `pyproject.toml`; document the constraint.
6. The function is stateless — model is loaded fresh per call (acceptable for CLI batch mode; model caching can be added later if interactive use emerges).

**Signature change from `tts_sarvam.py`:** The new function adds `ref_audio_path: str` and `ref_text: str` as required positional arguments and removes `lang_code` and `speaker`. The CLI must thread `ref_voice` and a new `--ref-text` option through to this function. This is the only CLI surface change.

---

## CLI Change Required

The `clone` command currently takes `--ref-voice` but not `--ref-text`. The new pipeline needs the reference audio transcript to condition IndicF5. Two options:

**Option A — Required `--ref-text` flag (breaking but honest):**
```
indic-voice clone --text "नमस्ते" --ref-voice ref.wav --ref-text "Hello, my name is..."
```
This is the correct approach. IndicF5 needs the transcript; omitting it produces garbled output.

**Option B — Auto-transcribe ref-text with Whisper (better UX, slightly slower):**
If `--ref-text` is not provided, run Whisper on the ref audio to auto-generate the transcript. This keeps the CLI interface fully unchanged.

**Recommendation:** Option B for `clone` command (zero breaking change); Option A as an override flag for when the user wants to supply an exact transcript. The `translate` command already has the source audio, so Whisper transcription of the reference is a natural fit.

---

## Data Flow Through New Pipeline

### `clone` Command (new)

```
User Input:
  text: str               (Indic text, e.g., "नमस्ते")
  ref_voice: str          (Path to reference speaker .wav)
  ref_text: str           (Optional — transcript of ref_voice)
  output: str             (Output path, default "clone_output.wav")

Step 0 (if ref_text not provided):
  Input: ref_voice
  Process: transcribe_audio(ref_voice)   [reuses existing asr.py]
  Output: ref_text (transcript of reference audio)

Step 1: IndicF5 TTS + Voice Clone
  Input: text, ref_voice, ref_text
  Process: tts_indicf5.generate_speech(text, ref_voice, ref_text, output)
    1. Load AutoModel "ai4bharat/IndicF5" (auto-downloads on first run)
    2. model(text, ref_audio_path=ref_voice, ref_text=ref_text)
    3. Normalize int16 → float32 if needed
    4. soundfile.write(output, audio, samplerate=24000)
  Output: output.wav (cloned speech, 24kHz WAV)

No cleanup needed (no temporary file produced)
```

### `translate` Command (new)

```
User Input:
  audio: str              (Path to English audio .wav)
  target_lang: str        (Language code, default "hi")
  output: str             (Output path, default "translated_clone.wav")

Step 1: ASR (Whisper) — unchanged
  Input: audio
  Output: en_text (English transcript)

Step 2: Translation — unchanged
  Input: en_text, target_lang
  Output: indic_text

Step 3: Transcribe reference audio for IndicF5 conditioning
  Input: audio (the original English source audio is ALSO the voice reference)
  Process: transcribe_audio(audio)   [reuses existing asr.py; output is en_text — already computed]
  Note: ref_text for IndicF5 is en_text (the English transcript of the reference audio).
        IndicF5 conditions on acoustic features of ref_audio, not on text semantics —
        the language of ref_text does not need to match the target language.

Step 4: IndicF5 TTS + Voice Clone
  Input: indic_text, audio (reference), en_text (reference transcript)
  Process: tts_indicf5.generate_speech(indic_text, audio, en_text, output)
  Output: output.wav (translated speech in original speaker's voice, 24kHz)

No cleanup needed (no temporary file produced)
```

**Key simplification:** The two-step TTS → tone_transfer sequence collapses to one step. The temporary file `tmp_sarvam_tts.wav` disappears entirely.

---

## EnCodec Post-Processing

EnCodec is an additive, optional step applied AFTER IndicF5 output is written. It does not change the IndicF5 interface.

**When to add:** Only after IndicF5 standalone is benchmarked and confirmed working. Do not co-develop with IndicF5 integration.

**Proposed module:** `pipeline/encodec_postprocess.py`

**Interface contract:**

```python
def postprocess(
    audio_path: str,
    output_path: str,
    bandwidth: float = 6.0,
) -> str:
    """Apply EnCodec encode→decode to reduce TTS artifacts.

    Args:
        audio_path: Path to input WAV (24kHz expected).
        output_path: Destination path for post-processed WAV.
        bandwidth: EnCodec target bitrate (kbps). Lower = more aggressive
            artifact removal, more detail loss. 6.0 is a balanced default.
            Options: 1.5, 3.0, 6.0, 12.0.

    Returns:
        The output_path string, for easy chaining.
    """
```

**Implementation notes:**
- Model: `facebook/encodec_24khz` via `transformers`. No custom weights needed.
- Input must be resampled to 24kHz if it isn't already (IndicF5 output is 24kHz — no resampling needed in the normal case).
- The encode→decode cycle smooths codec artifacts introduced by the neural vocoder. Lower bandwidth = more smoothing, less high-frequency detail. Start at 6.0 kbps.
- Controlled by a `--postprocess / --no-postprocess` CLI flag. Default off until quality is benchmarked.

---

## Benchmark Harness Architecture

Build the benchmark FIRST (before swapping production code). Purpose: confirm IndicF5 is better, not assume it is.

**Module:** `benchmarks/compare_pipelines.py` (standalone script, not part of `src/`)

**What it compares:**

| Dimension | How to measure |
|-----------|---------------|
| Subjective quality | Side-by-side WAV files for human listening |
| Speaker similarity | Cosine similarity of speaker embeddings (use SpeechBrain or resemblyzer) |
| Intelligibility | CER/WER of Whisper transcription on output audio vs source text |
| Latency | Wall-clock time per sample on CPU and GPU |
| Memory | Peak RSS during inference |

**Inputs to benchmark:** Same set of reference audio clips + same set of target texts, run through both pipelines, outputs saved as pairs.

**Build order within the benchmark:**

1. Implement `tts_indicf5.generate_speech` in isolation (no CLI wiring yet).
2. Run benchmark script with both pipelines on the same 5–10 sample set.
3. Inspect outputs. If IndicF5 wins: proceed to CLI swap. If not: stop and investigate.
4. Only after benchmark confirmation: update `cli.py` to call `tts_indicf5` instead of `tts_sarvam` + `tone_transfer`.

---

## Suggested Build Order

| Step | What | Why |
|------|------|-----|
| 1 | Create `pipeline/tts_indicf5.py` | Isolated module, no CLI impact, testable independently |
| 2 | Write `tests/test_tts_indicf5.py` | Required by project conventions; mock the heavy model for unit tests |
| 3 | Create `benchmarks/compare_pipelines.py` | Run old + new side by side before touching production CLI |
| 4 | Run benchmarks manually, review output WAVs | Confirm quality improvement is real |
| 5 | Update `cli.py`: swap imports, add Whisper ref-text auto-fill, add `--ref-text` flag | Smallest possible CLI change |
| 6 | Remove `tts_sarvam.py`, `models/tone_transfer.py`, `openvoice/` bundle | Only after CLI is confirmed working |
| 7 | Add `pipeline/encodec_postprocess.py` + `--postprocess` flag | Additive; do not block on it |
| 8 | Update `pyproject.toml`: add `indicf5` dep, remove `sarvamai`, pin `transformers==4.49.0` | Dependency hygiene last, after code is stable |

---

## Pitfalls Specific to This Integration

### Garbled output (HIGH severity)
Community reports (HF discussion #25) show IndicF5 producing random gibberish on some runs. Root cause is unclear — possibly seed non-determinism or incorrect reference conditioning. Mitigation: run each sample 3 times in the benchmark; flag instability. If garbled rate is >10%, block the swap.

### Transformers version pin conflict (MEDIUM severity)
`transformers==4.49.0` is required. If other dependencies in `pyproject.toml` pull a newer version, there will be silent breakage. Pin explicitly and test with a fresh `uv sync`.

### Apple Silicon (MPS) ISTFT crash (MEDIUM severity)
Discussion #22 confirms IndicF5 crashes on M4 Mac with a vocoder ISTFT error. Fall back to CPU explicitly when `mps` is detected until this is fixed upstream. Device selection logic in the new module: `cuda > cpu` (skip MPS).

### ref_text language mismatch (LOW severity)
In the `translate` command, the reference audio is English speech but the target text is Indic. IndicF5 conditions on acoustic features of the reference, not on text semantics — the English transcript as `ref_text` is correct and expected. Document this explicitly to avoid future confusion.

### No `language_code` parameter — language is script-implicit (LOW severity)
There is no explicit language selector. If a user passes Latin-script text (e.g., transliterated Hindi), the model may behave unexpectedly. The CLI should accept only Unicode-script Indic text; the translator already outputs proper Unicode so this is not an issue in the normal flow.

### Model weight size (INFORMATIONAL)
IndicF5 is ~1.4 GB (safetensors F32). Auto-downloads to HF cache. This replaces the OpenVoice ~500 MB checkpoint. Net increase: ~900 MB. Document in README.

---

## Dependency Changes

**Add:**
- `git+https://github.com/ai4bharat/IndicF5.git` (or PyPI package if published)
- `transformers==4.49.0` (pin; required for model loading)
- `soundfile` (already present for audio I/O)
- `numpy` (already present)

**Remove (after benchmark confirms swap):**
- `sarvamai` SDK
- `python-dotenv` (only needed for `SARVAM_AI_API`; remove if no other env vars remain)
- OpenVoice bundled library (`src/indic_voice/openvoice/` directory)
- `checkpoint_manager.py` (or repurpose for IndicF5 if custom cache logic is needed)

**No longer required after swap:**
- `SARVAM_AI_API` environment variable
- `.env` file (unless other secrets are added)

---

*Research date: 2026-04-15. IndicF5 model card HIGH confidence. Inference internals (model.py) MEDIUM confidence — file is gated behind HF auth, behavior inferred from public README and community discussion.*
