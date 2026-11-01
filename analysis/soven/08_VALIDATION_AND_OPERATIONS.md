# SOVEN validation and operations

Run verification from the exported checkout. Private runtime outputs belong in ignored .qa or temporary directories, never in public source. Historical measurements are useful context but cannot certify a different machine, model or deployment.

## Setup and supported commands

Use Python 3.12, Node.js 20.9 or later, npm and FFmpeg. In backend, create a virtual environment and install requirements-dev.txt. Copy .env.example only when no private environment file exists. Bootstrap the initial administrator with python scripts/bootstrap_teacher.py --username teacher; it prompts for a password and prints the classroom code. There is no shared default teacher password.

Start the backend with python main.py. In frontend run npm ci, npm run build -- --webpack and npm start, or npm run dev for development. The Windows start_soven.bat performs setup/build and launches services; start_speakflow.bat is a compatibility wrapper. The interactive launcher has not been independently exercised by this delivery.

Prepare local speech dependencies and model weights before offline use. Set WHISPER_MODEL deliberately, because base-model measurements do not establish tiny-model performance. OFFLINE_MODE=1 disables outbound inference/probes/sync. Browser voices are device-dependent.

From the repository root, run python backend/tests/test_regressions.py. From frontend run npm run lint, npx tsc --noEmit --incremental false and npm run build -- --webpack. Tests use temporary databases and substituted providers, plus a real synthetic acoustic/decoder check. They never use the production classroom database.

For browser checks install Playwright and Chromium outside committed source, build the frontend, then run python backend/tests/validate_enrollment_runtime.py. The default exercises child signup, approval and existing-profile linking. Set VALIDATION_BROWSER_SCRIPT=validate_dashboard_ui.cjs for the twelve dashboard cases or validate_accounts_ui.cjs for adult/profile API integration through the unchanged login UI. VALIDATION_NODE and PLAYWRIGHT_MODULE support nonstandard runtime locations. Outputs go to .qa/runtime-validation. Tests use isolated real authentication, fake microphones and controlled analysis responses; they are not live speech-quality tests.

## Validation evidence and limits

The repaired baseline had 41 passing backend tests and clean frontend checks. The new-export rerun and its dependency environment are recorded in VALIDATION_RESULTS.json. Separate remote CI proves fresh installation only for its actual runner; it does not establish cloud-provider or physical-device behavior.

Historical physical evidence: one user-confirmed exact sentence, 100% word match, 3.112 seconds total, local fallback on the tested browser/device. Earlier mismatched takes are retained as unresolved observations. No raw physical recording is published.

Historical child corpus: forty public clips across separate development and holdout speakers. Holdout flagged 29/110 expert-acceptable words and 4/5 expert-error words. Printed prompts were not verbatim transcripts, so edit rates are not pure ASR WER or diagnostic sensitivity. Attribution and detailed limitations are in evidence/LIVE_VALIDATION.md and the referenced reports. No downloaded child recordings are published.

Historical capacity: eight simultaneous recordings completed in about 11.47 seconds; thirty submissions returned eight successes and twenty-two busy responses. This is a small single-burst test. Sustained thirty-reader operation, noise resilience, Urdu quality, educator value and learning outcomes remain open.

## Hosting and recovery

HTTPS recording needs a trustworthy secure origin outside localhost. Set NEXT_PUBLIC_API_URL before build for separate hosting, or proxy same-origin /api and /pipeline plus /ws upgrades. Configure backend allowed origins, host, port and ENV=production; reload is disabled by default. No public hosting or domain is provisioned by repository creation.

Use private persistent storage for SQLite and backups. The migration path backs up an existing unversioned database and preserves attempts. Archive instead of deleting a reader. Restore with python scripts/restore_reader.py STUDENT_ID, then reapprove the account. Test restoration on a copy before relying on it operationally.

Coaching jobs persist and retry; old results cannot overwrite newer attempts. Optional sync needs a dedicated long shared secret, HTTPS and a receiver acknowledgement. Received snapshots are archives, not merged school databases. Define retention and deletion for server data before collecting real learners' records.

## Failure checks before a demo

Exercise microphone denial, silence, unreadable/oversized recording, missing local weights, provider timeout/malformed output, queue saturation, offline transition, expired identity and page navigation mid-request. Confirm understandable inline errors and a retry path, correct source labels, stopped microphone tracks and no stale results after account changes.

Do not fix apparent accuracy by passing the expected sentence into STT or hiding substitutions. Keep timestamps, confidence and acoustics explicitly unavailable when a provider does not supply adequate evidence. Freeze candidate configuration before evaluating untouched speakers.

## Export validation repair

The SOVEN rerun exposed open SQLite startup and backup connections during Windows teardown. Both now close explicitly. A connection-lifetime regression raises the supported suite from 41 to 42 passing tests; the isolated dashboard command completes with clean temporary-database cleanup. Windows HTTPS proxy logs can still include peer-reset callbacks during browser abort scenarios; browser runtime errors and scenario failures were zero. This repair follows the imported baseline and is included in the SOVEN branding/delivery commit.

## Multilingual validation plan

The target is 70+ languages; current evidence covers English workflows and limited Urdu UI/scoring, not broad speech quality. Track recognition, segmentation, content, coaching, TTS, translations, layout and reports independently per language. Test browser audio formats, RTL, long text and non-whitespace scripts where applicable. Agree representative speakers and language-specific thresholds before marking a language validated. Provider locale entries and translated menus are insufficient evidence.

## Latest foundation checks

The language/provider foundation passes 47 isolated backend regressions, frontend lint, standalone TypeScript and a production build. Run python tools/build_language_types.py --check from the root to detect contract drift; it is also in CI. The new public metadata GET is regression-tested separately from protected inference/account routes. FOUNDATION_VALIDATION.json records post-transfer browser/CI evidence; older counts remain dated baseline history.

## Account profile validation and rollout

The supported suite now passes 61 backend regressions. Fourteen account/profile cases exercise adult isolation, teacher boundaries, profile field validation, shared signup throttling, owner rebinding, atomic registration, version conflicts, partial settings, completion gating and v2 migration backups. A focused rerun verifies no-store profile responses. Lint, TypeScript and production build pass. Isolated browser evidence covers nine enrollment checks, twelve dashboard checks and six adult/profile integration checks; see ACCOUNT_PROFILE_VALIDATION.json for measured scope and limitations.

Profile migration is additive. Before deploying, back up the private database and test the v2-to-v3 path on a copy. The migration creates a before-profiles backup for an existing versioned database before changes; protect it like the source database. Repeated startup preserves profile versions, preferences, old tokens and stored scores. Never publish these backups.

Leave ENFORCE_PROFILE_COMPLETION=0 while the legacy UI is deployed. Enabling it without a completion form would strand new readers at a 403; the authenticated profile endpoint remains accessible for recovery. New child/adult profiles begin incomplete; migrated accounts retain access. The later UI rollout must cover forms, error/conflict handling, auth refresh, browser-preference reconciliation and applied accessibility before enabling the gate. Adult content and legacy child-focused labels also remain UI work. Native/translation preference storage is not a new translation service or evidence of 89-language runtime support.
