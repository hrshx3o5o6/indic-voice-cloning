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
│   └── models/
│       └── tone_transfer.py     # OpenVoice tone morphing (currently mocked)
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

## Known Caveats

- `tone_transfer.py` — OpenVoice is **currently mocked** (`shutil.copy2`). OpenVoice has strict PyTorch/NumPy version constraints that conflict with the current environment. Real integration is a pending feature branch.
- Whisper model path: tries `../faster_whisper_medium` locally before falling back to downloading `medium` from HuggingFace.
- Sarvam TTS hardcodes `speaker="meera"` and `model="bulbul:v3"` — parameterization is a future enhancement.

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
