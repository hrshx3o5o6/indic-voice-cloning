# Phase 3: CLI Integration - Research

**Researched:** 2026-04-18
**Domain:** CLI integration, UX guardrails, IndicF5 wiring
**Confidence:** HIGH

## Summary

This phase wires IndicF5 into the existing `clone` and `translate` commands while preserving backward compatibility. The core changes involve: (1) replacing Sarvam+OpenVoice with IndicF5 in both commands, (2) adding ref_text auto-fill via Whisper transcription, (3) adding reference audio duration validation, (4) adding CPU inference warnings, and (5) adding progress feedback for checkpoint downloads. All existing flags remain unchanged.

**Primary recommendation:** Modify `cli.py` to import `generate_speech` from `tts_indicf5` instead of `tts_sarvam` and `morph_tone`. Add `--ref-text` optional flag to `clone` command. Add audio duration validation using torchaudio. Thread Whisper transcripts through the pipeline as ref_text.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLI-01 | `clone` command auto-transcribes `--ref-voice` via Whisper if `--ref-text` is not supplied | Uses existing `transcribe_audio()` from pipeline.asr |
| CLI-02 | `translate` command threads Whisper transcript from Step 1 through as `ref_text` to IndicF5 | Pass `en_text` as `ref_text` to IndicF5 |
| CLI-03 | Optional `--ref-text` flag added to `clone` command | Add typer.Option with default=None |
| CLI-04 | Reference audio validation at CLI entry: warns if duration < 5s or > 12s | Use torchaudio.load and waveform.shape[1]/sample_rate |
| CLI-05 | CPU inference warning printed if no CUDA device detected | Check `torch.cuda.is_available()` and print warning |
| CLI-06 | First-run IndicF5 checkpoint download shows Rich progress bar | Use rich.progress for download feedback |
| CLI-07 | All existing flags unchanged — zero breaking changes | Keep --text, --ref-voice, --audio, --target-lang, --output |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| CLI entry points | API/Backend | — | Typer app serves as API layer, orchestrates all pipeline stages |
| Ref text auto-fill | API/Backend | — | Whisper transcription runs on CPU, passes text to IndicF5 |
| Audio validation | API/Backend | — | Duration check happens before any model loading |
| Device detection | API/Backend | — | CUDA availability check before IndicF5 inference |
| Checkpoint download | API/Backend | — | HuggingFace model download happens in generate_speech |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `typer` | 0.23.2 | CLI framework | Already in project, handles flags/options |
| `rich` | 14.3.3 | Terminal output | Already in project, progress bars |
| `torch` | 2.8.0 | Device detection | Already in project |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `torchaudio` | 2.11.0 | Audio loading for duration validation | CLI-04 audio validation |
| `faster-whisper` | 1.3.1 | Ref audio transcription | CLI-01, CLI-02 auto-fill |
| `transformers` | 4.49.0 | IndicF5 model loading | Already pinned in pyproject.toml |

**Installation:**
```bash
# No new packages needed - all already in project
```

## Architecture Patterns

### Modified CLI Data Flow (clone command)

```
User input (text + ref_voice)
    │
    ▼
[CLI-04] Audio duration validation ──► Warning if < 5s or > 12s
    │
    ▼
[CLI-05] CUDA availability check ──► Warning if CPU only
    │
    ▼
[CLI-01] If ref_text not provided ──► Whisper transcribe(ref_voice)
    │
    ▼
IndicF5 generate_speech(text, ref_voice, ref_text, output)
    │
    ▼
Output WAV file
```

### Modified CLI Data Flow (translate command)

```
User input (audio + target_lang)
    │
    ▼
[CLI-04] Audio duration validation on input audio
    │
    ▼
[CLI-05] CUDA availability check
    │
    ▼
Step 1: Whisper transcribe(audio) ──► en_text
    │
    ▼
Step 2: deep-translator translate(en_text, target_lang) ──► indic_text
    │
    ▼
[CLI-02] Thread en_text as ref_text to IndicF5
    │
    ▼
IndicF5 generate_speech(indic_text, ref_audio_path=audio, ref_text=en_text, output)
    │
    ▼
Output WAV file
```

### Recommended Project Structure

