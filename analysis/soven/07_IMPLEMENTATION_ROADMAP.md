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
- [ ] M1.6 Implement the configured reasoning-provider boundary and one permitted Meta/open-weight adapter with structured output, timeout and fallback tests. Live access requires actual provider details; do not invent credits or route around geographic restrictions.
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

- [ ] M3.1 Create the landing/how-to flow with one obvious reading action and a route for teachers.
- [ ] M3.2 Add the skippable short introductory sample before signup with permission, retry, anonymous rate/cost limits and accurate data-flow copy.
- [x] M3.3a Add backend profile state, child/adult/teacher modes and optional accessibility preferences. Evidence: core/reader_profiles.py and authenticated GET/PATCH /api/auth/profile.
- [x] M3.3b Add a tested completion enforcement gate with a recovery path. ENFORCE_PROFILE_COMPLETION defaults to 0 until the profile UI is usable; legacy accounts are grandfathered.
- [ ] M3.3c Build profile forms, completion routing and applied accessibility settings after the owner chooses the UI design. Stored settings alone do not apply presentation changes.
- [x] M3.4a Add independent adult registration with private owner-bound records; preserve classroom approval and child-first linking. Evidence: POST /api/auth/register-adult and isolation regressions.
- [ ] M3.4b Expose the adult signup choice and forms in the owner-selected UI. The existing signup page remains the child/classroom flow.
- [x] M3.5a Persist separate language preferences and migration defaults, backup version-2 databases and preserve historical attempts. Evidence: migration/idempotency/concurrent-save tests.
- [ ] M3.5b Connect server preferences to the new UI without overwriting existing browser choices or allowing stale account responses to apply settings.
- [x] M3.6a Verify account APIs, migration, concurrency, existing child linking and adult login/profile persistence with synthetic isolated tests. Evidence: ACCOUNT_PROFILE_VALIDATION.json.
- [ ] M3.6b Verify the complete new onboarding forms, routing, expired identity and denied-microphone journeys after those screens exist.

## Milestone four accessible responsive book

- [ ] M4.1 Build an illustrated desktop spread and single-page mobile sequence over shared reading state.
- [ ] M4.2 Start with reviewed, age-appropriate passages; keep generated drafts separate until content checks pass.
- [ ] M4.3 Add keyboard/touch navigation, stable target text, clear recording states and retry/next-page progression.
- [ ] M4.4 Add optional typography, line-height/spacing, contrast and pace controls appropriate to each script.
- [ ] M4.5 Pass an end-to-end book on desktop and a physical target phone, including RTL and long text.

## Milestone five spoken coaching and statistics

- [ ] M5.1 Add short user-requested/end-of-sentence coach turns as the default; automatic interruption stays optional future work.
- [ ] M5.2 Add word/sentence demonstrations, TTS voice discovery, mute/stop and retry without simultaneous listening/playback.
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

The owner asked to choose the design before UI redesign starts. Account/profile APIs and storage are ready. Stop here for the owner's design reference before M3.1, M3.2, M3.3c, M3.4b, M3.5b or book UI work. Do not turn the completion gate on while the UI has no completion form. Provider and speech-quality work remains independently waiting on the dependencies above.
