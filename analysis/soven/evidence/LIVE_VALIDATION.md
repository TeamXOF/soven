> Historical evidence from the SpeakFlow repair pass. For current SOVEN status and executable instructions, read ../00_START_HERE.md. Older test counts and workstation commands are historical.

# SpeakFlow runtime validation — 30 October 2026

The processing path now has real runtime evidence. Recognition quality on children's speech remains a material product issue. These checks do not establish learning outcomes, reliable pronunciation diagnosis, production capacity, or global language support.

## What ran

- Python 3.12.14 on this Windows machine, eight logical CPUs; cached faster-whisper **base**, CPU INT8. The project's local environment selects `base`; changing to `tiny` or another model requires a new benchmark.
- Separate temporary databases, generated accounts and local servers. No production classroom was changed. No cloud STT, paid model calls, sync upload or public deployment was used.
- Five locally synthesized adult English recordings, generated with Microsoft Zira, covering correct reading, an inserted word, an omitted word, a substituted word and a missing word ending.
- Network connections were blocked during cached-model fixture inference. All five recordings completed. Three seconds of actual digital silence produced `NoSpeechError`, rather than a fabricated transcript. The HTTP regression verifies that this becomes 422 without saving a failed attempt.
- An isolated Chromium browser signed in through the real UI, recorded a **simulated** microphone with MediaRecorder, uploaded WebM through HTTPS, and received a real local STT/scoring result. It then advanced to level two and started a new recording. This is separate from the physical microphone check.

Raw measurements: [current run](runtime-validation/results.json), [earlier baseline](runtime-validation/baseline-results.json), [browser result](runtime-validation/browser-results.json). The baseline precedes VAD, faster pitch analysis and the scoring corrections described below. It is not a controlled experiment isolating each change.

## Bugs found and fixed by executing the pipeline

1. **Audio decoder incompatibility:** faster-whisper 1.2.1 calls PyAV's `metadata_errors` option, which failed with PyAV 19. Pinned `av==16.0.1`; a real WAV decoder regression now covers the API call.
2. **Invented trailing speech:** the earlier decoder appended an unspoken “you” to several synthetic recordings. Voice activity detection and removal of instructional transcript prompts resolved this on the controls. The expected sentence is never supplied to STT.
3. **Prompt contamination in child speech:** the recognizer sometimes returned its own instructional prompt. Removed those prompts from local and hosted decoding requests. Hosted behavior still needs a real provider check.
4. **ASR uncertainty counted as a child error:** a correctly matched word could fail because recognition confidence was low or pitch/energy varied. Reading scores now represent transcript agreement; confidence and acoustic observations remain separate. This does not fix recognizer substitutions.
5. **Excessive acoustic cost:** pYIN took seconds per short clip. Descriptive features now use YIN with energy gating by default; pYIN is optional. Corrected pitch-frame indexing to use an explicit matching hop size.
6. **Silence handling:** unheard recordings return a retry message and do not create a failed reading attempt.
7. **Next-level recording state:** advancing after a successful result retained submission state. It now clears the old result/guard and enables the next recording; exercised in the browser check.
8. **WebSocket runtime dependency:** added the server's explicit `websockets` dependency.

The five final controlled transcripts matched their **spoken** references exactly. Reading scores against the printed target were 100%, 90%, 89%, 89% and 83%, respectively. These five adult synthesized examples are functional controls, not a population accuracy estimate.

Warm acoustic work on those controls took 13–32 ms; first acoustic initialization took 3.53 seconds. Warm STT took about 1.16–1.30 seconds; first STT call took 2.29 seconds in that run. Model initialization and hardware/cache state affect cold results.

## HTTPS and simultaneous submissions

The test reverse proxy used a one-day localhost certificate verified against an explicit test trust root by the HTTP client. The isolated browser accepted that test certificate and reported a secure context. No OS certificate trust settings were changed. This verifies local HTTPS routing and browser recording, **not a publicly trusted deployment**.