```
src/indic_voice/
├── cli.py                   # Modified: uses IndicF5, adds ref_text, validation
├── pipeline/
│   ├── asr.py               # Existing: transcribe_audio()
│   ├── translator.py        # Existing: translate()
│   ├── tts_indicf5.py       # Existing: generate_speech()
│   └── tts_sarvam.py        # Deleted in Phase 4
├── models/
│   ├── tone_transfer.py     # Deleted in Phase 4
│   └── checkpoint_manager.py # Deleted in Phase 4
└── openvoice/               # Deleted in Phase 4
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Audio duration | Custom duration detection | torchaudio.load(waveform).shape[1]/sample_rate | Simple, accurate |
| Device detection | Custom CUDA checks | torch.cuda.is_available() | Standard PyTorch API |
| Progress display | tqdm or custom | rich.progress | Already in project, matches existing UX |
| Ref text transcription | Custom Whisper wrapper | pipeline.asr.transcribe_audio() | Already implemented |

## Common Pitfalls

### Pitfall 1: Missing ref_text causes IndicF5 crash
**What goes wrong:** IndicF5 requires ref_text parameter, but old CLI didn't have it
**Why it happens:** Sarvam TTS didn't need reference transcript, IndicF5 does
**How to avoid:** Auto-fill via Whisper when --ref-text not provided (CLI-01)
**Warning signs:** ValueError("Reference text (ref_text) cannot be empty or None")

### Pitfall 2: Reference audio too short/long degrades quality
**What goes wrong:** IndicF5 produces poor quality with < 5s or > 12s reference
**Why it happens:** F5-TTS trained on 5-12s samples; > 12s hard clipped
**How to avoid:** Validate duration at CLI entry, warn user (CLI-04)
**Warning signs:** Output audio artifacts, poor speaker similarity

### Pitfall 3: First-run checkpoint download appears hung
**What goes wrong:** 1.4 GB download takes minutes, no feedback
**Why it happens:** HuggingFace download has no progress by default
**How to avoid:** Wrap model loading with Rich progress bar (CLI-06)
**Warning signs:** User Ctrl-C during download, assumption of hang

### Pitfall 4: CPU inference extremely slow without warning
**What goes wrong:** IndicF5 RTF is 10-50x slower on CPU, user thinks it's broken
**Why it happens:** CUDA not available, default to CPU silently
**How to avoid:** Print warning at CLI entry if no CUDA (CLI-05)
**Warning signs:** User complaints about 10+ minute generation times

## Code Examples

### Pattern 1: Audio duration validation

```python
import torchaudio

def validate_ref_audio(audio_path: str) -> float:
    """Validate reference audio duration.

    Args:
        audio_path: Path to reference audio file.

    Returns:
        Duration in seconds.

    Raises:
        FileNotFoundError: If audio file doesn't exist.
    """
    waveform, sample_rate = torchaudio.load(audio_path)
    duration = waveform.shape[1] / sample_rate
    return duration
```

### Pattern 2: Ref text auto-fill with Whisper

```python
from indic_voice.pipeline.asr import transcribe_audio

def ensure_ref_text(ref_text: str | None, ref_voice: str) -> str:
    """Auto-fill ref_text via Whisper if not provided.

    Args:
        ref_text: User-provided reference text (may be None).
        ref_voice: Path to reference audio.

    Returns:
        Reference text string.
    """
    if ref_text is None or ref_text.strip() == "":
        return transcribe_audio(ref_voice)
    return ref_text
```

### Pattern 3: Device detection warning

```python
import torch
from rich.console import Console

console = Console()

def warn_if_cpu() -> None:
    """Print warning if no CUDA available."""
    if not torch.cuda.is_available():
        console.print("[yellow]Warning: No CUDA detected. Running on CPU (10-50x slower).[/yellow]")
```

### Pattern 4: Optional ref-text flag for clone command

```python
@app.command()
def clone(
    text: str = typer.Option(..., "--text", "-t", help="The Hindi text to generate"),
    ref_voice: str = typer.Option(..., "--ref-voice", "-v", help="Path to your reference voice (.wav)"),
    ref_text: str | None = typer.Option(None, "--ref-text", help="Reference audio transcript (auto-transcribed if not provided)"),
    output: str = typer.Option("clone_output.wav", "--output", "-o", help="Path to save the cloned audio"),
) -> None:
    """Generate cloned Indic speech in your voice."""
