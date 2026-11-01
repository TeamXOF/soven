# SOVEN current implementation

The baseline has functioning local reading and teacher workflows. It is not a finished version of the new SOVEN vision. Test results describe bounded behavior, and the remaining recognition and production issues are material.

## Working application behavior

- Child account registration requires a classroom code. A student remains pending until teacher approval. Approval creates one reading profile or explicitly links an existing unoccupied profile, retaining its history. Same-name profiles require a choice; concurrent and repeated approvals are guarded.
- Teachers can copy the classroom code from Students or Settings. Add roster profile creates no credentials; it is optional teacher-led preparation.
- Authentication, record ownership and classroom boundaries cover HTTP and WebSocket paths. Tokens expire after 24 hours. Password changes and rejection revoke access. Global provider configuration and sync controls require server-administrator privileges.
- Three reading paths share scoring and reporting: the classic recording dashboard, fixed story checkpoints, and dynamically generated level attempts.
- Word match compares the recognized transcript to the target. Insertions, omissions, substitutions and word endings count consistently. Recognition confidence and pitch do not independently convert matched words into reading errors. Unicode punctuation, including Urdu full stops, does not become a scored word.
- Your Reading shows target/recognized pairs. Practice and Feedback distinguishes measured results, generated guidance, basic fallbacks, unavailable results and legacy metadata. Practice difficulty uses the current score. Progress requires a prior same-sentence, same-language comparison in the recent history window.
- Floating notifications are removed from the dashboard shell. The latest unresolved warning/error occupies page layout; dismissal is independent of bell read state. Completion appears with results. Recording controls lock during capture/processing; old responses cannot populate a new account.
- Teacher analytics, reports and practice libraries combine all three engines. Reader removal soft-archives records and preserves historical attempts. An administrator can restore and reapprove a reader.
- Persistent coaching jobs and sync retries recover after failure. Remote archival requires an authenticated receiver and matching acknowledgement. It is not bidirectional classroom database merging.

## Providers and offline behavior

Hosted reasoning still uses Google; online speech uses Groq, with local Whisper fallback. Provider availability has not been established by this import. Explicit offline mode disables outbound inference, probes and sync. Cached local model weights and dependencies are required. The prior tested model was base INT8 on CPU; the configuration default remains tiny unless changed, so reproduce benchmarks with an explicit model selection.

Browser speech synthesis is available when the device has an appropriate voice; availability and network behavior vary. No neural TTS service, Meta runtime adapter, Muse Image story generation, Spanish track or real-time interrupting coach is implemented.

## Measured limitations

The earlier physical microphone repeat produced an exact sentence match and 100% word match in 3.112 seconds on one browser/device. Earlier unmatched takes remain unadjudicated. This proves that workflow can work; it does not validate child pronunciation assessment.

The 20-speaker child-speech holdout flagged 29 of 110 expert-acceptable words and 4 of 5 expert-error words. Prompt-text edit rate was 34.78 percent, not pure ASR WER because the reference was the printed prompt. There is no equivalent Urdu benchmark or classroom noise/device study. Educator trials and learning-outcome evidence are absent.

On the prior eight-logical-CPU test machine, an eight-submission burst took about 11.47 seconds. A thirty-submission burst returned eight successes and twenty-two deliberate busy responses. Do not claim thirty-reader laptop capacity. Local HTTPS passed; publicly trusted deployment and sustained production load remain unverified.

## Verification baseline

The pre-import repair suite had 41 passing backend regressions, clean lint, TypeScript and a production build. Twelve isolated dashboard browser scenarios and the enrollment linking flow passed with synthetic accounts. See VALIDATION_RESULTS.json for the actual SOVEN-export rerun; do not substitute the earlier results for that run.

SOVEN branding does not implement future features or silently rewrite historical scores. Public repository setup, CI and the document-render review are tracked separately in the delivery record.

## Export validation repair

The SOVEN rerun exposed open SQLite startup and backup connections during Windows teardown. Both now close explicitly. A connection-lifetime regression raises the supported suite from 41 to 42 passing tests; the isolated dashboard command completes with clean temporary-database cleanup. Windows HTTPS proxy logs can still include peer-reset callbacks during browser abort scenarios; browser runtime errors and scenario failures were zero. This repair follows the imported baseline and is included in the SOVEN branding/delivery commit.

## Multilingual direction

The working reading languages remain English and Urdu. The owner confirmed a 70+ language goal on 1 November 2026. No additional language was implemented or validated by this brand/documentation revision. Spanish is a proposed addition within that wider goal. Provider language lists alone do not establish complete SOVEN support.

## Team ownership and first foundation

SOVEN is public at https://github.com/TeamXOF/soven. TRANSFER_RECEIPT.json verifies preserved repository identity, source head, redirect and admin access. The local origin points to TeamXOF. Existing organization defaults remain; no unidentified collaborators were added.

shared/languages.json now inventories 89 candidate languages with script/direction and separate capability status. Only English/Urdu are runtime-enabled. Generated Python/TypeScript types are checked for drift. GET /api/v1/capabilities publicly returns static language/provider metadata, without credentials, user data or inference. Provider presence in that inventory does not establish configuration or availability; Meta adapters remain planned.

Classic sentence generation and dynamic story routes reject planned/unknown language requests instead of silently substituting English. Existing session, scoring and ownership contracts are preserved. The frontend consumes generated reading-language types and rejects unsupported cached story-language preferences.

The foundation snapshot had 47 regressions, including five capability/gating/drift checks; the later account/profile suite has 61. Lint, standalone TypeScript and production build pass. Earlier foundation checks are in FOUNDATION_VALIDATION.json; current account/profile checks are in ACCOUNT_PROFILE_VALIDATION.json. Adopted defaults remain implementation targets until their checklist acceptance gates pass.

## Account and profile backend completion

POST /api/auth/register-adult now creates an approved independent reader, a private owner-bound personal scope and an incomplete profile, without a classroom code or teacher privileges. The technical role remains student for compatibility; reader_mode distinguishes adult. The adult declaration is self-reported, not verified age. Its internal grade 0 is an unset sentinel, not assessed placement. No personal join code is exposed, and child signup cannot use one.

Authenticated GET/PATCH /api/auth/profile stores separate reading/interface/native/translation preferences, optional accessibility choices and completion state. Reading/interface remain en/ur; native/translation can store candidate codes without enabling translation or new engines. Versioned saves reject stale updates. Schema v3 is additive, backs up existing v2 databases and preserves attempts, scores and tokens. Existing accounts are grandfathered complete; newly registered child/adult profiles are incomplete. Completion requires a native language; clearing it marks the profile incomplete.

ENFORCE_PROFILE_COMPLETION defaults to 0. Its tested opt-in gate blocks reading for incomplete readers while retaining profile and account recovery access. Leave it off until completion forms exist. Typed frontend API methods are ready, but adult signup/profile screens, server-to-browser preference hydration and presentation application are not implemented. No UI screens changed in this milestone; legacy child-focused labels are still present. The owner will choose the redesign before that work begins.

ACCOUNT_PROFILE_VALIDATION.json records 61 backend regressions, frontend checks and isolated child/dashboard/adult browser checks. These synthetic checks do not validate age, speech quality, provider access, physical devices or production capacity.
