---
phase: 02-indicf5-module
plan: 01
subsystem: Dependencies & Module Scaffold
tags: [dependencies, pinning, scaffolding, indicf5]
requires:
  - INDICF5-01 (Function signature spec)
  - INDICF5-03 (transformers version constraint)
  - INDICF5-04 (accelerate requirement)
  - INDICF5-05 (numpy upper bound)
provides:
  - IndicF5 module skeleton (tts_indicf5.py)
  - Pinned dependency set (pyproject.toml)
  - Test import contract (test_tts_indicf5.py)
affects:
  - 02-02-PLAN: IndicF5 Implementation (depends on module scaffold)
  - 02-03-PLAN: IndicF5 Testing (depends on test file structure)
decision_made: "Interface-first approach: define function contract before implementing inference logic"
duration_seconds: 120
completed_date: "2026-04-17T13:37:00Z"
---

# Phase 2 Plan 01: IndicF5 Dependencies & Module Scaffold Summary

**One-liner:** Pinned critical IndicF5 dependencies (transformers 4.49.0, numpy ≤1.26.4, accelerate 0.33.0) and created module skeleton with function signature contract.

## Execution Summary

| Task | Name | Status | Commit | Files |
|------|------|--------|--------|-------|
| 1 | Pin IndicF5 dependencies | ✅ PASS | b0a87c1 | pyproject.toml, uv.lock |
| 2 | Create tts_indicf5.py scaffold | ✅ PASS | f714ec5 | src/indic_voice/pipeline/tts_indicf5.py |
| 3 | Create test file placeholder | ✅ PASS | 9db4747 | tests/test_tts_indicf5.py |

**Plan Metrics:** 3 tasks | 3 files modified/created | 120 seconds | 0 deviations

## What Was Built

### 1. Updated pyproject.toml (Commit b0a87c1)

**Dependencies pinned:**
- `transformers==4.49.0` ✓ (exact version, prevents >=4.51 meta tensor error)
- `accelerate>=0.33.0` ✓ (new, enables distributed model loading)
- `numpy<=1.26.4` ✓ (upper bound, prevents numpy 2.0+ incompatibility)
- `torchaudio>=2.0.0` ✓ (maintained)

**uv sync results:**
```
Resolved 165 packages in 36.53s
Prepared 5 packages in 1m 34s
- Downgraded numpy: 2.4.3 → 1.26.4
+ Added accelerate: 1.13.0
```

All dependencies resolved with no conflicts. Lock file fully reproducible.

### 2. Created tts_indicf5.py Module (Commit f714ec5)

**File:** `src/indic_voice/pipeline/tts_indicf5.py` (33 lines)

**Module docstring:** Explains purpose — zero-shot Indic voice cloning using ai4bharat/IndicF5

**Function signature (lines 9-16):**
```python
def generate_speech(
    text: str,
    ref_audio_path: str,
    ref_text: str,
    output_path: str,
) -> str:
```

**Docstring (lines 17-32):**
- Google-style format (Args, Returns, Raises)
- Args: Describes each parameter with context (e.g., ref_audio_path: "5-12 seconds recommended")
- Returns: Confirms output_path returned for easy chaining
- Raises: Documents FileNotFoundError, ValueError, RuntimeError

**Implementation:** Raises `NotImplementedError` with clear message pointing to 02-02-PLAN

**Import verification:** ✓ Successful import with correct signature
```
Signature: (text: str, ref_audio_path: str, ref_text: str, output_path: str) -> str
```

### 3. Created test_tts_indicf5.py Placeholder (Commit 9db4747)

**File:** `tests/test_tts_indicf5.py` (18 lines)

**Module docstring:** Explains test scope per INDICF5-06 requirements
- Module imports without error
- Function signature and type hints
- Happy path verification
- Error handling verification

**Imports:**
```python
import os
import pytest
from unittest.mock import patch, MagicMock
from indic_voice.pipeline.tts_indicf5 import generate_speech
```

Matches existing test patterns (test_tts_sarvam.py structure).

**Placeholder note:** Clear comment indicating detailed tests come in Plan 02-03.

**Import verification:** ✓ Test file imports successfully

