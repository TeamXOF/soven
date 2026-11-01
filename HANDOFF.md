# SOVEN handoff

Read [analysis/soven/00_START_HERE.md](analysis/soven/00_START_HERE.md), then [decisions and continuation](analysis/soven/10_DECISIONS_AND_HANDOFF.md). These maintained files supersede historical SpeakFlow roadmaps. Delivery and validation records contain exact completed checks. The new product features are planned, not implied by branding.

Refresh navigation with `python tools/build_source_catalog.py`. Regenerate Word snapshots with `python tools/build_handoff.py`; install `docs/requirements-docs.txt` and render/review every changed page. Text-source hashes normalize CRLF to LF so they match Windows and Linux. DOCX hashes use exact binary bytes.

[Publication receipt](analysis/soven/PUBLICATION_RECEIPT.json) records the verified public commit, uploaded tree and passing fresh-install CI. The delivery record is an earlier dated snapshot.

The current remote is https://github.com/TeamXOF/soven.git. Continue the first unblocked task in [the checklist](analysis/soven/07_IMPLEMENTATION_ROADMAP.md), use [adopted defaults](analysis/soven/11_PRODUCT_DEFAULTS.md), and update [the execution log](analysis/soven/12_EXECUTION_LOG.md) after each acceptance check.
