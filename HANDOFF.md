# SOVEN handoff

Read [analysis/soven/00_START_HERE.md](analysis/soven/00_START_HERE.md), then [decisions and continuation](analysis/soven/10_DECISIONS_AND_HANDOFF.md). These maintained files supersede historical SpeakFlow roadmaps. Delivery and validation records contain exact completed checks. The language inventory and account/profile APIs are implemented. The illustrated signup/profile/library/book journey is implemented. New language engines and Meta runtime integration remain pending.

Refresh navigation with `python tools/build_source_catalog.py`. Regenerate Word snapshots with `python tools/build_handoff.py`; install `docs/requirements-docs.txt` and render/review every changed page. Text-source hashes normalize CRLF to LF so they match Windows and Linux. DOCX hashes use exact binary bytes.

[Publication receipt](analysis/soven/PUBLICATION_RECEIPT.json) preserves the original launch snapshot. [Account/profile validation](analysis/soven/ACCOUNT_PROFILE_VALIDATION.json) records current code checks; GitHub history and CI show subsequent commits.

The current remote is https://github.com/TeamXOF/soven.git. Continue the first unblocked task in [the checklist](analysis/soven/07_IMPLEMENTATION_ROADMAP.md), use [adopted defaults](analysis/soven/11_PRODUCT_DEFAULTS.md), and update [the execution log](analysis/soven/12_EXECUTION_LOG.md) after each acceptance check.


Current boundary: the owner supplied the UI references and the connected redesign is implemented. Read [account API integration](analysis/soven/14_ACCOUNT_PROFILE_API.md); keep completion enforcement off until forms and routing are usable.

See [UI implementation](analysis/soven/15_UI_DESIGN_AND_IMPLEMENTATION.md) and the live checklist for remaining release gates.
