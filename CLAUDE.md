# Indic Voice CLI — Claude AI Directives

> **CRITICAL:** Always enter thinking mode before responding. Spawn sub-agents for isolated sub-tasks. Brainstorm with the user *before* implementing. Keep code simple and focused.

---

## Project Overview

`indic-voice-cli` is an open-source CLI for **Zero-shot Indic Voice Cloning** and **Speech-to-Speech Translation (S2ST)**. It pipelines four models:

| Stage | Model | Role |
|---|---|---|
| ASR | OpenAI Whisper (`faster-whisper`) | Transcribe English audio |
| Translation | Google Translate (`deep-translator`) | English → Indic language text |
| TTS | Sarvam AI Bulbul v3 | Generate native-sounding Indic speech |
| Tone Transfer | OpenVoice | Zero-shot tone imprinting from reference voice |

**CLI entry point:** `indic-voice` (defined in `pyproject.toml` → `indic_voice.cli:app`)

Two commands exposed:
- `indic-voice clone` — Text-in, cloned Hindi audio out (TTS + tone morph)
- `indic-voice translate` — English audio-in, Indic cloned audio out (full S2ST pipeline)

---

## Repository Structure

```
indic-voice-cli/
├── src/indic_voice/
│   ├── cli.py                   # Typer app, command definitions
│   ├── pipeline/
│   │   ├── asr.py               # Whisper transcription
│   │   ├── translator.py        # Text translation
│   │   └── tts_sarvam.py        # Sarvam AI TTS (requires SARVAM_AI_API in .env)
│   ├── models/
│   │   ├── checkpoint_manager.py  # Auto-downloads OpenVoice v2 checkpoints from HF
│   │   └── tone_transfer.py       # OpenVoice v2 tone morphing (real, not mocked)
│   └── openvoice/               # Bundled OpenVoice v2 library (~3700 lines)
│       ├── api.py               # ToneColorConverter, BaseSpeakerTTS
│       ├── se_extractor.py      # Speaker embedding extraction
│       ├── models.py, modules.py, mel_processing.py, ...
│       └── text/                # Text processing utilities
├── tests/                       # 18 tests across 5 modules
├── pyproject.toml               # Dependencies, entry points, build config
├── uv.lock                      # Lockfile (managed by uv)
└── .env                         # API keys (not committed)
```

---

## Development Setup

**Package manager:** `uv` (not pip, not poetry)

```bash
# Install dependencies
uv sync

# Run the CLI
uv run indic-voice --help
uv run indic-voice clone --text "नमस्ते" --ref-voice ref.wav
uv run indic-voice translate --audio input.wav --target-lang hi

# Run tests
uv run pytest

# Add a dependency
uv add <package>
```

**Required `.env` file:**
```
SARVAM_AI_API=your_sarvam_api_key_here
```

---

## Code Style (Open Source Standards)

- **Type hints:** Required on all function arguments and return types.
- **Docstrings:** Google-style, on all public functions and classes.
- **CLI UX:** Use `typer` + `rich` for all output. No bare `print()` statements.
- **Modularity:** One file per pipeline stage. Never mix concerns across `pipeline/` and `models/`.
- **Error handling:** `try/except` with user-friendly `rich` error messages. No raw tracebacks exposed to the user.

---

## Implementation Status (dev branch)

Both end-to-end pipelines are **fully wired with real models** — nothing is mocked in production code:

| Stage | Status | Notes |
|---|---|---|
| ASR (Whisper) | ✅ Real | `faster-whisper`, falls back to HF download |
| Translation | ✅ Real | `deep-translator` → Google Translate |
| TTS (Sarvam) | ✅ Real | Bulbul v3, speaker/lang parameterized |
| Tone Transfer (OpenVoice v2) | ✅ Real | Full library bundled in `openvoice/`, checkpoints auto-downloaded |

`indic-voice clone` and `indic-voice translate` both work end-to-end on CPU or GPU.

## Known Caveats

- **OpenVoice checkpoint download** — ~500 MB, auto-fetched from `myshell-ai/OpenVoice` on HF into `~/.cache/indic-voice/checkpoints_v2/` on first run.
- **Whisper model path** — tries `../faster_whisper_medium` locally before downloading `medium` from HuggingFace (~1.5 GB). Path is cwd-relative and brittle.
- **Sarvam TTS speaker** — hardcoded to `speaker="meera"` in `tts_sarvam.py`. Speaker parameterization is a future enhancement.
- **OpenVoice TAU** — style transfer intensity hardcoded to `0.3` in `tone_transfer.py`.
- **`processed/` directory** — `se_extractor.py` writes intermediate audio segments to `./processed/` during speaker embedding extraction; not cleaned up automatically.
- **GPU recommended** — OpenVoice tone conversion works on CPU but is significantly slower for long audio.

