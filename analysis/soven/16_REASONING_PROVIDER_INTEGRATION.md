# SOVEN reasoning provider integration

The configurable coaching boundary is implemented and mock-tested. Google remains the default. Meta Chat Completions and a separately configured compatible endpoint now have adapters; neither has been called live in this delivery. This guide explains configuration, data flow, failure behavior and the evidence required before enabling either route. It does not establish regional permission, model quality or a provider account.

## Configuration and permitted access

Set server-side REASONING_PROVIDER to google, meta or chat_completions. Unknown values fail to basic guidance; they do not pick another provider. Keep OFFLINE_MODE=1 to disable all outbound reasoning. No secrets belong in browser configuration or Git.

Google retains the existing key selection and primary/alias retry. Its model controls remain FEEDBACK_MODEL, FEEDBACK_MODEL_FALLBACK and GEN1_AGENT_MODEL. For either new route, configure REASONING_MODEL and REASONING_ACCESS_CONFIRMED=1 after independently checking access, model licensing, intended users and privacy arrangements. This operator declaration is neither a policy exception nor automatic geographic enforcement.

The meta route uses the fixed https://api.meta.ai/v1/chat/completions endpoint and REASONING_API_KEY. REASONING_BASE_URL cannot redirect that route. Official documentation checked 1 November 2026 uses muse-spark-1.3; no model is silently selected for a new route. The team is in Pakistan, where Meta hosted access is restricted, including availability of integrated products to users there. Leave this route disabled here. No live Meta call, proxy arrangement or exception is claimed.

The chat_completions route uses an explicit REASONING_BASE_URL, including /v1 when required, and appends /chat/completions. Remote endpoints require HTTPS and a key. HTTP without a key is accepted only for literal loopback hosts localhost, 127.0.0.1 or ::1, for an independently installed local service. URL credentials, query strings, fragments and redirects are rejected. Separately hosted open weights still require their own license, provider, regional and hardware checks. The adapter does not install a model or guarantee every compatible server accepts its schema/token parameters.

## Request and response contract

services/model_client.py accepts instructions, a JSON task payload, model choice, timeout and output schema. Existing callers retain their dictionary interface. ModelResult carries provider/model attributes separately from generated fields, so generated content cannot forge provenance. Meta uses developer instructions; the compatible route uses system instructions. Reading observations are serialized as user data. Both request JSON-schema output, 2048 completion tokens and a non-streaming completion. No cross-turn memory, tools, audio or image upload is added.

The existing WordCoaching and CoachingFeedback Pydantic contracts still validate local output. Closed schemas with explicit required fields are sent to the new routes; nullable feedback fields remain nullable. Classic difficulty/practice also receive closed task schemas and retain their existing category, language, target-word and difficulty checks. Deterministic alignment and scoring never depend on generated guidance.

The request cap is 96 KiB and response cap 128 KiB. Connect timeout is at most three seconds; read timeout follows the caller, up to thirty seconds. Reads also check an elapsed deadline between chunks. The async await has a timeout plus one-second allowance. Cancelling that await cannot forcibly cancel an already-running HTTP thread; socket/read limits still apply, and a slow final read can outlast the checked deadline. These controls are not sustained-classroom capacity evidence.

Non-success HTTP status, redirects, transport failures, refusals, incomplete output and invalid JSON fail to existing templates. Non-Google routes make one attempt and never silently retry Google. Google preserves its previous model-alias retry. Provider bodies and transport exception text are excluded from application warning logs. No provider latency, usage or price is fabricated.

## Sources storage and privacy

Feedback source values now include gemini, meta, chat_completions, model_unknown and template_fallback. Word tips retain template/cache labels plus generated sources. Classic generated blocks retain source=model and add provider/model metadata; older objects remain legacy/unknown. Existing stored scores and source records are not rewritten. The technical latency key gemini_feedback remains for API compatibility and represents feedback elapsed time, not proof that Google ran.

Cached word guidance retains the existing word/language/context cache and is explicitly labeled cache. Changing providers does not invalidate historical cache entries or prove a new invocation. A provider-specific cache policy remains part of the later multilingual work.

Only structured text/reading observations cross this reasoning boundary. Speech recognition remains separate: approved reading uploads still reach the SOVEN server, and online STT can send audio to Groq. This adapter does not move audio inference into the browser, enable Spanish or turn 89 language candidates into working engines. Before real learners use hosted coaching, the operator still needs recipient disclosure, consent, retention/deletion arrangements and permitted service access.

## Acceptance evidence and remaining gate

Eighteen mocked provider regressions cover protocol shape, closed schemas, per-call credentials, Google compatibility, configured/loopback endpoints, blocked configuration, redacted failures, malformed/refused/truncated output, request/response/deadline limits, source provenance, strict validation, local fallbacks, async timeout and public inventory claims. The 62 existing backend cases pass. Frontend lint, standalone TypeScript and production build pass. The isolated illustrated journey passes 19 scenarios, including controlled Meta-source guidance; no provider request is involved in that browser case. See REASONING_PROVIDER_VALIDATION.json.

M1.6a closes implementation and mocked tests. M1.6b remains open until a permitted route is independently established. M1.7 requires a real permitted invocation, recorded exact model, latency, usage/cost evidence, failure checks and language-quality review. Do not enable this adapter with real child observations merely because tests pass. No credits, hosting, account, live invocation or model-quality claim has been supplied by this stage.

## Authoritative protocol references

The endpoint, role and token parameters follow [Meta Chat Completions](https://dev.meta.ai/docs/protocols/chat-completions). The response_format contract follows [Meta structured output](https://dev.meta.ai/docs/cookbook/structured-output). The regional boundary is documented in the [Meta geographic policy](https://dev.meta.ai/legal/geographic-use-policy). These sources were checked 1 November 2026; recheck before actual enablement. A compatible third-party endpoint needs its own current documentation and permissions.
