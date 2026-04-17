# Feature Landscape: Indic Voice Cloning Quality Improvement (v1)

**Domain:** Zero-shot Indic voice cloning CLI
**Researched:** 2026-04-15
**Milestone context:** Subsequent milestone — `clone` and `translate` commands already work end-to-end. Goal is quality improvement by replacing Sarvam AI + OpenVoice v2 with IndicF5.

---

## Research Findings (Inline)

Answers to the six specific research questions, sourced before categorization.

### Q1. Minimum reference audio length for zero-shot cloning with IndicF5

**Finding: 5–15 seconds. Treat 10 seconds as the practical minimum.**

IndicF5 inherits its architecture from F5-TTS (SWivid/F5-TTS). The upstream F5-TTS documentation specifies:

- Reference audio is **hard-clipped to ~12 seconds** at inference time. Audio longer than 12 seconds is silently truncated — the model never sees the tail.
- The recommendation is **"use reference audio under 12 seconds, with ~1 second of silence at the end"** to avoid mid-word truncation at the clip boundary.
- The prompt audio files bundled in the IndicF5 HuggingFace repository (`PAN_F_HAPPY_00001.wav`, `MAR_F_HAPPY_00001.wav`) are estimated at 14–25 seconds by file size at 16-bit/16kHz — the longer file would be clipped to 12 s. The shorter file is within range.
- Fish Audio S2 (a comparable architecture) specifies 10–30 seconds as the usable range, consistent with F5-family behaviour.
- Tortoise-TTS (different architecture) targets ~10 second clips at 22.05 kHz as its canonical reference length.

**Practical guidance for CLI:**
- Minimum: 3–5 seconds produces a voice embedding but quality degrades.
- Sweet spot: **8–12 seconds**, clean speech, minimal background noise.
- Maximum: 12 seconds (anything longer is silently clipped — users must know this).
- The current `clone` CLI doc says "3-second reference voice" — this is too short for IndicF5 and must be updated.

Confidence: MEDIUM. Upstream F5-TTS docs are authoritative on the 12s clip behaviour. IndicF5-specific minimum is inferred from F5 architecture + bundled prompt file sizes; not explicitly documented in IndicF5 model card.

---

### Q2. Does IndicF5 require the transcript of the reference audio?

**Finding: Yes. The transcript is a mandatory third input.**

IndicF5 requires three inputs at inference time:
1. Text to synthesize (the target utterance).
2. `ref_audio_path` — path to a WAV of the reference speaker.
3. `ref_text` — the verbatim transcript of whatever was spoken in the reference audio.

```python
audio = model(
    "नमस्ते! संगीत की तरह जीवन भी खूबसूरत होता है...",
    ref_audio_path="prompts/PAN_F_HAPPY_00001.wav",
    ref_text="ਭਹੰਪੀ ਵਿੱਚ ਸਮਾਰਕਾਂ ਦੇ ਭਵਨ ਨਿਰਮਾਣ ਕਲਾ...",
)
```

The upstream F5-TTS notes that passing `--ref_text ""` causes an ASR model to auto-transcribe the reference audio (at extra GPU memory cost). Whether IndicF5 exposes this escape hatch is not documented in the public model card.

**CLI implication:** The `--ref-voice` flag is insufficient. Users must also supply `--ref-text` (transcript of their reference clip). This is a **new required flag** when IndicF5 is integrated. The UX story is: "Record yourself saying a sentence, provide both the audio and what you said."

Confidence: HIGH. Documented directly in the IndicF5 HuggingFace model card with code example.

---

### Q3. Language coverage — IndicF5 vs Indic Parler-TTS

| Language | IndicF5 | Indic Parler-TTS | Notes |
|----------|---------|-----------------|-------|
| Hindi | Yes | Yes | Both strong |
| Bengali | Yes | Yes | Both supported |
| Tamil | Yes | Yes | Both supported |
| Telugu | Yes | Yes | Both supported |
| Kannada | Yes | Yes | Both supported |
| Malayalam | Yes | Yes | Both supported |
| Marathi | Yes | Yes | Both supported |
| Gujarati | Yes | Yes | Both supported |
| Odia | Yes | Yes | Both supported |
| Punjabi | Yes | Yes (unofficial) | IndicF5 official; Parler unofficial |
| Assamese | Yes | Yes | Both supported |
| Bodo | No | Yes | Parler only |
| Dogri | No | Yes | Parler only |
| Konkani | No | Yes | Parler only |
| Maithili | No | Yes | Parler only |
| Manipuri | No | Yes | Parler only |
| Nepali | No | Yes | Parler only |
| Sanskrit | No | Yes | Parler only |
| Santali | No | Yes | Parler only |
| Sindhi | No | Yes | Parler only |
| Urdu | No | Yes | Parler only |
| English | No | Yes | Parler includes English |

