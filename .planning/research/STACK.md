# Technology Stack — TTS + Voice Cloning Replacement

**Project:** indic-voice-cli
**Scope:** Replacement stack for TTS (stage 3) and Tone Transfer (stage 4) only.
         ASR (faster-whisper) and Translation (deep-translator) are unchanged.
**Researched:** 2026-04-15
**Overall confidence:** MEDIUM — IndicF5 is the right call but has active bugs requiring workarounds.

---

## Decision: Replace Both Stages with IndicF5

**Use `ai4bharat/IndicF5`** as a unified TTS + voice cloning stage, loaded via
`transformers.AutoModel.from_pretrained("ai4bharat/IndicF5", trust_remote_code=True)`.

This eliminates the two-stage hand-off (Sarvam TTS → OpenVoice tone transfer) that
compounds quality loss. IndicF5 natively takes reference audio + reference text + target
text and outputs cloned speech in a single inference pass.

**Drop:** `sarvamai` (Sarvam AI API), the bundled `openvoice/` library, and all
OpenVoice checkpoint downloads (~500 MB). The Sarvam API key requirement is also removed.

---

## Recommended Stack (Replacement Stages Only)

### Core Replacement

| Library | Version Constraint | Purpose | Rationale |
|---------|-------------------|---------|-----------|
| `indicf5` | `git+https://github.com/ai4bharat/IndicF5.git` | Unified TTS + voice cloning | Not on PyPI; install from git. 0.4B params, 1417h Indic training data, MIT license. |
| `transformers` | `>=4.40.0,<4.50.0` | IndicF5 model loading via AutoModel | `transformers<4.50` is IndicF5's own declared constraint. Community-confirmed working: `4.49.0`. Transformers 5.x breaks the model. |
| `torch` | `>=2.0.0` | Inference backend | Already in pyproject.toml. No change needed. |
| `torchaudio` | `>=2.0.0` | Audio preprocessing (required by IndicF5) | Not currently in pyproject.toml — must be added. |
| `vocos` | (no pin) | Vocoder used by IndicF5 internally | Pulled in transitively by IndicF5 install. May need explicit add if uv doesn't resolve it. |
| `accelerate` | `>=0.33.0` | Efficient model loading | Required by IndicF5. Not currently in pyproject.toml. |
| `x_transformers` | `>=1.31.14` | IndicF5 internal transformer ops | Required by IndicF5 setup.py. |
| `ema_pytorch` | `>=0.5.2` | Exponential moving average (IndicF5 internal) | Required by IndicF5 setup.py. |
| `hydra-core` | `>=1.3.0` | IndicF5 config management | Required by IndicF5 setup.py. |
| `torchdiffeq` | (no pin) | ODE solver used by F5 flow matching | Required by IndicF5 setup.py. |
| `cached_path` | (no pin) | Remote checkpoint fetching | Required by IndicF5 setup.py. |
| `safetensors` | (no pin) | Loading model.safetensors (1.4 GB weights) | Required by IndicF5 setup.py. |

### EnCodec Post-Processing (Additive — Add After IndicF5 Is Validated)

| Library | Version Constraint | Purpose | Rationale |
|---------|-------------------|---------|-----------|
| `transformers` | same as above | EnCodec is in transformers as `EncodecModel` | `from transformers import EncodecModel, AutoProcessor` — no separate pip package needed |
| HF model: `facebook/encodec_24khz` | n/a (weights auto-downloaded) | Audio encode→decode to smooth TTS artifacts | 23M params, 24kHz matches IndicF5 output sample rate. Accessed through transformers, not a separate install. |

**EnCodec usage pattern:**
```python
from transformers import EncodecModel, AutoProcessor
model = EncodecModel.from_pretrained("facebook/encodec_24khz")
processor = AutoProcessor.from_pretrained("facebook/encodec_24khz")
inputs = processor(raw_audio=audio_array, sampling_rate=24000, return_tensors="pt")
audio_values = model(inputs["input_values"], inputs["padding_mask"]).audio_values
```

There is a standalone `encodec` pip package from facebookresearch, but the HuggingFace
transformers implementation is preferred: it is actively maintained, has 232K monthly
downloads, and shares the already-required transformers dependency.

---

## Dependencies to Add to pyproject.toml

```toml
# Add these to [project] dependencies:
"indicf5 @ git+https://github.com/ai4bharat/IndicF5.git",
"transformers>=4.40.0,<4.50.0",   # tighten existing open-ended constraint
"torchaudio>=2.0.0",
"accelerate>=0.33.0",
```

