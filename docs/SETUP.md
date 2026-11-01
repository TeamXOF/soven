# SpeakFlow development and deployment

This is the current setup guide after the codebase repair pass. The older Alibaba/Gemma decks, scripts and pitch documents describe earlier snapshots. Refer to `analysis/meta-hackathon-2026/REPAIR_LOG.md` for verified changes and remaining validation.

## Requirements

- Python 3.12, Node.js 20.9 or newer, npm, and ffmpeg.
- Speech recognition uses Groq online or a locally cached Whisper model. Download local weights while connected before claiming offline readiness.
- Optional Google reasoning generates content/coaching; unavailable reasoning falls back to templates. No Meta model has been integrated in this repair pass.
- The frontend uses browser microphone capture. Use localhost during development or HTTPS for other devices. A plain HTTP LAN address will not reliably support microphone permission.

## Backend

Run in `backend/`:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
.venv\Scripts\python scripts/bootstrap_teacher.py --username teacher
.venv\Scripts\python main.py
```

On macOS/Linux use `.venv/bin/python` in place of `.venv\Scripts\python` and `cp .env.example .env`. Keep an existing `.env`; fill in only the provider settings you need. Do not overwrite existing credentials or databases when following setup again.

The bootstrap command prompts for a new password and prints the classroom signup code. It creates or resets an explicitly selected administrator. There is no shared default teacher password. A legacy account using the former default is disabled until bootstrap resets it. Teachers can copy their classroom signup code from Students or Settings.

The usual enrollment flow is child signup first:

1. The teacher shares the classroom code; the child creates a username/password account at `/signup`.
2. The teacher opens Students (reload if already open) and reviews **Waiting for approval**.
3. Approve with **Create a new student profile**, or explicitly choose an existing roster profile to preserve its grade, level and reading history. A same-name profile requires a choice; names are never automatically merged.
4. Approval links the account to that profile and enables login. New profiles start at Grade 3 / Level 1; the teacher can edit those fields in the roster.

**Add roster profile** is optional teacher-led setup for a learner without a login. It does not create credentials. Link that profile when approving the child's later signup. Occupied, archived and other-classroom profiles cannot be selected for a new account; repeated approval does not create a duplicate.

Bootstrap another classroom with `--classroom another-class`. Teachers and students are scoped to their classroom. Bootstrap grants server administrator privileges; ordinary teacher accounts cannot change global provider keys or operate global sync.

Bearer tokens expire after 24 hours. Password changes and account rejection revoke existing tokens. Login again after changing a password.

Before the first schema migration of an existing unversioned database, startup makes a consistent SQLite backup in `.db_backup/`. Keep that backup private. Schema changes add fields/tables and retain existing attempts. Archiving a reader hides the profile and disables their login while preserving history. An administrator can restore a profile with:

```powershell
.venv\Scripts\python scripts/restore_reader.py STUDENT_ID
```

Reapprove the restored student before login.

## Frontend

Run in `frontend/`:

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. The local API defaults to the same hostname on port 8000. For separate hosting set `NEXT_PUBLIC_API_URL` to the HTTPS backend origin before building. With HTTPS and no explicit URL, the frontend uses same-origin `/api/*` and `/pipeline/*`; configure your reverse proxy accordingly, including `/ws/*` WebSocket upgrades.

Production backend settings include `ENV=production`, `ALLOWED_ORIGINS=https://your-frontend.example`, `HOST`, and `PORT`. `RELOAD=0` is the default. Production disables interactive documentation pages and mock endpoints. Serve the API through an HTTPS reverse proxy; CORS alone does not secure an endpoint.

## Reading results and privacy

All current engines use word-alignment results for reading accuracy, expressed as 0–100 in API reports. Classic stored accuracy retains its historical 0–1 unit; the reporting adapter converts it. An overall classic score now represents word accuracy, rather than combining pace with inferred engagement.

Missing speech confidence is unavailable. Estimated timestamps are marked and do not drive exact word-acoustic features or hesitation timing. Scores are engineering heuristics for reading support, not validated pronunciation/clinical diagnostics. Placeholder reference vectors are excluded from scoring even if an old environment setting enables references.

Word accuracy is transcript agreement. Low recognition confidence, pitch variation and quietness do not turn a matched word into a reading error. Recognition can still substitute or miss words. Local decoding uses voice activity detection without instructional/target-text prompts; silence returns a retry response without saving a failed attempt. `PITCH_ESTIMATOR=yin` is the default descriptive pitch extractor; `pyin` is optional and slower. Keep the tested PyAV pin when installing faster-whisper.

Online STT uploads recordings to Groq. Google reasoning receives reading text and observations when configured. Audio is not uploaded for emotion inference; emotions are not inferred from reading. Temporary recording files are removed after analysis, while transcripts/results remain in SQLite. Browser speech voices may use the network. Do not claim that online mode keeps all data on the device.

`OFFLINE_MODE=1` disables cloud reasoning, online STT, network probes and outbound sync. Local speech dependencies and cached model weights remain necessary. Browser voice availability must be tested on each target device. Offline content/template coaching are fallbacks with finite content, not equivalent guarantees of model quality.

Mock analysis defaults off. `ENABLE_MOCK_ANALYSIS=1` enables development simulations outside production. Simulations do not create attempts, change progress or unlock levels. The normal reader UI never substitutes a perfect transcript for an empty recording.

The classic dashboard shows Your Reading and Practice & Feedback. Flagged words pair the sentence with recognized speech; generated advice and basic fallbacks are labeled. Practice difficulty uses the current score. Progress comparisons require the same sentence and language; the chart filters by reading language. Historical scores are not rewritten. Floating notification popups are removed: errors/warnings appear below the top bar, completion beside results, and routine messages in bell history.

## Recovery and optional sync

Coaching jobs are saved locally before dispatch and retried after failures/restarts. Superseded checkpoint coaching cannot overwrite a newer recording. Audio work runs in a bounded worker pool rather than blocking the HTTP event loop.

For optional cloud archival, configure the sender's `CLOUD_SYNC_URL` to the receiver's `/api/v1/sync/ingest` and configure the same dedicated `SYNC_SHARED_SECRET` of at least 32 characters on both servers. Remote sync requires HTTPS. All three reading engines are supported; no raw recording files are included. Records become synced only after a matching identifier/digest acknowledgement. Retries are persistent and run while online, including after a failed initial upload.

The receiver stores idempotent snapshots in `sync_received`. This is archival replication, not automatic merging of multiple schools or a bidirectional roster synchronization system. Keep the receiver protected and plan retention/access controls for the hosted environment.

## Verification

Backend regressions use temporary databases and substituted providers; they never use a production classroom:

```powershell
python tests/test_regressions.py
```

Frontend checks:

```powershell
npm run lint
npx tsc --noEmit --incremental false
npm run build -- --webpack
```

For the optional real-browser enrollment check, install Playwright/Chromium and run `python backend/tests/validate_enrollment_runtime.py` from the repository root after building the frontend. It starts temporary local HTTPS/API/frontend servers and uses a disposable database. Set `VALIDATION_NODE` or `PLAYWRIGHT_MODULE` if those runtimes are outside normal executable/module lookup paths. It writes a credential-free report to `analysis/meta-hackathon-2026/runtime-validation/enrollment-results.json`.

The legacy live test scripts require `RUN_LEGACY_LIVE_TESTS=1` and separately configured isolated accounts. They are historical integration scripts, not the supported automated regression suite. Do not run them against a real classroom.

Before a public demo, test actual microphones, local/online STT, HTTPS on the intended devices, provider failures and realistic concurrent use. Synthetic audio checks verify processing mechanics, not accuracy on children's voices. Educator evaluation, learning improvement, global language coverage, Meta access and hackathon prior-code eligibility remain separate validation tasks.

See [measured runtime validation](../analysis/meta-hackathon-2026/LIVE_VALIDATION.md): cached local STT, browser recording over local TLS, a physical microphone request, and burst load tests have run. A small public child-speech holdout exposed substantial recognition/assessment disagreement; do not present the current recognizer as validated child-pronunciation assessment. Public HTTPS deployment and educator trials remain outstanding.
