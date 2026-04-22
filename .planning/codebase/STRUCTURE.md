# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
indic-voice-cli/
├── .planning/                       # GSD planning directory (created by orchestrator)
├── src/indic_voice/                 # Main package source
│   ├── __init__.py                  # Empty package marker
│   ├── cli.py                       # CLI entry point (typer app)
│   ├── pipeline/                    # 4-stage processing pipeline
│   │   ├── __init__.py
│   │   ├── asr.py                   # ASR: Whisper transcription
│   │   ├── translator.py            # Translation: Google Translate via deep-translator
│   │   └── tts_sarvam.py            # TTS: Sarvam AI Bulbul v3
│   ├── models/                      # Model management and tone transfer
│   │   ├── __init__.py
│   │   ├── checkpoint_manager.py    # Download/cache OpenVoice v2 checkpoints from HF
│   │   └── tone_transfer.py         # Tone morphing orchestration
│   └── openvoice/                   # Bundled OpenVoice v2 library (~2936 lines)
│       ├── __init__.py
│       ├── api.py                   # ToneColorConverter and BaseSpeakerTTS classes
│       ├── se_extractor.py          # Speaker embedding extraction
│       ├── openvoice_app.py         # (Minimal/legacy)
│       ├── models.py                # PyTorch SynthesizerTrn architecture
│       ├── modules.py               # Neural network building blocks
│       ├── attentions.py            # Attention mechanisms
│       ├── commons.py               # Utility functions
│       ├── mel_processing.py        # Mel spectrogram processing
│       ├── transforms.py            # Audio/signal transformations
│       ├── utils.py                 # HParams loading, text splitting
│       └── text/                    # Text processing and phonetics
│           ├── __init__.py
│           ├── cleaners.py          # Text normalization
│           ├── symbols.py           # Symbol definitions
│           ├── english.py           # English phonetics
│           └── mandarin.py          # Chinese phonetics (not used)
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures (sample_wav, mock_sarvam_response)
│   ├── test_asr.py                  # Tests for Whisper integration
│   ├── test_translator.py           # Tests for Google Translate integration
│   ├── test_tts_sarvam.py           # Tests for Sarvam AI TTS
│   ├── test_tone_transfer.py        # Tests for OpenVoice v2 tone morphing
│   ├── test_checkpoint_manager.py   # Tests for checkpoint download/caching
│   └── test_cli.py                  # Tests for CLI commands
├── .env                             # API keys (not committed)
├── .env.example                     # Template: SARVAM_AI_API=your_key
├── .gitignore                       # Ignores .env, __pycache__, .venv
├── pyproject.toml                   # Project metadata, dependencies, build config
├── uv.lock                          # Lockfile (uv package manager)
├── CLAUDE.md                        # Project directives and implementation notes
├── README.md                        # User-facing documentation
├── processed/                       # Temporary directory (OpenVoice speaker extraction)
│   └── [audio_name]_v2_[hash]/
│       └── wavs/                    # Audio segments for embedding extraction
└── translated_cloned.wav            # Example output file (generated, not committed)
```

## Directory Purposes

**`src/indic_voice/`:**
- Purpose: Main Python package containing pipeline logic
- Contains: CLI, pipeline stages, models, OpenVoice library
- Key files: `cli.py` (entry point), stage modules, tone_transfer.py

**`src/indic_voice/pipeline/`:**
- Purpose: Four independent pipeline stages
- Contains: ASR (Whisper), translation (Google), TTS (Sarvam), (tone transfer is in models/)
- Key files: `asr.py`, `translator.py`, `tts_sarvam.py`

**`src/indic_voice/models/`:**
- Purpose: ML model management and tone transfer orchestration
- Contains: Checkpoint downloading, tone morphing logic
- Key files: `checkpoint_manager.py`, `tone_transfer.py`

**`src/indic_voice/openvoice/`:**
- Purpose: Bundled OpenVoice v2 speaker embedding and tone conversion library
- Contains: PyTorch model, speaker extraction, audio processing
- Key files: `api.py` (main classes), `se_extractor.py` (speaker embedding), `models.py` (NN architecture)

**`src/indic_voice/openvoice/text/`:**
- Purpose: Text normalization and language-specific phonetics
- Contains: English and Mandarin text-to-phoneme converters
- Key files: `cleaners.py`, `english.py`, `mandarin.py`, `symbols.py`

**`tests/`:**
- Purpose: Unit test suite
- Contains: Mocked tests for all pipeline stages
- Key files: `conftest.py` (fixtures), `test_*.py` (test modules)

**`processed/`:**
- Purpose: Temporary directory for OpenVoice speaker embedding extraction
- Contains: Split audio segments created by `se_extractor.py`
- Note: NOT cleaned up automatically; accumulates over time

## Key File Locations

**Entry Points:**
- `src/indic_voice/cli.py` - CLI app entry point (defined in `pyproject.toml` as `indic-voice = "indic_voice.cli:app"`)
- `pyproject.toml` - Project metadata and dependencies

**Configuration:**
- `.env` - Environment variables (SARVAM_AI_API)
- `.env.example` - Template showing required vars
- `pyproject.toml` - Dependencies, Python version requirement (3.9–3.12)

**Core Logic (Pipeline Stages):**
- `src/indic_voice/pipeline/asr.py` - Whisper transcription
- `src/indic_voice/pipeline/translator.py` - Google Translate wrapper
- `src/indic_voice/pipeline/tts_sarvam.py` - Sarvam AI TTS API
- `src/indic_voice/models/tone_transfer.py` - OpenVoice v2 tone morphing
- `src/indic_voice/models/checkpoint_manager.py` - HF checkpoint management

**Machine Learning (OpenVoice v2):**
- `src/indic_voice/openvoice/api.py` - ToneColorConverter class
- `src/indic_voice/openvoice/se_extractor.py` - Speaker embedding extraction
- `src/indic_voice/openvoice/models.py` - PyTorch SynthesizerTrn architecture

**Testing:**
- `tests/conftest.py` - Pytest fixtures
- `tests/test_asr.py` - ASR tests
- `tests/test_translator.py` - Translator tests
- `tests/test_tts_sarvam.py` - TTS tests
- `tests/test_tone_transfer.py` - Tone transfer tests
- `tests/test_checkpoint_manager.py` - Checkpoint manager tests
- `tests/test_cli.py` - CLI command tests

## Naming Conventions

**Files:**
- `[stage_name].py` in `pipeline/` for each pipeline stage (asr.py, translator.py, tts_sarvam.py)
- `[function_name].py` or `[class_name].py` in `models/` (checkpoint_manager.py, tone_transfer.py)
- `test_[module_name].py` in `tests/` matching source file names (test_asr.py → asr.py)

**Directories:**
- Lowercase with underscores: `openvoice/`, `pipeline/`, `models/`
- No hyphens in Python package names

**Functions:**
- Snake_case: `transcribe_audio()`, `generate_speech()`, `morph_tone()`, `translate()`
- All take positional (required) or keyword (optional) arguments

**Classes:**
- PascalCase: `ToneColorConverter`, `BaseSpeakerTTS`, `SynthesizerTrn`
- Located in `src/indic_voice/openvoice/api.py` and `src/indic_voice/openvoice/models.py`

**Environment Variables:**
- UPPERCASE: `SARVAM_AI_API`

## Where to Add New Code

**New Pipeline Stage (e.g., voice activity detection):**
- Create: `src/indic_voice/pipeline/[stage_name].py`
- Function signature: `def [stage_name](input: str, **kwargs) -> str:`
- Import in: `src/indic_voice/cli.py`
- Test in: `tests/test_[stage_name].py`

**New CLI Command:**
- Add: `@app.command()` decorated function in `src/indic_voice/cli.py`
- Signature: Takes `typer.Option` parameters, calls pipeline functions
- Error handling: Wrap in try-except, display via `console.print()`

**New Model or Utility:**
- Shared logic: `src/indic_voice/models/[utility_name].py`
- Pure function or class-based
- Test coverage in: `tests/test_[utility_name].py`

**New Test:**
- Location: `tests/test_[target_module].py`
- Use fixtures from: `tests/conftest.py`
- Mock external APIs with `unittest.mock.patch`

**Bundled Library Enhancement (OpenVoice):**
- Location: `src/indic_voice/openvoice/[module_name].py`
- Note: Keep separate from pipeline; avoid importing from pipeline modules

## Special Directories

**`processed/`:**
- Purpose: Temporary storage for audio segments during speaker embedding extraction
- Generated: Automatically by `src/indic_voice/openvoice/se_extractor.py`
- Committed: No (should be in `.gitignore`)
- Cleanup: Not automatic; manually delete or implement cleanup in `tone_transfer.py`
- Structure: `processed/[audio_name]_v2_[hash]/wavs/` containing .wav segments

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: By `uv sync`
- Committed: No

**`.pytest_cache/`:**
- Purpose: Pytest test collection cache
- Generated: Automatically by pytest
- Committed: No

**`.git/`:**
- Purpose: Git repository metadata
- Committed: Yes (but contents not tracked for individual commits)

## Module Import Order

**CLI → Pipeline:**
```python
# In src/indic_voice/cli.py
from indic_voice.pipeline.asr import transcribe_audio
from indic_voice.pipeline.translator import translate
from indic_voice.pipeline.tts_sarvam import generate_speech
from indic_voice.models.tone_transfer import morph_tone
```

**Pipeline → External:**
```python
# In src/indic_voice/pipeline/asr.py
from faster_whisper import WhisperModel

# In src/indic_voice/pipeline/translator.py
from deep_translator import GoogleTranslator

# In src/indic_voice/pipeline/tts_sarvam.py
from dotenv import load_dotenv
from sarvamai import SarvamAI

# In src/indic_voice/models/tone_transfer.py
from indic_voice.models import checkpoint_manager
from indic_voice.openvoice import se_extractor
from indic_voice.openvoice.api import ToneColorConverter
```

**No Circular Dependencies:**
- Pipeline modules do not import from models
- Models do not import from pipeline
- OpenVoice is standalone; only imported by models

## File Size Reference

**Bundled Code:**
- OpenVoice library: ~2936 lines across 20 files
- Pipeline stages: ~100 lines each (asr.py, translator.py, tts_sarvam.py)
- Models: ~100 lines total (checkpoint_manager.py, tone_transfer.py)
- CLI: ~80 lines (cli.py)

**Total Source:** ~3000 lines (mostly OpenVoice library)

---

*Structure analysis: 2026-04-15*
