# SOVEN product requirements

This document translates the supplied team notes into product requirements. It is a roadmap for the next stage, not a claim that the features exist. Working means implemented and exercised within the limits in CURRENT_STATE. Partly implemented means a reusable mechanism exists. Needs validation identifies an evidence gap. Awaiting a product decision means the owner has not settled the intended behavior.

## Entry and profile experience

R01 Landing and guidance — Planned. Explain read, review and practise in a short visual sequence, with an obvious start action. Acceptance: a first-time visitor can identify the purpose and next action without knowing the legacy dashboard. Exact copy and navigation should reflect completed capabilities.

R02 Introductory voice sample — Planned and needs validation. Offer a short sample before signup to demonstrate feedback. Twenty seconds is a proposed experience target, not a validated assessment duration. Acceptance: informed microphone permission, skip/retry, clear processing status, bounded anonymous requests and no invented level diagnosis. Public pre-signup inference requires a deliberately designed abuse/rate/cost boundary because reading APIs currently require approved accounts.

R03 Complete profiles — Planned and awaiting a product decision. Capture only information needed for reading preferences. The meeting asks for child, adult/language learner and dyslexia-related support. Prefer a reader persona plus optional accessibility preferences rather than making a condition disclosure a mandatory identity. Acceptance: required fields and completion gate are explicit, editable and tested. Define guardian/teacher authority and standalone adult signup before changing approval rules.

## Reading and help

R04 Responsive book — Planned, with existing content/progression reusable. Desktop shows an illustration and reading page; narrow screens show a clear single-page sequence. Acceptance: page controls, microphone and feedback work with keyboard/touch across selected launch languages, including Urdu RTL, with room for further scripts. Keep reading evidence independent of decorative page transitions.

R05 Accessibility preferences — Partly implemented through text-size/preferences and Urdu typography; expanded mode planned. Offer adjustable spacing, line height, contrast and reading pace support. No speed deduction is needed because current word-match scoring already avoids a speed-based overall score. Acceptance: preferences persist, remain optional and work with the script. Latin letter-spacing is not blindly applied to connected Urdu script. Test with users before claiming dyslexia-specific benefit.

R06 Conversational coach — Planned and awaiting a product decision. The goal is short spoken help and retry practice. Decide opt-in turn-based help versus automatic interruption before implementation. A 0.8-second pause is not proof of a mistake. Acceptance: user can pause/mute/disable help; only one party speaks/listens at a time; uncertain recognition invites a retry instead of alleging a pronunciation defect; stale turns are rejected and latency is measured.

R07 Spoken demonstrations — Partly implemented through browser TTS; improved TTS planned. Word and sentence playback already exist. Acceptance: per-language voice availability is detected, failures are visible, cached playback and provider fallbacks are explicit. edge-tts, if chosen, is an online dependency; browser synthesis is not guaranteed offline. Do not claim a new Meta speech-synthesis capability from a transcription model.

R08 Audio statistics — Partly implemented. Current telemetry includes WPM, duration, word match, pauses and descriptive acoustic features. Add interpretable pitch/energy/pause graphs and separately defined WCPM only where measurements support them. Acceptance: units, timing source, voiced/unvoiced gaps and unavailable values are labeled. Relative digital dBFS is not calibrated sound-pressure dB; recognition probability is not learner confidence or emotion. No universal voice-pitch health range is asserted.

R09 Multilingual reading across 70+ languages — Planned and needs validation. The owner confirmed 70+ languages as the product goal; English and Urdu work today, and Spanish is one proposed addition. Build a data-driven language registry. Acceptance: the agreed target set has explicit coverage for stories, recognition, script/tokenization, feedback, TTS, interface localization where offered, preferences, caches, progression and reports. Distinguish translated menus from complete reading support. Each promoted language needs reviewed content, compatible recognizer/voice paths, fallback behavior and representative evaluation. Unsupported capabilities remain clearly unavailable. Rollout order and language-specific release thresholds await a product decision.

R10 Language learning — Planned, optional, awaiting priority. Add word meanings, native-language translation and listen/repeat help without distracting from reading. Acceptance: language pairs, translation source, fallback and ambiguity are clear, and history does not mix unlike tasks as one learning trend.

## Delivery and trust

R11 Device support — Partly implemented and needs broader testing. Responsive web capture exists; mobile/tablet book layouts and real iOS Safari are future checks. Acceptance: HTTPS, permissions, interruption/backgrounding, audio/mp4 and audio/webm where supported, cleanup and touch navigation pass on target devices. Browser simulations are not physical-device evidence.

R12 Privacy — Partly implemented and needs a product policy. Temporary raw audio cleanup and offline controls exist, while results remain server-side. Acceptance: show exactly where microphone data goes in each mode, define consent/retention/deletion, protect identifiers, keep keys server-side and verify provider settings. No guarantee that all processing stays on the device or that every provider has zero retention.

R13 Simple navigation — Partly implemented; redesigned book navigation planned. Keep the core actions few and clearly named. Acceptance: Read Book, Voice Stats and Language/Mode do not strand teachers or hide failure/recovery. The current app still contains teacher and legacy reading routes.

R14 Meaningful Meta capability — Planned and blocked on a verified access route. Proposed uses are coaching, content and illustrations. Acceptance: a real permitted model invocation, schema validation, explicit source/fallback metadata, failure/cost tests and a visible user benefit. Retain the current provider adapters until replacements are proven; never relabel Google/Groq output as Meta output.

## Requirements that remain invariant

Keep classroom and record isolation, child-first approval linking, word-match scoring, unavailable-confidence semantics, no emotion inference, preserved history, guarded recordings and quiet notifications. Additional languages, book pages or an introductory sample must not regress these repaired flows. Future work needs meaningful acceptance evidence, not a broad search-and-replace of product or sponsor names.
