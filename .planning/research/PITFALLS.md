# Domain Pitfalls: IndicF5 Integration

**Domain:** Indic voice cloning CLI — replacing Sarvam AI TTS + OpenVoice v2 with IndicF5
**Researched:** 2026-04-15
**Confidence:** MEDIUM-HIGH (IndicF5 community discussions verified; F5-TTS upstream source code
verified; EnCodec official docs verified; some CPU/GPU numbers are estimates)

---

## Critical Pitfalls

These mistakes cause silent failures, broken audio output, or integration blockers.

---

### Pitfall 1: Meta Tensor Device Move Error Breaks Model Loading

**What goes wrong:**
`AutoModel.from_pretrained("ai4bharat/IndicF5", trust_remote_code=True)` succeeds but any
subsequent `.to(device)` call throws:

```
NotImplementedError: Cannot copy out of meta tensor; no data!
Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to()
when moving module from meta to a different device.
```

This error is triggered by the vocoder loading step inside `model.py`:
```python
vocoder = vocoder.eval().to(device)  # breaks with meta tensors
```

**Why it happens:**
`transformers >= 4.51` changed how meta tensors are initialized. The IndicF5 `model.py` was
written against `transformers==4.49.x` / `4.50.x`. Newer versions initialize weights lazily
on the "meta" device and require `to_empty()` instead of `to()` before loading state dicts.
This is confirmed in HF discussions #11, #12, #13, #14 with multiple affected users.

**Warning signs:**
- Works in a fresh conda env on `transformers==4.49.0` but fails after `uv sync` pulls latest
- The error appears in the vocoder init, not the main model — easy to misdiagnose
- Silent on import; only fails when `.to(device)` is called at inference time

