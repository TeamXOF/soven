# SOVEN architecture and engineering map

SOVEN is a Next.js frontend talking to a FastAPI backend with SQLite storage. Existing identifiers containing SpeakFlow are retained where they are technical contracts. Changing a display name does not require renaming every context, route, browser preference or table.

## Frontend structure

frontend/app uses the Next.js App Router with React 19, TypeScript, Tailwind and Recharts. Root ClientProviders wraps authentication, the classic reading context, student binding and the story session context. AuthGate protects the shared dashboard shell. KidAuthGate protects the fullscreen reading routes.

The dashboard shell includes dashboard, teacher, students, sessions, practice, reports, progress and settings routes. Story Mode lives outside that shell at /read; the dynamic level player is /read/play, while /read/[sessionId] handles story sessions. The root page is now the public landing/how-to experience; /home is the new reader entry and /teacher remains the teacher entry.

frontend/lib/api.ts is the typed HTTP boundary. HTTPS defaults to same-origin API routing; HTTP development defaults to the same host on port 8000. NEXT_PUBLIC_API_URL overrides this at build time. Requests carry stored bearer tokens. A late unauthorized response can clear only the token used for that request, not a newer login.

SpeakFlowContext owns classic recording state, sentence/language selection, results and notification history. It snapshots attempt identity and rejects stale responses. SpeakFlowSessionContext owns story/checkpoint state, asynchronous feedback, WebSocket authentication and polling fallback. useRecorder manages the dynamic recording path. Preserve the separate responsibilities until a deliberate consolidation is scoped.

## Backend flows and contracts

- /api/auth provides registration, login, identity, logout, password changes and teacher account approval/rejection. Teacher bootstrap is a local administrative script, not a public signup path.
- /pipeline/run accepts classic base64 audio, student ID, target sentence and reading language. It returns transcript, scored words, telemetry and diagnosis objects. Those object keys are retained for compatibility even though the UI no longer calls them diagnoses.
- /api/v1/sessions creates fixed-story sessions; analyze routes accept multipart recordings by checkpoint. Phase one contains scored reading evidence; phase two coaching arrives through authenticated WebSocket/polling.
- /api/v1/story provides dynamic level content, recording analysis, feedback and progression. Its attempts enter shared analytics.
- /api/v1/teacher and classroom/report routes expose scoped roster, summaries and reports. /api/students and /api/sessions preserve classic CRUD/list contracts.
- /api/v1/sync/ingest receives authenticated archival snapshots. Configuration and sync administration are restricted to server administrators.

API_MAP.md is generated from router decorators and supplements this overview. Use the source model and endpoint implementation for exact body/response validation; the initial branding delivery introduced no product endpoint; the later foundation adds the read-only capabilities endpoint described below.

## Speech and coaching data flow

Browser microphone capture creates an actual supported audio MIME type. The backend validates size, decodes recordings, invokes Groq or cached local Whisper, extracts descriptive acoustics with librosa, aligns recognized words to target tokens and computes word match. Temporary audio files are cleaned up. Transcripts, scores and results can remain in SQLite.

services/acoustic.py owns Unicode tokenization, alignment, morphology handling, word match, descriptive pitch/energy and pause detection. services/stt.py owns recognition and fallback. The expected target is not used to manufacture a perfect transcript. Estimated timing must stay marked as estimated and cannot imply exact word-level acoustic evidence. shared/speech-capabilities.json and core/speech_capabilities.py select the permitted recognition/playback route and derive speech_evidence. New classic/checkpoint evidence is stored in the additive speech_evidence table; dynamic attempts retain it in their existing result JSON. Exact word timing is preserved only when supplied and valid, and missing/partial timing propagates as unavailable rather than synthetic pause/phonetic evidence.

agents/orchestrator.py produces deterministic word observations, bounded generated guidance or templates, current-score practice selection and measured same-sentence history comparison. services/model_client.py uses stateless requests and output validation. services/reasoning.py serves other reading flows. services/jobs.py persists asynchronous coaching work; services/analytics.py merges historical formats.

