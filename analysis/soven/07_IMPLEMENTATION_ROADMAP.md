# SOVEN implementation checklist

Work from this checklist in dependency order. A checked item means the implementation and its acceptance evidence exist. An unchecked item is planned or waiting; it is never implied complete by a screenshot, provider language list or chosen product default. Record every finished task in 12_EXECUTION_LOG.md with files changed, checks, limitations and the next item. Keep historical evidence intact.

The current code uses the repaired reading baseline. The target is a worldwide platform with 70+ end-to-end reading languages. The shared inventory contains 89 candidate languages; only English and Urdu are enabled today. This is the catalogue foundation, not 89-language support.

## Milestone zero team ownership and working agreement

- [x] M0.1 Transfer the public repository to TeamXOF/soven and preserve repository identity, current commit, redirect and owner admin access. Evidence: TRANSFER_RECEIPT.json.
- [x] M0.2 Update the local remote and current repository links; preserve historical launch receipts and the original SpeakFlow repository.
- [x] M0.3 Record the owner's authorization to use recommended defaults. Evidence: 11_PRODUCT_DEFAULTS.md and decision register.
- [x] M0.4 Verify a successful GitHub CI run after the transfer and publish the updated handoff pack. Evidence: FOUNDATION_VALIDATION.json.

## Milestone one multilingual and provider foundation

- [x] M1.1 Create a shared candidate-language inventory with identifiers, names, script/direction, priorities and capability status. Evidence: shared/languages.json.
- [x] M1.2 Generate frontend and backend types from that inventory and check drift in CI. Evidence: tools/build_language_types.py and regression test.
- [x] M1.3 Gate existing reading routes on implemented languages; reject planned/unknown input instead of silently substituting English. Evidence: backend language-gate regressions.
- [x] M1.4 Expose a read-only public capabilities response without credentials, user data or inference. Evidence: GET /api/v1/capabilities and access-boundary regression.
- [x] M1.5 Connect existing frontend language types/preferences and add provider metadata that distinguishes current adapters from planned Meta adapters. Evidence: frontend/lib/languages.ts and backend/core/provider_capabilities.py.
- [x] M1.6a Implement configured Google/Meta/compatible reasoning adapters, structured-output requests, local validation, timeout/size bounds, accurate sources and failure tests. Evidence: guide 16 and REASONING_PROVIDER_VALIDATION.json; 18 mocked contracts, no live calls.
- [ ] M1.6b Verify a permitted account/endpoint, model license, regional availability and privacy configuration before enabling a new provider. Mocked adapter success does not establish this gate.
- [ ] M1.7 Verify one real permitted Meta invocation, record model/source/cost/latency and test its failure path. Waiting for verified account/access configuration.
- [x] M1.8 Persist separate reading, interface, native and translation language preferences with additive migrations. Evidence: user_profiles migration v3, profile API and ACCOUNT_PROFILE_VALIDATION.json. Enabling a stored candidate preference does not enable a reading engine.

## Milestone two speech reliability and coverage

- [ ] M2.1 Freeze a recognizer configuration and define language-specific release thresholds before evaluating untouched speakers.
- [ ] M2.2 Reproduce and improve the recorded child-speech disagreement; retain failed and uncertain observations rather than hiding them.
- [ ] M2.3 Validate Urdu on representative speakers, devices and noise; establish reviewed Spanish evaluation/content fixtures.
- [ ] M2.4 Implement explicit STT/TTS/timing capability selection and fallbacks per language. No timestamp or confidence fabrication.
- [ ] M2.5 Validate script-specific segmentation beyond the current English/Urdu aligner, including non-whitespace scripts where offered.
- [ ] M2.6 Publish the measured coverage matrix and enable each new language only after its end-to-end gate passes.

## Milestone three entry profiles and accounts

- [x] M3.1 Create the public landing/how-to flow, clear start action and teacher sign-in. Evidence: / and UI_REDESIGN_VALIDATION.json.
- [x] M3.2a Add a skippable 20-second browser-local microphone check with actual playback, permission/error handling and retry. No audio upload or AI score.
- [ ] M3.2b Add anonymous sample STT/feedback only after explicit server cost/rate/retention limits and consent are designed; keep the introductory sample non-diagnostic.
- [x] M3.3a Add backend profile state, child/adult/teacher modes and optional accessibility preferences. Evidence: core/reader_profiles.py and authenticated GET/PATCH /api/auth/profile.
- [x] M3.3b Add a tested completion enforcement gate with a recovery path. ENFORCE_PROFILE_COMPLETION defaults to 0 until the profile UI is usable; legacy accounts are grandfathered.
- [x] M3.3c Build connected versioned profile forms, new-journey completion routing and applied larger text/spacing/contrast/word/coach settings. Strict backend-wide enforcement remains opt-in for legacy compatibility.
- [x] M3.4a Add independent adult registration with private owner-bound records; preserve classroom approval and child-first linking. Evidence: POST /api/auth/register-adult and isolation regressions.
- [x] M3.4b Expose independent adult and classroom signup forms in the approved cream/coral design. Real HTTP registration and child approval/linking pass.
- [x] M3.5a Persist separate language preferences and migration defaults, backup version-2 databases and preserve historical attempts. Evidence: migration/idempotency/concurrent-save tests.
- [x] M3.5b Connect saved account preferences to the new UI, preserve unsaved legacy browser choices, and guard account/token identity on updates.
- [x] M3.6a Verify account APIs, migration, concurrency, existing child linking and adult login/profile persistence with synthetic isolated tests. Evidence: ACCOUNT_PROFILE_VALIDATION.json.
- [x] M3.6b Verify real adult forms/profile routing and browser denial/cancellation, plus preserved child approval and late-identity regressions. Evidence: isolated UI and compatibility scenarios.
- [ ] M3.6c Validate the complete onboarding journey on physical target devices and agree public child consent/age handling; browser automation is not that validation.

