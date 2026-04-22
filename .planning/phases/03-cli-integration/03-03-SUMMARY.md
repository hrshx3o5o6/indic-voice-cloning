---
phase: 03-cli-integration
plan: 03
subsystem: cli
tags: [indicf5, tts, ux, guardrails]

# Dependency graph
requires:
  - phase: 03-cli-integration-02
    provides: IndicF5 TTS pipeline wired to CLI
provides:
  - Audio duration validation (5-12s range check)
  - CPU warning (no CUDA detection)
  - First-run download message (~1.4GB)
affects: [future CLI enhancements]

# Tech tracking
tech-stack:
  added: [torchaudio (audio loading)]
  patterns: [UX guardrails with Rich warnings]

key-files:
  created: []
  modified:
    - src/indic_voice/cli.py

key-decisions:
  - "Used torchaudio.load for duration calculation (consistent with IndicF5 pipeline)"

patterns-established:
  - "UX guardrails: validation functions with ValueError for clear error messages"

requirements-completed: [CLI-04, CLI-05, CLI-06]

# Metrics
duration: 2min
completed: 2026-04-18
---

# Phase 03 Plan 03: UX Guardrails Summary

**Added audio duration validation, CPU warning, and first-run IndicF5 download message to CLI**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-18T17:22:00Z
- **Completed:** 2026-04-18T17:24:44Z
- **Tasks:** 5
- **Files modified:** 1

## Accomplishments
- Added `validate_ref_audio()` function to check audio duration (5-12s range)
- Added `check_device_warning()` function to warn users running on CPU
- Wired validations into both clone and translate commands
- Added first-run IndicF5 download message (~1.4GB)

## Task Commits

1. **UX Guardrails (Tasks 1-5)** - `6d99d9d` (feat)

**Plan metadata:** `607ddce` (docs: complete plan)

## Files Created/Modified
- `src/indic_voice/cli.py` - Added validation functions and wired into both commands

## Decisions Made
- Used torchaudio for audio loading (consistent with IndicF5 pipeline which uses torchaudio)
- Used Rich console for warnings (matches CLI's existing output style)
- Added download message before model load to prevent user confusion on first run

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## Next Phase Readiness
- CLI now has proper UX guardrails
- Ready for any future CLI enhancements

---
*Phase: 03-cli-integration-03*
*Completed: 2026-04-18*