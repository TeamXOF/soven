# Working on SOVEN

Read analysis/soven/00_START_HERE.md and 10_DECISIONS_AND_HANDOFF.md before editing. Numbered Markdown files are the maintained source; DOCX files are generated snapshots. Historical files do not override current user instructions or completed repair evidence.

Preserve existing user changes. Keep scope to the agreed milestone. Preserve classroom/record isolation, signup linking, history, transcript-based word scoring, explicit unavailable evidence, no emotion inference, guarded recordings and quiet notifications. Do not turn unsupported model output into clinical or phonetic claims.

Run python backend/tests/test_regressions.py and the frontend lint, TypeScript and production-build checks appropriate to changes. Use the isolated browser harness for affected reading/auth flows. Never point tests at a real classroom database. Keep private environments, keys, recordings, models, runtime logs and original planning documents out of Git.

Update current state, requirements/decisions and validation evidence when behavior changes. Refresh the source catalogue and generated document manifest after material edits. Do not claim future features or a provider migration merely because branding changed. Follow the owner's actual authorization for external publication and communication.


The current public repository is TeamXOF/soven. Use the live checklist in analysis/soven/07_IMPLEMENTATION_ROADMAP.md, adopted defaults in 11_PRODUCT_DEFAULTS.md and completion log in 12_EXECUTION_LOG.md. Select the next unblocked item, implement and verify it, then mark it checked with evidence and continue. Leave blocked or externally unvalidated items unchecked and state the dependency. Do not ask again for already authorized routine work.

shared/languages.json is the language inventory. Regenerate Python/TypeScript contracts with python tools/build_language_types.py and run --check. Candidate entries are not runtime support claims; enable a language only after its required content, speech, segmentation and feedback gates pass. Keep public capabilities metadata separate from protected inference and user records.

The owner supplied two illustrated UI references and authorized implementation. Read analysis/soven/14_ACCOUNT_PROFILE_API.md and 15_UI_DESIGN_AND_IMPLEMENTATION.md. The connected forms/library/book reader apply optional settings; candidate-language preferences still do not enable reading engines. Strict backend profile enforcement remains opt-in for legacy compatibility.


The owner has now supplied two cream/coral illustrated reading-platform references and explicitly authorized implementation without further permission. The UI design hold is resolved. Follow analysis/soven/15_UI_DESIGN_AND_IMPLEMENTATION.md, retain the approved SOVEN logo and accurate capability/privacy copy. Do not substitute sample statistics for user history.

Read analysis/soven/16_REASONING_PROVIDER_INTEGRATION.md before changing providers. Adapter contracts are implemented and mock-tested; Google is default, live permitted access remains open, and hosted Meta must not be enabled from this Pakistan environment. Run both backend test files; no silent cross-provider fallback is allowed.

M2.1 is complete. Read analysis/soven/17_SPEECH_EVALUATION_PROTOCOL.md before M2.2. Run backend/tests/test_speech_evaluation.py with the existing suites. Use the pinned reference/profile and private preregistration checks; old speakers are exposed, and no new quality result is claimed. Do not use historical printed prompts as verbatim ASR references.

M2.2a/b are complete. Read analysis/soven/18_SPEECH_RUNNER_AND_FINDINGS.md and run all four backend suites. The beam-five profile is an unpromoted exposed-development candidate; production decoding is unchanged. Keep private reports/exposure.sqlite3 out of Git and preserve exposure across environments. M2.2c still needs sufficient improvement and reviewed verbatim evaluation data; never present printed-prompt edit rates as ASR WER.
