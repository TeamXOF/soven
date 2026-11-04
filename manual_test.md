# Soven (SpeakFlow 2.0) — Manual Feature Testing Guide

**Document:** `manual_test.md`  
**Purpose:** Step-by-step manual QA test plan to verify all 13 Soven features and Meta AI integrations in your web browser.  
**Prerequisites:**  
- Backend running at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Frontend running at: [http://localhost:3000](http://localhost:3000)
- Browser: Google Chrome, Microsoft Edge, or Safari (Microphone permission allowed).

---

## Quick Navigation Matrix

| # | Feature to Test | Target URL | Key Action to Perform |
|---|---|---|---|
| **1** | Landing Page & 3-Step Guide | `/` | Verify Soven brand, problem hook, 3-step guide & Privacy Shield |
| **2** | 20s Pre-Signup Voice Test | `/onboarding/test` | Record 20s voice clip, check acoustic metrics & localStorage |
| **3** | 3 Reader Personas & Onboarding | `/onboarding/profile` | Select Dyslexia Mode, verify waived speed deductions |
| **4** | 2D Open Storybook UI | `/book/story_forest_01` | Verify 2-page book spread, center spine & illustrations |
| **5** | Dyslexia-Friendly Mode | `/book/story_forest_01` | Verify syllable splits, cream paper tint & wide typography |
| **6** | Live Voice Coach Turn | `/book/story_forest_01` | Intentionally hesitate (>0.8s), trigger "Hear Coach" + "Repeat Now" |
| **7** | Trilingual TTS Audio | `/book/story_forest_01` | Click speaker icons to hear neural English, Urdu, and Spanish |
| **8** | Audio Stats Dashboard | `/stats` | View Pitch Wave (65–2093 Hz), Loudness dB, and WCPM charts |
| **9** | Trilingual Support | `/languages` | Verify active EN, UR (Nastaliq), and ES language inventory |
| **10** | "Learn a Language" Toggle | `/book/story_forest_01` | Click translation icon in reader toolbar to reveal native meanings |
| **11** | Mobile / Tablet Responsiveness | Inspect (F12) | Toggle mobile viewport (390px), confirm 1-page vertical collapse |
| **12** | Privacy & Audio Ephemerality | Network Tab (F12) | Confirm zero raw audio retained and no student PII sent |
| **13** | 3-Tab Navigation & Sync Badge | App Sidebar | Verify Books, Stats, Profile tabs & `Online · Synced` indicator |

---

## Step-by-Step Manual Test Cases

---

### Test Case 1: Landing Page & How-To Guide
- **URL:** [http://localhost:3000/](http://localhost:3000/)
- **Steps:**
  1. Open [http://localhost:3000/](http://localhost:3000/) in your browser.
  2. Inspect the hero section.
  3. Locate the **Privacy Shield** badge.
  4. Review the 3-step visual onboarding guide.
  5. Click the primary button: **"Start 20s Voice Test"**.
- **Expected Results:**
  - [ ] App displays "Soven (SpeakFlow 2.0)" branding and dyslexia problem hook.
  - [ ] Privacy Shield badge states: *"Zero Student Audio Kept · 100% On-Device Anonymization"*.
  - [ ] 3-step visual guide reads: *"1. 20s Voice Test → 2. Pick Reader Mode → 3. Read in 2D AI Book"*.
  - [ ] Clicking the CTA navigates immediately to `/onboarding/test`.

---

### Test Case 2: 20-Second Pre-Signup Voice Test
- **URL:** [http://localhost:3000/onboarding/test](http://localhost:3000/onboarding/test)
- **Steps:**
  1. Observe the reading sentence on screen (default English: *"The little fox woke up early in the morning."*).
  2. *(Optional)* Switch language tab to **اردو (Urdu)** or **Español (Spanish)**.
  3. Click **"Start Recording"** (grant microphone permission when prompted).
  4. Read the sentence aloud into your microphone.
  5. Click **"Stop & Analyze"** (or allow the 20-second timer to auto-stop).
  6. Review the acoustic results card.
  7. Open Browser DevTools (Press `F12` -> `Application` tab -> `Local Storage` -> `http://localhost:3000`).
  8. Click **"Save Results & Pick Your Reader Mode"**.
- **Expected Results:**
  - [ ] Microphone records smoothly without browser permission errors.
  - [ ] Diagnostic analysis completes in <2 seconds and displays:
    - Starting Reading Level (e.g. *Level 2* or *Level 3*)
    - WCPM (Words Correct Per Minute)
    - Accuracy percentage
    - Pause count (>0.4s hesitations)
    - Pitch stability score
  - [ ] `localStorage` contains key `soven_diagnostic_result` with valid JSON data.
  - [ ] Clicking the continue button navigates to `/onboarding/profile`.

---

### Test Case 3: Mandatory Profile Completion & 3 Personas
- **URL:** [http://localhost:3000/onboarding/profile](http://localhost:3000/onboarding/profile)
- **Steps:**
  1. Check the top banner: it should display your recommended reading level from the 20s voice test.
  2. Click on each of the 3 persona cards to test interactive selection:
     - **Child Reader**
     - **Dyslexia Mode**
     - **Adult Learner**
  3. Select **"Dyslexia Mode"**.
  4. Notice the feature highlights: wide letter/word spacing, syllable splits, and waived speed penalties.
  5. Choose your native language (English, Urdu, or Spanish).
  6. Click **"Start Reading in 2D AI Book"**.
- **Expected Results:**
  - [ ] Persona cards toggle actively with visual highlight borders.
  - [ ] Explanatory note explains: *"Slow, careful reading is rewarded — raw speed and pause deductions are waived."*
  - [ ] Clicking the button saves profile preferences and redirects directly to the 2D Book.

---

### Test Case 4: 2D Interactive Open-Book UI
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. Inspect the visual layout on a desktop or laptop screen.
  2. Look at the left page: story illustration and coach avatar.
  3. Look at the center: realistic 3D paper spine dividing the two pages.
  4. Look at the right page: reading sentence, interactive word chips, microphone button, and page navigation controls (*"Try again"* and *"Next page"*).
- **Expected Results:**
  - [ ] Page resembles a warm physical open storybook with cream-tinted pages.
  - [ ] Center spine `.soven-book-spine` creates a distinct 3D visual division between left and right pages.
  - [ ] Story title, chapter/page counter (e.g. *Page 1 / 5*), and navigation buttons render cleanly.

---

### Test Case 5: Dyslexia-Friendly Reading Mode
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. Ensure Dyslexia Mode is active (indicated by badge in top toolbar: *"Dyslexia Mode Active"*).
  2. Inspect the typography of the story sentence.
  3. Verify wide letter tracking (`tracking-wider`) and comfortable line height.
  4. Check syllable hyphenation on multi-syllable words (e.g. `lit-tle`, `morn-ing`, `ap-ple`).
  5. Click the **Record** microphone button and read very slowly, deliberately pausing for 2–3 seconds between words.
  6. Click **Stop** to analyze.
- **Expected Results:**
  - [ ] Text uses high-legibility dyslexia styling on warm cream paper (`#FDFBF7`).
  - [ ] Pacing feedback indicator displays: *"Dyslexia pacing active: no pause penalty."*
  - [ ] WCPM fluency score is **not penalized** for pauses or slow reading speed — score is tied purely to word accuracy!

---

### Test Case 6: Live Back-and-Forth Voice Coach Turn
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. Click the microphone button to start recording Page 1 (*"The little fox woke up early in the morning."*).
  2. Deliberately mispronounce a word (for example, say *"box"* instead of *"fox"*, or pause for >1 second before saying *"early"*).
  3. Click the Stop button.
  4. Look at the right sidebar under **"Practice & feedback"**.
  5. Check the **Live Voice Coach** card.
  6. Click the **"Hear Coach"** button.
  7. Click the **"Repeat Now"** button.
- **Expected Results:**
  - [ ] The mispronounced or hesitated word is flagged with a red chip.
  - [ ] A dedicated card appears: **"Live Voice Coach: Let’s practice: '[flagged word]'"**.
  - [ ] Clicking **"Hear Coach"** plays the correct pronunciation aloud via Text-to-Speech.
  - [ ] Clicking **"Repeat Now"** immediately re-opens the microphone for a quick practice attempt.

---

### Test Case 7: Text-to-Speech (TTS) Audio Playback
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. In the reader toolbar at top right, click the **Speaker icon** (*"Listen to this page"*).
  2. Listen to the audio through your speakers/headphones.
  3. Tap any individual word in the sentence (e.g. click *"fox"* or *"morning"*).
  4. Test Urdu playback: Change story language to Urdu and click the speaker button.
  5. Test Spanish playback: In the URL, open `http://localhost:3000/book/story_forest_01?lang=es` and click the speaker button.
- **Expected Results:**
  - [ ] Audio plays clearly in English (`en-US-JennyNeural`).
  - [ ] Tapping an individual word speaks that word immediately with instant pronunciation help.
  - [ ] Urdu plays with natural Urdu accent (`ur-PK-UzmaNeural`).
  - [ ] Spanish plays with natural Spanish voice (`es-ES-ElviraNeural`).
  - [ ] If offline, browser `window.speechSynthesis` speaks as local fallback.

---

### Test Case 8: Full Audio Statistics Dashboard
- **URL:** [http://localhost:3000/stats](http://localhost:3000/stats)
- **Steps:**
  1. Navigate to [http://localhost:3000/stats](http://localhost:3000/stats).
  2. Review the top KPI cards: Reading Level, WCPM, Pause Count, Pitch Stability.
  3. Scroll down to the interactive **Recharts graphs**:
     - **Pitch Contour (F0: 65–2093 Hz)**: Hover your mouse over the blue line to see timestamped Hz values.
     - **Loudness & Energy Envelope (dB)**: Hover over the purple area chart to see dB intensity.
     - **WCPM vs Raw Speed Comparison**: Inspect the bar chart comparing correct words per minute against raw pace.
- **Expected Results:**
  - [ ] Recharts graphs render without errors or layout shifts.
  - [ ] Tooltips display exact acoustic values on hover.
  - [ ] Fluency summary explains how accuracy and pause detection formed the WCPM metric.

---

### Test Case 9: Trilingual Support & "Learn a Language" Toggle
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. In the reader toolbar, locate the **Languages icon** button (*"Toggle Learn a Language translation"*).
  2. Click the icon.
  3. Look directly beneath the English story sentence.
  4. Review the native Urdu / Spanish translation card that slides into view.
  5. Click the translation icon again to toggle it off.
- **Expected Results:**
  - [ ] Clicking the icon highlights it in amber.
  - [ ] Translation box appears: *"Learn a Language · Native Translation"*.
  - [ ] Displays accurate Urdu translation in Noto Nastaliq script or Spanish translation.
  - [ ] Smooth toggle transition on/off without re-rendering the page.

---

### Test Case 10: Cross-Device Responsiveness (Mobile vs Desktop)
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. Press `F12` in Chrome/Edge to open Developer Tools.
  2. Click the **Device Toggle** icon (or press `Ctrl+Shift+M`) to switch to mobile emulation (e.g. *iPhone 14* or *Pixel 7*, 390px width).
  3. Inspect the open-book layout.
  4. Scroll down to inspect the story illustration, text, and recorder controls.
  5. Rotate to Tablet view (768px width) and Desktop view (>1024px width).
- **Expected Results:**
  - [ ] On desktop (>1024px): 2-page horizontal spread with center spine.
  - [ ] On mobile (<768px): 2-page book collapses into a single-column vertical layout (`grid-cols-1`).
  - [ ] Microphone button and action buttons remain large, touch-friendly, and fully accessible.

---

### Test Case 11: Privacy-First Architecture & Cleanup
- **URL:** [http://localhost:3000/book/story_forest_01](http://localhost:3000/book/story_forest_01)
- **Steps:**
  1. Open DevTools -> **Network** tab (`F12`).
  2. Record a reading attempt and stop.
  3. Inspect the outgoing `POST /api/v1/story/analyze` network request payload.
  4. Inspect the response JSON payload.
  5. Check that no student real names, emails, or personal identifiers are transmitted.
- **Expected Results:**
  - [ ] Audio payload contains only the recording clip and checkpoint ID.
  - [ ] Server deletes temporary audio files immediately after acoustic grading.
  - [ ] Response returns aggregated accuracy, WCPM, and phoneme chips without PII.

---

### Test Case 12: 3-Tab Navigation & Live Sync Indicator
- **URL:** [http://localhost:3000/books](http://localhost:3000/books)
- **Steps:**
  1. Look at the left sidebar navigation.
  2. Confirm the 3 simplified views:
     - **2D AI Book** (`/books`)
     - **Voice Stats** (`/my-progress` or `/stats`)
     - **Mode & Language** (`/profile`)
  3. Check the bottom of the sidebar for the status badge:
     - When backend is running: Displays green pulse with **`Online · Synced`**.
  4. Simulate offline mode: Disconnect your internet connection or turn on Airplane mode.
  5. Observe the status badge.
- **Expected Results:**
  - [ ] Clean, uncluttered 3-tab navigation.
  - [ ] Status badge dynamically switches between **`Online · Synced`** and **`Offline · Synced Locally`**.
  - [ ] No crash or error screens when operating offline.

---

## Automated Smoke-Test Verification Command

If you want to run the automated probe suite before or after manual testing:

```powershell
python backend/tests/test_exhaustive_suite.py
```

Expected output:
```
======================================================================
STEP 2: FASTAPI BACKEND & API ENDPOINT EXHAUSTIVE VERIFICATION
======================================================================
[1.1] GET /                     -> HTTP 200 (Online, Meta Models Active)
[1.2] GET /health               -> HTTP 200 (Healthy)
[2.1] POST /api/auth/signup     -> HTTP 201 (PBKDF2-SHA256 SQLite verified)
[2.2] POST /api/auth/login      -> HTTP 200 (Session Token Acquired)
[2.3] GET /api/profiles/me      -> HTTP 200 (Profile Loaded)
[2.4] PUT /api/profiles/me      -> HTTP 200 (Dyslexia Persona Saved)
[3.1] POST /api/diagnostic-test -> HTTP 200 (WCPM & Level Calculated)
[4.1] Pipeline Formula          -> Dyslexia Penalty Waived (79.2 vs 70.2 WCPM)
[4.2] Acoustic Service          -> Pitch 65-2093 Hz & Loudness dB Verified
[5.1] POST /api/sync/ingest     -> HTTP 200 (SHA-256 Validated)
======================================================================
ALL STEP 2 BACKEND ENDPOINTS AND PROCESSES VERIFIED (100% PASS)
======================================================================
```

---

## Summary Checklist for 2-Minute Hackathon Demo Video

Use this quick checklist during your video recording:

- [ ] **0:00 - 0:20**: Open [`/`](http://localhost:3000/). Show Soven brand, dyslexia hook, 3-step guide, and **Privacy Shield** badge.
- [ ] **0:20 - 0:45**: Click **"Start 20s Voice Test"**. Record audio on [`/onboarding/test`](http://localhost:3000/onboarding/test). Show instant acoustic metrics (Reading Level, WCPM, Pauses, Pitch).
- [ ] **0:45 - 1:05**: Select **Dyslexia Mode** on [`/onboarding/profile`](http://localhost:3000/onboarding/profile). Emphasize that slow, careful reading is never penalized.
- [ ] **1:05 - 1:40**: Open the **2D AI Book** on [`/book/story_forest_01`](http://localhost:3000/book/story_forest_01). Show the 3D center spine, cream paper aesthetic, and syllable splits. Intentionally pause or mispronounce a word to trigger the **Live Voice Coach** ("Hear Coach" + "Repeat Now").
- [ ] **1:40 - 1:55**: Toggle **"Learn a Language"** to show instant Urdu/Spanish translation and neural TTS audio.
- [ ] **1:55 - 2:00**: Switch to the **Voice Stats** dashboard on [`/stats`](http://localhost:3000/stats) showing Recharts Pitch Contour and Loudness envelopes. Highlight the **Online · Synced** status badge and conclude on Pakistan Geographic Use Policy compliance via `SPEAKFLOW_LLM_BASE_URL`.

