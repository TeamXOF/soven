# SOVEN Real-Runtime QA Validation Report — 2 November 2026

## Executive Summary

A real-runtime QA audit of SOVEN was conducted at commit `bcc66c8b4a1e787a7ce6e044dda54a891fe46aea` (branch `main`). The audit covered static checks, regression suites, isolated clean instance startup, end-to-end adult HTTP journeys, live cloud STT/coaching services with synthetic fixtures, and browser UI automation.

**Overall Verdict**: **Stable for the verified scope.**

One frontend omission bug was identified and resolved during this QA pass, backed by a new regression test and verified through all 23 browser journey scenarios.

---

## 1. Environment & Preflight Status

To respect credential isolation and safety boundaries, environment variable values are never displayed or logged. Configuration state is reported strictly using booleans:

| Check / Setting | Boolean Status | Detail / Scope |
|---|---|---|
| `backend/.env` Google keys present | `False` | Baseline repository template |
| `backend/.env` Groq key present | `False` | Baseline repository template |
| Uploaded environment Google keys present | `True` | In-memory overlay during live audit |
| Uploaded environment Groq key present | `True` | In-memory overlay during live audit |
| Meta reasoning provider access permitted | `False` | Restricted in Pakistan environment; zero Meta calls made |
| Offline mode enabled | `False` | Online mode active for live service audit |
| Mock analysis enabled | `False` | Real live analysis enabled for audit |
| Git repository status | Clean (`bcc66c8`) | Main branch, origin/main tracking |

---

## 2. Automated Test Suites & Verification Rerun

All backend test suites, browser voice contracts, frontend typechecks, and production builds were executed:

### Backend Suites (159 Tests)
- `python backend/tests/test_regressions.py`: **63 passed** (62 original + 1 added QA regression test `test_book_reader_component_renders_speech_evidence_pauses`).
- `python backend/tests/test_reasoning_providers.py`: **18 passed** (adapter contracts, schema validation, timeout redaction, local fallback).
- `python backend/tests/test_speech_evaluation.py`: **21 passed** (freeze contracts, receipt validation, corpus isolation).
- `python backend/tests/test_speech_runner.py`: **31 passed** (multiprocessing worker contracts, timeout enforcement, exposure ledger).
- `python backend/tests/test_speech_capabilities.py`: **26 passed** (STT/TTS route policies, evidence availability, pause detection, additive schema).
- **Total Backend Tests**: **159 passed, 0 failed**.

### Frontend Suites
- `node tools/test_speech_playback.cjs`: **15 checks passed** (browser voice selection contract, locale matching, stop handling).
- `npm run lint`: **Passed** (0 errors, 0 warnings).
- `npx tsc --noEmit --incremental false`: **Passed** (strict TypeScript compilation clean).
- `npm run build -- --webpack`: **Passed** (production build created clean optimized bundles for all 28 static/dynamic routes).

### Isolated Browser Journey
- `python backend/tests/validate_enrollment_runtime.py` with `validate_soven_ui.cjs`: **23 scenarios passed, 0 failed, 0 page runtime errors, 4 analysis submissions**.

---

## 3. Clean Real Backend Instance Check

A dedicated test instance was launched on `127.0.0.1:8000` with strict isolation:
- `DATABASE_URL` pointed to an isolated temporary database: `D:\[Project]\SOVEN\.qa\qa_audit_runtime.db`.
- Existing `speakflow.db` and classroom databases were untouched.
- `CLOUD_SYNC_URL` and `SYNC_SHARED_SECRET` were set empty to disable external sync attempts.
- Server startup and endpoint verification:
  - `GET /health`: **HTTP 200 OK** (`{"status": "ok", "api_key_count": 4}`)
  - `GET /api/v1/capabilities`: **HTTP 200 OK** (schema version 1, 7 providers inventory, enabled reading languages: `["en", "ur"]`, public notice present).

---

## 4. Real HTTP Adult Product Journey

Using a fresh synthetic adult account (`adult_auditor_qa`), the complete user lifecycle was exercised over HTTP:

1. **Adult Registration** (`POST /api/auth/register-adult`):
   - Result: **HTTP 201 Created** (`{"ok": true, "status": "approved", "profile_required": true}`)
   - Role assigned: `student` with `reader_mode: adult`. No classroom code required.
2. **Authentication** (`POST /api/auth/login`):
   - Result: **HTTP 200 OK**, issued bearer token, `profile_completed: false`.
3. **Profile Read & Update** (`GET /api/auth/profile`, `PATCH /api/auth/profile`):
   - Initial profile: version 1, `profile_completed: false`.
   - Update: set `native_language: "en"`, `reading_language: "en"`, `interface_language: "en"`, `complete_profile: true`, `accessibility: {"larger_text": true}`.
   - Result: **HTTP 200 OK**, version incremented to 2, `profile_completed: true`.
4. **Catalogue Retrieval** (`GET /api/v1/stories`):
   - English (`?language=en`): **HTTP 200 OK**, 3 stories returned (`story_forest_01`, `story_space_02`, `story_ocean_03`).
   - Urdu (`?language=ur`): **HTTP 200 OK**, 3 stories returned with Nastaliq titles.
