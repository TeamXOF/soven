# Working on SOVEN

Read analysis/soven/00_START_HERE.md and 10_DECISIONS_AND_HANDOFF.md before editing. Numbered Markdown files are the maintained source; DOCX files are generated snapshots. Historical files do not override current user instructions or completed repair evidence.

Preserve existing user changes. Keep scope to the agreed milestone. Preserve classroom/record isolation, signup linking, history, transcript-based word scoring, explicit unavailable evidence, no emotion inference, guarded recordings and quiet notifications. Do not turn unsupported model output into clinical or phonetic claims.

Run python backend/tests/test_regressions.py and the frontend lint, TypeScript and production-build checks appropriate to changes. Use the isolated browser harness for affected reading/auth flows. Never point tests at a real classroom database. Keep private environments, keys, recordings, models, runtime logs and original planning documents out of Git.

Update current state, requirements/decisions and validation evidence when behavior changes. Refresh the source catalogue and generated document manifest after material edits. Do not claim future features or a provider migration merely because branding changed. Follow the owner's actual authorization for external publication and communication.
