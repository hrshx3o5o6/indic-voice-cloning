---
slug: indicf5-ckpt-path-error
created: "2026-04-21T00:00:00Z"
updated: "2026-04-21T00:00:00Z"
trigger: "load_model() missing 1 required positional argument: 'ckpt_path' when running IndicF5 TTS"
status: investigating
---

# Debug Session: indicf5-ckpt-path-error

## Symptoms

**Expected behavior:**
IndicF5 TTS should generate cloned speech and save to output file.

**Actual behavior:**
Error occurs when trying to load the IndicF5 model after downloading Vocos.

**Error message:**
```
Error: Failed to load IndicF5 model from HuggingFace: load_model() missing 1 required positional argument: 'ckpt_path'
```

**Timeline:**
Issue discovered during Phase 3 testing. Has not worked yet with the IndicF5 integration.

**Reproduction:**
```bash
uv run indic-voice clone --ref-voice /Users/harsha/Downloads/ventures_hacks_projects_backup/iitb/audio_data/Harsa_2.m4a --text "नमस्ते मेरा नाम हर्षा है"
```

**Additional context:**
- Error occurs after "Download Vocos from huggingface charactr/vocos-mel-24khz" completes
- Model successfully downloads vocab.txt (11.3kB)
- Error originates from tts_indicf5.py when calling model(text, ref_audio_path, ref_text)
- Previous fix resolved meta tensor error by removing device_map="auto"

## Current Focus

```yaml
hypothesis: |
  The IndicF5 model has an internal load_model() method that requires a checkpoint path
  argument, but the model is being called incorrectly. The AutoModel.from_pretrained()
  may not be the right way to initialize this specific model.

test: |
  Check how IndicF5 model is supposed to be loaded - may need different loading pattern
  than standard transformers AutoModel.

expecting: |
  Find the correct way to load and call IndicF5 model that satisfies the ckpt_path requirement.

next_action: |
  Research IndicF5 model loading pattern from ai4bharat/IndicF5 repository.

reasoning_checkpoint: null
```

## Evidence

- Error traceback: load_model() missing 1 required positional argument: 'ckpt_path'
- File: src/indic_voice/pipeline/tts_indicf5.py
- Function: generate_speech() calling model(text, ref_audio_path, ref_text)
- Model loads successfully via AutoModel.from_pretrained() but fails on inference call

## Eliminated

- Meta tensor error: FIXED by removing device_map="auto" and using explicit .to(device)

## Resolution

- root_cause: |
  IndicF5 model.safetensors contains BOTH ema_model (transformer) keys AND vocoder keys.
  The checkpoint is loaded twice: once via load_model() -> load_checkpoint() (expects only
  ema_model keys) and separately via load_vocoder() -> Vocos.from_hparams() -> load_state_dict()
  (expects vocoder keys). When load_checkpoint() loads the full checkpoint including vocoder keys,
  it fails because CFM state_dict expects transformer keys only.

  Additionally, the vocoder is already loaded separately by load_vocoder(), so passing vocoder
  keys to load_checkpoint() would cause a parameter mismatch regardless.

- fix: |
  Strip "ema_model._orig_mod." prefix from transformer keys (existing fix).
  NEW: Drop all "vocoder.*" keys from checkpoint before passing to load_model() — the vocoder
  is already loaded by load_vocoder() and must not be in the checkpoint passed to the CFM model.

- verification: |
  uv run indic-voice clone --ref-voice /Users/harsha/Downloads/ventures_hacks_projects_backup/iitb/audio_data/Harsa_2.m4a --text "नमस्ते मेरा नाम हर्षा है"
  Output: "Success! Saved cloned audio to clone_output.wav"

- files_changed:
  - src/indic_voice/pipeline/tts_indicf5.py
