# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**Sarvam AI Bulbul v3 TTS:**
- Service: Sarvam AI (Indian AI speech synthesis company)
- What it's used for: Generate native Indic speech (Hindi, Tamil, Telugu, etc.) from text
  - Parameterized by language code (e.g., `hi-IN`, `ta-IN`, `te-IN`)
  - Parameterized by speaker voice (e.g., `ritu`, `aditya`, `arvind`, `meera`)
  - Model: `bulbul:v3`
- SDK/Client: `sarvamai` 0.14.3 (Python SDK)
- Auth: Environment variable `SARVAM_AI_API` (API subscription key required in `.env`)
- Implementation: `src/indic_voice/pipeline/tts_sarvam.py`
  - Function: `generate_speech(text, output_path, lang_code="hi-IN", speaker="ritu")`
  - Handles both legacy (raw bytes) and new (base64-encoded audios) response formats

**Google Translate (via deep-translator):**
- Service: Google Translate (auto-detection + translation)
- What it's used for: Translate English text to target Indic language (auto-detects source)
- SDK/Client: `deep-translator` 1.11.4 (Google Translate wrapper)
- Auth: None required (free tier, rate-limited)
- Implementation: `src/indic_voice/pipeline/translator.py`
  - Function: `translate(text, target_lang="hi")`
  - Supports BCP-47 language codes (e.g., `hi`, `ta`, `te`, `mr`, `gu`)

**OpenAI Whisper (via faster-whisper):**
- Service: OpenAI Whisper (model hosted on HuggingFace Hub)
- What it's used for: Transcribe English audio to text (ASR)
- SDK/Client: `faster-whisper` 1.3.1 (C/C++ optimized inference)
- Model: `medium` (1.5 GB download on first run)
- Auth: None required (downloaded from HuggingFace Hub)
- Implementation: `src/indic_voice/pipeline/asr.py`
  - Function: `transcribe_audio(audio_path)`
  - Loads local copy `../faster_whisper_medium` if available, otherwise downloads from HF
  - Runs on CPU with `int8` quantization by default

## Model Checkpoints & Downloads

**OpenVoice v2 Checkpoints:**
- Source: HuggingFace Hub (`myshell-ai/OpenVoiceV2` repository)
- What: Tone color converter model and base speaker embeddings
- Files Downloaded:
  - `converter/config.json` - Model architecture config
  - `converter/checkpoint.pth` - Model weights (~50 MB)
  - `base_speakers/ses/en-default.pth` - Default English speaker embedding
- Download Size: ~500 MB total
- Cache Location: `~/.cache/indic-voice/checkpoints_v2/` (default) or custom via `checkpoint_manager.ensure_checkpoints(cache_dir=...)`
- Auto-Download: On first call to `morph_tone()` in `src/indic_voice/models/tone_transfer.py`
- SDK: `huggingface-hub` 0.28.1 (`hf_hub_download()` function)

**Whisper Model:**
- Source: HuggingFace Hub (OpenAI model registry)
- Model: `medium` (1.5 GB)
- Downloaded by: `faster-whisper` library
- Auto-Download: On first call to `transcribe_audio()` if local model not found

## Data Flow & API Boundaries

### `clone` Command

```
User Input (text, ref_voice)
  ↓
[1. TTS] Sarvam AI API → generate_speech()
  ↓ (generates temp audio)
[2. Tone Transfer] OpenVoice v2 (local) → morph_tone()
  ↓
Output (cloned audio)
```

**API Calls:**
- **Sarvam AI:** 1 call per `clone` command
- **HuggingFace Hub:** 0 calls (checkpoints cached after first run)

### `translate` Command

```
User Input (audio, target_lang)
  ↓
[1. ASR] Whisper (HF Hub) → transcribe_audio()
  ↓
[2. Translation] Google Translate (deep-translator) → translate()
  ↓
[3. TTS] Sarvam AI API → generate_speech()
  ↓
[4. Tone Transfer] OpenVoice v2 (local) → morph_tone()
  ↓
Output (translated cloned audio)
```

**API Calls:**
- **Whisper:** 1 call (first time only, then cached)
- **Google Translate:** 1 call per `translate` command
- **Sarvam AI:** 1 call per `translate` command
- **HuggingFace Hub:** 0 calls (checkpoints cached)

## Environment Configuration

**Required Environment Variables:**
- `SARVAM_AI_API` - API key for Sarvam AI TTS (must be set before calling `generate_speech()`)
  - Loaded from `.env` file via `python-dotenv`
  - If missing: Raises `ValueError("SARVAM_AI_API environment variable is missing in .env")`

**Optional Environment Variables:**
- None currently; GPU device detection is automatic via `torch.cuda.is_available()`

**Configuration Files:**
- `.env` - Contains `SARVAM_AI_API` key (NOT committed, must be set by developer)
- `.env.example` - Template file showing required vars

## Webhooks & Callbacks

**Incoming Webhooks:**
- None implemented

**Outgoing Webhooks:**
- None implemented

## Offline Capability

**Fully Offline After First Run:**
1. All model checkpoints cached locally:
   - Whisper `medium` model cached by `faster-whisper`
   - OpenVoice v2 checkpoints cached in `~/.cache/indic-voice/`
2. Local inference (PyTorch models run locally):
   - ASR (Whisper on CPU with int8)
   - Tone transfer (OpenVoice v2 on GPU/CPU)
3. **Requires Network:**
   - First call to `transcribe_audio()` - downloads Whisper model
   - First call to `morph_tone()` - downloads OpenVoice v2 checkpoints
   - Any call to `translate()` - requires Google Translate API access
   - Any call to `generate_speech()` - requires Sarvam AI API access

## Rate Limiting & Quotas

**Sarvam AI:**
- API key-based rate limiting (check Sarvam documentation)
- No built-in retry logic in `src/indic_voice/pipeline/tts_sarvam.py`

**Google Translate:**
- Rate-limited by deep-translator (typically 100-200 requests/minute)
- No explicit handling in `src/indic_voice/pipeline/translator.py`

**HuggingFace Hub:**
- Bandwidth limits for free users
- No explicit handling in `src/indic_voice/models/checkpoint_manager.py`

---

*Integration audit: 2026-04-15*
