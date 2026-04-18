---
phase: 03-cli-integration
plan: 02
subsystem: cli
tags: [auto-transcription, indicf5, zero-breaking-changes]
dependency_graph:
  requires:
    - 03-01
  provides:
    - CLI-01: clone command auto-transcribes ref_voice when --ref-text not provided
    - CLI-02: translate command uses Whisper transcript as ref_text
  affects:
    - src/indic_voice/cli.py
tech_stack:
  added: []
  patterns:
    - Auto-transcription when ref_text is None
    - Whisper transcript threaded to IndicF5 as ref_text
key_files:
  created: []
  modified:
    - src/indic_voice/cli.py
decisions:
  - Used source audio as ref_audio_path for voice cloning in translate command
  - Removed Sarvam and OpenVoice dependencies from CLI (IndicF5 does both)
metrics:
  duration: ""
  completed: 2026-04-18
  tasks: 3
  files: 1
---

# Phase 03 Plan 02: Auto-Transcription Integration Summary

## Objective

Implemented auto-transcription for ref_text: clone command auto-transcribes ref_voice if --ref-text not provided, and translate command threads Whisper transcript through to IndicF5.

## Tasks Completed

| Task | Name | Commit |
|------|------|--------|
| 1 | Add auto-transcription logic to clone command | 44cb2c5 |
| 2 | Wire translate command to use IndicF5 with ref_text | 44cb2c5 |
| 3 | Clean up unused imports after migration | 44cb2c5 |

## Key Changes

### 1. Clone Command Auto-Transcription (CLI-01)

Added auto-transcription logic before calling IndicF5 in the clone command:

```python
# Auto-transcribe ref_voice if ref_text not provided (CLI-01)
if ref_text is None:
    console.print("   [dim]Auto-transcribing reference audio...[/dim]")
    ref_text = transcribe_audio(ref_voice)
    console.print(f"   [dim]Ref transcript: '{ref_text}'[/dim]")
```

- When `--ref-text` is not provided, the clone command now auto-transcribes the reference audio
- The transcript is passed to IndicF5 for voice cloning

### 2. Translate Command Uses IndicF5 (CLI-02)

Replaced Sarvam + OpenVoice pipeline with IndicF5 in the translate command:

```python
console.print("3. Generating cloned speech via IndicF5...")
indicf5_generate_speech(
    text=hi_text,
    ref_audio_path=audio,  # Use source audio as reference
    ref_text=en_text,  # Use Whisper transcript as ref_text (CLI-02)
    output_path=output,
)
```

- Uses source audio as reference for voice cloning
- Passes Whisper transcript as ref_text
- Removed OpenVoice tone morph step (IndicF5 does voice cloning in one pass)

### 3. Import Cleanup

Removed unused imports:
- `import os` (no longer needed)
- `from indic_voice.pipeline.tts_sarvam import generate_speech`
- `from indic_voice.models.tone_transfer import morph_tone`

## Deviation from Plan

None - plan executed exactly as written.

## Verification

- `clone` command auto-transcribes when `--ref-text` not provided
- `translate` command uses IndicF5 with Whisper transcript as ref_text
- No manual ref_text required for either command

## Commits

- 44cb2c5: feat(03-cli-integration-03-02): add auto-transcription to clone and translate commands

## Self-Check

- [x] clone command calls transcribe_audio(ref_voice) when ref_text is None
- [x] The ref_text is then passed to indicf5_generate_speech
- [x] A progress message is printed during auto-transcription
- [x] translate command uses indicf5_generate_speech
- [x] ref_text is set to en_text (Whisper transcript)
- [x] ref_audio_path is set to audio (source audio)
- [x] No Sarvam or OpenVoice calls remain in translate command
- [x] No unused imports exist

## TDD Gate Compliance

N/A - this is not a TDD plan.

## Threat Flags

None - no new security surface introduced.