## Milestone four accessible responsive book

- [x] M4.1 Build an illustrated desktop spread and single-page mobile sequence using real checkpoint sessions; English/Urdu browser layouts pass.
- [x] M4.2a Connect the existing authored three-story English/Urdu corpus and generate matching cover/hero artwork with provenance.
- [ ] M4.2b Complete editorial, age-suitability and educator review of starter passages before learner release; do not treat existing content or artwork as validated review.
- [x] M4.3 Add native accessible controls, stable targets, explicit recording/processing states, duplicate-submit protection, retry and guarded next-page progression. Physical touch validation remains M4.5.
- [x] M4.4a Apply saved larger text, script-aware line spacing and high contrast to the new reader, with reduced-motion support.
- [ ] M4.4b Add user-adjustable playback/pace controls and validate script-specific accessibility with intended users.
- [x] M4.5a Pass desktop and narrow-browser book opening, capture, feedback, retry, next-page and Urdu RTL scenarios. Synthetic microphone/controlled analysis scope is explicit.
- [ ] M4.5b Validate full-book completion, long text and audio interruption on physical target phones, including iOS Safari.

## Milestone five spoken coaching and statistics

- [x] M5.1a Display existing post-reading guidance and add user-requested spoken playback with stop/unavailable-voice handling; capture stops speech first.
- [ ] M5.1b Build actual conversational coach turns and validate timing/latency; do not call one-way guidance free-form conversation. Automatic interruption remains deferred.
- [x] M5.2a Add word/page browser demonstrations, authenticated word tips, source labels, stop control and no simultaneous capture/playback.
- [ ] M5.2b Validate target-device voice coverage and any new TTS/provider/cache strategy before promising offline spoken support.
- [ ] M5.3 Reject stale coach turns and make uncertain recognition invite another attempt.
- [ ] M5.4 Add interpretable pause/pitch/energy graphs and separately defined WCPM, without speed deductions or emotion/health claims.
- [ ] M5.5 Test provider failure, unavailable voices, navigation, repeated attempts and real-device latency.

## Milestone six language learning and rollout

- [ ] M6.1 Expand the candidate inventory through reviewed stories, recognition, feedback and spoken-playback validation.
- [ ] M6.2 Validate English/Urdu/Spanish as the initial demonstration priorities; this subset does not reduce the 70+ product goal.
- [ ] M6.3 Add optional meanings, native-language translation and listen/repeat after the core reading journey is reliable.
- [ ] M6.4 Preserve separate language/task history, preferences, caches and teacher reports.
- [ ] M6.5 Reach 70+ end-to-end reading languages with recorded evidence. Provider-advertised coverage or translated menus alone cannot complete this item.

## Milestone seven deployment operations and submission

- [ ] M7.1 Choose hosting, domain, persistence and inference hardware after available accounts/credits/budget are known; no paid provision is authorized by a blank budget.
- [ ] M7.2 Deploy publicly trusted HTTPS, working API/WebSocket routing, persistent private storage and tested recovery.
- [ ] M7.3 Define and implement consent, retention/deletion and minimum stored reading data; preserve temporary-audio cleanup.
- [ ] M7.4 Measure sustained classroom load, bounded queues and busy/retry behaviour instead of assuming a class-size guarantee.
- [ ] M7.5 Run educator and target-user trials and physical mobile/browser checks; keep outcomes and limitations visible.
- [ ] M7.6 Verify submission requirements, prior-code disclosure, team roles and deadline in the actual participant portal.
- [ ] M7.7 Produce the demonstration and submission from features and Meta calls that actually work.

## Execution rule

After each task: implement, verify, update its checkbox, add a dated execution-log entry, refresh affected manifests/documents and move to the next unblocked item. Record the dependency when skipping a waiting item. Do not purchase services, invite unidentified collaborators or infer provider access from the defaults. Owner corrections supersede these defaults.

## Current design boundary

The owner supplied the two illustrated references and explicitly authorized implementation. The hold is resolved. The connected cream/coral entry/account/library/book journey is implemented; see 15_UI_DESIGN_AND_IMPLEMENTATION.md and UI_REDESIGN_VALIDATION.json. The next dependencies are anonymous sample service design, permitted provider configuration, stronger speech/content validation and physical-device/public-rollout work. Strict backend completion enforcement remains opt-in for compatibility with legacy routes.
