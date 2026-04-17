# indic-voice-cli

## What This Is

Open-source CLI for zero-shot Indic voice cloning and speech-to-speech translation.
Takes English audio (or text) and produces natural-sounding speech in Hindi, Tamil, Telugu,
and other Indic languages — cloned in any target speaker's voice. Runs fully locally:
no subscriptions, no API keys required after setup, no data leaves the machine.

## Core Value

The easiest open-source way to clone a voice into an Indic language — better quality than
ElevenLabs at Indic specifically, free to run, privacy-first.

## Requirements

### Validated

- ✓ ASR pipeline: Whisper transcribes English audio to text — existing
- ✓ Translation pipeline: Google Translate converts English → Indic text — existing
- ✓ TTS pipeline: Sarvam AI Bulbul v3 generates Indic speech — existing
- ✓ Tone transfer: OpenVoice v2 applies reference speaker's voice characteristics — existing
- ✓ `indic-voice clone` command: text-in, cloned Indic audio out — existing
- ✓ `indic-voice translate` command: English audio-in, Indic cloned audio out — existing
- ✓ CPU/GPU auto-detection for tone transfer inference — existing
- ✓ Checkpoint auto-download on first run — existing

### Active

- [ ] Benchmark IndicF5 vs current Sarvam+OpenVoice pipeline (same reference audio, same text)
- [ ] Replace Sarvam AI TTS + OpenVoice with IndicF5 (if benchmarks confirm quality improvement)
- [ ] Add EnCodec post-processing for artifact removal (after IndicF5 standalone is validated)
- [ ] Support Hindi, Tamil, Telugu as primary Indic languages (+ Bengali, Marathi, Kannada)
- [ ] Keep CLI interface unchanged (`indic-voice clone`, `indic-voice translate`, same flags)
- [ ] Polish for open-source release: clear error messages, README, <5min setup for developers

### Out of Scope

- Web UI or REST API — CLI is the product; simplicity is a feature
- Real-time / streaming TTS — batch processing is sufficient for v1
- English TTS quality improvements — Indic-specialized, not general-purpose
- Custom speaker fine-tuning — zero-shot only; no per-user training
- ElevenLabs parity on English — compete on Indic, not breadth
- Multi-speaker mixing or audio editing — out of scope for this tool

## Context

**Current pipeline weakness:** Sarvam AI generates decent Indic speech but is not a voice
cloning model — it's a generic TTS with a fixed speaker. OpenVoice v2 then tries to graft
speaker characteristics on top, but loses prosody and accent fidelity. Each handoff compounds
quality loss. The clone command works but sounds noticeably synthetic.

**Proposed replacement:** IndicF5 (AI4Bharat) is trained on 1417 hours of high-quality Indic
audio across 11 languages and natively supports voice cloning from a 5-10 second reference
sample. Speaker embedding happens inside the model — no separate tone transfer step needed.
This removes the multi-stage quality loss.

**EnCodec strategy:** Meta's EnCodec neural audio codec preserves speaker characteristics
well at low bitrates and can smooth TTS artifacts via encode→decode. VALL-E 2 uses this
architecture to achieve human parity in voice cloning. Add after IndicF5 is validated alone.

**Competitive angle:** ElevenLabs supports 32 languages broadly but Indic is not specialized.
IndicF5 and Indic Parler-TTS are purpose-built for Indic phonetics and prosody. We win on
depth (Indic-native quality) not breadth (language count).

**Architecture:** Four-stage modular pipeline. Each stage is a pure function — easy to swap
individual stages without touching the rest. IndicF5 replaces stages 3+4 (TTS + tone transfer)
with a single model.

## Constraints

- **CLI Interface:** Same commands and flags — no breaking changes for existing users
- **Simplicity:** No new required API keys after IndicF5 swap (IndicF5 runs fully locally)
- **Setup time:** Developer should be able to install and run in under 5 minutes
- **Hardware:** Works on CPU (slower) and GPU (faster); no GPU requirement
- **Python packaging:** `uv` for dependency management; must stay reproducible via `uv.lock`
- **Open source:** MIT or Apache 2 license; no proprietary model weights bundled

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Benchmark before swapping | Don't swap IndicF5 blindly — confirm improvement on real audio | — Pending |
| Replace both Sarvam + OpenVoice with IndicF5 | Fewer stages = fewer quality handoffs; IndicF5 does both natively | — Pending |
| EnCodec as optional post-processing | Test IndicF5 alone first; EnCodec is additive not foundational | — Pending |
| Keep CLI interface stable | Existing users / scripts shouldn't break | ✓ Good |
| Local-first architecture | No API key juggling; privacy preserving; works offline | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-17 after initialization*
