"""Synthetic local files only; no benchmark contents or network required."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.math500 import _read_records, inspect_local, normalize_record
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


if __name__ == '__main__':
    unittest.main()
