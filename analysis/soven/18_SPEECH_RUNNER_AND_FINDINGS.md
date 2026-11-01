# SOVEN speech evaluation runner and findings

M2.2 now has a reproducible offline runner, persistent exposure tracking and measured development results. Five synthetic controls passed. The 20 previously inspected child clips reproduced the old disagreement; an explicitly declared beam-five variant reduced acceptable-word flags from 29/110 to 24/110 on that same exposed sample. The variant remains unpromoted. This result does not establish general ASR accuracy or pronunciation assessment.

## Implemented runner

tools/evaluate_speech.py supports development, holdout, controls and historical modes. core/speech_runner.py verifies the frozen source/environment and rehashes actual model artifacts before processing. Only audio bytes and language enter the local worker; reading targets and reference text remain in the parent scoring process. The worker uses the recorded faster-whisper implementation with local_files_only, an offline environment and blocked socket connections. There is no cloud call, download or alternative recognizer fallback.

The sealed speech_runner_protocol.json fixes a 60-second startup deadline, 45-second clip deadline, 0.2–30-second decoded duration, text/token limits and a three-consecutive-failure stop. A stalled worker is terminated; remaining clips are explicitly not_run. Decode errors, absent speech, changed inputs, startup failure and interruption remain visible. Reports distinguish initialization and per-clip elapsed time. Estimated or unavailable timing is not converted into measured timestamps.

Detailed reports stay under ignored .qa. They are created exclusively and updated atomically, retain every scheduled clip and end with a content checksum. Error text excludes raw exception messages. A process killed before finalization can leave a running report and reserved exposure; it cannot become a successful result. Receipt checksums detect accidental changes, not a trusted signature against a deliberate editor.

## Metrics and exposure

core/speech_metrics.py computes deterministic minimum-edit substitutions/deletions/insertions with Unicode normalization, aggregate WER and mean speaker WER. Target flags use the existing alignment/scorer. Insertions stay visible separately. Rates with zero denominators remain unavailable. WER denominators cover completed clips only, and every failed/not-run clip blocks release review.

Uncertainty uses 2000 seeded resamples of whole speaker clusters, rather than independent word draws. Fewer than two completed speakers yields unavailable intervals. Percentile intervals and small cohort summaries remain exploratory. The declared language thresholds apply overall and within recorded cohorts; sample coverage also has to pass. quality_validated remains false and no language is automatically enabled.

The private .qa/speech-evaluation/exposure.sqlite3 ledger reserves corpus/speaker IDs and audio hashes before worker startup. Atomic reservations prevent concurrent duplicate holdouts. Failed, interrupted and abandoned reservations remain exposed; choosing another output filename or candidate does not restore freshness. The CLI uses this fixed ledger. Deleting it, changing machines or renaming people/recompressing audio can defeat local checks; a custodian must preserve exposure history across environments.

Human development/holdout modes require adjudicated verbatim references. Controls instead require synthetic_script/scripted labels and cannot become release evidence. Historical mode accepts printed_prompt/historical_expert_ratings only for speakers in the recorded exposure registry; device/noise can remain unknown. It reports printed-prompt edit rate and expert-rating disagreement separately, never ASR WER. A holdout additionally needs a matching preregistration and unchanged development/holdout manifests, exposure registry and configuration.

## Measured development results

The final controls used five existing locally synthesized adult-voice scripts: correct reading, extra leading word, omission, substitution and missing ending. All 42 scripted spoken words matched the recognized transcript. All 39 matching target positions remained accepted, all three scripted differing target positions were flagged, and the leading insertion remained visible. These are functional controls with one synthetic voice, not human speech-quality evidence.

The historical reproduction used the same 20 already exposed English clips and 115 printed target words. Beam one produced 40 prompt edits, 29/110 acceptable words flagged and 4/5 expert-error words flagged, reproducing the old result. Beam five produced 38 prompt edits, 24/110 acceptable words flagged and the same 4/5 expert-error flags. Acceptable-word disagreement changed from 26.36 to 21.82 percent, a 4.55 percentage-point difference on this sample. Prompt references and expert pronunciation ratings are different evidence from verbatim ASR references.

The final sequential baseline/candidate runs took about 26.04 and 32.88 seconds including startup/report work on this machine. These single-run timings are descriptive, not capacity or latency guarantees. An earlier runner check also processed five controls and the exposed historical sample; no unfavorable run or fresh holdout is omitted. The final source-bound comparison repeats development data explicitly. SPEECH_EXPLORATORY_COMPARISON.json records aggregates and report hashes; detailed transcripts/audio remain private.

## Continue from this point

The default production decoder, provider choices, scores and enabled languages are unchanged. backend/data/speech_evaluation_beam5.json is an explicit unpromoted development candidate with the same thresholds, weights and constructor settings. Use --profile with that file when freezing/verifying/running the candidate; the default selects the reference profile. For the freeze tool the global --profile option precedes the action. A candidate cannot silently use another profile's freeze.

SPEECH_BASELINE_FREEZE.json now binds the completed runner/metrics code. SPEECH_BEAM5_DEVELOPMENT_FREEZE.json binds the declared variant. The original M2.1 receipt is preserved as evidence/SPEECH_BASELINE_FREEZE_M21.json; its old source hashes are historical and are not expected to verify against changed tooling. Thresholds, weights and the reference decoder choice were preserved before these exposed development runs.

M2.2a runner/controls and M2.2b historical reproduction/candidate measurement are complete. M2.2c remains open: improve recognition enough on reviewed development data, then preregister untouched evaluation with verbatim transcripts and sufficient target-label coverage. Do not promote beam five from these 20 clips. Representative Urdu/Spanish, devices/noise, educator review and public release gates remain open. No suitable new human-adjudicated manifest has been supplied.

Run test_regressions.py, test_reasoning_providers.py, test_speech_evaluation.py and test_speech_runner.py under backend/tests. The stage passes 132 backend tests: 62 application, 18 provider, 21 freeze/preregistration and 31 runner/metric cases. CI also checks generated-language drift and the frontend. Public facts, limitations and protocol references remain in guide 17 and the reviewed evidence records.