```

### Pattern 5: Progress wrapper for model loading

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn
from huggingface_hub import hf_hub_download

def download_with_progress(repo_id: str, filename: str) -> str:
    """Download file with Rich progress bar."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
    ) as progress:
        task = progress.add_task(f"Downloading {filename}...", total=None)
        path = hf_hub_download(repo_id=repo_id, filename=filename)
        progress.update(task, completed=True)
    return path
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sarvam AI + OpenVoice pipeline | IndicF5 single-pass TTS | Phase 2 (complete) | Better speaker similarity, no two-stage loss |
| No ref_text handling | Auto-fill via Whisper | This phase (CLI-01, CLI-02) | Zero new user input required |
| No audio validation | Duration check with warning | This phase (CLI-04) | Prevents poor quality output |
| Silent CPU fallback | Explicit warning | This phase (CLI-05) | Manages user expectations |
| No download progress | Rich progress bar | This phase (CLI-06) | Reduces support requests |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | IndicF5 model download is 1.4 GB | CLI-06 | Minor — progress bar still works regardless of size |
| A2 | torch.cuda.is_available() is sufficient for GPU detection | CLI-05 | Low — doesn't detect MPS, but MPS causes crashes anyway |
| A3 | Reference audio duration calculated correctly via torchaudio | CLI-04 | Low — torchaudio is standard library |

## Open Questions

1. **Should we also validate the input audio in `translate` command?**
   - What we know: CLI-04 mentions "reference audio" validation, translate uses source audio as reference
   - What's unclear: Whether source audio validation should apply to translate command too
   - Recommendation: Apply same 5-12s validation to translate's ref audio (the source audio)

2. **How to detect first-run download vs cached model?**
   - What we know: HuggingFace caches models in ~/.cache/huggingface/
   - What's unclear: Whether IndicF5 checkpoint already exists before download
   - Recommendation: Check model path existence before showing progress bar

3. **Should checkpoint download progress use specific repo ID?**
   - What we know: Model is ai4bharat/IndicF5
   - What's unclear: Exact filename to track for progress
   - Recommendation: Use transformers snapshot path check

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| torch | Device detection | ✓ | 2.8.0 | — |
| torchaudio | Audio validation | ✓ | 2.11.0 | — |
| faster-whisper | Ref text transcription | ✓ | 1.3.1 | — |
| rich | Progress display | ✓ | 14.3.3 | — |

**Missing dependencies with no fallback:**
- None — all required packages already in project

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.4.0+ |
| Config file | pytest.ini (if exists) |
| Quick run command | `uv run pytest tests/test_cli.py -x` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | Clone auto-transcribes ref_voice when no ref_text | unit | `pytest tests/test_cli.py::test_clone_auto_ref_text -x` | ❌ New file needed |
| CLI-02 | Translate threads Whisper transcript to IndicF5 | unit | `pytest tests/test_cli.py::test_translate_ref_text_flow -x` | ❌ New file needed |
| CLI-03 | Clone accepts optional --ref-text flag | unit | `pytest tests/test_cli.py::test_clone_ref_text_flag -x` | ❌ New file needed |
| CLI-04 | CLI warns if audio duration < 5s or > 12s | unit | `pytest tests/test_cli.py::test_audio_duration_validation -x` | ❌ New file needed |
| CLI-05 | CLI prints warning if no CUDA | unit | `pytest tests/test_cli.py::test_cpu_warning -x` | ❌ New file needed |
| CLI-06 | Download shows Rich progress bar | integration | `pytest tests/test_cli.py::test_download_progress -x` | ❌ New file needed |
| CLI-07 | Existing flags unchanged | smoke | `uv run indic-voice clone --help` | ✅ Existing |

### Sampling Rate
- **Per task commit:** `pytest tests/test_cli.py -x`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_cli.py` — covers CLI-01 through CLI-06
- [ ] `tests/conftest.py` — shared fixtures (may reuse existing)
- [ ] No new test framework needed — pytest already configured

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — CLI runs locally |
| V3 Session Management | no | N/A — no session state |
| V4 Access Control | no | N/A — local file access only |
| V5 Input Validation | yes | Path validation, audio file existence checks |
| V6 Cryptography | no | N/A — no encryption needed |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in output | Tampering | os.path.abspath(), directory validation |
| Malformed audio file | DoS | torchaudio.load try/except, clear error message |
| Empty ref_text injection | Availability | Validation in ensure_ref_text() |

## Sources

### Primary (HIGH confidence)
- `src/indic_voice/cli.py` — Current CLI implementation
- `src/indic_voice/pipeline/tts_indicf5.py` — IndicF5 module
- `src/indic_voice/pipeline/asr.py` — Whisper transcription

### Secondary (MEDIUM confidence)
- PyTorch torch.cuda.is_available() — Standard device detection API
- torchaudio.load() — Standard audio loading API

### Tertiary (LOW confidence)
- N/A — all patterns are standard library usage

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages already in project
- Architecture: HIGH — clear data flow modification
- Pitfalls: HIGH — well-understood from Phase 2

**Research date:** 2026-04-18
**Valid until:** 30 days (stable — implementation details are straightforward)