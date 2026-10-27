"""Offline candidate triage, not semantic deduplication or task admission."""
from fractions import Fraction
from pathlib import Path
import re
import time
import unicodedata

from .math500 import SHA256, _read_records, development_proposal
from .model import Invalid, digest
from .response_boundary import decode_response


def _features(text):
    normalized = ' '.join(unicodedata.normalize('NFC', text).casefold().split())
    tokens = re.findall(r'\w+|[^\w\s]', normalized)
    return normalized, set(tokens), {'<integer>' if t.isdecimal() else t for t in tokens}


def _jaccard(left, right):
    union = left | right
    return Fraction(len(left & right), len(union)) if union else Fraction(0)


def _triage(records, selected_ids):
    by_id = {r.source_id: r for r in records}
    selected = set(selected_ids)
    if len(by_id) != len(records) or len(selected) != len(selected_ids) or not selected <= set(by_id):
        raise Invalid('review source identities')
    features = {key: _features(r.problem) for key, r in by_id.items()}
    candidates = {}
    compared = set()
    for identity in sorted(selected):
        ranked = []
        left = features[identity]
        for other in sorted(by_id):
            if other == identity:
                continue
            pair = tuple(sorted((identity, other)))
            compared.add(pair)
            right = features[other]
            exact = left[0] == right[0]
            literal = _jaccard(left[1], right[1])
            masked = _jaccard(left[2], right[2])
            score = max(literal, masked)
            row = {'source_ids': list(pair), 'normalized_text_equal': exact,
                   'token_jaccard': str(literal), 'integer_masked_jaccard': str(masked),
                   'crosses_reserved_boundary': bool(set(pair) - selected),
                   'review_status': 'pending'}
            ranked.append((score, other, row))
            if exact or score >= Fraction(3, 5):
                candidates[pair] = row
        # Always retain three nearest neighbours, even below the triage threshold.
        for _, _, row in sorted(ranked, key=lambda item: (-item[0], item[1]))[:3]:
            candidates[tuple(row['source_ids'])] = row
    return {'unique_pairs_compared': len(compared),
            'candidate_pairs': [candidates[key] for key in sorted(candidates)],
            'selected_problem_cards': [
                {'source_id': identity, 'subject': by_id[identity].subject,
                 'level': by_id[identity].level, 'problem': by_id[identity].problem,
                 'contains_asy_markup': '[asy]' in by_id[identity].problem,
                 'family_review': 'pending', 'workflow_feasibility': 'pending',
                 'required_outputs': None, 'complementary_tasks': None,
                 'admission_reason': None}
                for identity in sorted(selected)]}


def prepare_review(data_path, proposal_path):
    start = time.process_time()
    raw = Path(proposal_path).read_bytes()
    if len(raw) > 65536:
        raise Invalid('proposal byte limit')
    supplied = decode_response(raw.decode('utf-8'))
    expected = development_proposal(data_path)
    if supplied != expected:
        raise Invalid('proposal differs from pinned deterministic selection')
    records = _read_records(data_path, SHA256, 500)
    review = _triage(records, [row['source_id'] for row in supplied['development']])
    return {'schema': 'phase2-math500-offline-review-v1',
            'status': 'review_pending', 'proposal_digest': supplied['proposal_digest'],
            'dataset_sha256': SHA256, **review,
            'triage_policy': {
                'version': 'nfc-casefold-token-jaccard-integer-mask-v1',
                'threshold': '3/5', 'nearest_per_selected': 3,
                'scope': 'selected_vs_all_including_selected_selected',
                'selection_uses_answers_or_solutions': False,
                'threshold_is_semantic_decision': False},
            'rubric': [
                'Review candidate families before freezing any held-out split.',
                'Retain unsuitable sources and reasons; never silently replace or reseed.',
                'Tasks need complementary deliverables, not duplicate whole-question answers.',
                'Every task must be required or an ancestor of a required output.',
                'Record meaningful task count and eligible owner counts; never pad.',
                'Record declared parent inputs; exposure alone is not semantic necessity.',
                'Treat diagram markup as data, never executable code.'],
            'semantic_deduplication_verified': False,
            'workflow_size_coverage_verified': False, 'task_execution_allowed': False,
            'model_executed': False, 'historical_scores_changed': False,
            'accounting': 'Separate offline preparation; no model or task-execution charges implied.',
            'offline_cpu_seconds': time.process_time() - start}
