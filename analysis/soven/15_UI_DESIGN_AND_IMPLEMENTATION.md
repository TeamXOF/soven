# SOVEN reference driven interface

The owner supplied two illustrated reading-platform reference boards and explicitly authorized implementation without further permission. This resolves the earlier design hold. The screenshots establish the visual direction, not verified product claims or new provider capabilities. Preserve the approved SOVEN symbol and wordmark.

## Selected visual direction

Use warm cream surfaces, coral primary actions, dark ink navigation, clear white cards and polished storybook illustrations. Preserve a calm reading spread with the illustration on the left, stable target text on the right and feedback beside it. Use a single-page sequence at narrow widths, real form labels, visible keyboard focus and reduced-motion support. Keep the existing self-hosted DM Sans and Nastaliq fonts. Do not put sponsor names, taglines or language lists inside the logo.

The references show example scores, streaks, medical-support labels and a statement that data stays on the device. Those are not adopted as facts. SOVEN uses actual saved history, calls its comparison Word Match and explains browser/server/provider audio boundaries. The introductory sample stays browser-local; approved reading analysis reaches the backend. Optional comfortable text settings are not treatment or a dyslexia diagnosis.

## Routes and implemented contracts

- / is a public landing/how-to page with entry points for a microphone check, signup and sign in. It distinguishes English/Urdu from planned coverage.
- /try is a skippable 20-second browser microphone check with actual recording and playback, permission/error handling, retry and track/object-URL cleanup. It makes no inference request and gives no AI score. Anonymous STT/feedback remains pending a deliberate cost/rate/retention design.
- /signup offers classroom readers and independently registered adults. Classroom signup stays pending until teacher approval/linking; the adult option calls the existing personal-scope API. There are no role/admin/classroom overrides in the form.
- /login preserves the existing token flow, validates internal return paths, and sends newly approved incomplete readers to /profile by default.
- /profile reads/saves the versioned owner profile, handles conflicts inline and updates the current auth identity only when its token/user still match. It stores four separate language roles, completion and optional accessibility settings. Missing legacy server preferences retain existing browser choices. Candidate native/translation codes remain preference storage, not supported reading engines or translation output.
- /home shows real aggregate reader statistics, language-filtered recent readings, actual flagged words, a next-book entry and history. New accounts get empty states rather than fabricated charts. Aggregate statistics are labeled across languages. The recent chart is not a learning-gain estimate.
- /books uses GET /api/v1/stories with student ID and language, actual checkpoint progress, search and sequential unlock presentation. The optional language query preserves the older API contract; unsupported reading languages are rejected. Language-specific progress is regression-tested.
- /book/[storyId] opens a real checkpoint session on explicit action. It supports recording, bounded analysis, word comparisons, inline errors, retry, guarded next-page progression and completion. Existing results remain in the backend. Resume links can use an existing session ID and validate book/language identity before adopting it.
- /my-progress presents the same actual history with explicit reading language; it does not invent streaks or imply that different sentences establish a learning trend.
- /languages offers only enabled English/Urdu reading and shows the wider candidate catalogue as planned. Spanish remains unavailable for runtime reading.
- /privacy explains the current microphone sample, reading transfers, provider processing, server storage and offline limits. Consent, retention/deletion administration and public learner deployment remain unfinished.

The existing classic dashboard, teacher screens and dynamic adventure routes remain available. The shared shell adopts the cream/coral/dark navigation styling. They are not replaced with static mockups. Existing non-English interface coverage is partial; new main navigation/profile/reader copy has Urdu support, while several legacy/helper labels remain English.

## Reading behavior and safeguards

The book reads target sentences returned by the backend; it does not use decorative text as a different scoring target. Recording starts only after an explicit click. It stops spoken playback first, freezes page actions during capture/processing and bounds a recording at 30 seconds. The microphone hook guards delayed permission, initialization failures, cancellation and unmount; late streams stop their tracks. Processing results are tied to account token, route and attempt generation. Duplicate stop clicks do not create duplicate submissions.

After analysis, word buttons show matched/flagged evidence and can request the existing authenticated word-tip endpoint. Tip source is labeled as basic, generated or cached. A missing tip/voice stays unavailable. The coach panel uses existing phase-two guidance, polls for a bounded period and offers user-requested spoken playback. It does not implement free-form voice conversation, automatic interruptions or a new provider. Reader preferences can disable guidance and word help. Larger text, line spacing and high contrast apply to the new reader; these controls make no measured learning/clinical claim.

The new UI guards incomplete readers on its entry routes. ENFORCE_PROFILE_COMPLETION remains 0 by default for compatibility with the legacy interfaces; strict backend-wide rollout remains an operational choice. A profile page now exists, but do not claim that an inactive server flag rejects API bypasses. Existing migrated accounts remain grandfathered.

## Artwork and provenance

Four new illustration assets were generated with the built-in image-generation tool, then encoded as project-owned WebP delivery files under frontend/public/illustrations. The original generated raster outputs remain local and are not mislabeled as vectors. The approved logo was not regenerated. The hero depicts a reader in a sunny nook with a book and cat; covers illustrate the existing fox, rocket and whale stories. The story passages come from the existing backend/data/stories.json corpus. Editorial, age-suitability and educator review remains a separate gate; artwork generation does not validate content.

The hero prompt requested polished gouache storybook art, a South Asian reader in a coral hoodie and headphones, deep teal book, sleeping cat, books/plants/window, warm ivory, generous space, no text/logos/UI/watermark. Cover prompts requested a fox/apple-tree/stream forest, a coral rocket/moon/stars, and a blue whale/fish/coral ocean in full-bleed portrait gouache/watercolor, without text or logos. Asset generation and byte hashes are recorded in UI_ARTWORK_MANIFEST.json.

## Verification and continuation

Use UI_REDESIGN_VALIDATION.json for the final measured checks; the first implementation passed 62 backend cases, lint, TypeScript and production build. The isolated browser harness supports VALIDATION_BROWSER_SCRIPT=validate_soven_ui.cjs. It uses real disposable account/profile/catalogue APIs, a fake microphone and controlled analysis responses. Screenshots use synthetic accounts. These checks do not validate real speech, real providers, physical phones or educator outcomes.

Continue from the live checklist. Priorities after this interface are anonymous sample analysis if desired, a permitted real Meta adapter, stronger speech evaluation, reviewed content, physical-device testing and production/consent/retention work. Keep the 70+ language goal separate from the two enabled reading tracks. Do not mark the remaining product done because the reference layout is implemented.