---

## Testing

Every new utility function or module **requires a corresponding test**. Place tests in `tests/` mirroring `src/` structure.

```bash
uv run pytest tests/
```

---

## Git Workflow

| Change Type | Branch |
|---|---|
| Bug fixes, refactors, minor tweaks | `dev` |
| Major new features | `feat/<feature-name>` |
| Hotfixes | `hotfix/<description>` |

**Commit convention:** [Conventional Commits](https://www.conventionalcommits.org/)
```
feat(tts): add speaker parameterization to Sarvam TTS
fix(asr): handle missing audio file with clear error message
refactor(cli): extract temp file cleanup into context manager
```

**Rules:**
- Always confirm with the user before committing or pushing any major change.
- `main` is the stable baseline — never push broken code there.
- Never use `--no-verify` to skip hooks.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**indic-voice-cli**

Open-source CLI for zero-shot Indic voice cloning and speech-to-speech translation.
Takes English audio (or text) and produces natural-sounding speech in Hindi, Tamil, Telugu,
and other Indic languages — cloned in any target speaker's voice. Runs fully locally:
no subscriptions, no API keys required after setup, no data leaves the machine.

**Core Value:** The easiest open-source way to clone a voice into an Indic language — better quality than
ElevenLabs at Indic specifically, free to run, privacy-first.

### Constraints

- **CLI Interface:** Same commands and flags — no breaking changes for existing users
- **Simplicity:** No new required API keys after IndicF5 swap (IndicF5 runs fully locally)
- **Setup time:** Developer should be able to install and run in under 5 minutes
- **Hardware:** Works on CPU (slower) and GPU (faster); no GPU requirement
- **Python packaging:** `uv` for dependency management; must stay reproducible via `uv.lock`
- **Open source:** MIT or Apache 2 license; no proprietary model weights bundled
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.9–3.12 - Main application language, full pipeline implementation
## Runtime & Package Management
- Python 3.9–3.12 (pinned in `pyproject.toml`)
- `uv` - Package manager and lock file (`uv.lock` present)
- `uv` (not pip, not poetry)
- Lockfile: `uv.lock` present (495 KB, fully pinned dependencies)
## Frameworks & Core Libraries
- `typer` 0.23.2 - Command-line application framework for `indic-voice clone` and `indic-voice translate` commands
- `rich` 14.3.3 - Terminal output formatting, progress messages, error display
- `librosa` 0.11.0 - Audio feature extraction and spectrogram processing (imported in OpenVoice modules)
- `soundfile` 1.5.4 - WAV file I/O operations
- `pydub` 0.25.1 (actually 2.41.5 in lock) - Audio segment manipulation and format conversion
- `torchaudio` 2.11.0 - Audio tensor operations for tone transfer
- `torch` 2.8.0 - Core ML framework for OpenVoice v2 inference
- `numpy` 2.2.6 - Numerical computations, audio array operations
## Pipeline Dependencies
### ASR (Automatic Speech Recognition)
- `faster-whisper` 1.3.1 - Lightweight Whisper implementation for English audio transcription
- `whisper-timestamped` 0.0.3 - Timestamp and confidence extraction from transcription segments
- `ctranslate2` 4.7.1 - Runtime for faster-whisper (compiled inference)
### Translation
- `deep-translator` 1.11.4 - Google Translate API wrapper (uses `GoogleTranslator` class)
- `langid` 1.1.6 - Language detection (for translator auto-detection)
### TTS (Text-to-Speech)
- `sarvamai` 0.14.3 - Official SDK for Sarvam AI Bulbul TTS v3 API
### Tone Transfer (OpenVoice v2)
- `huggingface-hub` 0.28.1 - Download OpenVoice v2 checkpoints from `myshell-ai/OpenVoiceV2` repository
- Bundled locally in `src/indic_voice/openvoice/` (~2936 lines across 20 files)
- No external package; uses:
## Text Processing & Language Support
- `eng-to-ipa` 0.0.2 - English text to IPA conversion (used in OpenVoice text processing)
- `pypinyin` 0.50.0 - Chinese pinyin conversion (for Chinese language support in text)
- `jieba` 0.42.1 - Chinese text segmentation
- `cn2an` 0.5.22 - Chinese numeral conversion
- `inflect` 7.5.0 - English morphology (pluralization, verb conjugation)
- `unidecode` 1.3.0 - Unicode text transliteration to ASCII
- `python-dotenv` 1.0.1 - Load `.env` file (requires `SARVAM_AI_API`)
## Audio Watermarking
- `wavmark` 0.0.3 - Audio watermarking (present as dependency but not used in current pipeline)
## Testing & Development
- `pytest` 7.4.0+ - Test runner
- `pytest-cov` 4.1.0+ - Coverage reporting
- Python built-in `unittest.mock` - Mocking in tests
## Build System
- `hatchling` (specified in `pyproject.toml` build-system)
## Platform Requirements
- Python 3.9–3.12
- ~1.5 GB disk (Whisper `medium` model on first run)
- ~500 MB disk (OpenVoice v2 checkpoints on first run)
- `uv` CLI tool installed
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Four independent pipeline stages (ASR, Translation, TTS, Tone Transfer) composed sequentially
- Each stage is a pure function with well-defined inputs/outputs
- Stages can be used independently or chained together via CLI commands
- No shared state between stages (except temporary file passing)
- External services (APIs) are abstracted behind module interfaces
- Tone transfer and TTS are the only heavy compute stages; ASR is lightweight (int8 Whisper)
## Layers
- Purpose: Command-line interface, user input validation, orchestration
- Location: `src/indic_voice/cli.py`
- Contains: Two commands (`clone`, `translate`) using `typer` framework
- Depends on: All pipeline stages (import and call functions)
- Used by: Direct user invocation via `indic-voice` CLI entry point
- Purpose: Manage model downloads and inference initialization
- Location: `src/indic_voice/models/`
- Contains:
- Depends on: `huggingface-hub` (checkpoint downloads), `torch` (inference)
- Used by: Tone transfer stage
- Purpose: Bundled speaker embedding and tone color conversion implementation
- Location: `src/indic_voice/openvoice/`
- Contains: ~2936 lines across 20 files:
- Depends on: `torch`, `librosa`, `numpy`
- Used by: Tone transfer layer (internal, not exposed to CLI)
## Data Flow
### `clone` Command Data Flow
```
```
### `translate` Command Data Flow
```
```
## State Management
- Each command is stateless; all state is local to the function call
- Temporary files (TTS output) are cleaned up in `finally` block
- Models are loaded fresh on each invocation (no session management)
- Whisper model cached by `faster-whisper` library (user's HF cache directory)
- OpenVoice v2 checkpoints cached in `~/.cache/indic-voice/checkpoints_v2/`
- Both caches checked on subsequent runs; reused if present
## Key Abstractions
- Purpose: Encapsulate a single transformation (e.g., ASR, TTS)
- Pattern: Pure function with (inputs) → outputs signature
- Examples:
- Purpose: Handle lazy download and caching of ML model weights
- Pattern: `ensure_checkpoints() -> str` returns local cache directory
- Implementation: `src/indic_voice/models/checkpoint_manager.py`
- Idempotent: Safe to call multiple times; skips download if files exist
- Purpose: Extract and apply speaker embeddings
- Classes: `ToneColorConverter` (in `src/indic_voice/openvoice/api.py`)
- Methods:
## Entry Points
- Location: `src/indic_voice/cli.py`
- Triggers: User runs `indic-voice clone` or `indic-voice translate`
- Responsibilities:
## Error Handling
- No retry logic for transient API failures
- No timeout handling for long audio processing
- Raw exception tracebacks shown to user in some cases
## Cross-Cutting Concerns
- Approach: `rich.console.Console()` for styled terminal output
- Levels: Print statements only (no logging module)
- Examples: `console.print("[dim]Downloading checkpoints...[/dim]")`
- File existence checked before processing
- API keys checked before API calls
- No input sanitization for text (assumes valid UTF-8)
- Environment variable (`SARVAM_AI_API`) passed directly to `SarvamAI` SDK
- No API token refresh or expiration handling
- `tone_transfer.py:38-42` - Auto-detect: CUDA > MPS > CPU
- Whisper uses CPU with int8 quantization (hardcoded in `asr.py:13`)
- OpenVoice respects device selection for faster inference on GPU
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