## Success Criteria — All Met ✅

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `uv run python -c "from indic_voice.pipeline.tts_indicf5 import generate_speech"` succeeds | ✅ | Import successful, signature verified |
| `uv run python -c "import tests.test_tts_indicf5"` succeeds | ✅ | Test file imports without error |
| `grep "transformers==4.49.0" pyproject.toml` exits 0 | ✅ | Line 31 confirmed |
| `grep "accelerate>=0.33.0" pyproject.toml` exits 0 | ✅ | Line 33 confirmed |
| `grep "numpy<=1.26.4" pyproject.toml` exits 0 | ✅ | Line 17 confirmed |
| TOML syntax valid | ✅ | tomllib parse successful |
| All must-have truths verified | ✅ | See below |

## Must-Have Verification

**Truths (from plan frontmatter):**

1. ✅ "transformers==4.49.0 is pinned in pyproject.toml (not >=4.51 which breaks with meta tensor error)"
   - Confirmed in pyproject.toml line 31
   - Lock file shows transformers==4.49.0 locked

2. ✅ "torchaudio>=2.0.0 and accelerate>=0.33.0 are listed as dependencies"
   - torchaudio>=2.0.0 on line 32
   - accelerate>=0.33.0 on line 33
   - Lock file shows accelerate==1.13.0 (satisfies >=0.33.0)

3. ✅ "numpy is upper-bounded to <=1.26.4"
   - pyproject.toml line 17: numpy<=1.26.4
   - Lock file: numpy==1.26.4 installed

4. ✅ "tts_indicf5.py module imports and defines generate_speech function signature"
   - Module created at src/indic_voice/pipeline/tts_indicf5.py
   - Function signature: (text: str, ref_audio_path: str, ref_text: str, output_path: str) -> str
   - Imports without error

**Artifacts (from plan frontmatter):**

1. ✅ **pyproject.toml**
   - Provides: Dependency pinning for IndicF5 (transformers, torchaudio, accelerate, numpy bounds)
   - Contains: ["transformers==4.49.0", "torchaudio>=2.0.0", "accelerate>=0.33.0", "numpy<=1.26.4"]

2. ✅ **src/indic_voice/pipeline/tts_indicf5.py**
   - Provides: Module skeleton with generate_speech function signature
   - Exports: ["generate_speech(text, ref_audio_path, ref_text, output_path) -> str"]

3. ✅ **tests/test_tts_indicf5.py**
   - Provides: Test file placeholder and imports setup
   - Contains: ["import pytest", "from indic_voice.pipeline.tts_indicf5 import"]

## Deviations from Plan

**None.** Plan executed exactly as written:
- No bugs encountered
- No missing functionality discovered
- No architectural decisions required
- All three tasks completed in sequence
- All verification criteria passed

## Architecture Decisions

**Decision: Interface-first approach**
- Rationale: Define function contract (signature, docstring, error handling) before implementing inference logic
- Benefits: Decouples interface from implementation; 02-02 can swap implementations without changing 02-01; test contract established before test implementation
- Applied in: Task 2 (function raises NotImplementedError with clear message; docstring fully documented)

## Threat Surface Assessment

No new security surface introduced in this plan:
- Module skeleton only; no inference code executed
- Dependencies are from trusted sources (transformers, accelerate from HuggingFace)
- Test file has no implementation yet
- Trust boundaries unchanged from existing pipeline

Threat mitigations from plan's threat_model will be applied in 02-02 (model loading, audio validation) and 02-03 (test coverage for error paths).

## Known Stubs

None. Intentional NotImplementedError in generate_speech is deferred implementation, not a stub blocking completion — future plan 02-02 will resolve.

## Next Steps

**Plan 02-02: IndicF5 Implementation** will:
1. Replace NotImplementedError with actual model loading (ensure_checkpoints, device selection)
2. Implement generate_speech logic (transcribe ref_audio, run IndicF5 TTS, write output)
3. Add error handling per threat_model (file validation, GPU device selection)

**Plan 02-03: IndicF5 Testing** will:
1. Expand tests/test_tts_indicf5.py with pytest fixtures
2. Test happy path (valid audio, valid output)
3. Test error paths (missing ref_audio, empty ref_text)
4. Mock model inference to avoid 500 MB checkpoint download in CI

---

## Self-Check: PASSED ✅

- [x] All 3 files created/modified exist on disk
- [x] All 3 commits exist in git log (b0a87c1, f714ec5, 9db4747)
- [x] pyproject.toml valid TOML syntax
- [x] Module imports without error
- [x] Test file imports without error
- [x] All must-have truths verified
- [x] All artifacts present with required contents