All requests below used the real reading endpoint and cached model through TLS. Each burst ran once; p95 is linearly interpolated and has little statistical strength with so few successful requests. “Busy” is the bounded worker pool's deliberate HTTP 503 response.

| Simultaneous submissions | Successful / busy | Burst elapsed | Successful p50 / p95 | Health p95 |
|---:|---:|---:|---:|---:|
| 1 | 1 / 0 | 1.55 s | 1.44 / 1.44 s | 39 ms |
| 4 | 4 / 0 | 5.50 s | 4.19 / 5.19 s | 50 ms |
| 8 | 8 / 0 | 11.47 s | 10.10 / 10.92 s | 28 ms |
| 16 | 8 / 8 | 11.29 s | 10.04 / 10.80 s | 38 ms |
| 30 | 8 / 22 | 11.26 s | 9.90 / 10.75 s | 146 ms |

The earlier one-request latency was 7.25 seconds, and the eight-request burst took 58.05 seconds. The new measurements are substantially faster, but the pool still accepts only eight jobs including queued work. **Thirty simultaneous submissions are not supported without busy responses.** Increasing that number blindly would increase waiting and memory pressure. A deployment needs measured worker/GPU capacity or an explicit fair queue and retry workflow, followed by sustained, varied-duration testing.

The Windows test harness emitted connection-reset callbacks when TLS keep-alive transports closed. All measured HTTP outcomes matched success/busy behavior; the browser reported no JavaScript errors or failed requests. WebM decoded through the installed FFmpeg fallback, with librosa deprecation warnings. Those warnings should be addressed before a future librosa upgrade.

## Child-speech evaluation

