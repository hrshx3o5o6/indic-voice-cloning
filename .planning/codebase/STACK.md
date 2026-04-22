# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.9–3.12 - Main application language, full pipeline implementation

## Runtime & Package Management

**Environment:**
- Python 3.9–3.12 (pinned in `pyproject.toml`)
- `uv` - Package manager and lock file (`uv.lock` present)

**Package Manager:**
- `uv` (not pip, not poetry)
- Lockfile: `uv.lock` present (495 KB, fully pinned dependencies)

## Frameworks & Core Libraries

**CLI Framework:**
- `typer` 0.23.2 - Command-line application framework for `indic-voice clone` and `indic-voice translate` commands
- `rich` 14.3.3 - Terminal output formatting, progress messages, error display

**Audio Processing:**
- `librosa` 0.11.0 - Audio feature extraction and spectrogram processing (imported in OpenVoice modules)
- `soundfile` 1.5.4 - WAV file I/O operations
- `pydub` 0.25.1 (actually 2.41.5 in lock) - Audio segment manipulation and format conversion
- `torchaudio` 2.11.0 - Audio tensor operations for tone transfer

**ML & Computation:**
- `torch` 2.8.0 - Core ML framework for OpenVoice v2 inference
- `numpy` 2.2.6 - Numerical computations, audio array operations

## Pipeline Dependencies

### ASR (Automatic Speech Recognition)

**Whisper Transcription:**
- `faster-whisper` 1.3.1 - Lightweight Whisper implementation for English audio transcription
- `whisper-timestamped` 0.0.3 - Timestamp and confidence extraction from transcription segments
- `ctranslate2` 4.7.1 - Runtime for faster-whisper (compiled inference)

### Translation

**Language Translation:**
- `deep-translator` 1.11.4 - Google Translate API wrapper (uses `GoogleTranslator` class)
- `langid` 1.1.6 - Language detection (for translator auto-detection)

### TTS (Text-to-Speech)

**Sarvam AI Bulbul v3:**
- `sarvamai` 0.14.3 - Official SDK for Sarvam AI Bulbul TTS v3 API
  - Requires `SARVAM_AI_API` environment variable (API key)
  - Supports speaker parameterization and language codes (hi-IN, ta-IN, etc.)

### Tone Transfer (OpenVoice v2)

**HuggingFace Integration:**
- `huggingface-hub` 0.28.1 - Download OpenVoice v2 checkpoints from `myshell-ai/OpenVoiceV2` repository
  - ~500 MB checkpoint download on first run
  - Cached to `~/.cache/indic-voice/checkpoints_v2/`

**OpenVoice v2 Library:**
- Bundled locally in `src/indic_voice/openvoice/` (~2936 lines across 20 files)
- No external package; uses:
  - `torch` for speaker embedding extraction and tone conversion
  - `librosa` for audio feature processing

## Text Processing & Language Support

**Phonetics & Text Normalization:**
- `eng-to-ipa` 0.0.2 - English text to IPA conversion (used in OpenVoice text processing)
- `pypinyin` 0.50.0 - Chinese pinyin conversion (for Chinese language support in text)
- `jieba` 0.42.1 - Chinese text segmentation
- `cn2an` 0.5.22 - Chinese numeral conversion
- `inflect` 7.5.0 - English morphology (pluralization, verb conjugation)
- `unidecode` 1.3.0 - Unicode text transliteration to ASCII

**Environment Configuration:**
- `python-dotenv` 1.0.1 - Load `.env` file (requires `SARVAM_AI_API`)

## Audio Watermarking

**Optional Watermark Embedding:**
- `wavmark` 0.0.3 - Audio watermarking (present as dependency but not used in current pipeline)

## Testing & Development

**Test Framework:**
- `pytest` 7.4.0+ - Test runner
- `pytest-cov` 4.1.0+ - Coverage reporting
- Python built-in `unittest.mock` - Mocking in tests

**Note:** Tests use mocking extensively; no integration tests hit real APIs in CI/CD.

## Build System

**Build Backend:**
- `hatchling` (specified in `pyproject.toml` build-system)

**Entry Point:**
```
[project.scripts]
indic-voice = "indic_voice.cli:app"
```

## Platform Requirements

**Development:**
- Python 3.9–3.12
- ~1.5 GB disk (Whisper `medium` model on first run)
- ~500 MB disk (OpenVoice v2 checkpoints on first run)
- `uv` CLI tool installed

**Production / Inference:**
- Same as development (model files auto-downloaded)
- GPU recommended: CUDA 12.0+ (automatically detected; falls back to CPU)
- Tested on: CPU (int8 Whisper), GPU (faster tone transfer with CUDA)

## Key Dependency Notes

| Dependency | Version | Purpose | Critical |
|---|---|---|---|
| `torch` | 2.8.0 | OpenVoice v2 inference | Yes |
| `faster-whisper` | 1.3.1 | English transcription | Yes |
| `sarvamai` | 0.14.3 | Indic TTS generation | Yes |
| `deep-translator` | 1.11.4 | Text translation | Yes |
| `typer` | 0.23.2 | CLI framework | Yes |
| `huggingface-hub` | 0.28.1 | Checkpoint downloads | Yes |
| `numpy` | 2.2.6 | Audio/tensor operations | Yes |
| `librosa` | 0.11.0 | Audio features | Yes |
| `wavmark` | 0.0.3 | Watermarking (unused) | No |

---

*Stack analysis: 2026-04-15*