5. **Session Creation** (`POST /api/v1/sessions`):
   - Created session for `story_forest_01` in English: **HTTP 201 Created**, 5 story checkpoints initialized.
6. **Cross-Account Security & Boundary Isolation**:
   - Registered a second synthetic adult account (`second_auditor_qa`).
   - Second user attempted `GET /api/v1/sessions/{session_id_of_user_a}`: **HTTP 403 Forbidden** (safe rejection).
   - Second user listed sessions via `GET /api/v1/sessions`: User A's session was **not** present (zero leak).
   - Unauthenticated request (no token): **HTTP 401 Unauthorized**.
   - Invalid token request: **HTTP 401 Unauthorized**.

---

## 5. Live Configured-Service Check (Real API Invocations)

> [!IMPORTANT]
> Audio safety boundary: Only the pre-existing synthetic control recording was used (`.qa/speech-evaluation/runner-v1/controls/correct.wav`, Microsoft Zira functional control). **Zero child, learner, or historical audio was transmitted.**

### Phase 1: Real STT Service Execution
- Audio submitted to `POST /api/v1/sessions/{session_id}/analyze` with `checkpoint_id="cp_1"`.
- Target sentence: *"The little fox woke up early in the morning."*
- **Outcome**:
  - HTTP Status: **200 OK**
  - Processing Latency: **4,512.3 ms**
  - STT Source: **`groq`** (Live Groq Whisper online API succeeded)
  - Accuracy Score: **100%**
  - Reading Speed: **166.7 WPM**
  - Checkpoint Result: **Passed**
  - Speech Evidence Metadata:
    - Provider: `groq`
    - Engine: `groq_whisper`
    - Fallback Reason: `null` (No fallback; online provider handled request)
    - Word Timing: `available`
    - Recognition Confidence: `unavailable` (*model token probability is never claimed as child pronunciation quality*)
    - Pause Assessment: `available`
    - Quality Validated: `false` (*explicit unvalidated boundary preserved*)

### Phase 2: Live Reasoning & Feedback Execution
- Background phase-two coaching was polled via `GET /api/v1/sessions/{session_id}/feedback/cp_1`.
- **Outcome**:
  - Polling rounds taken: 3 rounds (~3.0s total background time)
  - Feedback received: **`True`**
  - Feedback Source: **`gemini`** (Live Google Gemini API succeeded)
  - Feedback text generated: **`True`**
  - Comprehension question generated: **`True`**
  - Practice recommendation generated: **`True`**
  - Teacher note generated: **`True`**

---

## 6. Bugs Discovered & Resolved

### BUG-QA-01: Book Reader Missing Pause Evidence Indicator
- **Symptom**: `backend/tests/validate_soven_ui.cjs` timed out waiting for `Unavailable` text in the reading results panel during the book reader test flow.
- **Root Cause**: In commit `bcc66c8`, pause evidence display was added to `frontend/app/read/[sessionId]/page.tsx` (the classic reader) and added to the assertion in `validate_soven_ui.cjs`, but the corresponding pause observation JSX was omitted from the newly redesigned reader at `frontend/app/(app)/book/[storyId]/page.tsx`.
- **Fix Applied**: Updated `frontend/app/(app)/book/[storyId]/page.tsx` to render the pause evidence indicator:
  ```tsx
  <p className="soven-fine mt-2">{ur ? "وقفے" : "Pauses"}: <span>{result.speech_evidence?.pause_assessment === "available" ? result.hesitations.length : (ur ? "دستیاب نہیں" : "Unavailable")}</span></p>
  ```
- **Regression Guard**: Added `test_book_reader_component_renders_speech_evidence_pauses` to `backend/tests/test_regressions.py`.
- **Verification**: Rebuilt frontend with webpack. Executed `validate_soven_ui.cjs` via `validate_enrollment_runtime.py`; all 23 scenarios passed cleanly with zero page errors.

---

## 7. Explicit Boundaries and Limitations

1. **Synthetic Controls Only**: Real API testing was conducted strictly on synthetic control audio. Child learner speech remains unvalidated by these checks.
2. **Meta Reasoning Provider**: Meta reasoning access was not executed or enabled from this environment (per regional compliance policies in Pakistan). Adapters remain mock-tested.
3. **Urdu Speech Quality**: Urdu text and RTL layout function cleanly in the UI and catalogue, but Urdu speech recognition accuracy has not been validated against human child benchmarks.
4. **Planned Languages**: 89 languages are catalogued in capabilities metadata, but only English (`en`) and Urdu (`ur`) are runtime-enabled.
5. **Physical Hardware**: Browser automation verifies UI state transitions, synthetic Web Audio hooks, and fake microphone permissions. It does not validate physical microphone hardware, acoustic noise robustness, or mobile classroom acoustics.

---

## 8. Final Verdict

**SOVEN is stable for the verified scope.**

- Code integrity: Verified across 159 backend tests, 15 playback contracts, and 23 browser scenarios.
- Runtime isolation: Zero cross-tenant data leaks, strict session access control, clean temporary database disposal.
- Live services: Groq STT and Google Gemini reasoning respond accurately with correct source attribution, truthful evidence labels, and fallback readiness.
