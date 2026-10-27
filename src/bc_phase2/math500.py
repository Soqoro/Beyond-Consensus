"""Pinned local MATH-500 inspection; no downloads, evaluation or dispatch."""
from collections import Counter
from dataclasses import dataclass, field
import hashlib
from pathlib import Path

from .model import Invalid, digest
from .response_boundary import decode_response

DATASET = 'HuggingFaceH4/MATH-500'
REVISION = '6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be'
# User-supplied staging receipt, not an independently authenticated publisher hash.
SHA256 = '35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132'
MAX_FILE_BYTES = 5_000_000
SUBJECTS = ('Algebra', 'Counting & Probability', 'Geometry',
            'Intermediate Algebra', 'Number Theory', 'Prealgebra', 'Precalculus')
SPLIT_POLICY = 'math500-two-per-subject-source-hash-v1'


@dataclass(frozen=True)
class MathRecord:
    source_id: str
    problem: str = field(repr=False)
    answer: str = field(repr=False)
    solution: str = field(repr=False)
    subject: str
    level: int

    def public(self):
        return {'id': self.source_id, 'problem': self.problem}

    def private(self):
        return {'answer': self.answer, 'solution': self.solution}


def normalize_record(row):
    if type(row) is not dict:
        raise Invalid('MATH record must be an object')
    for key in ('unique_id', 'problem', 'answer', 'solution', 'subject'):
        if type(row.get(key)) is not str or not row[key].strip():
            raise Invalid('MATH required string field invalid')
    if type(row.get('level')) is not int or not 1 <= row['level'] <= 5:
        raise Invalid('MATH level invalid')
    return MathRecord(row['unique_id'], row['problem'], row['answer'],
                      row['solution'], row['subject'], row['level'])


def _read_records(path, expected_hash, expected_count):
    # Read once: the bytes parsed must be the bytes hashed. Never follow source IDs
    # as filesystem paths, and never execute eval.yaml or a dataset script.
    with Path(path).open('rb') as handle:
        raw = handle.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise Invalid('MATH file byte limit')
    if hashlib.sha256(raw).hexdigest() != expected_hash:
        raise Invalid('MATH file hash mismatch')
    try:
        lines = raw.decode('utf-8').splitlines()
    except UnicodeError as exc:
        raise Invalid('MATH UTF-8 invalid') from exc
    records = tuple(normalize_record(decode_response(line)) for line in lines if line.strip())
    if len(records) != expected_count:
        raise Invalid('MATH record count mismatch')
    if len({r.source_id for r in records}) != len(records):
        raise Invalid('MATH duplicate original source IDs')
    return records


def inspect_local(path):
    records = _read_records(path, SHA256, 500)
    return {
        'schema': 'phase2-math500-inspection-v1',
        'status': 'pinned_hash_and_structure_verified',
        'dataset': DATASET, 'revision': REVISION, 'sha256': SHA256,
        'hash_evidence': 'user_supplied_download_receipt',
        'upstream_split': 'test', 'records': len(records),
        'source_ids_digest': digest(sorted(r.source_id for r in records)),
        'subjects': dict(sorted(Counter(r.subject for r in records).items())),
        'levels': dict(sorted(Counter(r.level for r in records).items())),
        'public_fields': ['id', 'problem'], 'private_fields': ['answer', 'solution'],
        'development_split_selected': False, 'semantic_deduplication_verified': False,
        'official_evaluator_verified': False, 'rights_review': 'unresolved',
        'task_execution_allowed': False, 'model_executed': False,
    }


def _development_proposal(records):
    """Fixed seed/quotas, no outcome-based selection or family claims."""
    ids = [r.source_id for r in records]
    if len(ids) != len(set(ids)) or set(r.subject for r in records) != set(SUBJECTS):
        raise Invalid('split requires unique IDs and exactly seven declared subjects')
    selected = []
    for subject in SUBJECTS:
        candidates = [r.source_id for r in records if r.subject == subject]
        if len(candidates) < 2:
            raise Invalid('split requires two sources per subject')
        ranked = sorted(candidates, key=lambda identity: (
            digest([SPLIT_POLICY, 0, DATASET, subject, identity]), identity))
        selected.extend({'source_id': identity, 'subject': subject,
                         'rank_hash': digest([SPLIT_POLICY, 0, DATASET, subject, identity])}
                        for identity in ranked[:2])
    chosen = {row['source_id'] for row in selected}
    reserved = sorted(set(ids) - chosen)
    result = {
        'schema': 'phase2-math500-development-proposal-v1',
        'status': 'proposed_pending_source_family_review',
        'policy': SPLIT_POLICY, 'seed': 0, 'per_subject': 2,
        'source_ids_digest': digest(sorted(ids)),
        'development': selected, 'development_count': len(selected),
        'reserved_source_ids': reserved, 'reserved_count': len(reserved),
        'reserved_role': 'unused_unassigned_not_final_test_set',
        'final_test_selected': False, 'semantic_deduplication_verified': False,
        'workflow_size_coverage_verified': False, 'task_execution_allowed': False,
        'model_executed': False,
    }
    return result


def development_proposal(path):
    records = _read_records(path, SHA256, 500)
    result = {**_development_proposal(records), 'dataset': DATASET,
              'revision': REVISION, 'sha256': SHA256, 'upstream_split': 'test',
              'rights_review': 'unresolved', 'official_evaluator_verified': False}
    return {**result, 'proposal_digest': digest(result)}
