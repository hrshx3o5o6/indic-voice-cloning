# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Modular Pipeline (4-stage sequential composition)

**Key Characteristics:**
- Four independent pipeline stages (ASR, Translation, TTS, Tone Transfer) composed sequentially
- Each stage is a pure function with well-defined inputs/outputs
- Stages can be used independently or chained together via CLI commands
- No shared state between stages (except temporary file passing)
- External services (APIs) are abstracted behind module interfaces
- Tone transfer and TTS are the only heavy compute stages; ASR is lightweight (int8 Whisper)

## Layers

**CLI Layer:**
- Purpose: Command-line interface, user input validation, orchestration
- Location: `src/indic_voice/cli.py`
- Contains: Two commands (`clone`, `translate`) using `typer` framework
- Depends on: All pipeline stages (import and call functions)
- Used by: Direct user invocation via `indic-voice` CLI entry point

**Pipeline Layer (4 Stages):**

1. **ASR (Automatic Speech Recognition)**
   - Purpose: Transcribe English audio to text
   - Location: `src/indic_voice/pipeline/asr.py`
   - Contains: `transcribe_audio(audio_path: str) -> str`
   - Depends on: `faster-whisper` library
   - Used by: `translate` command (Step 1)
   - Entry: Audio file path
   - Exit: Transcribed English text

2. **Translator (Text Translation)**
   - Purpose: Translate text from English (or auto-detected) to Indic language
   - Location: `src/indic_voice/pipeline/translator.py`
   - Contains: `translate(text: str, target_lang: str = "hi") -> str`
   - Depends on: `deep-translator` library (Google Translate backend)
   - Used by: `translate` command (Step 2)
   - Entry: English text, target language code (BCP-47, e.g., `hi`, `ta`, `te`)
   - Exit: Indic language text

3. **TTS (Text-to-Speech)**
   - Purpose: Generate native Indic speech from text using Sarvam AI Bulbul v3
   - Location: `src/indic_voice/pipeline/tts_sarvam.py`
   - Contains: `generate_speech(text: str, output_path: str, lang_code: str = "hi-IN", speaker: str = "ritu") -> str`
   - Depends on: `sarvamai` SDK (Sarvam AI API)
   - Used by: Both `clone` and `translate` commands
   - Entry: Text (Indic language), language code, speaker voice
   - Exit: WAV file containing synthetic speech
   - Note: Requires `SARVAM_AI_API` environment variable

4. **Tone Transfer (Speaker Embedding & Morphing)**
   - Purpose: Extract tone color from reference voice and apply to generated speech
   - Location: `src/indic_voice/models/tone_transfer.py`
   - Contains: `morph_tone(source_audio: str, ref_audio: str, output_path: str) -> str`
   - Depends on: OpenVoice v2 (bundled), `torch`, checkpoint manager
   - Used by: Both `clone` and `translate` commands (final step)
   - Entry: Base audio file (TTS output), reference audio file (speaker source)
   - Exit: Tone-morphed WAV file with speaker characteristics applied

**Model & Checkpoint Layer:**
- Purpose: Manage model downloads and inference initialization
- Location: `src/indic_voice/models/`
- Contains:
  - `checkpoint_manager.py` - Auto-download OpenVoice v2 checkpoints from HF Hub
  - `tone_transfer.py` - Tone morphing orchestration
- Depends on: `huggingface-hub` (checkpoint downloads), `torch` (inference)
- Used by: Tone transfer stage

**OpenVoice v2 Library Layer:**
- Purpose: Bundled speaker embedding and tone color conversion implementation
- Location: `src/indic_voice/openvoice/`
- Contains: ~2936 lines across 20 files:
  - `api.py` - `ToneColorConverter` and `BaseSpeakerTTS` classes
  - `se_extractor.py` - `get_se()` function for speaker embedding extraction
  - `models.py` - PyTorch model architecture (`SynthesizerTrn`)
  - `modules.py`, `commons.py`, `mel_processing.py` - Audio processing utilities
  - `text/` - Text normalization and phonetics processing
- Depends on: `torch`, `librosa`, `numpy`
- Used by: Tone transfer layer (internal, not exposed to CLI)

## Data Flow

### `clone` Command Data Flow

```
User Input:
  text: str            (Hindi text, e.g., "नमस्ते")
  ref_voice: str       (Path to reference audio .wav)
  output: str          (Output path, default "clone_output.wav")

Step 1: TTS (Sarvam AI)
  Input: text
  Process: generate_speech(text, tmp_sarvam_tts.wav)
  Output: tmp_sarvam_tts.wav (synthetic Hindi speech)

Step 2: Tone Transfer (OpenVoice v2)
  Input: tmp_sarvam_tts.wav (source audio), ref_voice (reference audio)
  Process:
    1. Download OpenVoice checkpoints if missing
    2. Load ToneColorConverter model
    3. Extract speaker embedding from ref_voice
    4. Apply tone color to tmp_sarvam_tts.wav
  Output: clone_output.wav (cloned speech with user's voice)

Cleanup:
  Remove: tmp_sarvam_tts.wav (temporary file)
```

