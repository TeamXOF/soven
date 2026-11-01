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