## Storage and security

database/schema.py owns additive migrations, the unversioned-database backup, WAL/busy timeout and rollback behavior. students and users belong to classrooms; auth_tokens expire. Classic sessions and diagnoses coexist with story_sessions/checkpoint_results and story_levels/story_progress/story_attempts/story_phase2. Supporting tables store jobs, word-tip caches, sync retries, received archives, metadata and migration versions.

Classic stored accuracy uses a 0–1 historical unit; API/report adapters expose percentages where specified. Do not multiply an already-percentage value by 100. Same-sentence comparison returns percentage-point change, not a learning-gain estimate.

AccessMiddleware and core/access.py enforce identity, role, classroom and record ownership. Request size and per-user inference limits bound inputs. core/workload.py supplies a bounded audio pool. Password hashing uses salted PBKDF2 and constant-time comparisons. No broad security certification is implied by these controls.

## Operational boundaries

Deployments need same-origin /api and /pipeline proxy routes, /ws upgrades, HTTPS, appropriate origins and persistent private storage. Recording security depends on the browser context. Changing the language type from en/ur to include es later requires coordinated changes across STT, content, progression, UI, caches and tests.

Required fonts are self-hosted in frontend/app/fonts. Generated branding is in assets/brand/soven and frontend/public/brand. Preserve third-party notices. SOURCE_CATALOG.json contains current file hashes and discovered symbols rather than stale line-number promises.

## Implemented multilingual foundation and next work

shared/languages.json is the additive planning inventory. core/languages.py owns canonical identifiers and runtime guards; tools/build_language_types.py generates Python and frontend unions; routers/capabilities.py exposes the public read-only inventory. core/provider_capabilities.py separates adapter implementation from verified live availability. This boundary does not yet replace the existing provider implementations. Keep reading language, interface locale, native language and translation target distinct. Each language declares content, script/direction, recognition, timing, TTS, coaching, translations and validation status. Preserve existing en/ur APIs and stored records. Content, voices, tokenization, caches, progression, reports and preferences need coordinated changes. Whitespace tokenization cannot be assumed suitable for every script; define and test segmentation per language instead of silently applying the English path.

Runtime-enabled languages remain en/ur. Existing content engines still need language-specific content/segmentation work before any new language is enabled. frontend/lib/languages.ts defines language roles and typed capability responses; lib/api.ts exposes fetchPlatformCapabilities. Public access is limited to GET /api/v1/capabilities; inference and account records remain protected. Regenerate types after registry edits and run the drift check.


### Contract and access boundaries

The catalogue returns schema_version, target_minimum_languages and language rows. Each row separates content, recognition, word timing, coaching, speech playback, interface and translation status. enabled_for_reading is intentionally stricter than being listed. The capability response also describes Google/Groq/local/browser services, mock-tested reasoning adapters and planned Meta speech; it makes no network calls or credential checks.

Only the exact public metadata GET is exempted from AccessMiddleware authentication. POSTs to that path, neighbouring private paths and learner/inference endpoints still require approved identity. The backend returns copied metadata so a caller cannot mutate the process inventory. Existing record ownership, classroom scopes and generated-type validation remain in place.

### Changing language coverage

Edit the shared registry, run python tools/build_language_types.py, then run its --check mode and the backend/frontend checks. Regenerated Literal/union types keep canonical reading identifiers consistent without enabling every candidate. A real language addition also needs its content engine, STT/voice route, segmentation, coaching, history/reporting and evaluation. Do not enable it by configuration alone while the existing content paths still assume en/ur.

### Acceptance evidence and next adapter work

Five new regressions verify inventory claims, unsupported-language rejection before inference, identifier normalization, public-GET isolation and generated-type drift. The foundation had 47 cases; the account/profile snapshot had 61 cases. The provider inventory is descriptive foundation code; configured reasoning adapters now have mocked contracts; a permitted real invocation and measured language quality remain explicit next tasks.