Source: [SpeechOcean762 author's repository](https://github.com/jimbozhang/speechocean762), Junbo Zhang et al., Interspeech 2021. [OpenSLR SLR101](https://openslr.elda.org/101/) lists **CC BY 4.0**, Mandarin-speaking English learners, and independent expert pronunciation ratings. Downloads and derived text/ratings retain this attribution. No audio is added to Git.

Selection was deterministic: the lowest utterance ID for each distinct eligible test speaker aged 5–10. The first 20 speakers were an exploratory development sample. After removing prompt contamination and confidence-based reader penalties, the next 20 previously uninspected speakers were evaluated with the same frozen decoder/scorer. No model weights were trained. Sample selection was not based on favorable ratings or model outcomes. File hashes are included for the holdout clips.

| Sample | Clips / speakers | Prompt-text edit rate | Expert-acceptable words flagged | Expert-error words flagged |
|---|---:|---:|---:|---:|
| Development, earlier implementation | 20 / 20 | 81.48% | 46 / 74 (62.16%) | 7 / 7 |
| Development, corrected implementation | 20 / 20 | 58.02% | 33 / 74 (44.59%) | 6 / 7 |
| Small holdout, corrected implementation | 20 / 20 | 34.78% | 29 / 110 (26.36%) | 4 / 5 |

Reports: [earlier development](runtime-validation/child-corpus-before.json), [corrected development](runtime-validation/child-corpus-results.json), [holdout](runtime-validation/child-corpus-holdout.json).

Interpret these numbers carefully:

- The corpus reference is the printed reading prompt, **not a verified verbatim transcription of what each child actually said**. Prompt edit rate therefore combines speech-recognition errors and actual reading differences. It is not pure ASR WER.
- Expert word scores 7–10 were treated as acceptable and 0–6 as errors for this exploratory comparison, following the source's rating descriptions. Pronunciation ratings and transcript agreement measure different things. These disagreement counts are not validated diagnostic sensitivity/specificity.
- The holdout contains only five expert-error words. Its 4/5 flag count is far too small to establish dependable error detection.
- The 26.36% disagreement on expert-acceptable holdout words is a serious warning against presenting this base-model pipeline as reliable pronunciation assessment. It also misses at least one expert-rated error.
- There is no Urdu benchmark, multilingual coverage, accent-balanced sample, classroom noise/device study or educator product trial here. Development and holdout results cannot be compared as an improvement estimate because they contain different speakers.

Next recognition work should compare stronger candidate recognizers on development data, freeze the configuration, then evaluate a larger untouched speaker-disjoint set with verbatim transcripts and expert reading/pronunciation labels. Do not improve apparent scores by feeding the expected sentence to STT or hiding mistakes in target-text autocorrection.

## Physical microphone evidence

The user explicitly started a real browser recording on a loopback-only test page. The first request contained 94,629 bytes of recorded audio, completed with HTTP 200 using local STT, and took 5.26 seconds including initialization. Its transcript did not exactly match the target; the reported word match was 78% under the earlier implementation.

The user reported reading the sentence as written but was unsure about the word rendered around “woke.” The first take therefore does **not** establish a confirmed child/reader pronunciation error or a confirmed exact ASR error. Raw microphone audio was deleted after processing; it cannot now be independently adjudicated.

On **31 October 2026**, the user confirmed a successful repeat: “The little fox woke up early in the morning.” The saved server result independently confirms HTTP 200, 60,531 recorded bytes, `local_fallback`, exact target match and 100% word match. Processing took **3,112 ms total** (STT 2,798 ms; acoustics 311 ms). The physical microphone → browser recording → upload → cached local recognition → displayed result workflow therefore **passes this functional check on the tested browser/device**.

The helper also logged an earlier repeat with 12% word match and 10,642 ms processing time. Its spoken content was not confirmed by the user, so its cause cannot be adjudicated. Preserve it as an unresolved observation rather than excluding it or treating this successful repeat as a population accuracy estimate. These few takes do not resolve the separate child-speech benchmark failures.

Only summary telemetry is written locally for the physical check, and it is ignored by Git. The temporary account/database belongs to that helper process and is removed when it stops. The server binds to loopback. The initial 15-minute expiry caused the next-day repeat page to lose its upload connection. On 31 October the helper was changed to allow 60 minutes without activity, with visible-page heartbeats and a four-hour maximum session. It checks server availability before microphone capture, retains a failed upload in browser memory for retry, and distinguishes analysis success from a failed summary save. A server restart requires reloading the page for its new temporary session.

## What is still needed

1. More physical-microphone recordings across browsers/devices and classroom noise conditions. One user-confirmed exact-match repeat now passes; the earlier unmatched recordings remain unadjudicated.
2. A materially better validated recognition/assessment approach for children's speech, including Urdu if that track remains in scope.
3. Actual educator trials and measured usefulness/learning outcomes. A public corpus cannot substitute for teachers using this product.
4. A deployment target, domain and hosting access before provisioning public HTTPS; then real deployment load and provider/cost checks. No public deployment was created in this pass.
5. Real online STT/model-provider checks with the eventual approved Meta integration and credentials. Local success does not verify hosted API access.

Backend regression suite: **27 passed**. Frontend lint, TypeScript and production build passed after the reader UI changes. The automated browser check passed with the recording-state fix; the subsequent UI copy changes were compiled and linted.

## Reproducing

`backend/tests/test_regressions.py` is the normal isolated regression suite. The additional `validate_*.py` / `validate_browser.cjs` scripts are opt-in local validation helpers, not production startup commands. On this machine they use the bundled Python/Node/Playwright installation and cached base weights, plus ignored `.test-deps`. Review their runtime paths before using another machine.

Generate the local TTS controls with `runtime-validation/generate-fixtures.ps1`, build the frontend, then run `backend/tests/validate_local_runtime.py`. The test needs development dependencies, FFmpeg, cached base weights, Chromium and Playwright; it provisions its own temporary accounts, database and certificate. `VALIDATION_LOAD_LEVELS=1,4,8,16,30` selects the burst sizes. Never point these helpers at a real classroom database.

`backend/tests/validate_child_corpus.py` downloads the small author-hosted sample. Set `CHILD_VALIDATION_SKIP_SPEAKERS=20` and `CHILD_VALIDATION_REPORT=child-corpus-holdout.json` to reproduce the holdout selection. Downloaded child audio/annotations and private microphone telemetry are ignored by Git. Retain source/license attribution with derived reports.
