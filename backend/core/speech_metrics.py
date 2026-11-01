"""Deterministic transcript metrics; never send references to the recognizer."""
from collections import Counter, defaultdict
import random

from services.acoustic import tokenize, _norm, align_words, score_word


def edit_counts(reference, hypothesis, maximum_tokens=1024):
    ref = [_norm(word) for word in tokenize(reference)]
    hyp = [_norm(word) for word in tokenize(hypothesis)]
    if max(len(ref), len(hyp)) > maximum_tokens:
        raise ValueError('Token limit exceeded')
    # Tuple stores edits/substitutions/deletions/insertions. Tie order is diagonal,
    # deletion, insertion; this makes repeated-word reports reproducible.
    previous = [(j, 0, 0, j) for j in range(len(hyp) + 1)]
    for i, left in enumerate(ref, 1):
        row = [(i, 0, i, 0)]
        for j, right in enumerate(hyp, 1):
            prior = previous[j-1]
            substitution = int(left != right)
            diagonal = (prior[0]+substitution, prior[1]+substitution, prior[2], prior[3])
            prior = previous[j]
            deletion = (prior[0]+1, prior[1], prior[2]+1, prior[3])
            prior = row[-1]
            insertion = (prior[0]+1, prior[1], prior[2], prior[3]+1)
            row.append(min([diagonal, deletion, insertion], key=lambda item: item[0]))
        previous = row
    edits, substitutions, deletions, insertions = previous[-1]
    return {'edits': edits, 'substitutions': substitutions, 'deletions': deletions,
            'insertions': insertions, 'reference_words': len(ref), 'hypothesis_words': len(hyp),
            'wer': edits / len(ref) if ref else None}


def score_clip(clip, result, mode, protocol):
    transcript = result['text']
    if not isinstance(transcript, str) or len(transcript) > protocol['maximum_text_characters']:
        raise ValueError('Invalid recognizer text')
    counts = edit_counts(clip['reference_text'], transcript, protocol['maximum_tokens'])
    if not counts['hypothesis_words']:
        raise ValueError('No speech recognized')
    # Use actual recognizer words where available; mark text-only tokenization as
    # unavailable timing, never invent word timestamps for an evaluation.
    words = result.get('words') or [{'word': word, 'timing_source': 'unavailable'} for word in tokenize(transcript)]
    entries = align_words(clip['target_text'], words)
    predictions = [score_word({**entry, 'language': clip['language']}, {}) for entry in entries if entry['target']]
    flags = [not prediction['correct'] for prediction in predictions]
    extra_words = [word for entry in entries for word in entry.get('extra_words', [])]
    row = {'status': 'ok', 'id': clip['id'], 'speaker_id': clip['speaker_id'],
           'language': clip['language'], 'age_band': clip['age_band'], 'device': clip['device'], 'noise': clip['noise'],
           'transcript': transcript, 'target_flags': flags, 'extra_words': extra_words,
           'audio_seconds': result.get('audio_seconds'), 'asr_invoked': result.get('asr_invoked'), 'timing_source': result.get('timing_source', 'unavailable')}
    if mode == 'historical':
        row['prompt_counts'] = counts
        row['prompt_counts'].pop('wer')
        confusion = Counter()
        labels = clip.get('expert_word_labels') or []
        for index in range(max(len(predictions), len(labels))):
            if index >= len(predictions) or index >= len(labels):
                confusion['unmatched_word_labels'] += 1
                continue
            label, prediction = labels[index], predictions[index]
            if [_norm(w) for w in tokenize(label['text'])] != [_norm(w) for w in tokenize(prediction['word'])]:
                confusion['unmatched_word_labels'] += 1
                continue
            expert_error = float(label['accuracy']) <= 6
            key = ('expert_error_' if expert_error else 'expert_acceptable_') + ('model_accept' if prediction['correct'] else 'model_flag')
            confusion[key] += 1
        row['historical_expert_comparison'] = dict(confusion)
    else:
        expected = clip['target_word_matches']
        if len(expected) != len(flags):
            raise ValueError('Target alignment length changed')
        row['asr_counts'] = counts
        row['flag_counts'] = {'matching': sum(expected), 'differing': sum(not value for value in expected),
                              'false_flags': sum(match and flag for match, flag in zip(expected, flags)),
                              'differing_flagged': sum(not match and flag for match, flag in zip(expected, flags))}
    return row


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def summarize(rows, mode, protocol, uncertainty=True):
    complete = [row for row in rows if row['status'] == 'ok']
    counts = Counter(row['status'] for row in rows)
    summary = {'scheduled': len(rows), 'completed': len(complete), 'failed': counts['failed'],
               'not_run': counts['not_run'], 'failure_free': len(complete) == len(rows),
               'denominator_scope': 'Completed clips only; failures remain listed and block release review'}
    if mode == 'historical':
        reference = sum(row['prompt_counts']['reference_words'] for row in complete)
        errors = sum(row['prompt_counts']['edits'] for row in complete)
        comparison = Counter()
        for row in complete: comparison.update(row['historical_expert_comparison'])
        summary.update(prompt_reference_words=reference, prompt_edits=errors,
                       prompt_text_edit_rate=_ratio(errors, reference),
                       historical_expert_comparison=dict(comparison),
                       interpretation='Printed-prompt agreement and expert-rating disagreement; not ASR WER')
        return summary
    reference = sum(row['asr_counts']['reference_words'] for row in complete)
    errors = sum(row['asr_counts']['edits'] for row in complete)
    flags = Counter()
    speakers = defaultdict(Counter)
    for row in complete:
        flags.update(row['flag_counts'])
        speakers[row['speaker_id']].update({'errors': row['asr_counts']['edits'],
            'reference': row['asr_counts']['reference_words'], **row['flag_counts']})
    summary.update(reference_words_on_completed=reference, edits_on_completed=errors,
        wer_on_completed=_ratio(errors, reference),
        mean_speaker_wer_on_completed=(sum(value['errors']/value['reference'] for value in speakers.values()) / len(speakers)) if speakers else None,
        flag_counts=dict(flags), false_flag_rate_on_completed=_ratio(flags['false_flags'], flags['matching']),
        reference_difference_recall_on_completed=_ratio(flags['differing_flagged'], flags['differing']))
    if uncertainty:
        if len(speakers) < 2:
            summary['speaker_bootstrap'] = {'available': False, 'reason': 'Fewer than two completed speakers'}
        else:
            rng = random.Random(protocol['bootstrap_seed'])
            clusters = [speakers[key] for key in sorted(speakers)]
            samples = {'wer': [], 'false_flag_rate': [], 'reference_difference_recall': []}
            for _ in range(protocol['bootstrap_replicates']):
                aggregate = Counter()
                for _ in clusters: aggregate.update(rng.choice(clusters))
                for key, numerator, denominator in [('wer','errors','reference'),
                    ('false_flag_rate','false_flags','matching'),('reference_difference_recall','differing_flagged','differing')]:
                    value = _ratio(aggregate[numerator], aggregate[denominator])
                    if value is not None: samples[key].append(value)
            alpha = (1 - protocol['bootstrap_confidence']) / 2
            intervals = {}
            for key, values in samples.items():
                values.sort()
                intervals[key] = {'lower': values[int(alpha*(len(values)-1))],
                                  'upper': values[int((1-alpha)*(len(values)-1))], 'replicates': len(values)} if values else None
            summary['speaker_bootstrap'] = {'available': True, 'method': protocol['uncertainty'],
                'seed': protocol['bootstrap_seed'], 'confidence': protocol['bootstrap_confidence'], 'intervals': intervals}
    return summary


