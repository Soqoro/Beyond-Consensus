"""Synthetic-only similarity and proposal-integrity tests."""
from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.math500 import MathRecord
from bc_phase2.math500_review import _triage, prepare_review
from bc_phase2.model import Invalid


class Review(unittest.TestCase):
    def fixtures(self):
        return tuple(MathRecord(str(i), text, 'GOLD_SENTINEL', 'SOLUTION_SENTINEL', 'fixture', 1)
                     for i, text in enumerate(('Find 12 plus 5.', 'Find 13 plus 8.',
                         '  FIND 12 plus 5. ', 'Explain an unrelated triangle.', 'Other text.')))

    def test_no_gold_or_reserved_problem_text(self):
        result = _triage(self.fixtures(), ['0'])
        raw = json.dumps(result)
        for private in ('GOLD_SENTINEL', 'SOLUTION_SENTINEL', 'unrelated triangle'):
            self.assertNotIn(private, raw)
        self.assertEqual(len(result['selected_problem_cards']), 1)
        self.assertEqual(result['selected_problem_cards'][0]['problem'], 'Find 12 plus 5.')

    def test_exact_and_number_variant_candidates(self):
        pairs = {tuple(p['source_ids']): p for p in _triage(self.fixtures(), ['0'])['candidate_pairs']}
        self.assertTrue(pairs[('0', '2')]['normalized_text_equal'])
        self.assertEqual(pairs[('0', '1')]['integer_masked_jaccard'], '1')
        self.assertEqual(pairs[('0', '1')]['review_status'], 'pending')

    def test_order_invariance_and_gold_independence(self):
        records = self.fixtures()
        self.assertEqual(_triage(records, ['0', '1']),
                         _triage(tuple(reversed(records)), ['1', '0']))
        self.assertEqual(_triage(records, ['0']),
                         _triage(tuple(replace(r, answer='new', solution='new') for r in records), ['0']))
        self.assertEqual(_triage(records, ['0', '1'])['unique_pairs_compared'], 7)

    def test_nearest_returned_even_below_threshold(self):
        result = _triage(self.fixtures(), ['4'])
        self.assertGreaterEqual(len(result['candidate_pairs']), 3)

    def test_bad_source_identity_rejected(self):
        for selected in (['0', '0'], ['missing']):
            with self.assertRaises(Invalid):
                _triage(self.fixtures(), selected)

    def test_changed_proposal_rejected_before_triage(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'proposal.json'
            p.write_text('{"changed":true}')
            with patch('bc_phase2.math500_review.development_proposal', return_value={'changed': False}), \
                 patch('bc_phase2.math500_review._read_records') as read:
                with self.assertRaisesRegex(Invalid, 'proposal differs'):
                    prepare_review('unused', p)
                read.assert_not_called()
