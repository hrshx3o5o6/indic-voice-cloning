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
