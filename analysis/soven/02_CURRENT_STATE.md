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

Browser speech synthesis is available when the device has an appropriate voice; availability and network behavior vary. No neural TTS service, live verified Meta use, Muse Image story generation, Spanish track or real-time interrupting coach is implemented. Meta/compatible reasoning adapter mechanics are mock-tested.

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

SOVEN is public at https://github.com/TeamXOF/soven; TRANSFER_RECEIPT.json verifies repository identity, redirect and owner access. No unidentified collaborators were added.

The shared registry contains 89 candidate languages; only English/Urdu are enabled. Generated contracts, explicit language gates and the read-only public capabilities API reject unsupported reading instead of silently substituting English. Metadata exposes no credentials, learner data or inference. Provider implementation does not establish availability. Dated foundation/account evidence is retained in FOUNDATION_VALIDATION.json and ACCOUNT_PROFILE_VALIDATION.json.

## Account and profile backend completion

POST /api/auth/register-adult creates an approved independent reader in an owner-bound personal scope without teacher privileges. The technical role remains student; reader_mode distinguishes adult. Mode is self-declared, not verified age; internal grade 0 is an unset sentinel, not placement. Personal join codes are not exposed or accepted by child signup.

Authenticated GET/PATCH /api/auth/profile stores four separate language preferences, optional accessibility and completion state. Saves reject stale versions. Reading/interface accept en/ur; candidate native/translation preferences do not enable engines or translation. New child/adult profiles start incomplete and require a native language to complete. Existing accounts are grandfathered.

Schema v3 backs up versioned databases and preserves scores, attempts and tokens. Backend-wide completion enforcement is tested but opt-in for legacy compatibility. The connected UI below now applies saved settings and guides incomplete readers to their profile. ACCOUNT_PROFILE_VALIDATION.json preserves the 61-test account milestone; UI_REDESIGN_VALIDATION.json records the later 62-test UI checks.

## Reference driven interface milestone

The owner has now supplied the preferred design. New public landing, browser-local microphone check, child/adult signup, connected profile form, reader home, illustrated library, checkpoint book reader, language catalogue and data-use explanation are implemented. Real account/profile/catalogue/session APIs drive the journey. Optional larger text, spacing, contrast and word/coach guidance apply in the new reader. Teacher/classic/dynamic routes retain their underlying behavior. The earlier design-hold notes describe the preceding milestone, not the current authorization.

New accounts see honest empty history. Book progress and unlock presentation can be filtered by reading language; English does not unlock Urdu books. The recording hook handles delayed microphone permission and route teardown. Word-help and spoken guidance reuse existing providers/browser voices, with explicit source/unavailable labels. See 15_UI_DESIGN_AND_IMPLEMENTATION.md and UI_REDESIGN_VALIDATION.json. Anonymous AI sample analysis, free-form coaching, new language engines/live providers, physical-device/educator validation and public production safeguards remain unfinished.

## Configurable reasoning milestone

Default Google and opt-in Meta/compatible reasoning adapters pass 18 mocked contracts for structured output, validation, provenance, limits and fallback. The UI journey passes 19 controlled browser scenarios; frontend checks pass. Live permitted access and measured provider quality/cost remain open. See guide 16 and REASONING_PROVIDER_VALIDATION.json.

## Frozen speech evaluation foundation

The frozen reference, preregistration and bounded offline runner now pass 52 focused tests. Five synthetic controls pass. Historical reproduction matches the old 29/110 acceptable-word flags; a predeclared beam-five variant yields 24/110 with the same 4/5 expert-error flags. This exposed-sample signal is insufficient for promotion. Production decoding is unchanged, and fresh recognition quality remains unvalidated. Read guides 17–18.
