# SOVEN handoff

Read [analysis/soven/00_START_HERE.md](analysis/soven/00_START_HERE.md), then [decisions and continuation](analysis/soven/10_DECISIONS_AND_HANDOFF.md). These maintained files supersede historical SpeakFlow roadmaps. Delivery and validation records contain exact completed checks. The language inventory and account/profile APIs are implemented. The illustrated signup/profile/library/book journey is implemented. New language engines and Meta runtime integration remain pending.

Refresh navigation with `python tools/build_source_catalog.py`. Regenerate Word snapshots with `python tools/build_handoff.py`; install `docs/requirements-docs.txt` and render/review every changed page. Text-source hashes normalize CRLF to LF so they match Windows and Linux. DOCX hashes use exact binary bytes.

[Publication receipt](analysis/soven/PUBLICATION_RECEIPT.json) preserves the original launch snapshot. [Account/profile validation](analysis/soven/ACCOUNT_PROFILE_VALIDATION.json) preserves the account milestone; later provider/speech records and GitHub CI show subsequent checks.

The current remote is https://github.com/TeamXOF/soven.git. Continue the first unblocked task in [the checklist](analysis/soven/07_IMPLEMENTATION_ROADMAP.md), use [adopted defaults](analysis/soven/11_PRODUCT_DEFAULTS.md), and update [the execution log](analysis/soven/12_EXECUTION_LOG.md) after each acceptance check.


Current boundary: the owner supplied the UI references and the connected redesign is implemented. Read [account API integration](analysis/soven/14_ACCOUNT_PROFILE_API.md); backend-wide completion enforcement stays opt-in for remaining legacy-route compatibility.

See [UI implementation](analysis/soven/15_UI_DESIGN_AND_IMPLEMENTATION.md) and the live checklist for remaining release gates.

Read analysis/soven/16_REASONING_PROVIDER_INTEGRATION.md before changing providers. Adapter contracts are implemented and mock-tested; Google is default, live permitted access remains open, and hosted Meta must not be enabled from this Pakistan environment. Run both backend test files; no silent cross-provider fallback is allowed.

M2.1 is complete. Read analysis/soven/17_SPEECH_EVALUATION_PROTOCOL.md before M2.2. Run backend/tests/test_speech_evaluation.py with the existing suites. Use the pinned reference/profile and private preregistration checks; old speakers are exposed, and no new quality result is claimed. Do not use historical printed prompts as verbatim ASR references.

M2.2a/b are complete. Read analysis/soven/18_SPEECH_RUNNER_AND_FINDINGS.md and run all four backend suites. The beam-five profile is an unpromoted exposed-development candidate; production decoding is unchanged. Keep private reports/exposure.sqlite3 out of Git and preserve exposure across environments. M2.2c still needs sufficient improvement and reviewed verbatim evaluation data; never present printed-prompt edit rates as ASR WER.

M2.4 is complete. Read analysis/soven/19_SPEECH_CAPABILITY_SELECTION.md and SPEECH_CAPABILITY_VALIDATION.json before changing speech routes. Run all five backend suites, tools/test_speech_playback.cjs and affected isolated browser flows. English/Urdu route mechanics are implemented; neither voice coverage nor speech quality is established. M2.5 is next but has not started.
