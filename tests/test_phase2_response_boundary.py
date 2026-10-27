"""Offline text-boundary tests; no model execution or provider imports."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.model import Invalid, Task, Workflow
from bc_phase2.response_boundary import (
    MAX_RESPONSE_BYTES, decode_response, review_allocation_texts,
)


class ResponseBoundary(unittest.TestCase):
    def setUp(self):
        self.w = Workflow('synthetic:text', tuple(Task(x) for x in 'abcd'), tuple('abcd'))
        self.valid = json.dumps({'groups': [['b', 'a'], ['d', 'c']]})
        for name in ('socket.socket.connect', 'socket.create_connection'):
            guard = patch(name, side_effect=AssertionError('network forbidden'))
            guard.start()
            self.addCleanup(guard.stop)

    def test_valid_tuple_and_no_live_authorization(self):
        result = review_allocation_texts(self.w, 2, [self.valid])
        self.assertEqual(result['groups'], (('a', 'b'), ('c', 'd')))
        self.assertEqual(result['attempts'], ['valid'])
        self.assertEqual(result['parsing'], ['decoded'])
        self.assertFalse(result['task_execution_allowed'])
        self.assertFalse(result['usage_verified'])

    def test_malformed_consumes_correction_slot(self):
        result = review_allocation_texts(self.w, 2, ['{', self.valid])
        self.assertEqual(result['attempts'], ['invalid', 'valid'])
        self.assertEqual(result['parsing'], ['invalid', 'decoded'])
        self.assertEqual(result['status'], 'valid')

    def test_ext01_not_repaired(self):
        result = review_allocation_texts(self.w, 2, ['{"groups":["ab","cd"]}'])
        self.assertEqual(result['status'], 'invalid_allocation')
        self.assertFalse(result['fallback'])

    def test_no_third_attempt_or_correction_after_success(self):
        with self.assertRaises(Invalid):
            review_allocation_texts(self.w, 2, ['{', '{', self.valid])
        result = review_allocation_texts(self.w, 2, [self.valid, self.valid])
        self.assertEqual(result['status'], 'invalid_allocation')
        self.assertEqual(result['attempts'], ['valid'])
        self.assertEqual(result['parsing'], ['decoded', 'not_read'])

    def test_strict_wire_rejections(self):
        for text in ('{"x":1,"x":2}', '{"x":1,"\\u0078":2}',
                     '{"a":{"x":1,"x":2}}', '{"x":NaN}', '{"x":1e999}',
                     '```json\n{}\n```', '<think>x</think>{}', '{}{}',
                     '"\\ud800"', None, ' ' * (MAX_RESPONSE_BYTES + 1)):
            with self.subTest(text=repr(text)[:80]), self.assertRaises(Invalid):
                decode_response(text)

    def test_no_unicode_normalization(self):
        result = decode_response('{"é":1,"e\\u0301":2}')
        self.assertEqual(len(result), 2)

    def test_two_invalid_attempts_retained(self):
        result = review_allocation_texts(self.w, 2, ['{', 'null'])
        self.assertEqual(result['attempts'], ['invalid', 'invalid'])
        self.assertIsNone(result['groups'])

    def test_payload_is_not_mutated(self):
        texts = [self.valid]
        review_allocation_texts(self.w, 2, texts)
        self.assertEqual(texts, [self.valid])


if __name__ == '__main__':
    unittest.main()
