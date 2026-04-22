# Indic Voice CLI — Claude AI Directives

> **CRITICAL:** Always enter thinking mode before responding. Spawn sub-agents for isolated sub-tasks. Brainstorm with the user *before* implementing. Keep code simple and focused.

---

## Project Overview

`indic-voice-cli` is an open-source CLI for **zero-shot Indic voice cloning** and **speech-to-speech translation (S2ST)**. The pipeline runs IndicF5 end-to-end — no Sarvam, no OpenVoice, no API keys required after setup.

**CLI entry point:** `indic-voice` (defined in `pyproject.toml` → `indic_voice.cli:app`)

Two commands:
- `indic-voice clone` — Text + reference audio → cloned Indic speech
- `indic-voice translate` — English audio → Indic speech in cloned voice

---

## Repository Structure

```
indic-voice-cli/
├── src/indic_voice/
│   ├── cli.py                   # Typer app, command definitions
│   ├── pipeline/
│   │   ├── asr.py               # Whisper transcription
│   │   ├── translator.py        # Text translation (Google Translate)
│   │   └── tts_indicf5.py      # IndicF5 TTS (fully local)
│   ├── models/
│   │   └── checkpoint_manager.py  # (legacy — not used with IndicF5)
│   └── openvoice/               # (deprecated — to be removed in Phase 4)
├── tests/                       # pytest test suite
├── benchmark/                    # Benchmark harness (Phase 1 artifact)
├── pyproject.toml               # Dependencies, entry points
├── uv.lock                      # Lockfile (managed by uv)
└── .env                         # Optional: HF_TOKEN for gated models
```

---

## Development Setup

**Package manager:** `uv`

```bash
uv sync
uv run indic-voice --help
uv run indic-voice clone --text "नमस्ते" --ref-voice ref.wav
uv run pytest tests/
```

---

## Code Style

- **Type hints:** Required on all function arguments and return types
- **Docstrings:** Google-style, on all public functions and classes
- **CLI UX:** Use `typer` + `rich` for all output — no bare `print()`
- **Error handling:** `try/except` with user-friendly `rich` error messages

---

## Git Workflow

| Change Type | Branch |
|---|---|
| Bug fixes, refactors | `dev` |
| Major new features | `feat/<feature-name>` |
| Hotfixes | `hotfix/<description>` |

**Commit convention:** [Conventional Commits](https://www.conventionalcommits.org/)
```
feat(tts): add speaker parameterization to IndicF5 TTS
fix(asr): handle missing audio file with clear error message
refactor(cli): extract temp file cleanup into context manager
```

**Bug fix rule:** When a bug is reported and fixed, commit immediately with a descriptive message. Do not group unrelated fixes.

---

## Technology Stack

- **ASR:** `faster-whisper` — English transcription
- **Translation:** `deep-translator` — Google Translate wrapper
- **TTS:** `ai4bharat/IndicF5` via `f5-tts` — fully local, single-pass voice cloning
- **CLI:** `typer` + `rich`
- **Package manager:** `uv`

### Key Constraints

- `transformers==4.49.0` must be pinned — later versions cause meta tensor loading errors
- MPS (Apple Silicon) explicitly excluded — Vocos iSTFT crashes on M-series chips
- Device selection: CUDA > CPU only

---

## Phase Status

| Phase | Status |
|---|---|
| 1. Benchmark Harness | ✅ Complete |
| 2. IndicF5 Module | ✅ Complete |
| 3. CLI Integration | ✅ Complete |
| 4. Dependency Cleanup | ⏳ Pending |
| 5. Open-Source Polish | ⏳ Pending |

Phase 4 removes: `sarvamai`, `openvoice/`, `models/tone_transfer.py`, `models/checkpoint_manager.py`, and all dead-weight dependencies (wavmark, langid, whisper-timestamped, inflect, unidecode, eng-to-ipa, pypinyin, jieba, cn2an).
