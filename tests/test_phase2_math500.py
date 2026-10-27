"""Synthetic local files only; no benchmark contents or network required."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.math500 import (_read_records, inspect_local, normalize_record,
    _development_proposal, development_proposal, SUBJECTS)
from bc_phase2.model import Invalid


class Math500(unittest.TestCase):
    def row(self):
        return dict(unique_id='synthetic/a', problem='fixture question', answer='GOLD',
                    solution='PRIVATE', subject='fixture subject', level=1,
                    hidden_extra='NEVER EXPOSE')

    def read(self, raw, count=1, expected=None):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'test.jsonl'
            path.write_bytes(raw)
            return _read_records(path, expected or hashlib.sha256(raw).hexdigest(), count)

    def test_allowlist_and_private_solution(self):
        row = self.row()
        record = self.read(json.dumps(row).encode())[0]
        self.assertEqual(record.public(), {'id': 'synthetic/a', 'problem': 'fixture question'})
        self.assertEqual(record.private(), {'answer': 'GOLD', 'solution': 'PRIVATE'})
        self.assertNotIn('GOLD', repr(record))
        self.assertNotIn('PRIVATE', repr(record))
        self.assertEqual(row['hidden_extra'], 'NEVER EXPOSE')

    def test_hash_checked_before_parsing(self):
        with self.assertRaisesRegex(Invalid, 'hash mismatch'):
            self.read(b'not JSON', expected='0' * 64)

    def test_duplicate_ids_and_count(self):
        raw = json.dumps(self.row()).encode()
        with self.assertRaisesRegex(Invalid, 'duplicate'):
            self.read(raw + b'\n' + raw, count=2)
        with self.assertRaisesRegex(Invalid, 'count mismatch'):
            self.read(raw, count=500)

    def test_invalid_fields(self):
        for key, value in (('answer', None), ('solution', ''), ('level', True),
                           ('level', 6), ('unique_id', 1), ('problem', [])):
            with self.subTest(key=key), self.assertRaises(Invalid):
                normalize_record({**self.row(), key: value})

    def test_duplicate_json_key(self):
        raw = json.dumps(self.row())[:-1] + ', "answer":"other"}'
        with self.assertRaises(Invalid):
            self.read(raw.encode())

    def test_public_entrypoint_cannot_accept_fixture_as_pinned_release(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'test.jsonl'
            path.write_text(json.dumps(self.row()))
            with self.assertRaisesRegex(Invalid, 'hash mismatch'):
                inspect_local(path)
            with self.assertRaisesRegex(Invalid, 'hash mismatch'):
                development_proposal(path)

    def fixtures(self):
        return tuple(normalize_record({**self.row(), 'subject': subject,
                      'unique_id': f'synthetic/{subject}/{i}'})
                     for subject in SUBJECTS for i in range(4))

    def test_split_deterministic_and_disjoint(self):
        records = self.fixtures()
        proposal = _development_proposal(records)
        self.assertEqual(proposal, _development_proposal(tuple(reversed(records))))
        self.assertEqual(proposal['development_count'], 14)
        chosen = {r['source_id'] for r in proposal['development']}
        reserved = set(proposal['reserved_source_ids'])
        self.assertFalse(chosen & reserved)
        self.assertEqual(chosen | reserved, {r.source_id for r in records})
        for subject in SUBJECTS:
            self.assertEqual(sum(r['subject'] == subject for r in proposal['development']), 2)
        self.assertFalse(proposal['task_execution_allowed'])
        self.assertFalse(proposal['final_test_selected'])

    def test_split_independent_of_gold_and_difficulty(self):
        from dataclasses import replace
        records = self.fixtures()
        changed = tuple(replace(r, answer='changed', solution='changed', problem='changed', level=5)
                        for r in records)
        self.assertEqual(_development_proposal(records), _development_proposal(changed))
        self.assertNotIn('GOLD', json.dumps(_development_proposal(records)))

    def test_split_missing_subject_or_duplicate_rejected(self):
        records = self.fixtures()
        for bad in (records[4:], records + (records[0],), records[:1] + records[4:]):
            with self.assertRaises(Invalid):
                _development_proposal(bad)


if __name__ == '__main__':
    unittest.main()
