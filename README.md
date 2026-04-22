# indic-voice

**Zero-shot Indic voice cloning — fully local, no API keys, no subscriptions.**

Clone a voice into Hindi, Tamil, Telugu, and 8 other Indic languages. Give it any English audio and a reference speaker — it transcribes, translates, and generates speech in the target language using the reference speaker's voice. Runs entirely on your machine.

Built on [ai4bharat/IndicF5](https://huggingface.co/ai4bharat/IndicF5), a diffusion Transformer trained on 1,417 hours of Indic speech.

## Features

- **Voice cloning in one pass** — IndicF5 does in a single model what other pipelines need TTS + tone transfer to accomplish
- **11 Indic languages** — Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati, Punjabi, Odia, Nepali
- **Fully local** — after first-run model download, everything runs on your hardware
- **No API keys** — no subscriptions, no per-character charges, no data leaving your machine
- **Reference audio auto-transcription** — supply a reference `.wav` without a manual transcript; Whisper transcribes it automatically

## Installation

### Prerequisites

- Python 3.11 or 3.12
- `uv` package manager ([install guide](https://github.com/astral-sh/uv))

### Steps

```bash
git clone https://github.com/hrshx3o5o6/indic-voice-cloning.git
cd indic-voice-cloning
uv sync
```

On first run, the CLI will download ~1.4 GB in model weights (IndicF5 + Whisper). This happens once and is cached locally.

## Quick Start

### Voice clone

Give it text and a reference voice — get cloned Indic speech back:

```bash
indic-voice clone \
  --text "नमस्ते, मैं हिंदी में बात कर रहा हूँ" \
  --ref-voice my_voice.wav \
  --output cloned.wav
```

### Speech-to-Speech translation

Give it English audio — get the same content spoken in your voice in Hindi (or any supported language):

```bash
indic-voice translate \
  --audio english_speech.wav \
  --target-lang hi \
  --output translated.wav
```

Use `--target-lang ta` for Tamil, `--target-lang te` for Telugu, etc.

### Reference audio requirements

- **Duration**: 5–12 seconds
- **Format**: WAV or M4A recommended
- **Content**: Clean speech with minimal background noise
- The reference audio's transcript is auto-generated if you don't provide `--ref-text`

### Hardware

| Hardware | Status | Notes |
|---|---|---|
| NVIDIA GPU (CUDA) | Recommended | 10–50x faster than CPU |
| Apple Silicon (MPS) | Not supported | Vocos ISTFT crash on M-series chips |
| CPU | Works | Slow for long audio; ~30s per sentence |

## Supported Languages

| Code | Language | Code | Language |
|------|----------|------|----------|
| `hi` | Hindi | `mr` | Marathi |
| `ta` | Tamil | `gu` | Gujarati |
| `te` | Telugu | `pa` | Punjabi |
| `kn` | Kannada | `or` | Odia |
| `ml` | Malayalam | `ne` | Nepali |
| `bn` | Bengali | | |

## How It Works

```
indic-voice clone
──────────────────
ref_audio + ref_text  ──►  IndicF5  ──►  cloned Indic speech

indic-voice translate
───────────────────────────────
english_audio  ──►  Whisper  ──►  Google Translate  ──►  IndicF5  ──►  cloned Indic speech
              (ASR)          (translation)              (TTS + voice clone)
```

IndicF5 is a diffusion Transformer (0.4B params) trained by AI4Bharat on 1,417 hours of Indic audio. Unlike two-stage pipelines (TTS + tone transfer), it performs voice cloning in a single forward pass — no separate tone imprinting step.

## Configuration

### HuggingFace token (optional)

Some IndicF5 model files may require accepting the model license on HuggingFace. If you hit an authentication error:

```bash
huggingface-cli login
```

Then follow the browser prompt to authenticate.

### Custom model cache location

Models are cached at `~/.cache/huggingface/` by default. To change:

```bash
HF_HOME=/path/to/cache uv run indic-voice clone ...
```

## CLI Reference

```
indic-voice --help
indic-voice clone --help
indic-voice translate --help
```

### `clone`

```bash
indic-voice clone [OPTIONS]
  --text TEXT              Indic text to synthesize (required)
  --ref-voice PATH         Reference audio file, 5–12s (required)
  --ref-text TEXT          Transcript of reference audio (auto-generated if omitted)
  --output PATH            Output WAV path (default: clone_output.wav)
```

### `translate`

```bash
indic-voice translate [OPTIONS]
  --audio PATH             English source audio file (required)
  --target-lang LANG       Target language code, e.g. hi, ta, te (default: hi)
  --output PATH            Output WAV path (default: translated_clone.wav)
```

## Known Limitations

- **CPU performance** — IndicF5 on CPU is significantly slower than GPU. For casual use it's fine; for batch processing, use a GPU.
- **Apple Silicon (MPS)** — Not supported due to a Vocos/iSTFT incompatibility on M-series chips. Use CPU or NVIDIA GPU on these machines.
- **Reference audio quality** — Noisy reference audio degrades clone quality. Use clean speech with minimal background noise.
- **No speaker ID** — The model clones the reference speaker's voice directly; there is no separate speaker selection step.

## Running Tests

```bash
uv run pytest tests/ -v
```

## Uninstall

```bash
pip uninstall indic-voice
# Remove cached model weights (~1.4 GB):
rm -rf ~/.cache/huggingface/hub/models--ai4bharat--IndicF5
```

## Related Projects

| Project | Role |
|---|---|
| [ai4bharat/IndicF5](https://huggingface.co/ai4bharat/IndicF5) | Base TTS model |
| [SWivid/F5-TTS](https://github.com/SWivid/F5-TTS) | Parent architecture |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | ASR transcription |
| [deep-translator](https://github.com/nidhaloff/deep-translator) | Google Translate wrapper |

## License

MIT — see [LICENSE](LICENSE).