**Summary:**
- IndicF5: 11 languages. All are mainstream Indic languages (spoken by ~1.3B+ people). No English.
- Indic Parler-TTS: 21 languages including English, plus 3 unofficial. Covers tribal/minority languages (Bodo, Santali, Manipuri) that IndicF5 does not.

**Critical difference beyond language count:** IndicF5 does genuine zero-shot voice cloning from a reference speaker. Indic Parler-TTS uses 69 pre-trained named voices and cannot clone an arbitrary speaker — it accepts a text description of voice style, not a reference audio clip. These are fundamentally different tasks. Parler-TTS is not a competitor for voice cloning; it is relevant only as a baseline TTS for naturalness comparison.

Confidence: HIGH for both model cards; both confirmed via HuggingFace model pages.

---

### Q4. Quality metrics for voice cloning evaluation

Three metrics are standard in the voice cloning literature (confirmed via F5-TTS eval harness):

**WER (Word Error Rate)**
- What: Transcribe the generated audio with Whisper/ASR, compare to the target text.
- Why: Measures intelligibility and content fidelity. A cloned voice that sounds right but garbles words is useless.
- Tool: `faster-whisper` (already in this project's stack). For Indic languages, `ai4bharat/indicwav2vec` or `ai4bharat/indic-conformer` are more accurate ASR systems than English Whisper.
- Target: WER under 5% for Hindi/Tamil/Telugu on clean test sentences.

**Speaker Similarity (SIM)**
- What: Cosine similarity between speaker embeddings of the reference audio and the generated audio.
- Why: Measures whether the clone actually sounds like the target speaker.
- Tool: `microsoft/wavlm-base-plus-sv` (WavLM speaker verification model). Extract embeddings from both clips, compute cosine similarity. Threshold ~0.86 for "same speaker".
- Outputs a score in [−1, 1]; higher is more similar. Voice cloning papers typically report mean SIM over a test set.

**UTMOS (Unified Text-to-Speech MOS Score)**
- What: An automated neural predictor of Mean Opinion Score (MOS), trained to predict human naturalness ratings on a 1–5 scale.
- Why: Proxy for "does this sound natural?" without needing human raters. The F5-TTS eval harness uses UTMOS as their automated naturalness metric.
- Tool: `sarulab-speech/UTMOS22` (strong variant). Outputs a predicted MOS score 1–5.
- Limitation: UTMOS was trained primarily on English TTS. Its calibration on Indic languages is unknown — treat absolute scores with caution, but relative comparisons (IndicF5 vs Sarvam+OpenVoice) on the same test set are still valid.

**The F5-TTS eval harness** (confirmed from repo) structures evaluation as:
1. Batch inference: generate audio for a fixed test set of (text, reference audio, reference transcript) triples.
2. WER: run ASR on all generated files, compare to reference transcripts.
3. SIM: run WavLM embeddings on (reference, generated) pairs, compute cosine similarity.
4. UTMOS: run MOS predictor on all generated files, report mean.
5. Output: results compiled to `.jsonl` files per model, then compared side-by-side.

For this project's benchmark (IndicF5 vs Sarvam+OpenVoice), add a fourth metric:

**RTF (Real-Time Factor)**
- What: `inference_time_seconds / audio_duration_seconds`. RTF < 1.0 means faster than real time.
- Why: Practical usability. If IndicF5 takes 3x longer than Sarvam+OpenVoice on CPU, that's a quality-vs-latency tradeoff users need to know about.

Confidence: HIGH for WER and SIM (confirmed in F5-TTS eval docs and WavLM model card). MEDIUM for UTMOS (F5-TTS uses it, but its Indic calibration is unknown).

---

### Q5. Anti-features common in open-source voice cloning tools

Based on patterns across F5-TTS, Tortoise-TTS, OpenVoice, and IndicF5 community discussions:

**Silent truncation of reference audio**
F5-TTS clips reference audio to 12 seconds without warning. Users providing a 30-second clip get degraded quality with no error message. Mitigation: validate and warn before inference.

**Mandatory transcript without auto-fallback**
IndicF5 requires a reference audio transcript. If the user does not have it, there is no documented fallback. In contrast, F5-TTS CLI has `--ref_text ""` to trigger auto-ASR. Forcing users to manually transcribe their reference clip is a significant friction point.

**Brittle local model paths**
The current project already has this: `../faster_whisper_medium` is a cwd-relative path. Breaks whenever the CLI is run from a different directory. Common in research-code-turned-CLI tools.

**Opaque first-run experience**
Large checkpoint downloads (500 MB to 1.5 GB) happen silently or crash mid-download with no progress bar. Users see nothing for 2–5 minutes and assume the process is broken.

**Undocumented hardware requirements**
OpenVoice and IndicF5 work on CPU but are 5–20x slower. Tools rarely document the expected inference time on CPU vs GPU. Users on laptops are surprised by 2-minute waits for a 5-second clip.

**`processed/` directory pollution**
OpenVoice's `se_extractor.py` writes intermediate audio segments to `./processed/` and never cleans up. Multiple runs accumulate hundreds of files in the user's working directory.

**Hard-coded speakers/parameters**
Current project hardcodes `speaker="meera"` (now `"ritu"`) and `tau=0.3`. Users cannot experiment without editing source code.

**Unhelpful error messages on model failures**
Raw Python tracebacks from model loading errors (e.g., transformers version mismatches) surfaced directly to users. IndicF5 community discussions show frequent "meta tensor" errors and "transformers 5.0.0 incompatibility" issues with no guidance.

**No input validation**
If a user passes an MP3 or a corrupted WAV, the failure happens deep in the model stack with an inscrutable error, not at the CLI input validation layer.

Confidence: HIGH for project-specific issues (confirmed in codebase). MEDIUM for general OSS patterns (confirmed via IndicF5 discussion page and F5-TTS docs).

---

### Q6. What a benchmark harness for voice cloning looks like

**Standard structure (confirmed from F5-TTS eval harness):**

```
benchmark/
  test_cases.json          # list of {id, text, ref_audio, ref_text, language}
  reference_audio/         # 10–20 reference clips, 1 per speaker, 8–12 s each
  generate.py              # runs each model on all test cases, writes generated/
  generated/
    indicf5/               # output WAVs from IndicF5
    sarvam_openvoice/      # output WAVs from current pipeline
  eval_wer.py              # ASR all generated files, output WER per file and mean
  eval_sim.py              # WavLM cosine sim between ref and generated, per file
  eval_utmos.py            # UTMOS predictor scores, per file
  eval_rtf.py              # measure wall-clock inference time per file
  results/
    indicf5_results.jsonl
    sarvam_openvoice_results.jsonl
  compare.py               # side-by-side table: mean WER, SIM, UTMOS, RTF
```

**Test set design for this project:**
- 5–10 reference speakers (diverse: male/female, different Indic languages).
- 3–5 test sentences per language (Hi, Ta, Te as primary; Kn, Bn, Mr as secondary).
- Reference audio: clean, single-speaker, 8–12 seconds, with transcript.
- Test sentences: drawn from a fixed set so results are reproducible across runs.

**Side-by-side eval output:**

| Metric | Sarvam + OpenVoice | IndicF5 | Delta |
|--------|-------------------|---------|-------|
| WER (Hindi) | X% | Y% | ... |
| SIM (cosine) | X | Y | ... |
| UTMOS | X | Y | ... |
| RTF (CPU) | X | Y | ... |

**Important:** the WER evaluator for Indic must use an Indic-capable ASR model. Using English Whisper to evaluate Hindi output will produce inflated WER because English Whisper transliterates rather than transcribes Devanagari. Use `faster-whisper` with the `large-v3` model, which has reasonable Hindi support, or `ai4bharat/indicwav2vec`.

Confidence: HIGH for harness structure (confirmed from F5-TTS repo). MEDIUM for Indic-specific ASR guidance (known limitation of English Whisper on Indic scripts, confirmed from general knowledge).

---

## Table Stakes

Features users expect from any voice cloning tool. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Zero-shot cloning from a short reference clip | Core product promise | Med | IndicF5 does this natively; current pipeline approximates it |
| Reference audio length validation and warning | Prevents silent degradation | Low | F5-TTS clips silently at 12s; must warn user |
| Clear error messages on model load failures | OSS tools routinely fail on env mismatches | Low | Community reports transformers version errors |
| Progress indicator on first-run checkpoint download | Downloads are 400–600 MB; users assume hang | Low | Rich progress bar already in stack |
| Input file validation (format, existence) before inference | Prevents deep-stack crashes | Low | Check file exists, is WAV/acceptable format at CLI layer |
| RTF transparency (warn when CPU inference will be slow) | Users on laptops need to know | Low | Simple: detect CPU, print estimated time |
| Support Hindi, Tamil, Telugu | Three largest Indic language communities | Already done | IndicF5 covers all three |
| Clean output — no leftover temp files | `processed/` directory pollution is a known anti-feature | Low | Context manager or explicit cleanup |
| Stable CLI flags across model swaps | Existing users must not be broken | Low | PROJECT.md constraint: `--ref-voice`, `--text`, etc. unchanged |

---

## Differentiators

Features that set this tool apart. Not universally expected, but meaningfully valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Native Indic phonetics and prosody | ElevenLabs supports Indic but is not specialized; IndicF5 is trained on 1417h Indic data | Foundational | This is the entire migration rationale |
| Transcript auto-detection for reference audio | Removes the biggest UX friction of IndicF5: users should not need to type out what they said | Med | Run Whisper on ref_audio to generate ref_text if user omits --ref-text; explicitly flag this as "auto-transcribe mode" |
| Built-in benchmark comparison mode | `indic-voice benchmark` command that runs both pipelines and prints a quality table | High | Supports the project's active requirement to benchmark before swapping |
| EnCodec artifact removal (post-IndicF5) | Smooth residual synthesis artifacts via Meta's EnCodec encode→decode pass | High | Scope: after IndicF5 standalone is validated (PROJECT.md) |
| Language auto-detection from reference audio | User provides audio; tool infers the Indic language without `--target-lang` | Med | Useful for `translate` command; reduces required flags |
| Explicit speaker-language pairing in CLI help | Show users which languages are supported and which example sentences work well | Low | Documentation feature; reduces setup friction |

---

## Anti-Features

Things to deliberately NOT build, and patterns to actively avoid.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Silent reference audio truncation | F5-TTS clips at 12s without warning; users think they provided 30s but only 12s was used | Validate audio length at CLI input; print warning if >12s and note the clip boundary |
| Mandatory --ref-text without auto-fallback | Transcript requirement is the #1 friction point; no escape hatch forces manual transcription | Auto-transcribe ref_audio with Whisper if --ref-text is omitted; show transcript so user can correct it |
| Cwd-relative model paths | `../faster_whisper_medium` breaks when CLI is run from any directory other than one specific location | Always resolve to `~/.cache/indic-voice/` or use HuggingFace cache; never relative paths |
| Downloading models without progress | Large downloads appear as hangs; first-run abandonment | Use Rich progress or `tqdm` with a download hook |
| Exposing raw Python tracebacks to users | Research-grade error messages destroy CLI UX | Catch at CLI boundary; map known errors (transformers version, CUDA OOM, missing model files) to plain-English messages |
| Processing/temp files left in working directory | `processed/` accumulates silently; users find mystery files | Use `tempfile.mkdtemp()` scoped to a context manager; clean on success and failure |
| Hard-coded speaker identity | `speaker="ritu"` means all users get the same voice for the TTS stage, defeating cloning | Expose `--tts-speaker` flag (or remove Sarvam entirely with IndicF5, which makes this moot) |
| GPU-only framing | Claiming GPU is required when CPU works (slowly) | Always support CPU; document expected inference times: "~45s on CPU, ~5s on GPU" |
| Web UI, streaming, or REST API scope creep | Dilutes CLI simplicity; PROJECT.md explicitly excludes these | Maintain CLI-only surface; no Flask/FastAPI, no websockets, no real-time mode |
| Per-user fine-tuning | Scope creep; zero-shot is sufficient and the project differentiator | If quality is insufficient, improve zero-shot reference audio quality, not training |

---

## Benchmark Criteria

How quality improvement will be measured for the IndicF5 migration.

### Metrics

| Metric | Tool | What It Measures | Target |
|--------|------|-----------------|--------|
| WER | `faster-whisper large-v3` transcribing generated audio | Intelligibility — does the speech say the right words? | <5% for Hindi on clean test set |
| Speaker Similarity (SIM) | `microsoft/wavlm-base-plus-sv` cosine similarity | Does it sound like the reference speaker? | >0.75 mean cosine similarity |
| UTMOS | `sarulab-speech/UTMOS22` | Automated naturalness proxy (1–5 MOS scale) | >3.5 mean predicted MOS |
| RTF (Real-Time Factor) | Wall-clock inference time / generated audio duration | Practical speed | Report only; no hard requirement |

### Benchmark Test Set Design

- **Reference speakers:** 8–10 clips (mix of male/female voices, different Indic language backgrounds).
- **Reference audio spec:** 8–12 seconds, clean single-speaker speech, with transcript.
- **Test sentences:** 5 per language for Hindi, Tamil, Telugu (primary); 3 each for Kannada, Bengali, Marathi (secondary). Use fixed sentences from AI4Bharat's IndicTTS evaluation set where available.
- **Comparison pairs:** Each (reference audio, target text) pair run through both pipelines. Results are paired — same input, different pipeline.

### Harness Structure

```
benchmark/
  test_cases.json           # {id, text, ref_audio, ref_text, language}
  reference_audio/          # 8-12s WAV clips with transcripts
  run_pipeline.py           # generate audio for each model
  generated/
    indicf5/
    sarvam_openvoice/
  eval/
    wer.py                  # faster-whisper ASR → WER
    sim.py                  # WavLM cosine similarity
    utmos.py                # UTMOS22 MOS prediction
    rtf.py                  # timing measurement
  results/
    indicf5.jsonl
    sarvam_openvoice.jsonl
  compare.py                # prints side-by-side table
```

### Interpretation Rules

- IndicF5 is accepted if WER improves AND SIM improves on the primary languages (Hindi, Tamil, Telugu), even if UTMOS is neutral.
- If IndicF5 is slower by more than 3x RTF on CPU, document it clearly but do not use it as a veto — quality improvement is the primary goal.
- EnCodec post-processing is evaluated separately after IndicF5 is accepted as baseline.

### Indic ASR Caveat

English Whisper transcribes Hindi in Roman transliteration, not Devanagari. WER computed in transliteration is unreliable. Use `faster-whisper large-v3` which has better multilingual coverage, or cross-check with `ai4bharat/indicwav2vec`. This is a known pitfall in Indic TTS evaluation.

---

## Feature Dependencies

```
Reference audio validation → IndicF5 integration (validation must ship before users use the new --ref-text flag)
Auto-transcribe ref_audio → IndicF5 integration (parallel; reduces UX friction of new required input)
Benchmark harness → IndicF5 swap decision (benchmark results gate the migration per PROJECT.md)
IndicF5 standalone validation → EnCodec post-processing (EnCodec is additive, not foundational)
```

---

## MVP Recommendation for This Milestone

**Prioritize:**
1. Reference audio validation + user-facing length guidance (table stakes, low complexity, directly fixes known silent truncation anti-feature).
2. Auto-transcribe mode for `--ref-text` using existing Whisper pipeline (differentiator, removes the single largest UX friction point IndicF5 introduces).
3. Benchmark harness: WER + SIM metrics, 5-speaker test set, Hindi-first (required before the swap per PROJECT.md).

**Defer:**
- UTMOS integration: adds a large model dependency for marginal signal; use WER + SIM for the initial gate decision.
- Language auto-detection: useful but not required for the quality-improvement goal.
- EnCodec: explicitly deferred in PROJECT.md until IndicF5 standalone is validated.

---

## Sources

- IndicF5 model card: https://huggingface.co/ai4bharat/IndicF5 (HIGH confidence)
- Indic Parler-TTS model card: https://huggingface.co/ai4bharat/indic-parler-tts (HIGH confidence)
- F5-TTS inference docs: https://raw.githubusercontent.com/SWivid/F5-TTS/main/src/f5_tts/infer/README.md (HIGH confidence — reference audio 12s clip behaviour confirmed)
- F5-TTS eval harness: https://raw.githubusercontent.com/SWivid/F5-TTS/main/src/f5_tts/eval/README.md (HIGH confidence — WER/SIM/UTMOS metric structure confirmed)
- WavLM speaker verification: https://huggingface.co/microsoft/wavlm-base-plus-sv (HIGH confidence — cosine similarity embedding approach confirmed)
- Fish Audio S2: https://raw.githubusercontent.com/fishaudio/fish-speech/main/README.md (MEDIUM confidence — 10–30s reference audio range, corroborating evidence)
- Tortoise-TTS source: https://raw.githubusercontent.com/neonbjb/tortoise-tts/main/tortoise/api.py (MEDIUM confidence — ~10s reference audio at 22.05kHz confirmed in code)
- IndicF5 community discussions (HuggingFace): transformers version errors, meta tensor issues — MEDIUM confidence (community-reported, not officially documented)
