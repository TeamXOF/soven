# SOVEN frozen speech evaluation protocol

M2.1 freezes a reproducible baseline and acceptance criteria in SPEECH_BASELINE_FREEZE.json. It does not improve recognition or validate a language. Production configuration is unchanged; its default can still be tiny. The benchmark runner, new evaluation data and quality improvements remain M2.2 and later work.

## Frozen reference configuration

The profile backend/data/speech_evaluation_profile.json is fw-base-cpu-int8-2026-11-01. It pins faster-whisper 1.2.1, PyAV 16.0.1, CTranslate2 4.8.4, tokenizers 0.23.3, NumPy 2.5.4 and ONNX Runtime 1.31.1. Reproduce this observed environment separately; a different platform/runtime needs its own identified development configuration before holdout evaluation.

The cached model is Systran/faster-whisper-base at revision ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66. Four artifact checksums pin weights, configuration, tokenizer and vocabulary; no weights are published. The profile uses CPU INT8, four CPU threads and one worker, greedy beam size one, temperature zero, word timestamps, VAD with 300 ms minimum silence and 200 ms padding, and explicit remaining transcription defaults. The language is supplied per clip. Initial prompt, prefix and hotwords are absent; previous-text conditioning is disabled. Never send the expected reading sentence to the recognizer.

The frozen baseline is an evaluation reference, not a claim that this model is suitable for children's speech. Production can still fall back to another local engine; the future benchmark runner must instantiate the exact recorded engine and fail rather than silently substitute it. Model initialization, cold/warm timing, device and codec differences must be reported separately.

## Engineering acceptance criteria

These owner-authorized defaults are initial engineering gates, not clinical standards, research-derived thresholds or measured outcomes. Freeze them before seeing a new holdout. Changes after inspecting outcomes require a new development cycle and a fresh holdout; report earlier failures.

For English and Spanish, maximum aggregate ASR WER is 15 percent and maximum mean speaker WER is 20 percent. For Urdu the initial limits are 20 and 25 percent respectively, reflecting a separately declared rollout gate rather than evidence of quality. Every language also requires at most 5 percent false flags on target positions adjudicated as matching the spoken reference, and at least 80 percent flag recall on adjudicated differing target positions. Apply the corresponding language limits to the recorded age/device/noise cohorts as well as the overall result. Spanish criteria do not enable Spanish in the app.

WER is substitutions plus deletions plus insertions divided by the number of words in a human-adjudicated verbatim transcript; it can exceed 100 percent. Normalize using the frozen Unicode tokenization/casefold rules, preserving genuine letters and word differences. The printed reading target is separate. Mean speaker WER averages speaker-level edit/reference ratios, so a prolific speaker cannot alone determine it. Word flag agreement concerns reference transcript differences, not expert pronunciation ratings or a medical condition. Target-position ambiguity needs human adjudication before registration.

Before a release-quality evaluation, each language needs at least 30 distinct speakers, 90 clips, three clips per speaker, 1000 reference words, 500 matching target positions and 50 differing target positions. Include child/adult, phone/desktop and quiet/background cohorts, with at least ten distinct speakers in each named cohort. These minima are screening requirements, not statistical power or representativeness guarantees; intersections, dialects, hardware and intended ages still need review. Report denominators, failures and speaker-clustered uncertainty rather than treating correlated words as independent observations. A coverage pass never means quality passed.

## Historical exposure and new datasets

SPEECH_EXPOSURE_REGISTRY.json records 40 previously inspected SpeechOcean762 speaker IDs and 20 available audio checksums. Both earlier samples are exposed, suitable for reproduction/development rather than a fresh holdout. Printed prompts are not verbatim transcripts. Historical 29/110 acceptable-word disagreement and 4/5 expert-error flags are not equivalent to the new transcript criteria.

Use corpus-scoped pseudonymous speaker IDs consistently, including across languages. Audio hashes detect exact reuse even across renamed corpora. Renaming a person/corpus or recompressing audio can defeat mechanical checks, so a human custodian must confirm identity separation and that the holdout has not guided model selection. A tool cannot prove consent, rights or untouched status from a declaration.

Keep recordings and manifests in a private directory. Each development/holdout manifest has schema_version 1, corpus_id, split, rights_basis and a nonempty clips array. Each clip needs id, speaker_id, language, age_band, device, noise, audio_path, audio_sha256, target_text, reference_text, reference_kind=verbatim, reference_review=adjudicated and target_word_matches. That final array has one strict boolean per normalized target word, adjudicated against what was actually spoken. Age bands are child/adult; device phone/desktop; noise quiet/background. These are evaluation strata, not verified account ages.

Audio paths must stay within the private manifest directory; symlink/path escape, changed checksums, duplicate clips/audio and missing metadata are rejected. Files are limited to 32 MiB and manifests to 8 MiB. Duration, actual decodability, language correctness and annotation fidelity still need the next runner/human checks. Never commit the manifests, recordings, private registration receipts or raw transcripts.

## Supported workflow

Run python tools/freeze_speech_evaluation.py check to inspect the declared profile without weights or inference. To recreate a freeze, use its freeze command with --model-dir pointing to the existing cached snapshot and --out pointing inside .qa/speech-evaluation. It verifies artifact hashes and dependency versions, hashes the relevant source, and creates a new exclusive receipt. It never downloads or transcribes audio. The public SPEECH_BASELINE_FREEZE.json is a reviewed copy containing no local absolute paths, credentials or learner text.

Run the verify command with --freeze pointing to that receipt to check its seal, current source/profile and installed package versions. It checks receipt/source/environment, not current weight files; the future runner must rehash model artifacts immediately before inference. Receipts use a content checksum to detect accidental changes, not a trusted digital signature.

Run the register command with --freeze, --development, --holdout and --out paths. It checks source/environment drift, references, rights declaration, cohort fields, audio checksums and cross-split/historical exposure. It writes hashed dataset identities, private speaker/audio keys and coverage gaps into a new private receipt. Pilot samples with insufficient coverage can be registered, but remain release_sample_eligible=false. None of these commands performs inference or claims validated quality.

The next M2.2 runner must consume the preregistered hashes, reject changed data/model/configuration, withhold holdout transcripts from tuning, log every attempted clip including failures, and record the exposure after evaluation. It must prevent silent reruns from becoming a new independent result. Those runner, scoring-report and exposure-ledger mechanisms are not implemented by preregistration alone. Use exposed development data for model selection before any untouched evaluation.

## Verification and sources

Twenty offline regressions test frozen profile compatibility, weight/version/source drift, malformed manifests, privacy boundaries, label types, overlap and sampling eligibility. The existing 62 application and 18 provider regressions also pass. See SPEECH_EVALUATION_VALIDATION.json. No new learner audio, ASR benchmark, physical device, educator trial or release promotion is claimed.

Decoder parameter semantics were checked against the [pinned faster-whisper implementation](https://github.com/SYSTRAN/faster-whisper/blob/v1.2.1/faster_whisper/transcribe.py). Historical corpus attribution and limitations remain in evidence/LIVE_VALIDATION.md and its linked author/OpenSLR sources. Thresholds above are SOVEN engineering decisions; do not attribute them to that corpus or library.