**Prevention:**
Pin `transformers` to a confirmed-working version. Community consensus (HF discussions #16, #20)
is `transformers==4.49.0`. The alternative fix is patching `model.py` to use `to_empty()`:
```python
# instead of:  vocoder = vocoder.eval().to(device)
# use:
vocoder = vocoder.eval().to_empty(device=device)
```
Add a PR against AI4Bharat's repo if you patch this locally — the fix is pending merge (#33).

**Which phase:** Phase 1 (IndicF5 integration) — must be resolved before any inference works.

---

### Pitfall 2: Reference Transcript Is Mandatory and Must Be Accurate

**What goes wrong:**
IndicF5 (via F5-TTS) requires the transcript of the reference audio as a third input alongside
the audio file. Missing it, passing an empty string, or passing a wrong transcript produces one
of three failure modes:
- Garbled/gibberish audio fragments (HF discussion #25, confirmed on Telugu, Hindi)
- Silent/empty output
- Output that drifts in style mid-sentence

**Why it happens:**
F5-TTS (which IndicF5 is built on) uses the reference transcript to align the reference audio's
mel-spectrogram with its text tokens. Without accurate alignment, the model's duration predictor
and style conditioning produce nonsense. The default sentinel value `"666"` is used when no
transcript is passed — this will produce garbage output.

The current `translate` command pipes the original English audio as the reference voice:
```python
morph_tone(tmp_tts, audio, output)  # audio = English source file
```
After the IndicF5 swap, the English audio's transcript (already computed by Whisper in Step 1)
must be passed as `ref_text`. If omitted, IndicF5 will auto-call `whisper-large-v3-turbo` to
transcribe it — adding latency and a new dependency, plus Whisper may transcribe English into
the wrong language if the audio is short.

**Warning signs:**
- Output audio sounds robotic, garbled, or wrong language
- Output varies between runs on identical input (nondeterministic behavior from bad alignment)
- Inference takes longer than expected (auto-Whisper transcription running in background)

**Prevention:**
- Always pass `ref_text` explicitly. For the `translate` command, reuse `en_text` from Step 1
  (Whisper already produced it — pass it directly to IndicF5 as the reference transcript)
- For the `clone` command, users must provide a reference transcript alongside `--ref-voice`
  (new required flag, or auto-transcribe it with the existing Whisper ASR stage)
- Validate that `ref_text` is non-empty and does not equal `"666"` before calling the model

**Which phase:** Phase 1 (IndicF5 integration) — affects both `clone` and `translate` commands.

---

### Pitfall 3: Reference Audio Length Limit (12 Seconds, Effective Cap ~6s)

**What goes wrong:**
F5-TTS (and by inheritance IndicF5) hard-clips reference audio at 12 seconds via silence
detection. But the total generation budget is ~25-30 seconds including both reference and
generated audio. Using a 10-12 second reference leaves only ~15 seconds for the generated
speech — very short for a translation task.

Community guidance from HF discussion #16 recommends keeping reference audio at **6 seconds
or less** to leave headroom for generation. Feeding a 30-second interview clip as reference
produces clipped, truncated output without any error message.

**Why it happens:**
The model calculates output duration as:
`ref_audio_len + (ref_audio_len / ref_text_len) * gen_text_len / speed`
Reference audio length directly eats into the generation budget. The 12-second clipping is
automatic but silent — users see no warning, just truncated output.

**Warning signs:**
- Output audio gets cut off before the text finishes
- No error is raised — output file is written successfully but is short
- Happens silently when users pass long reference recordings (interviews, conversations)

**Prevention:**
- Validate reference audio duration at CLI entry; reject or trim to <6 seconds with a warning
- Document 5-10s as the optimal reference length in help text and README
- Add `1 second of silence at start and end` when trimming (prevents word truncation at edges)
- If users pass a long recording, trim to the first 6 seconds automatically with a rich warning

**Which phase:** Phase 1 (IndicF5 integration) — add duration validation in the new TTS wrapper.

---

### Pitfall 4: Reference Audio Sample Rate Must Be 24 kHz (Or Will Be Silently Resampled)

**What goes wrong:**
IndicF5 operates at 24 kHz. F5-TTS `utils_infer.py` resamples reference audio automatically
using `torchaudio.transforms.Resample()` if `sr != 24000`. This sounds safe — but resampling
noisy or compressed audio (e.g., 8 kHz phone audio, 44.1 kHz music with reverb) introduces
artifacts that corrupt the speaker embedding extraction, degrading voice cloning quality
significantly.

The Sarvam TTS output is 22.05 kHz. The existing `morph_tone` OpenVoice pipeline handles
this. After the swap, if any intermediate audio file is not at 24 kHz, silent resampling
will happen inside IndicF5 — potentially degrading the reference speaker characteristics.

**Why it happens:**
The auto-resampling path exists for convenience but does not validate audio quality. Low-
bitrate or noisy source audio resampled to 24 kHz amplifies compression artifacts.

**Warning signs:**
- Voice cloning output sounds like the reference speaker with added buzz or hiss
- Quality degrades noticeably on phone-recorded reference audio vs. studio recordings
- Output quality is inconsistent across different reference audio sources

**Prevention:**
- Use `soundfile` to check the sample rate of reference audio at input validation time
- If `sr != 24000`, resample explicitly with `librosa.resample(y, orig_sr=sr, target_sr=24000)`
  using `res_type='kaiser_best'` before passing to IndicF5 (better quality than default)
- Document that reference audio should be 24 kHz, 16-bit, mono WAV for best results
- Reject reference audio below 16 kHz or with obvious clipping (peak amplitude > 0.98)

**Which phase:** Phase 1 (IndicF5 integration) — add reference audio validation helper.

---

### Pitfall 5: `torch.compile()` Breaks on Windows (Vocoder Loading)

**What goes wrong:**
The original `model.py` wraps the vocoder in `torch.compile()`:
```python
self.vocoder = torch.compile(load_vocoder(...))
```
This raises `RuntimeError: Windows not yet supported for torch.compile` on Windows.
The fix (HF discussion #21, PR not yet merged) removes the `torch.compile()` wrapper.

**Why it matters for this project:**
The CLI is open-source and the README must promise cross-platform support. If contributors
or users run on Windows, the model fails at load time before any inference. This is a
silent blocker for contributors who do not read the GitHub issues.

**Warning signs:**
- `RuntimeError: Windows not yet supported for torch.compile` in the traceback
- Works on macOS/Linux, fails only on Windows

**Prevention:**
- When vendoring or pinning IndicF5's `model.py`, apply the `torch.compile()` removal patch
- Or conditionally skip compilation: `vocoder = load_vocoder(...)` without `torch.compile()`
- Test CI on a Windows runner; the error is deterministic and immediate

**Which phase:** Phase 1 (IndicF5 integration) — patch before shipping; add Windows CI check.

---

### Pitfall 6: Apple Silicon (M4) ISTFT Compatibility Failure

**What goes wrong:**
IndicF5 with the `vocos` vocoder fails on Apple Silicon M4 Macs with:
```
RuntimeError: istft(...) window overlap add min: 1 [CPUBoolType{}]
```
The issue is in the `vocos` library's ISTFT spectral operation and is architecture-specific
to ARM64 (Apple Silicon). M1/M2/M3 compatibility status is unknown. Intel Mac works.

**Why it matters:**
macOS on Apple Silicon is a primary developer platform. An open-source CLI that silently fails
on M4 Macs (a mainstream machine since mid-2024) is a significant adoption blocker.

**Warning signs:**
- The error occurs in the vocoder decode step, after inference completes — audio is never written
- Error is device-specific; exact same code works on Intel Mac and Linux
- No workaround confirmed yet (HF discussion #22 open as of Oct 2025)

**Prevention:**
- Test on Apple Silicon during Phase 1 before announcing IndicF5 support
- If unresolved, add a platform check with a clear error message rather than a traceback:
  ```python
  import platform
  if platform.processor() == 'arm' and platform.system() == 'Darwin':
      console.print("[yellow]Warning: IndicF5 vocoder has known issues on Apple Silicon M4.[/yellow]")
  ```
- Watch for vocos library updates or PyTorch MPS fixes for ARM64 ISTFT

**Which phase:** Phase 1 (IndicF5 integration) — validate on Apple Silicon before release.

---

## Moderate Pitfalls

These cause degraded quality or confusing behavior, but do not break the pipeline entirely.

---

### Pitfall 7: Transformers Version Pinning Creates Dependency Conflicts With Existing Stack

**What goes wrong:**
IndicF5 needs `transformers==4.49.0`. The existing `indic-voice-cli` stack uses `faster-whisper`,
`sarvamai` SDK, and `huggingface-hub` — all of which express their own `transformers` version
constraints. Pinning to `4.49.0` for IndicF5 can silently downgrade or conflict with other
packages, breaking Whisper or the Sarvam SDK.

The confirmed-working dependency set from HF discussion #16 is very specific:
```
torch==2.2.0, transformers==4.49.0, accelerate==0.33.0, soundfile==0.12.1,
safetensors==0.4.3, huggingface_hub==0.29.0, scipy==1.13.0, numpy==1.26.4
```

**Warning signs:**
- `uv sync` installs without error but inference crashes with unexpected AttributeErrors
- Whisper transcription breaks after adding IndicF5 dependency
- `uv.lock` diff shows unexpected downgrades to multiple packages

**Prevention:**
- Run `uv add` for IndicF5 in a test branch and inspect the full lock diff before committing
- If `transformers==4.49.0` conflicts, test each version up to `4.50.3` (also reported working)
- Prefer `transformers>=4.49.0,<4.51.0` constraint with `uv.lock` pin rather than exact pin
- Maintain a separate `test_imports.py` that instantiates every pipeline stage after dependency
  changes to catch silent breakage

**Which phase:** Phase 1 (IndicF5 integration) — validate lock file before merging.

---

### Pitfall 8: Generation Budget Exhaustion Silently Truncates Long Translations

**What goes wrong:**
F5-TTS (and IndicF5) has a ~25-30 second combined generation budget (reference audio + output).
Long Indic text (e.g., a paragraph translation of a 20-second English audio) may exceed this.
The model silently truncates output — the WAV file is written, shorter than expected, with no
error raised. The CLI reports "Success!" even though the audio is incomplete.

Text chunking is handled automatically in CLI mode but requires FFmpeg for cross-fade blending
between chunks. Missing FFmpeg produces silent output (no audio at all) with no error message.

**Warning signs:**
- Output audio is shorter than the source speech duration
- Translation of long English input produces clipped Indic output
- Empty WAV files written on Linux systems without FFmpeg

**Prevention:**
- Check FFmpeg availability at CLI startup with a clear error if missing
- Implement explicit text chunking: split translated text at sentence boundaries before
  passing to IndicF5, then concatenate output audio with `pydub`
- Warn the user if `len(translated_text) > 300 characters` that chunking will occur
- Add an integration test with a 30-second input audio to catch this scenario

**Which phase:** Phase 2 (multi-language support and polish) — not a blocker for initial
integration, but must be addressed before open-source release.

---

### Pitfall 9: Model Is Gated on Hugging Face — Trust-Remote-Code Required

**What goes wrong:**
`ai4bharat/IndicF5` is a gated model requiring HF account login and contact-sharing agreement.
Additionally, `AutoModel.from_pretrained(..., trust_remote_code=True)` is required because
the model uses custom Python code in `model.py` (not a standard HF architecture).

`trust_remote_code=True` executes arbitrary code from the HF repo. This is a security concern
for open-source users, and a setup friction point for new contributors.

**Why it matters:**
- First-run setup requires HF CLI login (`huggingface-cli login`) — must be documented clearly
- `trust_remote_code=True` is a security footgun; contributors who read this in the code may
  file security concerns
- The gating means automated CI/CD on forks will fail unless a HF token is in the environment

**Warning signs:**
- `OSError: ai4bharat/IndicF5 is not a local folder and is not a valid model identifier`
  on first run without HF login
- CI pipeline fails with authentication error on contributor forks

**Prevention:**
- Add explicit HF login check at startup with a user-friendly message and link to setup docs
- Document `huggingface-cli login` as a setup prerequisite in README
- Store HF token as a CI secret; document this requirement for contributors
- Add a comment in the code explaining why `trust_remote_code=True` is necessary for this model

**Which phase:** Phase 1 (IndicF5 integration) — document in README before first commit.

---

### Pitfall 10: CPU Inference Is Very Slow — Not Just "Slower"

**What goes wrong:**
F5-TTS (IndicF5 base) uses a Conditional Flow Matching diffusion model with multiple ODE solver
steps. On CPU, generating 5 seconds of speech from a short text takes 60-180 seconds on a
modern laptop. The project constraint says "Works on CPU (slower)" — but users may abandon
the tool if 30-second English audio takes 10+ minutes to translate.

The benchmark data shows an L20 GPU achieving RTF ~0.04 (25x faster than real-time). CPU RTF
for a diffusion TTS model is typically 5-20x slower than real-time — 10 seconds of audio
takes 50-200 seconds on CPU. This is materially worse than the current OpenVoice pipeline.

**Warning signs:**
- Benchmark test on CPU shows RTF > 1.0 (slower than real-time)
- User testing reveals 5+ minute wait for a 30-second input translation

**Prevention:**
- Benchmark IndicF5 CPU performance early (Phase 1) against the current pipeline's CPU time
- If CPU time > 3x the current pipeline, add a `--device cpu` warning: "CPU inference may
  take several minutes for long audio. Use --device cuda for faster results."
- Reduce default NFE (number of function evaluations) for CPU: test NFE=8 vs NFE=32 for
  quality/speed tradeoff; F5-TTS supports `nfe_step` parameter
- Document realistic CPU timing expectations in README before open-source release

**Which phase:** Phase 1 (benchmark phase) — measure before deciding to swap.

---

### Pitfall 11: Language Code Format Mismatch — Short vs. BCP-47

**What goes wrong:**
The existing pipeline uses two different language code conventions that must be mapped when
replacing the TTS stage:

- Translator stage (`translator.py`) accepts 2-letter ISO codes: `"hi"`, `"ta"`, `"te"`
- Sarvam TTS (`tts_sarvam.py`) requires BCP-47 codes: `"hi-IN"`, `"ta-IN"`, `"te-IN"`
- IndicF5 does NOT use language codes as a model input parameter — language is inferred from
  the input text script, not from an explicit language argument

This means:
1. The current `lang_code` threading from CLI → TTS breaks with IndicF5 (no matching arg)
2. Passing the wrong script (e.g., sending Tamil text to a Hindi reference voice) may produce
   output that sounds like the right voice but wrong language, silently
3. The `translate` command's `--target-lang` flag must still drive the Translation stage but
   no longer needs to be passed to TTS

**Warning signs:**
- `TypeError: unexpected keyword argument 'language'` when adapting current TTS call signature
- CLI accepts `--target-lang ta` but output is in Hindi (language code not passed to translation)

**Prevention:**
- Remove `lang_code` from the new `generate_speech_indicf5()` function signature
- Validate that `translate()` is called with the correct target language before IndicF5 receives
  the translated text (the text itself carries the script information)
- Add an assertion in tests: Tamil input text produces Tamil phoneme output (measurable via ASR)

**Which phase:** Phase 1 (IndicF5 integration) — impacts CLI wiring and function signatures.

---

### Pitfall 12: Noisy or Multi-Speaker Reference Audio Degrades Cloning Quality

**What goes wrong:**
IndicF5 extracts speaker characteristics directly from the reference audio. Reference audio
with background music, multiple speakers, noise, or reverb produces a blended or corrupted
speaker embedding. The output audio adopts a mix of acoustic characteristics rather than
a clean voice profile. This is not an error — the model runs and outputs audio — it just
sounds wrong.

The existing OpenVoice pipeline had the same weakness, but OpenVoice's VAD (voice activity
detection) filtered some of this. IndicF5's F5-TTS base removes silence edges but does not
apply denoising or speaker diarization.

**Warning signs:**
- Reference audio with audible background noise produces robotic or blended-voice output
- Users report "it doesn't sound like me" when using phone recordings as reference

**Prevention:**
- Add a reference audio quality check: compute SNR estimate using `librosa.effects.split()`;
  warn if energy in non-speech segments > 10% of total energy
- Recommend (in CLI help text) clean, single-speaker recordings recorded in quiet environment
- Consider optional denoising with `noisereduce` library as a `--denoise-ref` flag (Phase 2)
- Document 5-10s of clean speech in quiet environment as the reference requirement

**Which phase:** Phase 1 (add validation); Phase 2 (add optional denoising).

---

## Benchmark Methodology Pitfalls

Specific to the "benchmark IndicF5 vs. Sarvam+OpenVoice" task in PROJECT.md.

---

### Pitfall 13: Evaluating on the Same Reference Audio Used for Training

**What goes wrong:**
IndicF5 is trained on Rasa, IndicTTS, IndicVoices-R datasets. If benchmark reference audio
comes from one of these datasets (or sounds similar), IndicF5 will appear to perform better
not because of zero-shot cloning ability but because it has seen similar voices during training.
This overfits the benchmark result.

**Prevention:**
- Use reference audio from completely out-of-distribution speakers (not professional Indian
  studio recordings — those overlap with training data)
- Use your own voice or recordings from contributors as reference audio
- Test at least 3-5 different reference speakers across different gender/age/accent profiles

**Which phase:** Phase 1 (benchmark phase) — set up before running any comparisons.

---

### Pitfall 14: Using WER on Indic Languages Without Indic ASR Models

**What goes wrong:**
The standard automated TTS quality metric is WER (Word Error Rate) via ASR transcription.
Using English Whisper to compute WER on Hindi or Telugu output produces meaningless scores
because Whisper's Indic ASR quality is much lower than its English quality, and character-
level word segmentation differs from English.

**Prevention:**
- Use subjective MOS (Mean Opinion Score) via manual listening from bilingual speakers for
  the primary quality metric
- For automated metrics, use IndicWhisper or a language-specific ASR (e.g., `vakyansh-wav2vec2`)
  that was trained on the target Indic language
- Measure Speaker Similarity (SIM) using WavLM cosine similarity between reference and output
  embeddings — this is language-agnostic and reliable
- Report metrics separately per language; averaged Indic quality masks per-language variance

**Which phase:** Phase 1 (benchmark phase).

---

### Pitfall 15: Cherry-Picking Reference Audio to Favor One Model

**What goes wrong:**
When manually selecting reference audio for the benchmark, it's easy to unconsciously choose
audio where the new model performs well. This produces a benchmark that confirms the hypothesis
rather than testing it.

**Prevention:**
- Define reference audio selection criteria before running any benchmarks:
  - Fixed duration: 6 seconds exactly
  - Fixed content: use the same 5 sentences per language
  - Fixed recording conditions: same device and environment
- Blind evaluation: have at least one person who doesn't know which output came from which
  model rate the quality
- Report failure cases alongside success cases

**Which phase:** Phase 1 (benchmark phase).

---

## EnCodec Post-Processing Pitfalls

Relevant for Phase 3 (EnCodec artifact removal, per PROJECT.md).

---

### Pitfall 16: 24 kHz Model Requires Mono Audio — Stereo Input Silently Produces Wrong Output

**What goes wrong:**
`EncodecModel.encodec_model_24khz()` operates on monophonic audio. The `convert_audio()`
utility from the `encodec` library handles channel reduction, but using the HuggingFace
`transformers` EnCodec integration without explicit channel handling will silently process
only one channel if stereo audio is passed, dropping half the audio data.

**Warning signs:**
- Output audio at half the expected amplitude
- Stereo input produces mono output without error

**Prevention:**
- Always convert to mono before EnCodec: `audio = audio.mean(dim=0, keepdim=True)` for tensors
  or `librosa.to_mono(y)` for numpy arrays
- Use `encodec.utils.convert_audio(wav, sr, model.sample_rate, model.channels)` which handles
  both resampling and channel reduction atomically

**Which phase:** Phase 3 (EnCodec integration).

---

### Pitfall 17: EnCodec Encode→Decode on Long Audio Causes OOM

**What goes wrong:**
EnCodec processes audio by running encode and decode on the entire file at once. For audio
> 30 seconds, this loads the full waveform as a tensor and can OOM on GPU with < 8 GB VRAM.
The README explicitly notes: "We apply the model at once on the entire file," and warns of
OOM risk. The library does not implement intelligent chunking internally.

**Warning signs:**
- CUDA OOM error for translated audio > 30 seconds on consumer GPUs
- Memory grows linearly with audio length with no upper bound

**Prevention:**
- Implement chunked processing: split into 10-second segments with 1% overlap before encode
- Process each chunk independently and concatenate decoded segments
- Or use the streamable mode: `model.set_target_bandwidth(6.0)` with streaming=True flag

**Which phase:** Phase 3 (EnCodec integration).

---

### Pitfall 18: Output Clipping After Decode Causes Distortion

**What goes wrong:**
EnCodec decode can produce output with amplitude > 1.0 (clipping) when the input audio
had high dynamic range or compression artifacts. The README notes the `-r` rescale flag
for the CLI, but when using the Python API there is no automatic rescale — writing clipped
audio to WAV produces distorted output.

**Warning signs:**
- Output WAV sounds distorted or buzzy despite clean input
- Peak amplitude of decoded tensor > 0.99 when inspected with `decoded.abs().max()`

**Prevention:**
- After decode, normalize: `decoded = decoded / decoded.abs().max().clamp(min=1e-8)`
- Use `soundfile.write()` with `subtype='PCM_16'` which clips silently — prefer
  `subtype='FLOAT'` to preserve dynamic range in intermediate files

**Which phase:** Phase 3 (EnCodec integration).

---

## Phase-Specific Warning Summary

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| Phase 1 | IndicF5 model loading | Meta tensor error with transformers >= 4.51 | Pin `transformers==4.49.0`; verify in lock file |
| Phase 1 | IndicF5 model loading | `torch.compile()` fails on Windows | Patch model.py before release |
| Phase 1 | Reference transcript | Missing/wrong `ref_text` produces garbled audio | Reuse Whisper transcript; validate non-empty |
| Phase 1 | Reference audio length | >12s clips silently; >6s truncates output | Validate duration at CLI input |
| Phase 1 | Reference audio quality | Noisy audio corrupts speaker embedding | Add SNR check; document requirements |
| Phase 1 | Sample rate | Non-24kHz audio gets silently resampled | Explicit resample at 24kHz before passing |
| Phase 1 | Language codes | IndicF5 has no lang arg; existing wiring breaks | Remove lang_code from new TTS signature |
| Phase 1 | CPU performance | 10x+ slower than current pipeline on CPU | Benchmark early; document timing expectations |
| Phase 1 | HF gating | Setup fails without `huggingface-cli login` | Document login step; add CI secret |
| Phase 1 | Dependencies | transformers pin conflicts with Whisper/Sarvam | Test lock diff; use compatible range constraint |
| Phase 1 | Apple Silicon | vocos ISTFT fails on M4 Mac | Test on ARM64 before release; add warning |
| Phase 1 | Benchmark | Training data overlap inflates IndicF5 scores | Use out-of-distribution reference voices |
| Phase 1 | Benchmark | English Whisper WER unreliable for Indic | Use WavLM SIM metric + manual MOS |
| Phase 2 | Long audio | Text > 300 chars silently truncates | Add chunking + FFmpeg check |
| Phase 3 | EnCodec | Stereo input silently drops channel | Force mono before encode |
| Phase 3 | EnCodec | OOM on long audio (> 30s) on consumer GPU | Implement 10s chunking |
| Phase 3 | EnCodec | Output clipping after decode | Normalize after decode |

---

## Sources

- HF IndicF5 discussions #11-#14 (meta tensor error): https://huggingface.co/ai4bharat/IndicF5/discussions
- HF IndicF5 discussion #16 (dependency pinning, reference audio guidance): https://huggingface.co/ai4bharat/IndicF5/discussions/16
- HF IndicF5 discussion #21 (torch.compile Windows fix): https://huggingface.co/ai4bharat/IndicF5/discussions/21
- HF IndicF5 discussion #22 (M4 Mac ISTFT failure): https://huggingface.co/ai4bharat/IndicF5/discussions/22
- HF IndicF5 discussion #25 (garbled output, nondeterminism): https://huggingface.co/ai4bharat/IndicF5/discussions/25
- HF IndicF5 discussion #6 (offline inference, ema_model structure): https://huggingface.co/ai4bharat/IndicF5/discussions/6
- F5-TTS utils_infer.py source (sample rate handling, 12s clip, transcript auto-detection): https://raw.githubusercontent.com/SWivid/F5-TTS/main/src/f5_tts/infer/utils_infer.py
- F5-TTS inference README (reference audio guidance, FFmpeg requirement): https://raw.githubusercontent.com/SWivid/F5-TTS/main/src/f5_tts/infer/README.md
- F5-TTS infer_cli.py source (sentinel value "666", ref_text handling): https://raw.githubusercontent.com/AI4Bharat/IndicF5/refs/heads/main/f5_tts/infer/infer_cli.py
- EnCodec GitHub README (OOM on long files, stereo/mono, Python API): https://raw.githubusercontent.com/facebookresearch/encodec/main/README.md
- EnCodec HuggingFace model card (24kHz monophonic spec): https://huggingface.co/facebook/encodec_24khz
- IndicF5 README (model inputs, 24kHz output, MIT license): https://raw.githubusercontent.com/AI4Bharat/IndicF5/main/README.md
- F5-TTS eval README (WER, SIM, UTMOS metrics): https://raw.githubusercontent.com/SWivid/F5-TTS/main/src/f5_tts/eval/README.md

---

*Analysis confidence: MEDIUM-HIGH. All critical and moderate pitfalls are sourced from verified
community discussions or upstream source code. CPU performance numbers and Apple Silicon M4
status are extrapolated from patterns — measure directly during Phase 1.*