def threshold_checks(summary, criteria):
    return {'failure_free': summary['failure_free'],
        'corpus_wer': summary.get('wer_on_completed') is not None and summary['wer_on_completed'] <= criteria['max_corpus_wer'],
        'mean_speaker_wer': summary.get('mean_speaker_wer_on_completed') is not None and summary['mean_speaker_wer_on_completed'] <= criteria['max_mean_speaker_wer'],
        'false_flags': summary.get('false_flag_rate_on_completed') is not None and summary['false_flag_rate_on_completed'] <= criteria['max_reference_matching_target_false_flag_rate'],
        'difference_recall': summary.get('reference_difference_recall_on_completed') is not None and summary['reference_difference_recall_on_completed'] >= criteria['min_reference_difference_flag_recall']}


def summarize_run(rows, mode, profile, protocol, coverage):
    languages = {}
    for language in sorted({row['language'] for row in rows}):
        subset = [row for row in rows if row['language'] == language]
        summary = summarize(subset, mode, protocol)
        cohorts = {}
        for dimension in ['age_band', 'device', 'noise']:
            for value in sorted({row[dimension] for row in subset}):
                group = summarize([row for row in subset if row[dimension] == value], mode, protocol)
                if mode != 'historical': group['checks'] = threshold_checks(group, profile['language_criteria'][language])
                cohorts[dimension+':'+value] = group
        summary['cohorts'] = cohorts
        summary['coverage'] = coverage.get(language)
        if mode != 'historical': summary['checks'] = threshold_checks(summary, profile['language_criteria'][language])
        summary['release_review_eligible'] = (mode == 'holdout' and bool(coverage.get(language, {}).get('release_sample_eligible'))
            and all(summary['checks'].values()) and all(all(group['checks'].values()) for group in cohorts.values()))
        languages[language] = summary
    return {'languages': languages, 'quality_validated': False,
            'release_review_eligible': bool(languages) and all(value['release_review_eligible'] for value in languages.values()),
            'interpretation': 'Engineering screening only; no automatic language promotion or pronunciation diagnosis'}
