"""Injected synthetic contracts, no real data, models or network."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.calibration_contracts import (
    SourceBinding, TokenObservation, math_development_views, validate_split,
)
from bc_phase2.model import Invalid


class CalibrationContracts(unittest.TestCase):
    def setUp(self):
        self.dev = SourceBinding('HuggingFaceH4/MATH-500', 'synthetic-revision', 'a', 'family:a', 'development')
        self.test = replace(self.dev, problem_id='b', source_family='family:b', split='test')

    def test_split_order_invariant_and_not_authorization(self):
        result = validate_split((self.dev, self.test))
        self.assertEqual(result, validate_split((self.test, self.dev)))
        self.assertFalse(result['task_execution_allowed'])
        self.assertFalse(result['semantic_deduplication_verified'])

    def test_cross_release_and_family_leakage(self):
        for other in (replace(self.dev, revision='another', split='test'),
                      replace(self.test, source_family=self.dev.source_family)):
            with self.subTest(other=other), self.assertRaises(Invalid):
                validate_split((self.dev, other))
        with self.assertRaises(Invalid):
            validate_split((self.dev, self.dev, self.test))

    def test_missing_split_and_identity_rejected(self):
        with self.assertRaises(Invalid):
            validate_split((self.dev,))
        with self.assertRaises(Invalid):
            replace(self.dev, revision='')

    def test_gold_and_raw_extras_not_public(self):
        row = {'id': 'a', 'problem': 'synthetic question', 'answer': '2',
               'solution': 'private explanation', 'other': 'private extra'}
        public, private = math_development_views(self.dev, row)
        self.assertEqual(public, {'id': 'a', 'problem': 'synthetic question'})
        self.assertEqual(private, {'answer': '2'})
        self.assertEqual(row['solution'], 'private explanation')

    def test_heldout_mismatch_and_missing_problem_rejected(self):
        for binding, row in ((self.test, {'id': 'b', 'problem': 'x'}),
                             (self.dev, {'id': 'wrong', 'problem': 'x'}),
                             (self.dev, {'id': 'a', 'problem': None})):
            with self.subTest(row=row), self.assertRaises(Invalid):
                math_development_views(binding, row)
        _, private = math_development_views(self.dev, {'id': 'a', 'problem': 'x'})
        self.assertIsNone(private['answer'])

    def observation(self, **changes):
        return replace(TokenObservation('attempt:1', 'slot:1', 'model:fixture',
            'tokenizer:fixture', 'complete', 100, 40, 20, 30), **changes)

    def test_subcounts_not_double_counted(self):
        self.assertEqual(self.observation().total_tokens, 140)
        self.assertFalse(self.observation().retain_reservation)

    def test_unknown_not_zero_or_partial_full_bill(self):
        for status in ('unknown', 'incomplete'):
            observation = self.observation(status=status, output_tokens=None)
            self.assertEqual(observation.input_tokens, 100)
            self.assertIsNone(observation.total_tokens)
            self.assertTrue(observation.retain_reservation)

    def test_malformed_usage_rejected(self):
        for change in ({'input_tokens': True}, {'output_tokens': -1},
                       {'output_tokens': 2.0}, {'input_tokens': None},
                       {'cached_input_tokens': 101}, {'reasoning_output_tokens': 41},
                       {'physical_attempt_id': ''}):
            with self.subTest(change=change), self.assertRaises(Invalid):
                self.observation(**change)


if __name__ == '__main__':
    unittest.main()
