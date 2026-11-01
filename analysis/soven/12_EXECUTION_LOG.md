# SOVEN execution log

This log records completed work and its acceptance evidence. The live checklist is 07_IMPLEMENTATION_ROADMAP.md. Dates below are 1 November 2026; precise transfer time and source commit are in TRANSFER_RECEIPT.json. Do not replace an older result with a new claim that was not measured.

## Team transfer

Completed M0.1 and M0.2: moved the existing public repository from Waleed-Khalid-dev/soven to TeamXOF/soven. Verified repository ID 1441605840, preserved commit 5f36be5819f2e4127f679024380c6f82059f01e1, public visibility, owner admin permission and the old URL redirect. Updated the local origin. The original SpeakFlow repository is unchanged; no unidentified collaborators were invited. Evidence: TRANSFER_RECEIPT.json.

## Recommended defaults and task tracking

Completed M0.3: recorded the owner's authorization and adopted defaults in 11_PRODUCT_DEFAULTS.md. Replaced the narrative roadmap with dependency-ordered checkboxes and evidence requirements. Selected defaults are targets; adult signup, introductory recording and book/coaching features are still pending implementation.

## Multilingual and provider foundation

Completed M1.1 through M1.5: added shared/languages.json with 89 candidates and only en/ur enabled; generated backend/frontend language types; added a read-only public capabilities response; connected existing API types and preferences; and described current versus planned providers without exposing configuration or credentials.

Repaired a real boundary issue in classic sentence generation and dynamic story routes: planned or unknown language input previously fell back silently to English. Existing routes now reject it before inference/scoring. Existing en/ur records and account boundaries remain intact. Five additional regressions cover false support claims, provider evidence gaps, unsupported-language rejection, public GET isolation and generated-type drift.

Verification: 47 backend regressions passed locally. Frontend lint, standalone TypeScript and production build passed. Local backend checks use the prepared dependency environment; fresh installation and post-transfer Actions execution require remote CI. Browser/signup rerun evidence and the final CI receipt are recorded in FOUNDATION_VALIDATION.json when completed.

Remaining: no new language engine or Meta adapter was enabled; real provider credentials, permitted access, budget and team identities remain unspecified. Next independent work is account/profile and language-preference persistence; real-model validation remains waiting on provider configuration. Checklist items for these are still unchecked.

## Post-transfer CI and handoff publication

Completed M0.4: the exact TeamXOF tree matches the published code commit 38e912cb3153d9b40a8ff97df7f082523106042d. Fresh Linux dependency installation, generated-language drift check and all 47 regressions passed. Frontend installation, lint, TypeScript and optimized build passed. CI: https://github.com/TeamXOF/soven/actions/runs/41294373171. All six Word companions were regenerated and all 24 pages inspected. The following documentation-only completion commit records this evidence; its own SHA cannot be embedded in its contents.

## Account profiles and language preference persistence

Completed M1.8, M3.3a/b, M3.4a, M3.5a and M3.6a: added independent adult signup, owner-bound personal scopes, strict versioned profile APIs, separate four-language preferences, optional accessibility settings and opt-in completion enforcement. New child/adult profiles are incomplete; legacy accounts are grandfathered and teachers stay completed. Migration v3 backs up existing versioned databases and preserves tokens/history. Child-first approval/linking remains intact. Grade 0 for adult storage is an unset sentinel; adult mode is self-declared, not age verification.

Changed backend auth, profile model/router, middleware, schema, bootstrap and sanitized validation errors; added frontend API contracts without changing screens. Fourteen new regressions bring the suite to 61; local frontend lint, TypeScript and optimized build pass. ACCOUNT_PROFILE_VALIDATION.json records browser evidence, precise scope and CI publication status. See 14_ACCOUNT_PROFILE_API.md for payloads, conflicts and recovery. Historical foundation evidence is retained.

The owner requested a stop at UI redesign to supply their preferred design. No UI screens were changed. Keep ENFORCE_PROFILE_COMPLETION=0 until completion forms/routing ship. Remaining M3 UI items stay unchecked; next action is the owner's design reference. Real provider configuration, language quality, public deployment and physical-device/educator validation remain open.


Remote verification of account code d909f34781e418070d5bffc7f30c92a8acc02edc passed fresh Linux backend/frontend installs, all 61 regressions, generated-type drift, lint, TypeScript and production build. CI: https://github.com/TeamXOF/soven/actions/runs/41301125811. Final corrected-proxy browser reruns passed nine enrollment, twelve dashboard and six adult/profile checks. The checklist now has 15 checked and 36 open items; the next UI work waits for the owner design reference.

All six Word companions were regenerated from maintained sources and all 28 page images reviewed, including unchanged pages verified by reviewed hashes. Document/source hashes and API catalogue were checked. The public pack includes 15 numbered guides and preserves older evidence as historical snapshots.

## Owner reference driven UI implementation

The owner provided two design boards and authorized continuous implementation. Resolved the design hold, retained the SOVEN mark and built the cream/coral/dark illustrated entry and reader journey. Added public landing/how-to and local microphone sample; child/adult signup, connected profile forms, real-data home/progress, illustrated bookshelf and checkpoint reader; language availability and privacy explanation. Word-tip and user-requested guidance playback use existing APIs/voices with source/error labels.

