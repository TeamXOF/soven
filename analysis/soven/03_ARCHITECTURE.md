# SOVEN architecture and engineering map

SOVEN is a Next.js frontend talking to a FastAPI backend with SQLite storage. Existing identifiers containing SpeakFlow are retained where they are technical contracts. Changing a display name does not require renaming every context, route, browser preference or table.

## Frontend structure

frontend/app uses the Next.js App Router with React 19, TypeScript, Tailwind and Recharts. Root ClientProviders wraps authentication, the classic reading context, student binding and the story session context. AuthGate protects the shared dashboard shell. KidAuthGate protects the fullscreen reading routes.

The dashboard shell includes dashboard, teacher, students, sessions, practice, reports, progress and settings routes. Story Mode lives outside that shell at /read; the dynamic level player is /read/play, while /read/[sessionId] handles story sessions. The root page is still an application entry redirect, not the proposed marketing landing page.

frontend/lib/api.ts is the typed HTTP boundary. HTTPS defaults to same-origin API routing; HTTP development defaults to the same host on port 8000. NEXT_PUBLIC_API_URL overrides this at build time. Requests carry stored bearer tokens. A late unauthorized response can clear only the token used for that request, not a newer login.

SpeakFlowContext owns classic recording state, sentence/language selection, results and notification history. It snapshots attempt identity and rejects stale responses. SpeakFlowSessionContext owns story/checkpoint state, asynchronous feedback, WebSocket authentication and polling fallback. useRecorder manages the dynamic recording path. Preserve the separate responsibilities until a deliberate consolidation is scoped.

## Backend flows and contracts

- /api/auth provides registration, login, identity, logout, password changes and teacher account approval/rejection. Teacher bootstrap is a local administrative script, not a public signup path.
- /pipeline/run accepts classic base64 audio, student ID, target sentence and reading language. It returns transcript, scored words, telemetry and diagnosis objects. Those object keys are retained for compatibility even though the UI no longer calls them diagnoses.
- /api/v1/sessions creates fixed-story sessions; analyze routes accept multipart recordings by checkpoint. Phase one contains scored reading evidence; phase two coaching arrives through authenticated WebSocket/polling.
- /api/v1/story provides dynamic level content, recording analysis, feedback and progression. Its attempts enter shared analytics.
- /api/v1/teacher and classroom/report routes expose scoped roster, summaries and reports. /api/students and /api/sessions preserve classic CRUD/list contracts.
- /api/v1/sync/ingest receives authenticated archival snapshots. Configuration and sync administration are restricted to server administrators.

API_MAP.md is generated from router decorators and supplements this overview. Use the source model and endpoint implementation for exact body/response validation; no new product endpoint is introduced merely by this branding delivery.

## Speech and coaching data flow

Browser microphone capture creates an actual supported audio MIME type. The backend validates size, decodes recordings, invokes Groq or cached local Whisper, extracts descriptive acoustics with librosa, aligns recognized words to target tokens and computes word match. Temporary audio files are cleaned up. Transcripts, scores and results can remain in SQLite.

services/acoustic.py owns Unicode tokenization, alignment, morphology handling, word match, descriptive pitch/energy and pause detection. services/stt.py owns recognition and fallback. The expected target is not used to manufacture a perfect transcript. Estimated timing must stay marked as estimated and cannot imply exact word-level acoustic evidence.

agents/orchestrator.py produces deterministic word observations, bounded generated guidance or templates, current-score practice selection and measured same-sentence history comparison. services/model_client.py uses stateless requests and output validation. services/reasoning.py serves other reading flows. services/jobs.py persists asynchronous coaching work; services/analytics.py merges historical formats.

## Storage and security

database/schema.py owns additive migrations, the unversioned-database backup, WAL/busy timeout and rollback behavior. students and users belong to classrooms; auth_tokens expire. Classic sessions and diagnoses coexist with story_sessions/checkpoint_results and story_levels/story_progress/story_attempts/story_phase2. Supporting tables store jobs, word-tip caches, sync retries, received archives, metadata and migration versions.

Classic stored accuracy uses a 0–1 historical unit; API/report adapters expose percentages where specified. Do not multiply an already-percentage value by 100. Same-sentence comparison returns percentage-point change, not a learning-gain estimate.

AccessMiddleware and core/access.py enforce identity, role, classroom and record ownership. Request size and per-user inference limits bound inputs. core/workload.py supplies a bounded audio pool. Password hashing uses salted PBKDF2 and constant-time comparisons. No broad security certification is implied by these controls.

## Operational boundaries

Deployments need same-origin /api and /pipeline proxy routes, /ws upgrades, HTTPS, appropriate origins and persistent private storage. Recording security depends on the browser context. Changing the language type from en/ur to include es later requires coordinated changes across STT, content, progression, UI, caches and tests.

Required fonts are self-hosted in frontend/app/fonts. Generated branding is in assets/brand/soven and frontend/public/brand. Preserve third-party notices. SOURCE_CATALOG.json contains current file hashes and discovered symbols rather than stale line-number promises.

## Planned multilingual foundation

Replace two-track assumptions through an additive language registry before expanding to 70+ languages. Keep reading language, interface locale, native language and translation target distinct. Each language declares content, script/direction, recognition, timing, TTS, coaching, translations and validation status. Preserve existing en/ur APIs and stored records. Content, voices, tokenization, caches, progression, reports and preferences need coordinated changes. Whitespace tokenization cannot be assumed suitable for every script; define and test segmentation per language instead of silently applying the English path.