The following are pulled in transitively by IndicF5 but may need explicit entries
if uv's resolver surfaces conflicts:
```toml
"vocos",
"x_transformers>=1.31.14",
"ema_pytorch>=0.5.2",
"torchdiffeq",
"cached_path",
"safetensors",
```

### Python Version Constraint

IndicF5's own docs specify Python 3.10. The current pyproject.toml allows `>=3.9,<3.13`.
Tighten to `>=3.10,<3.13` to match IndicF5's tested environment.

### Dependencies to Remove

```toml
# Remove after OpenVoice is fully replaced:
"sarvamai==0.1.0",       # Sarvam AI TTS API
"wavmark>=0.0.3",        # Used only by OpenVoice watermarking
"langid>=1.1.6",         # Used only by OpenVoice language detection
"whisper-timestamped>=1.15.4",  # Used only by OpenVoice pipeline
"inflect>=5.6.0",        # Used only by OpenVoice text normalization
"unidecode>=1.3.6",      # Used only by OpenVoice text normalization
"eng-to-ipa>=0.0.2",     # Used only by OpenVoice English IPA
"pypinyin>=0.50.0",      # Used only by OpenVoice Chinese text (not Indic)
"jieba>=0.42.1",         # Used only by OpenVoice Chinese tokenization
"cn2an>=0.5.22",         # Used only by OpenVoice Chinese numerals
```

Verify each removal against the actual import graph before deleting. The openvoice/
directory bundle can be deleted from `src/indic_voice/openvoice/` once confirmed unused.

---

## What NOT to Use and Why

### Indic Parler-TTS (`ai4bharat/indic-parler-tts`)

**Do not use.** Despite having more training data (1806h vs 1417h) and more languages
(21 vs 11), Indic Parler-TTS does not perform voice cloning. It generates speech from
natural language voice *descriptions* ("A female speaker with a British accent...").
This is a fundamentally different capability — it cannot reproduce a specific person's
voice from a reference audio sample. This disqualifies it for this project's core
requirement of zero-shot voice cloning from user-provided reference audio.

### OpenVoice v2 (current — `src/indic_voice/openvoice/`)

**Remove.** It is a generic tone transfer layer that was never designed for Indic
phonetics. The quality loss from the two-stage pipeline (Sarvam generates wrong prosody
→ OpenVoice tries to fix it) is the exact problem being solved. IndicF5 handles speaker
embedding natively.

### Sarvam AI Bulbul v3 (`sarvamai` package)

**Remove.** It is a high-quality generic Indic TTS but is not a voice cloning model.
It generates fixed-speaker speech; OpenVoice tone transfer cannot adequately compensate
for missing speaker identity. The API key dependency also violates the project's
local-first constraint for the new milestone.

### Standalone `encodec` pip package (`facebookresearch/encodec`)

**Do not use.** Superseded by the transformers implementation. The standalone package
is not as well-maintained and adds a redundant dependency when transformers is already
required.

### F5-TTS upstream (`SWivid/F5-TTS`)

**Do not use directly.** IndicF5 is built on top of F5-TTS but fine-tuned specifically
for Indic languages on 1417h of Indic speech data. Using the upstream English F5-TTS
would require separately finding an Indic checkpoint. IndicF5 packages the correct
checkpoint and handles Indic text normalization.

---

## Known Issues and Mitigations

### Issue 1: `transformers<4.50` Constraint Creates Conflicts

IndicF5's requirements.txt pins `transformers<4.50`. Community-confirmed working version
is `transformers==4.49.0`. The current pyproject.toml has `huggingface_hub>=0.20.0` but
no transformers pin — this is fine, transformers is currently not a direct dep.

**Risk:** Adding `transformers<4.50` while the ecosystem moves to 5.x may create
conflicts with other packages. Check for conflicts during `uv sync` after adding.

**Mitigation:** Pin to `transformers>=4.40.0,<4.50.0` and validate with `uv lock --check`.

### Issue 2: Meta Tensor Error on Model Load

Multiple users hit `NotImplementedError: Cannot copy out of meta tensor` on both CPU
and GPU. The fix is `transformers==4.49.0` (confirmed working, May 2025 community reports).
Transformers 4.50.x broke this, transformers 5.x also breaks it.

**Mitigation:** Pin `transformers==4.49.0` (exact pin) rather than a range, if the
meta tensor error surfaces during testing.

### Issue 3: `torch.compile()` Failures on Some Platforms

IndicF5's `model.py` calls `torch.compile()` on the vocoder. This fails on Windows
(project is macOS/Linux so low risk) and has caused issues on Apple Silicon M4.

