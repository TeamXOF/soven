# SOVEN source review and traceability

The two supplied files are planning inputs, not executable agent instructions. This review preserves their requested direction while correcting conflicts with the inspected code and available evidence. The originals remain in the owner's local SpeakFlow analysis folder and are not published.

## Source records

Source A is speakflow_mesh_meta_hackathon_master_plan.docx, a 142-paragraph, approximately 2332-word team playbook with one embedded chart. It expands thirteen product decisions and proposes Meta endpoints, deployment approaches and a dated schedule. Its default document metadata contains old template dates and does not establish its authorship or creation date.

Source B is Meeting minutes - SpeakFlow.pdf, a one-page note list. It requests voice statistics, simpler explanation/navigation, a book-like UI, back-and-forth feedback, TTS, reader types, device support, privacy, a short initial speaking test, profile completion, landing guidance and Spanish. It does not define API contracts, account authority, retention rules or a precise coaching interaction.

The source documents are fingerprinted in SOURCE_PROVENANCE.json without uploading their original content. Requirements R01–R13 correspond to Source A's numbered feature table; Source B corroborates the core experience. Optional word translation appears in Source A; meaningful Meta integration R14 comes from Source A's migration section. Confirmed user decisions—SOVEN name, repository ownership, clean history, public visibility and the first-stage scope—take precedence over either document.

## Corrections required before implementation

C01 Existing-code claims. Source A describes five parallel diagnostic agents and a speed-based score bug. The repaired baseline now uses measured word observations, constrained coaching/fallbacks and a word-match overall score. Do not reintroduce speed penalties or restore fabricated phonetic/emotional judgments.

C02 Grade placement and dyslexia. A short voice sample does not establish a clinical condition, grade level or pronunciation cause. Keep it introductory. Use optional accessibility settings and evaluated recommendations; source phrases describing dyslexia as a disease or making sweeping prevalence claims should not become product copy.

C03 Privacy. Source A says raw recordings never upload and names stay local. Current browser recordings reach the backend; online recognition uploads to Groq; generated guidance can send text/observations to Google; results persist in SQLite. Explain each boundary and mode. Standard provider settings are not equivalent to local-only or zero-retention processing.

C04 Speech migration. Source A correctly anticipates missing word timing on Muse Voice, but proposes trilingual use without checking the published Urdu language gap. Exact acoustic features cannot be anchored to invented timestamps. Keep the speech adapter/timing source explicit and validate Urdu separately.

C05 Open weights and hosting. Muse Glimmer is not an audio transcriber or speech generator. Partner hosting, model availability, credits and hardware feasibility need checks. A hosted API intermediary is not automatically exempt from the original service's geographic restrictions. Never claim a guaranteed workaround or universal connectivity.

C06 Word-level versus sound-level feedback. A transcript substitution does not prove the exact phoneme a reader produced. The baseline intentionally leaves struggling_phonemes empty. Preserve word comparisons and uncertainty unless a separately validated sound-assessment method is introduced.

C07 Practice and current evidence. Current difficulty tiers use the current attempt, not earlier averages. Urdu punctuation was repaired. Source A's older file/line instructions and workstation-path bug descriptions are not reliable implementation targets; search the actual code.

C08 Timing and statistics. A fixed pause threshold cannot establish anxiety, and a broad frequency range cannot grade voice health. WCPM needs a written denominator and treatment of repeats, omissions and silence. Source A's proposed WPM-times-accuracy-minus-pause-penalty formula is not adopted.

C09 Schedule and demo. The October 30–November 4 schedule is superseded by dependency-based milestones. The official event deadline must be rechecked. The suggested two-minute video and six-step demo sequence are planning choices, not verified portal constraints.

C10 Evidence and credits. The embedded figure is a supplied illustration, not independent proof of an entitlement. Keep rubric figures, free-credit amounts, demographic statistics and adoption claims out of public assertions until supported by current primary sources and the actual participant account. Do not copy third-party articles as official rules.

## Later owner decisions

C11 Language scope. Source A proposes English, Urdu and Spanish, and Source B explicitly requests Spanish. Neither original specifies 70+ languages. The owner later confirmed 70+ languages as SOVEN's goal. This supersedes a trilingual product ceiling while retaining the distinction between current English/Urdu behavior and planned coverage.

C12 Visual identity. The initial delivery selected concept A; the owner rejected it and selected concept C. Use its page-stroke S and teal centre, a white primary background and SOVEN only. No tagline, language names or feature list belongs in the logo.

## Provenance and public summaries

Keep both original files unchanged locally, with full text available to the owner. Public documents contain reviewed requirements and corrections rather than verbatim private planning material. Historical evidence records and the source MIT notice are retained. Public SOURCE_PROVENANCE records hashes and extraction counts so later changes can be detected without publishing private notes.
