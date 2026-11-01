# SOVEN adopted product defaults

On 1 November 2026 the owner explicitly approved transferring SOVEN to TeamXOF, retaining public visibility, using recommended defaults for unspecified fields, and documenting progress through a checklist. These are adopted implementation targets; a selected default does not mean the feature already exists.

## Audience accounts and onboarding

The first release serves children and adult/language learners, with teachers retaining classroom tools. Prioritize a calm reader journey while preserving teacher access. Children retain classroom-code signup, approval and explicit linking to existing profiles. Standalone adult registration now exists as an API with a private personal record scope and no school-record access. Its signup screen remains planned. This self-declared mode is not verified age. A separate guardian administration role is deferred rather than invented during signup work.

Use a short, skippable introductory reading sample before signup, with microphone consent and retry. Twenty seconds is an experience target, not an assessment standard. Keep anonymous sampling separately rate/cost bounded. Do not promise grade placement or infer a reading condition. Require profile completion after signup for the chosen reader mode and language preferences. Make accessibility preferences optional and editable without a required medical disclosure.

## Coach book and language experience

Begin with short user-requested or end-of-sentence spoken help. Provide mute/stop/disable, then a controlled retry. Automatic interruption while reading is deferred until recognition and timing are sufficiently evaluated. A pause is not proof of an error.

Use a reviewed starter library suitable for early readers, with an adult-appropriate selection as the adult journey is introduced. Proposed initial child content spans approximately ages six to twelve; reading difficulty remains a content choice, not an inferred age/grade diagnosis. Generated stories and illustrations can be added through a permitted provider with content/failure checks, while reviewed material remains usable.

The product goal is 70+ end-to-end reading languages. Use English, Urdu and Spanish as initial demonstration priorities while preserving the existing English/Urdu flows. The 89-entry candidate inventory is a planning set, not a finished coverage promise. Keep reading language, interface language, native language and translation target distinct. Introduce optional meanings/translations and listen/repeat after the main reading loop is reliable.

## Privacy offline operation and spending

Preserve existing server-local recognition when dependencies and weights are cached; retain useful reviewed content offline. Audio reaches the backend, and hosted modes can send it or derived observations to providers. Fully browser-local inference is outside the first release unless separately scoped. Default to no retained raw recordings after processing and the minimum history needed for progress; define and implement consent, deletion and retention controls before public learner use. Do not call these policy targets completed controls.

No provider account, credited balance, hosting budget or deployment hardware was supplied. Default to no new spending or paid provisioning. Do not assume personal hosted Meta access is permitted from Pakistan. Develop provider-independent boundaries and use a separately verified permitted route when available. Existing provider names and fallback labels remain accurate.

No additional team usernames were supplied. Preserve owner/admin access and existing organization policy. Do not send invitations or grant new write/admin access to unidentified people. Hosting/domain choices, real provider configuration and team membership remain external inputs; implementation can continue on independent tasks while those are pending.

## Definition of complete

Mark work complete only after its stated check passes and the evidence is recorded. Keep planned functionality, implemented mechanics and validated quality distinct. Maintain 07_IMPLEMENTATION_ROADMAP.md and 12_EXECUTION_LOG.md after each finished task. Update affected Markdown, DOCX snapshots, source/API catalogues and validation records, and mirror the handoff to the original workspace.

## Implementation checkpoint before design

The account/profile backend now stores separate language and accessibility preferences and exposes a versioned owner-only API. New child/adult accounts begin incomplete; migrated accounts remain complete. Completion enforcement is implemented but disabled by default until UI routing exists. Settings storage does not apply the redesigned presentation. The owner has since supplied the references and the illustrated UI is implemented; see 15_UI_DESIGN_AND_IMPLEMENTATION.md.

The owner-selected UI references now supersede the prior design hold. The account/profile forms and illustrated reading journey implement those preferences. The introductory public sample is deliberately browser-local microphone recording/playback only; anonymous AI feedback remains a separate bounded-service task. New reader routes guide incomplete profiles to /profile, while backend-wide enforcement remains opt-in for legacy compatibility.