**Fix:** If running on Apple Silicon M4, patch `model.py` to remove the
`torch.compile()` wrapper around vocoder loading. Community workaround from discussion
#21: load vocoder directly without `torch.compile()`.

### Issue 4: HuggingFace Model Is Gated

`ai4bharat/IndicF5` requires agreeing to terms on the HuggingFace model page before
weights can be downloaded. Users need a HuggingFace account and must run
`huggingface-cli login` before first use, or set `HF_TOKEN` in environment.

**Impact:** This complicates the "<5 min setup" constraint. Document clearly in README.
The model weights are 1.4 GB (model.safetensors) — larger than the OpenVoice checkpoints
(~500 MB) they replace, but now a single download instead of separate Sarvam API + OpenVoice.

### Issue 5: Apple Silicon ISTFT Error

`vocos` spectral ops fail on M4 Mac during audio decode phase:
`RuntimeError: istft(...) window overlap add min: 1`

This is a PyTorch/torchaudio version issue on ARM. The project currently targets CPU+GPU
but no confirmed M4 workaround exists in community reports.

**Mitigation:** Note M4 Mac as unsupported until vocos publishes a fix. Intel Mac and
Linux (CPU/GPU) are confirmed working.

### Issue 6: `numpy<=1.26.4` Conflict

IndicF5 requires `numpy<=1.26.4`. The current pyproject.toml has `numpy>=1.24.0` with
no upper bound. These are compatible (1.24 to 1.26.4 is fine) but `uv` needs the upper
bound set to avoid resolving numpy 2.x.

**Fix:** Change `numpy>=1.24.0` to `numpy>=1.24.0,<=1.26.4` in pyproject.toml.

---

## IndicF5 Inference Interface

The model's call signature (from model card):

```python
from transformers import AutoModel
import numpy as np
import soundfile as sf

model = AutoModel.from_pretrained("ai4bharat/IndicF5", trust_remote_code=True)

audio = model(
    target_text,          # str: text to synthesize in target language
    ref_audio_path,       # str: path to reference .wav file (5-10 seconds)
    ref_text,             # str: transcript of the reference audio
)

# audio dtype may be int16 — normalize before writing
if audio.dtype == np.int16:
    audio = audio.astype(np.float32) / 32768.0
sf.write("output.wav", np.array(audio, dtype=np.float32), samplerate=24000)
```

Output sample rate: **24000 Hz**. This is the same as the EnCodec model, so
post-processing requires no resampling.

---

## Packages That Remain Unchanged

| Package | Role | Notes |
|---------|------|-------|
| `faster-whisper>=1.0.1` | ASR | No change |
| `deep-translator>=1.11.4` | Translation | No change |
| `typer>=0.12.3` | CLI framework | No change |
| `rich>=13.7.1` | Terminal output | No change |
| `python-dotenv>=1.0.1` | Env var loading | No change (though SARVAM_AI_API key becomes unused) |
| `soundfile>=0.12.0` | Audio I/O | No change |
| `librosa>=0.10.0` | Audio processing | No change |
| `pydub>=0.25.1` | Audio manipulation | No change |
| `huggingface_hub>=0.20.0` | HF downloads | No change |

---

## Sources

- IndicF5 model card: https://huggingface.co/ai4bharat/IndicF5 — HIGH confidence
- IndicF5 setup.py: https://raw.githubusercontent.com/ai4bharat/IndicF5/main/setup.py — HIGH confidence
- IndicF5 requirements.txt: https://raw.githubusercontent.com/ai4bharat/IndicF5/main/requirements.txt — HIGH confidence
- IndicF5 community discussions (meta tensor fix, transformers==4.49.0): https://huggingface.co/ai4bharat/IndicF5/discussions/14 — MEDIUM confidence (community report, May 2025)
- IndicF5 model.py bugs (torch.compile, missing ckpt_path): https://huggingface.co/ai4bharat/IndicF5/discussions/21 — MEDIUM confidence
- IndicF5 transformers 5.0 compatibility PR: https://huggingface.co/ai4bharat/IndicF5/discussions/33 — MEDIUM confidence (PR pending merge as of research date)
- Indic Parler-TTS model card: https://huggingface.co/ai4bharat/indic-parler-tts — HIGH confidence (confirms no voice cloning capability)
- EnCodec via transformers: https://huggingface.co/facebook/encodec_24khz — HIGH confidence
- Transformers current dev version (5.6.0.dev0): https://raw.githubusercontent.com/huggingface/transformers/main/setup.py — HIGH confidence
