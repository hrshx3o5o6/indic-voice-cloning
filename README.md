# indic-voice

Zero-shot Indic voice cloning and Speech-to-Speech Translation (S2ST) CLI.
Feed it English audio — get back the same content spoken in Hindi (or another Indic language) in **your own voice**.

## Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                     indic-voice translate                        │
│                                                                  │
│   English WAV                                                    │
│       │                                                          │
│       ▼                                                          │
│  [1] ASR (faster-whisper)  →  English text                       │
│       │                                                          │
│       ▼                                                          │
│  [2] Translation (Google)  →  Indic text (hi / ta / te / …)     │
│       │                                                          │
│       ▼                                                          │
│  [3] TTS (Sarvam Bulbul v3) →  Base Indic WAV                   │
│       │                                                          │
│       ▼                                                          │
│  [4] Tone Transfer (OpenVoice v2) →  Cloned Indic WAV           │
└──────────────────────────────────────────────────────────────────┘

indic-voice clone  skips steps 1-2 and takes text directly.
```

## Installation

**Recommended — uv:**
```bash
git clone https://github.com/hrshx3o5o6/indic-voice-cloning.git
cd indic-voice-cloning
uv sync
```

**pip:**
```bash
pip install -e .
```

## Quick Start

```bash
# Text -> cloned Hindi audio
indic-voice clone \
  --text "नमस्ते दुनिया, मैं हिंदी बोल रहा हूँ" \
  --ref-voice my_voice.wav \
  --output cloned.wav

# English speech -> translated + cloned Indic audio
indic-voice translate \
  --audio english_speech.wav \
  --target-lang hi \
  --output translated_cloned.wav
```

## Configuration

Create a `.env` file in the project root (see `.env.example`):

```
SARVAM_AI_API=your_sarvam_api_key_here
```

Get a Sarvam AI API key at [sarvam.ai](https://sarvam.ai).

OpenVoice v2 checkpoints are downloaded automatically from HuggingFace
(`myshell-ai/OpenVoice`) into `~/.cache/indic-voice/` on first run.

## Supported Languages

| Code | Language   |
|------|------------|
| `hi` | Hindi      |
| `ta` | Tamil      |
| `te` | Telugu     |
| `kn` | Kannada    |
| `ml` | Malayalam  |
| `bn` | Bengali    |
| `mr` | Marathi    |
| `gu` | Gujarati   |

Pass the code via `--target-lang` (translate command).

## Running Tests

```bash
uv run pytest tests/ -v --cov=indic_voice
```

## Implementation Status

Both commands are **fully wired with real models** — nothing is mocked. The pipeline runs end-to-end on CPU or GPU.

| Stage | Model | Status |
|-------|-------|--------|
| ASR | faster-whisper (medium) | ✅ Real |
| Translation | Google Translate (deep-translator) | ✅ Real |
| TTS | Sarvam AI Bulbul v3 | ✅ Real |
| Tone Transfer | OpenVoice v2 | ✅ Real |

First run downloads ~2 GB of model weights total (Whisper + OpenVoice v2 checkpoints).

## Known Limitations

- **GPU recommended** — OpenVoice v2 tone conversion runs significantly faster
  on CUDA. CPU inference works but is slow for long audio.
- Whisper model (~1.5 GB) downloaded on first `translate` run if no local model
  is found at `../faster_whisper_medium`.
- OpenVoice v2 checkpoints (~500 MB) auto-downloaded from HuggingFace
  (`myshell-ai/OpenVoice`) into `~/.cache/indic-voice/checkpoints_v2/` on first run.
- Checkpoint cache lives at `~/.cache/indic-voice/` — not cleaned automatically.
- Speaker is hardcoded to Sarvam AI's `meera` voice for the TTS base layer.
- A `processed/` directory is created in the working directory during tone transfer
  for intermediate audio segments — safe to delete after a run.

## License

MIT
