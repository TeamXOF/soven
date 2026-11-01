# Dashboard feedback repairs — 31 October 2026

The screenshot review exposed presentation, notification, practice-selection and Urdu scoring defects. These repairs concern the classic reading dashboard. They do not establish speech-recognition accuracy on children.

## Resulting behavior

- Your Reading displays word match and target/recognized word pairs, including missing and extra recognized words. Word match describes transcript agreement, not a reading-health or phonetic diagnosis.
- Practice & Feedback displays recording observations, an actionable practice suggestion and a same-sentence comparison. Sources and availability distinguish measured results, generated advice, basic fallbacks, unavailable observations and legacy results without metadata.
- Empty and processing states are plain content without blurred overlays or simulated agent completion.
- Current word match sets the requested practice tier: below 70% easy, 70–89% medium, at least 90% hard. Generated exercises must include the named whole target word, use the requested language/tier and respect length limits. Fallbacks use flagged-word practice or repeat the current sentence.
- Progress compares the current attempt with the most recent earlier reading of the same normalized sentence and language in the last ten readings of that language. Differences are percentage points, not measured learning gains. Other sentences or languages do not establish a comparable trend.
- The chart shows the last seven readings in the selected language with labeled WPM and word-match axes.
- New diagnosis objects include source/status metadata; existing objects and database records remain readable. Session-list responses now expose language. Historical scores are retained.
- Unicode tokenization excludes punctuation, including Urdu full stops, commas and question marks. Genuine letter differences remain differences. Combining marks and normalized Unicode spellings are preserved.
- Urdu reading feedback and exercises have localized text, RTL layout and Nastaliq typography. The complete application interface is not fully localized.
- Recording snapshots the account, student, sentence and language. Synchronous guards prevent repeated starts/stops, controls lock during capture/processing, and stale reading/sentence responses are ignored. An old unauthorized request cannot clear a newer account's token.

## Notifications

There are no floating notification popups in the dashboard shell. The latest unresolved warning/error occupies a normal layout region below the top bar, above the scrolling content. Completion is shown beside reading results. Routine messages remain in bell history and have polite accessible announcements.

Dismissal belongs to notification state, independently of bell read status. Opening the bell, navigating within the app or adding another message cannot resurrect a dismissed message. Account changes clear the previous account's notification state. Notification history remains in memory; it is not a durable cross-reload inbox.

## Verification

- 41 isolated backend regressions cover existing repairs plus nine dashboard cases: Urdu punctuation, Unicode/letter distinctions, consistent flagged words, current-score difficulty and boundaries, invalid exercises, explicit fallback availability, unavailable timing and comparable history.
- The browser scenarios use temporary accounts/database, real authentication, a fake microphone and controlled reading responses. They test UI behavior and stale-response protection; they do not test physical microphones, live model output quality or real speech accuracy.
- All 12 browser scenarios passed with zero browser runtime errors. Report: [dashboard-results.json](runtime-validation/dashboard-results.json). Screenshots are saved beside it for English, Urdu and mobile layouts.
- Frontend lint has zero findings; TypeScript and the optimized webpack production build passed. Git whitespace checks passed for the changed tracked files.
- Failed intermediate browser runs were used to repair session-verification cancellation and to correct test selectors/navigation waits. The final report records the completed run. Windows emitted connection-reset messages while test browser connections closed; these did not fail the final harness or produce browser runtime errors.

Run the optional browser scenarios after building the frontend, using the same isolated harness as enrollment:

```powershell
$env:VALIDATION_BROWSER_SCRIPT = 'validate_dashboard_ui.cjs'
python backend/tests/validate_enrollment_runtime.py
```

Node and Playwright/Chromium must be available. Set VALIDATION_NODE and PLAYWRIGHT_MODULE when they are outside normal lookup paths. The harness never opens the production classroom database.

Restart the backend and frontend to load the repaired implementation. No new remote repository, deployment or provider integration is part of this change.
