# SOVEN account and profile integration

The account backend is ready for the next UI stage. This reference covers implemented API behavior and the remaining design integration. The later owner-approved UI now connects these endpoints through signup, profile and book screens. See 15_UI_DESIGN_AND_IMPLEMENTATION.md; the API contracts below remain authoritative.

## Adult registration and login

POST /api/auth/register-adult accepts exactly name, username and password. Example:

```json
{"name":"Example Reader","username":"example-reader","password":"a-long-unique-password"}
```

Success is 201 with a confirmation message; no login token is issued automatically. Use POST /api/auth/login, then the existing Bearer token contract. Names are required, usernames are normalized to lowercase and limited to letters/numbers/dot/dash/underscore, and passwords require at least ten characters. Unknown fields are rejected. Duplicate usernames return 409 across both child and adult accounts. Registration endpoints share an IP attempt bucket; callers should show 429 inline and retry later.

The transaction creates one approved account, one personal scope, one reader and one incomplete profile. A personal scope is bound to its owner on each authenticated request. The technical role is student, is_admin is 0, account_scope is personal and reader_mode is adult. Do not treat the technical student role as an age statement. Adult mode is self-declared, not verified age or guardian consent. Grade 0 is an internal unset sentinel, not placement. Parent updates are off. No personal join code is returned, and child registration cannot enroll in that scope.

Child POST /api/auth/register is unchanged in purpose: require a real classroom code, remain pending and use teacher approval with explicit existing-reader linking. Teacher accounts remain local-bootstrap controlled. Personal readers cannot use teacher/admin endpoints or read another personal/school reader. School teachers cannot approve, reject or delete readers outside their classroom.

## Profile reads and saves

GET /api/auth/profile requires an approved Bearer identity and returns {profile: ...}. It resolves the user from the token; a query parameter cannot select another user. Both successful reads and saves use Cache-Control no-store. Login and /api/auth/me also include profile, reader_mode, profile_completed and account_scope; old response keys are retained.

PATCH /api/auth/profile requires expected_version from the latest profile. Example:

```json
{"expected_version":1,"reading_language":"ur","interface_language":"en","native_language":"fr","translation_language":"es","accessibility":{"larger_text":true,"line_spacing":"comfortable"},"complete_profile":true}
```

reading_language and interface_language accept en/ur only and cannot be null. native_language and translation_language are separate, nullable values from the shared 89-candidate registry. Storing fr/es does not enable their reading engines, translation or localized menus. Completion currently requires native_language; name and credentials already exist from registration. Clearing native_language marks the profile incomplete. complete_profile false does not clear an otherwise complete profile.

Accessibility fields are larger_text false, word_tips true, high_contrast false, line_spacing normal, coach_enabled true and autoplay_coach false by default. line_spacing accepts normal, comfortable or wide. Nested saves merge supplied fields without resetting other settings. Booleans and versions are strict; unknown fields, null settings and attempts to change role/mode/owner/classroom/admin are rejected. No medical condition or birth date is required or stored by this change.

A successful save returns the whole saved profile with incremented version and UTC updated_at. Every accepted save increments the version. A stale or concurrent save returns 409 without overwriting newer choices; refetch and ask the user to reconcile. Invalid requests return 422 with sanitized field errors, never raw input/password echoes. Authentication expiry returns 401; forbidden resource access returns 403. UI errors belong in page layout, not floating popups.

## Completion rollout and migration

ENFORCE_PROFILE_COMPLETION defaults to 0 because completion forms do not exist yet. With value 1, incomplete nonteachers receive 403 PROFILE_REQUIRED on reading/inference entry routes while profile, identity, password and logout remain usable. Approval status is still enforced first; completing a pending child does not grant access. New child/adult registrations create incomplete profiles; existing users are grandfathered complete and teacher bootstrap creates a completed teacher profile.

Migration v3 adds classroom kind/owner and user_profiles. It preserves historical scores, tokens and readers. Existing versioned v2 databases receive a before-profiles backup before changes; protect it privately. Repeated initialization preserves existing profile values and versions. A missing profile for an older direct integration receives legacy defaults on read; a later save materializes it transactionally. Never classify an old technical student record as adult without an explicit future migration decision.

## Frontend integration checkpoint

frontend/lib/api.ts exports apiRegisterAdult, fetchReaderProfile, saveReaderProfile and typed request/results. These helpers do not mutate auth state. The owner-selected UI now includes adult signup, a profile form, new-journey completion routing, accessible conflict/error states, guarded auth refresh and applied settings. Legacy routes retain compatibility and strict backend-wide enforcement stays opt-in. Resolve reading/interface/native/translation independently. Deliberately reconcile existing browser preferences rather than silently resetting them on first login. Use request identity/version guards so a late response cannot affect another account. The existing AuthProvider cancellation rules remain in place.

StudentBinding now distinguishes independent and classroom readers rather than inventing a Grade 3 label for adult users. Do not enable profile enforcement before the new completion route is usable. Test child/adult/teacher/migrated sessions, stale saves, logout during save, denied microphone and page navigation in the final design. No raw speech, real provider or physical-device quality claim follows from these API tests.

## Acceptance evidence

ACCOUNT_PROFILE_VALIDATION.json records the 61 backend cases and isolated browser scenarios. backend/tests/validate_accounts_ui.cjs exercises real HTTP signup/profile persistence and the unchanged login UI with synthetic data. It does not automate a new adult signup form. The source catalogue and API map locate handlers and types; the live checklist keeps the remaining UI tasks unchecked.