## Account profiles and personal scopes

Migration v3 adds classrooms.kind and owner_user_id plus user_profiles keyed to users. Existing classroom rows retain kind classroom; existing accounts receive safe legacy completion defaults. Versioned databases receive a before-profiles backup before schema changes. Attempts, scores and token records are not rewritten.

Adult signup atomically creates a personal classroom, its owner account, a single reader row and an incomplete adult profile. It keeps technical role student and is_admin 0. Authentication verifies the personal owner binding on every request. Existing student/record authorization then limits reads to that reader; school teachers cannot manage another scope. Children still use pending classroom signup and explicit approval/linking. Teacher bootstrap creates a completed teacher profile.

core/reader_profiles.py defines strict profile input and defaults; routers/profiles.py exposes authenticated owner-only GET/PATCH /api/auth/profile with no-store responses. Updates require expected_version, merge optional accessibility fields and return 409 on concurrent or stale edits. reading_language and interface_language accept enabled en/ur; native_language and translation_language accept canonical candidate codes, independently nullable. Completion requires native_language. No role, mode, admin or classroom changes are accepted through this route.

AccessMiddleware includes adult signup in the shared IP registration bucket and provides the optional ENFORCE_PROFILE_COMPLETION gate. The flag remains opt-in for legacy compatibility; the new UI has profile completion routing. frontend/lib/api.ts includes apiRegisterAdult, fetchReaderProfile, saveReaderProfile and typed contracts; these do not mutate the active auth store automatically. The new UI guards profile responses by account token/identity and reconciles legacy browser preferences. See 14_ACCOUNT_PROFILE_API.md for payloads, recovery and rollout details.

## Connected illustrated interface

New client components under components/soven and routes /home, /books, /book/[storyId], /my-progress, /languages and /profile reuse existing auth, catalogue, session and feedback APIs. The public landing is rendered at /; /try uses browser-local capture/playback only. useRecorder now guards late permission and cancellation and exposes a completed Blob for bounded analysis. ReaderPreferences hydrates an explicitly saved account profile without replacing legacy browser defaults merely because a v1 profile exists. AuthProvider.setProfile updates only the current matching user.

BookReader ties results and word tips to token/route/attempt generation; phase-two polling is bounded. /api/v1/stories accepts an optional validated language query for checkpoint progress and unlock presentation. Existing callers that omit it retain the legacy aggregate contract. See 15_UI_DESIGN_AND_IMPLEMENTATION.md for route behavior, compatibility limits and recording lifecycle.

## Configured reasoning boundary

services/model_client.py selects one server-configured provider per call. Google keeps its existing model retry. Meta and explicit compatible endpoints use Chat Completions with closed schemas and no cross-provider fallback. ModelResult carries provenance outside generated fields; reasoning.py validates its existing Pydantic output and returns accurate source labels, while orchestrator.py preserves measured scoring and validated practice. Existing database source text fields accept new values without rewriting old records. Public inventory reports adapter implementation separately from live validation. See 16_REASONING_PROVIDER_INTEGRATION.md for configuration, bounds and retained cache/latency compatibility.

## Speech evaluation tooling

core/speech_evaluation.py validates frozen profiles, artifact/dependency/source checksums, private manifests, disjoint speakers/audio and sample coverage. tools/freeze_speech_evaluation.py exposes check/freeze/verify/register commands without inference or downloads. backend/data/speech_evaluation_profile.json declares the reference configuration; the public exposure registry retains historical IDs/hashes. Runtime stt.py is unchanged. Fresh quality evaluation remains next work; guide 17 defines the protocol.

The implemented runner is core/speech_runner.py with metrics in core/speech_metrics.py and CLI tools/evaluate_speech.py. It rehashes model/input bytes, runs a bounded offline child process, keeps references out of recognition, reserves persistent private SQLite exposure and writes sealed private reports. Explicit --profile binds a separately declared candidate; it does not change app configuration. Guide 18 records measured outcomes and remaining limits.
