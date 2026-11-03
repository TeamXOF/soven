# SOVEN stable handoff checkpoint 2 November 2026

## What is complete

M2.4 is complete. The application now has an explicit speech capability policy for the two enabled reading languages, English and Urdu. Recognition routes are Groq Whisper when configured and permitted, with local Whisper fallback. Browser speech playback selects a matching device voice only; it exposes an inline unavailable state instead of speaking with an unrelated language voice.

New reading results carry source, engine, fallback, word-timing, token-confidence, pause-availability and quality metadata. The implementation does not invent word timestamps from segment durations, turn token probability into pronunciation quality, or invent pauses when timing is incomplete. Legacy records remain unchanged and report unknown/null provenance.

The three reading flows preserve this evidence: classic sessions, fixed checkpoints and dynamic-story attempts. Existing authentication, classroom isolation, child-first linking, word-match scoring, practice selection, notification behaviour and the connected book UI remain in place.

## Verified before this checkpoint

- 159 backend tests passed locally: 63 application (including book reader pause evidence regression), 18 reasoning-provider, 21 speech-evaluation, 31 speech-runner and 26 speech-capability contracts.
- 15 mocked browser speech-playback contracts passed.
- The isolated browser journey passed 23 scenarios with zero reported browser runtime errors.
- Frontend lint, standalone TypeScript and production build passed.
- Real-runtime QA audit verified clean instance startup, adult journey, tenant isolation, and live Groq STT (100% accuracy, available word timing) and Google Gemini reasoning (generated coaching feedback) on synthetic controls without classroom or child audio transmission. See REAL_RUNTIME_VALIDATION_2026-11-02.md and REAL_RUNTIME_VALIDATION_2026-11-02.json.
- Five existing synthetic offline local-model controls passed with no transcript edits against their scripts. They cover matching, insertion, omission, substitution and ending scoring.
- The current source/environment receipt verifies without inference: SPEECH_RUNTIME_CAPABILITY_FREEZE.json.

## Do not overclaim

This is an engineering stability checkpoint, not child-speech validation. Urdu quality, confidence calibration, device voice coverage, physical-device testing, classroom load, reviewed content, consent/retention policy, public deployment, live permitted Meta access and 70-plus end-to-end language support are still open. The beam-five recognizer experiment remains unpromoted; M2.2c is still open.

## Continue from here

Read 00_START_HERE.md, 10_DECISIONS_AND_HANDOFF.md, this checkpoint, 19_SPEECH_CAPABILITY_SELECTION.md, then the live checklist in 07_IMPLEMENTATION_ROADMAP.md. Do not modify historical scores or replace existing safety boundaries. The next unstarted engineering item is M2.5, script-specific segmentation validation; it requires a deliberate plan before implementation.