Repaired a language-progression issue while integrating books: GET /api/v1/stories now supports a validated optional language filter, and a new regression prevents English attempts unlocking Urdu books or foreign-reader access. Reworked useRecorder to close late-permission streams and clean up after navigation. Existing teacher, enrollment, classic score/feedback and dynamic routes remain. The first code pass passes 62 backend regressions, lint, TypeScript and production build; final browser/artifact/CI outcomes belong in UI_REDESIGN_VALIDATION.json. No new Meta provider, broad language engine, public anonymous inference or clinical claim was introduced.


UI code be43927230184c9e02c1ebbc8611202c79aa1399 passed fresh-install GitHub CI, including all 62 backend regressions and frontend checks: https://github.com/TeamXOF/soven/actions/runs/41321003114. Final browser runs passed 45 checks (18 new UI, 9 enrollment, 12 classic dashboard, 6 account compatibility), with no browser runtime errors. The tracker has 28 completed and 30 open items after splitting mechanics from external validation. A transient HTTP 408 on the original push was resolved by checking the remote and retrying the same commit; no history was rewritten. The next unblocked engineering task is the configured reasoning-provider boundary; live permitted access and speech-quality/production gates remain open.

The UI handoff now includes 16 maintained numbered guides, exact source/artwork manifests and six regenerated Word companions. All 31 final page images were reviewed. The source catalogue, document hashes, export review and mirrored handoff were checked before publication. The owner subsequently requested work to continue into the next unblocked engineering task without confirmation.

## Configurable reasoning adapters completed 1 November 2026

Followed the UI milestone with M1.6a: implemented opt-in Meta/compatible Chat Completions alongside default Google, explicit access/configuration gates, closed-schema requests, existing local validation, provenance outside generated JSON, request/response limits, timeouts, redacted failures and template fallback without silent provider switching. Extended frontend source contracts and legacy monitor/session labels; retained historical scores, cache labels and technical latency keys. No live new-provider calls or paid resources were used.

Verification: 62 existing backend regressions and 18 new mocked provider contracts pass; lint, standalone TypeScript and production build pass; the isolated illustrated journey now passes 19 scenarios with zero browser runtime errors, including controlled Meta-source guidance. A test-helper Windows encoding error was corrected before the final passing run; product Urdu files were unaffected. Existing enrollment/dashboard/account evidence remains the prior dated milestone. Added guide 16 and the provider validation record, corrected superseded design-hold wording, refreshed maintained handoff sources and scheduled regenerated DOCX/mirror/export review. M1.6b/M1.7 remain open for actual permitted access and invocation. Next independent work is the speech evaluation protocol/configuration freeze; physical devices, reviewed content, deployment and consent gates remain open.

Delivery checks complete: six Word companions rendered and all 33 final pages reviewed, with unchanged pages matched to prior reviewed hashes. Exact Markdown/DOCX/source hashes verified. Public export reviewed for credentials, private/runtime files, size and broken local links; handoff mirrored byte-for-byte to the original analysis folder. Empty optional provider notes remain null rather than the literal text None. CI runs both backend suites; publication outcome follows below.

Publication verified: commit 9cb7d61816f0426d93d0c7a10d67bc2931f84334 is public at TeamXOF/soven. Fresh-install CI passed both backend suites (62 + 18), language-contract drift, frontend lint, standalone TypeScript and production build: https://github.com/TeamXOF/soven/actions/runs/41328185301. Committed source/DOCX/Markdown hashes and all 66 mirrored handoff files match. This subsequent documentation-only commit records that evidence. Initial review for the next speech task confirms the old holdout remains a failed/uncertain quality signal; M2.1 is still open until its protocol and configuration are frozen. No new speech benchmark has run.

## M2.1 frozen speech baseline and protocol completed 1 November 2026

Pinned the cached faster-whisper base snapshot and four artifact hashes, six installed dependency versions, CPU/INT8/thread options and explicit decoding defaults. Sealed relevant source/profile hashes without new speech inference. Recorded all 40 historical speaker IDs and the 20 available audio hashes as exposed. Added private dataset validation/preregistration with verbatim/adjudicated references, separate targets and position labels, rights declaration, overlap/path/checksum checks and coverage gaps. Fixed engineering thresholds and sampling minima for English/Urdu/planned Spanish; none is a measured or clinical claim. Runtime decoder/defaults and enabled languages are unchanged.

Twenty new offline contracts pass, alongside the 62 application and 18 provider regressions. Added the CI hook, guide 17, freeze receipt and validation record. The next M2.2 work is a deterministic evaluation runner, development-data reproduction/model selection, then preregistered untouched evaluation when suitable human-reviewed data is available. Existing child-speech failures remain visible. A registration alone cannot prove consent/identity, score quality or prevent future manual reruns; those limits and the pending exposure ledger are documented.

M2.1 delivery review: six Word companions refreshed and all 35 final pages reviewed, including unchanged pages matched by prior reviewed hashes. Markdown/DOCX/source catalogue hashes verified. The actual cached model freeze and current source/environment check pass; no new learner inference ran. Public export inspected and the 18-guide handoff mirrored to the original analysis folder. Remote CI outcome is recorded after publication.

M2.1 publication verified: code commit 866d8570543bdc401eb2e97ff2404f40f2e8e4ab passed fresh-install GitHub CI with all 100 backend tests, frozen-profile check, generated-language drift, frontend lint, standalone TypeScript and production build. CI: https://github.com/TeamXOF/soven/actions/runs/41331965581. Exact remote tree, committed document/source hashes and all 70 mirrored handoff files match. The working tree was clean before this documentation-only evidence update. M2.2 remains open; no new recognition-quality result is implied.
