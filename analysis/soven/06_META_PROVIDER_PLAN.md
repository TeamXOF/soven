# SOVEN Meta integration and privacy plan

No Meta model is active in this imported runtime. This document records candidate capabilities and the decisions needed before a provider migration. Product quality, permitted access and honest data handling determine the route; branding alone does not establish a meaningful integration.

## Access and service boundaries

The team builds from Pakistan and intends a global audience. The Meta hosted geographic policy, updated 12 October 2026 and checked 1 November, restricts access from Pakistan and availability of integrated products to users there. A foreign proxy or VPN is not the plan. Hackathon acceptance does not itself establish a hosted-API exception. Investigate a separately licensed open-weight deployment and the chosen provider's actual terms and regional availability. Ask organizers about eligible access and prior-code reuse; no message has been sent by this delivery.

Policy source: https://dev.meta.ai/legal/geographic-use-policy. Obtain current authoritative clarification when making a deployment decision; this engineering note is not a legal determination or guarantee of eligibility.

## Candidate capabilities

Muse Spark is a hosted reasoning candidate for short coaching and structured content. Confirm supported parameters through the actual selected account; impose timeouts, output schemas and deterministic fallbacks. Do not send raw child audio merely to infer accents, emotional states or conditions. The official model catalogue distinguishes hosted models and separately run open weights: https://dev.meta.ai/docs/models.

Muse Voice Transcribe can provide streamed or file transcription, but publishes turn-level rather than word-level timestamps and no confidence values. Its evaluated language list includes English and Spanish but omits Urdu. It does not synthesize speech. The file endpoint requires supported PCM WAV conversion; realtime has its own PCM transport and handshake, not a drop-in replacement for browser MediaRecorder uploads. Keep word timing and recognition as separate capabilities and never fabricate missing evidence. Source: https://dev.meta.ai/docs/speech-to-text.

Muse Glimmer is a 30B text/image-input, text-output open-weight candidate. The official page identifies Apache 2.0 licensing and supported runtime options. It is not itself STT or TTS. Quantization, memory, latency and provider availability must be measured on the actual target. Ordinary laptop classroom operation cannot be promised from a model description. Source: https://dev.meta.ai/docs/muse-glimmer.

Muse Image is a possible illustration provider, subject to applicable access and image-specific restrictions. Cache and moderate illustrations, record source/model/license terms and show failure alternatives. No story-art service has been implemented here. Select one useful, verifiable Meta capability before adding multiple integrations.

## Proposed adapter approach

Retain an application-level JSON generation boundary rather than coupling prompts to one SDK. A future adapter should accept model/provider configuration, system instructions, task input and a validated output schema; return content, source, model, timings and fallback reason. Keep keys server-side and redact provider bodies from logs. Model calls must be bounded and fail to basic guidance, not invented results.

Speech adapters should declare language coverage, transcript, timestamp granularity and confidence availability. Align and score only using evidence they actually return. Raw-audio decoding, word timing, scoring and coaching remain independently testable. Keep the current offline pathway until the new route passes representative tests.

## Privacy requirements by mode

- Browser to server: microphone audio leaves the reader's device when uploaded to the configured backend, even if that backend is a teacher's laptop.
- Server-local mode: recognition and acoustic processing can run without external inference when weights are cached. This is not equivalent to browser-local inference.
- Hosted mode: recordings or reading observations reach the selected providers. Document recipients, retention and settings before collecting real user data.
- Stored state: usernames, transcripts, scores, attempts and teacher links can remain in SQLite. Sync is an optional archival transfer with its own credentials and receiver.

Do not place personal data in image prompts, repository fixtures, logs, screenshots or public documentation. Standard mode is a candidate requirement for hosted inference; it is not a blanket zero-retention promise across partners or browser voices.

## Acceptance gate for the next integration

Record the permitted route and actual model ID, run one real invocation, test malformed output and provider failure, measure latency/cost per completed reading, verify supported languages and annotate missing timestamps. Freeze a candidate configuration on development data before evaluating untouched speakers. Credentials, credits, public deployment, provider service guarantees and prior-code eligibility remain unverified unless new evidence closes them.

## Coverage for the 70+ language goal

The 70+ language target is an owner requirement, not a verified capability of one Meta endpoint. Evaluate STT, word timing, TTS, content, coaching and translation separately per language. Text-model understanding does not establish spoken-word assessment or voice availability. Track provider, script, timing source, fallback, measured quality and rollout status in a coverage matrix. Promote only capabilities that pass their gate; show gaps as unavailable. Preserve current adapters until a permitted replacement covers the required behavior.
