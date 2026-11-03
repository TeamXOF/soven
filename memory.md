# SOVEN — Developer Memory & Continuity Guide

> **Important**: This document preserves the full context, architecture, history, design decisions, verification evidence, and exact setup instructions so any engineer or collaborator can pick up work immediately without missing a step.

---

## 1. Project Overview & Hackathon Context

- **Project**: **SOVEN** (formerly SpeakFlow, public repository: [`TeamXOF/soven`](https://github.com/TeamXOF/soven))
- **Mission**: An agentic, privacy-first multilingual reading tutor for children and independent learners. It listens to a child read aloud, evaluates word-by-word accuracy, extracts real acoustic features (pauses, hesitations, rate), orchestrates a 5-agent pipeline to assess reading difficulty and engagement, and generates real-time, encouraging feedback and personalized practice drills using Meta Llama 3.
- **Hackathon**: **Meta Global AI Developer Hackathon** (hosted on Cerebral Valley)
  - **Portal**: `https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit`
  - **Deadline**: **Wednesday, November 4, 2026 at 9:00 PM EST**
  - **Pakistan Standard Time (Asia/Karachi)**: **Thursday, November 5, 2026 at 7:00 AM PKT**

---

## 2. Core Architecture & Tech Stack

```
                     ┌──────────────────────────────────────────────┐
                     │          Frontend (Next.js 16.2 / TS)        │
                     │  - Bookshelf & Checkpoint Reader (/books)   │
                     │  - Story Mode Adventure Map (/read)          │
                     │  - Sentence Practice Dashboard (/dashboard)  │
                     │  - Global Language Switcher [ EN | اردو | ES ]│
                     └──────────────────────┬───────────────────────┘
                                            │ HTTP / WebSockets
                                            ▼
                     ┌──────────────────────────────────────────────┐
                     │          Backend (FastAPI / Python 3.13)     │
                     │  - Auth & Strict Isolated Scopes             │
                     │  - Session & Checkpoint Engine               │
                     │  - 5-Agent Multi-Agent Orchestrator          │
                     │  - SQLite Database with Schema Migrations    │
                     └──────┬───────────────────────┬───────────────┘
                            │                       │
              ┌─────────────▼─────────┐   ┌─────────▼──────────────┐
              │     STT & Acoustics   │   │    Reasoning Engine    │
              │ - Groq Whisper Cloud  │   │ - Meta Llama 3.3 70B   │
              │ - Local faster-whisper│   │ - OpenRouter Gateway   │
              │ - Librosa (pitch/pause│   │ - Local Template Bank  │
              └───────────────────────┘   └────────────────────────┘
```

### Backend (`/backend`)
- **Framework**: Python 3.13 + FastAPI + Uvicorn
- **Database**: SQLite (`database/schema.py`) with versioned migrations (`schema_migrations`), zero-leakage test fixtures, and strict personal/classroom record isolation.
- **Speech Recognition (STT)**:
  - *Cloud*: Groq Cloud Whisper API (`whisper-large-v3`, ~1.2s latency, word-level timestamps).
  - *Offline Fallback*: Local INT8 `faster-whisper` (or standard `openai-whisper`), automatically engaged when offline or if API key is missing.
- **Acoustics**: `librosa` extracting real acoustic features (pause boundaries, duration, speech rates, pitch variance).
- **Reasoning Provider (`backend/services/reasoning.py` & `model_client.py`)**:
  - Provider: `chat_completions` (OpenRouter API gateway or native `api.meta.ai`).
  - Model: `meta-llama/llama-3.3-70b-instruct`.
  - Offline Fallback: Deterministic JSON template bank (`backend/data/feedback_templates.json`) covering all categories (`all_correct`, `hesitant`, `fluency`, `phoneme`, `strong`).

### Frontend (`/frontend`)
- **Framework**: Next.js 16.2.10 (App Router, webpack build) + React 19 + TypeScript + Tailwind CSS
- **Audio Capture**: In-browser MediaRecorder (`frontend/hooks/useRecorder.ts`) capturing 16kHz mono audio with explicit permission cleanup.
- **Speech Synthesis (TTS)**: Web Speech API (`frontend/lib/speech.ts`) mapped strictly to platform capability locales (`en-US`, `ur-PK`, `es-ES`) without silent fallbacks.

---

## 3. The 5-Agent Autonomous Pipeline (`POST /pipeline/run`)

When a child reads a sentence aloud, the audio and target text pass through a 5-agent sequential orchestration (`backend/agents/orchestrator.py`):

1. **Phonetic Analyst**: Compares spoken words against target sentence using normalized character alignment; identifies struggling words and specific phoneme/vowel substitutions (e.g., `woke` -> `wake`).
2. **Difficulty Assessor**: Evaluates word complexity, sentence length, and reading rate (WPM) to classify difficulty and identify reading hurdles.
3. **Engagement Tracker**: Analyzes pause durations, hesitations, and acoustic gaps; calculates hesitation scores and sets encouraging tone flags.
4. **Practice Generator**: Synthesizes child-friendly sentences targeting the exact struggling words identified in the current session.
5. **Progress Synthesizer**: Aggregates accuracy, tracks session attempt numbers, and persists student milestones.

---

## 4. Languages Implemented & Production Support

SOVEN strictly separates **verified reading languages** from **candidate languages**:

| Language Code | Language Name | Status | Stories & Checkpoints | STT Route | Live Reasoning / Word Tips |
|---|---|---|---|---|---|
| `en` | English | **Active** | 3 stories (15 checkpoints) | `en-US` (Groq/Local) | Meta Llama 3.3 70B |
| `ur` | اردو (Urdu) | **Active** | 3 stories (15 checkpoints) | `ur-PK` (Groq/Local) | Meta Llama 3.3 70B |
| `es` | Español (Spanish)| **Active** | 3 stories (15 checkpoints) | `es-ES` (Groq/Local) | Meta Llama 3.3 70B |
| `70+` | Wider Catalogue | **Roadmap** | Planned in `shared/languages.json` | Requires acoustic & phonetic gate | Planned |

> **Strategy Note on 70+ Languages**: Rushing 70+ languages with raw machine translation or untested speech decoders violates the hackathon rubric and academic standards. SOVEN enforces gates: content, script/segmentation, speech recognition, and phonetic feedback must pass verified contracts before a language is marked `enabled_for_reading: true`.

---

## 5. Offline Capabilities: What Works Disconnected

| Component | Online Mode | Disconnected / Offline Mode |
|---|---|---|
| **Speech Recognition** | Groq Whisper Cloud (~1.2s) | Local INT8 `faster-whisper` (on-device CPU/GPU) |
| **Acoustic Extraction** | Local Librosa | Local Librosa (never uses cloud) |
| **Feedback & Tips** | Meta Llama 3.3 70B via API | Local deterministic template bank (`feedback_templates.json`) |
| **Sentence Generation**| Dynamic LLM generation | Local difficulty sentence banks (`SENTENCE_BANKS_ES/UR/EN`) |
| **UI & Audio Capture** | Fully client-side Next.js | Fully client-side Next.js |

---

## 6. How to Set Up & Run the Project

### Prerequisites
- Node.js 18+ (tested with Node 20 & 24)
- Python 3.11+ (tested with Python 3.13 on Windows)
- FFmpeg installed and in PATH (or configured in `backend/.env`)

### Step 1: Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure Environment (`backend/.env`)
Create `backend/.env` with your API keys:
```ini
# Database & Network
DATABASE_URL=database/speakflow.db
HOST=127.0.0.1
PORT=8000
OFFLINE_MODE=0
ENABLE_MOCK_ANALYSIS=0
STT_MODE=auto

# STT Provider (Groq Whisper)
GROQ_API_KEY=your_groq_api_key_here

# Reasoning Provider (Meta Llama 3.3 via OpenRouter or Meta API)
REASONING_PROVIDER=chat_completions
REASONING_MODEL=meta-llama/llama-3.3-70b-instruct
REASONING_BASE_URL=https://openrouter.ai/api/v1
REASONING_API_KEY=your_openrouter_or_meta_api_key_here
REASONING_ACCESS_CONFIRMED=1
FEEDBACK_TIMEOUT_S=25
```

### Step 3: Run the Backend Server
```bash
# From repository root:
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at `http://127.0.0.1:8000/docs`.

### Step 4: Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 7. How to Verify Everything Compiles & Tests Pass

Run these commands before any commit or pull request. **All must pass with 0 errors:**

```bash
# 1. Check Language Contracts
python tools/build_language_types.py --check

# 2. Run All 5 Backend Test Suites (159 tests)
python backend/tests/test_regressions.py
python backend/tests/test_reasoning_providers.py
python backend/tests/test_speech_evaluation.py
python backend/tests/test_speech_runner.py
python backend/tests/test_speech_capabilities.py

# 3. Run Speech Playback Tests (Node.js)
node tools/test_speech_playback.cjs

# 4. Run Live Spanish Verification
python tools/test_spanish_live.py

# 5. Frontend Checks (from frontend/ directory)
cd frontend
npm run lint
npx tsc --noEmit
npm run build -- --webpack
```

---

## 8. Chronology of Recent Major Milestones

1. **Team Transfer & Repository Setup**:
   - Transferred from `Waleed-Khalid-dev/soven` to `TeamXOF/soven`.
   - Setup clean CI workflows and maintained documentation snapshots.
2. **Account Profiles & Isolation**:
   - Implemented independent adult signups, personal scopes, strict versioning, and teacher isolation.
3. **Cream / Coral UI Redesign**:
   - Modern illustrated reading experience across bookshelf (`/books`), reader (`/book/[id]`), map (`/read`), and practice dashboard (`/dashboard`).
4. **Meta Llama 3 Reasoning Gateway**:
   - Created `backend/services/model_client.py` and `reasoning.py` supporting both native Meta protocol (`api.meta.ai`) and OpenRouter gateway.
   - Pydantic schema validation ensuring strict structured JSON feedback.
5. **Real-Runtime Audio Testing**:
   - Tested real user audio (`.qa/my_recording.m4a`).
   - Achieved 1.28s transcription latency, 89% accuracy, correctly caught `woke` -> `wake` vowel substitution, generated live Llama 3 advice and practice drills.
6. **Full Spanish (`es`) Implementation**:
   - Enabled `es` in contracts and speech capabilities.
   - Added Spanish text for all 3 books (15 checkpoints).
   - Added `SENTENCE_BANKS_ES` (easy, medium, hard).
   - Added Spanish offline templates and live phonetic analysis.
   - Added `ES` switch to the persistent global top bar, preferences, and language directory.
   - Verified 159 backend tests, TypeScript, and live end-to-end integration.

---

## 9. Current Status & Next Steps for Collaborator

- **Status**: The codebase is completely clean, compiling, and fully passing all 159 backend tests and frontend production builds.
- **Immediate Next Steps for Meta Hackathon Submission**:
  1. **Demo Video / Screencast**: Record a 2-3 minute walkthrough showing:
     - The landing page and mic check (`/try`).
     - Logging in and reading a storybook in English, Urdu, and Spanish.
     - Tapping a word to show live Meta Llama 3.3 pronunciation tips.
     - The 5-agent pipeline running live on a voice recording on the dashboard (`/dashboard`).
  2. **Submission Form**:
     - Submission portal: `https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit`.
     - Project GitHub URL: `https://github.com/TeamXOF/soven`.
     - Mention Meta Llama 3 integration in `backend/services/reasoning.py` and multi-agent pipeline in `backend/agents/orchestrator.py`.
