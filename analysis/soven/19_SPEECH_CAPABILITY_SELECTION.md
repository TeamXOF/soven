# SOVEN speech capability selection and evidence

M2.4 makes the speech route explicit for each currently enabled reading language and makes unavailable evidence visible. It does not validate recognition quality, add a language, promise a browser voice, or enable a hosted Meta service.

## Current routes

`shared/speech-capabilities.json` is the single public route inventory. English (`en-US`) and Urdu (`ur-PK`) can request Groq Whisper and fall back to local Whisper. Playback is browser SpeechSynthesis. The backend rejects unknown or planned reading languages before it selects a provider. Forced local mode never probes a hosted provider; offline mode remains an outbound-inference block.

Browser playback selects only a matching device voice: exact locale first, then the same language subtag. It does not substitute an unrelated voice. An unavailable voice is an inline, retryable state; loading a voice later can succeed. Speech stops before capture and the reader can stop it explicitly. A browser route is not a claim of a validated voice, offline support, or device coverage.

## Evidence semantics

`TranscriptResult.words` retains provider word timestamps only when each finite `start < end` pair is present. Segment-level duration is never divided across words. Punctuation is ignored as a word. `speech_evidence` accompanies new classic, fixed-checkpoint and dynamic-story results and records source, engine, fallback reason, word-timing availability, token-confidence availability, pause availability and a `quality_validated` flag.

Confidence, when present, is labelled `model_token_probability_not_pronunciation`; it is never a child-reading or phonetic score. Pauses require ordered, complete word timing. Missing, partial, overlapping or simulated timing makes pause assessment unavailable. Descriptive pitch/energy values are not manufactured when no suitable timing evidence exists. Legacy stored results have no metadata and return `null`, preserving their original record rather than inventing provenance.

Classic session evidence is stored separately in `speech_evidence`. Checkpoint evidence is keyed to its checkpoint result and replaced atomically with a re-submission. Dynamic-story attempts retain evidence in their existing result JSON. All response keys and historical scores remain compatible.

## Validation completed 2 November 2026

The focused speech-capability suite contains 26 contracts. They cover language policy, no provider probe for forced/local-unconfigured routes, cloud fallback, no timestamp construction, invalid/partial/overlapping timing, unavailable simulation evidence, acoustic/coaching behaviour, public inventory, additive schema migration, persistence for each flow and legacy null metadata. Together with application, provider, frozen-profile and runner suites, 158 backend tests passed locally (62 + 18 + 21 + 31 + 26). A 15-case mocked browser-voice contract passed; it covers matching-only selection, unavailable/retry behaviour and stop. The isolated browser journey passed 23 scenarios with zero reported page runtime errors. Linter, standalone TypeScript and the production build also passed.

Five existing synthetic Microsoft Zira recordings passed through cached local faster-whisper base INT8 with outbound access disabled. They exercised matching, insertion, omission, substitution and ending scoring; none was edited against its script. This checks route mechanics only. It does not validate learner speech, Urdu, timestamps, confidence calibration, pronunciation assessment, physical devices or classroom load.

SPEECH_RUNTIME_CAPABILITY_FREEZE.json is a reviewed source/environment receipt for this code state. It verifies no inference and no quality validation; SPEECH_BASELINE_FREEZE.json remains the dated M2.1 reference receipt.

## Boundaries and next work

M2.2c remains open: the exposed historical child-speech sample and beam-five candidate are not release quality evidence. M2.3 still requires representative Urdu/device/noise work and reviewed Spanish fixtures. M2.5 is the next unblocked engineering item, but it has not started: each offered non-whitespace script needs its own segmentation and scoring validation. M2.6 remains the language-by-language end-to-end gate. Keep the 70+ product goal distinct from the two routes above.