### `translate` Command Data Flow

```
User Input:
  audio: str           (Path to English audio .wav)
  target_lang: str     (Language code, default "hi")
  output: str          (Output path, default "translated_clone.wav")

Step 1: ASR (Whisper)
  Input: audio
  Process: transcribe_audio(audio)
  Output: en_text (English transcript)

Step 2: Translation (Google Translate)
  Input: en_text, target_lang
  Process: translate(en_text, target_lang=target_lang)
  Output: hi_text (Indic language text)

Step 3: TTS (Sarvam AI)
  Input: hi_text
  Process: generate_speech(hi_text, tmp_sarvam_tts.wav)
  Output: tmp_sarvam_tts.wav (synthetic Indic speech)

Step 4: Tone Transfer (OpenVoice v2)
  Input: tmp_sarvam_tts.wav (source), audio (reference - original speaker)
  Process:
    1. Download OpenVoice checkpoints if missing
    2. Load ToneColorConverter model
    3. Extract speaker embedding from original audio
    4. Apply tone color to synthetic speech
  Output: translated_clone.wav (translated speech in original speaker's voice)

Cleanup:
  Remove: tmp_sarvam_tts.wav (temporary file)
```

## State Management

**No Persistent State:**
- Each command is stateless; all state is local to the function call
- Temporary files (TTS output) are cleaned up in `finally` block
- Models are loaded fresh on each invocation (no session management)

**Caching (Automatic):**
- Whisper model cached by `faster-whisper` library (user's HF cache directory)
- OpenVoice v2 checkpoints cached in `~/.cache/indic-voice/checkpoints_v2/`
- Both caches checked on subsequent runs; reused if present

## Key Abstractions

**Pipeline Stage:**
- Purpose: Encapsulate a single transformation (e.g., ASR, TTS)
- Pattern: Pure function with (inputs) → outputs signature
- Examples:
  - `transcribe_audio(audio_path: str) -> str`
  - `translate(text: str, target_lang: str) -> str`
  - `generate_speech(text: str, output_path: str, ...) -> str`
  - `morph_tone(source_audio: str, ref_audio: str, output_path: str) -> str`

**Checkpoint Manager:**
- Purpose: Handle lazy download and caching of ML model weights
- Pattern: `ensure_checkpoints() -> str` returns local cache directory
- Implementation: `src/indic_voice/models/checkpoint_manager.py`
- Idempotent: Safe to call multiple times; skips download if files exist

**Tone Color Converter:**
- Purpose: Extract and apply speaker embeddings
- Classes: `ToneColorConverter` (in `src/indic_voice/openvoice/api.py`)
- Methods:
  - `load_ckpt(ckpt_path)` - Load model weights
  - `convert(audio_src_path, src_se, tgt_se, output_path, message)` - Apply tone transfer

## Entry Points

**CLI Entry Point:**
- Location: `src/indic_voice/cli.py`
- Triggers: User runs `indic-voice clone` or `indic-voice translate`
- Responsibilities:
  - Parse CLI arguments (text, audio path, language, output path)
  - Call appropriate pipeline stages in sequence
  - Display rich console messages (progress, success, errors)
  - Clean up temporary files in finally block

## Error Handling

**Strategy:** Try-except with user-friendly `rich` console messages

**Patterns:**

1. **File Not Found:**
   - `asr.py:9` - Check audio file exists before Whisper load
   - `tone_transfer.py:33-36` - Check source and reference audio exist

2. **Missing API Key:**
   - `tts_sarvam.py:44-46` - Raise `ValueError` if `SARVAM_AI_API` not set
   - Caught by CLI and displayed via `console.print("[bold red]Error:[/bold red] ...")`

3. **API Errors:**
   - Sarvam TTS, Google Translate errors propagate to CLI layer
   - CLI catches with generic `except Exception as e` and displays

4. **Audio Processing Errors:**
   - Whisper, librosa, soundfile errors propagate to CLI
   - CLI displays with traceback via console

**Missing Robustness:**
- No retry logic for transient API failures
- No timeout handling for long audio processing
- Raw exception tracebacks shown to user in some cases

## Cross-Cutting Concerns

**Logging:**
- Approach: `rich.console.Console()` for styled terminal output
- Levels: Print statements only (no logging module)
- Examples: `console.print("[dim]Downloading checkpoints...[/dim]")`

**Validation:**
- File existence checked before processing
- API keys checked before API calls
- No input sanitization for text (assumes valid UTF-8)

**Authentication:**
- Environment variable (`SARVAM_AI_API`) passed directly to `SarvamAI` SDK
- No API token refresh or expiration handling

**Device Selection (GPU/CPU):**
- `tone_transfer.py:38-42` - Auto-detect: CUDA > MPS > CPU
- Whisper uses CPU with int8 quantization (hardcoded in `asr.py:13`)
- OpenVoice respects device selection for faster inference on GPU

---

*Architecture analysis: 2026-04-15*
