"""EXT-01 decoded-response controls; no raw parser, provider or model calls."""
from collections import UserDict
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bc_phase2 import allocation as a, runtime
from bc_phase2.model import Allocation, Invalid, Task, Workflow, groups


class LLMResponseBoundary(unittest.TestCase):
    def setUp(self):
        self.w = Workflow('EXT-01:synthetic', tuple(Task(t) for t in 'abcd'), tuple('abcd'))
        self.valid = {'groups': [['b', 'a'], ['d', 'c']]}
        # Neither structural rejection nor correction may invoke an optimizer or worker.
        self.guards = []
        for owner, name in ((a, 'solve'), (a, 'match_table'), (a, 'reference'),
                            (a, 'allocate'), (runtime, 'execute'), (runtime.MockWorker, 'invoke')):
            guard = patch.object(owner, name, side_effect=AssertionError('forbidden fallback/dispatch'))
            mock = guard.start()
            self.guards.append(mock)
            self.addCleanup(guard.stop)
        for name in ('socket.socket.connect', 'socket.create_connection'):
            guard = patch(name, side_effect=AssertionError('offline test'))
            guard.start()
            self.addCleanup(guard.stop)

    def tearDown(self):
        for guard in self.guards:
            guard.assert_not_called()

    def invalid(self, reply):
        before = copy.deepcopy(reply)
        result = a.llm_reply(self.w, 2, [reply])
        self.assertEqual(result['status'], 'invalid_allocation')
        self.assertIsNone(result['groups'])
        self.assertEqual(result['attempts'], ['invalid'])
        self.assertIs(result['fallback'], False)
        self.assertEqual(reply, before)

    def test_exact_string_group_counterexample(self):
        self.invalid({'groups': ['ab', 'cd']})

    def test_one_structural_correction_after_counterexample(self):
        replies = [{'groups': ['ab', 'cd']}, self.valid]
        before = copy.deepcopy(replies)
        result = a.llm_reply(self.w, 2, replies)
        self.assertEqual(result['status'], 'valid')
        self.assertEqual(result['groups'], (('a', 'b'), ('c', 'd')))
        self.assertEqual(result['attempts'], ['invalid', 'valid'])
        self.assertEqual(replies, before)

    def test_outer_containers_rejected(self):
        for value in ({'ab': 1, 'cd': 2}, 'abcd', (['a', 'b'], ['c', 'd']),
                      {'ab', 'cd'}, None, 2, True, 2.0):
            with self.subTest(value=value):
                self.invalid({'groups': value})

    def test_inner_containers_rejected(self):
        for value in ('ab', {'a': 1, 'b': 2}, ('a', 'b'), {'a', 'b'},
                      None, 2, True, 2.0):
            with self.subTest(value=value):
                self.invalid({'groups': [value, ['c', 'd']]})

    def test_group_size_count_and_coverage_rejected(self):
        for value in ([], [['a', 'b']], [['a'], ['b'], ['c', 'd']],
                      [[], ['a', 'b', 'c', 'd']], [['a', 'b', 'c'], ['d']],
                      [['a', 'b'], ['c']], [['a', 'b'], ['c', 'c']],
                      [['a', 'b'], ['a', 'd']]):
            with self.subTest(value=value):
                self.invalid({'groups': value})

    def test_entries_are_exact_known_nonempty_string_ids(self):
        for entry in (None, False, True, 1, 1.0, {}, {'id': 'a'}, ['a'],
                      ('a',), '', 'unknown', ' a', 'a ', 'A', 'ab'):
            with self.subTest(entry=entry):
                self.invalid({'groups': [[entry, 'b'], ['c', 'd']]})

    def test_top_level_schema_rejected(self):
        for reply in (None, [], 'groups', 1, True, (), set(), UserDict(self.valid),
                      {}, {'group': self.valid['groups']}, {**self.valid, 'extra': None}):
            with self.subTest(reply=reply):
                self.invalid(reply)

    def test_valid_pairs_singletons_and_two_character_id(self):
        cases = [(self.w, 2, self.valid, (('a', 'b'), ('c', 'd'))),
                 (self.w, 3, {'groups': [['d'], ['b', 'a'], ['c']]},
                  (('a', 'b'), ('c',), ('d',))),
                 (Workflow('EXT-01:ids', (Task('ab'), Task('c'), Task('d')),
                           ('ab', 'c', 'd')), 2,
                  {'groups': [['d', 'c'], ['ab']]}, (('ab',), ('c', 'd')))]
        for workflow, n, reply, expected in cases:
            with self.subTest(ids=workflow.ids, n=n):
                before = copy.deepcopy(reply)
                result = a.llm_reply(workflow, n, [reply])
                self.assertEqual(result['status'], 'valid')
                self.assertEqual(result['attempts'], ['valid'])
                self.assertEqual(result['groups'], expected)
                self.assertEqual(reply, before)

    def test_two_invalid_attempts_no_fallback(self):
        replies = [{'groups': ['ab', 'cd']}, {'groups': [['a', 'b'], ['c']]}]
        before = copy.deepcopy(replies)
        result = a.llm_reply(self.w, 2, replies)
        self.assertEqual(result['status'], 'invalid_allocation')
        self.assertEqual(result['attempts'], ['invalid', 'invalid'])
        self.assertIsNone(result['groups'])
        self.assertIs(result['fallback'], False)
        self.assertEqual(replies, before)

    def test_extra_reply_unread_and_invalid_transcript_lengths(self):
        class Unreadable(dict):
            def __iter__(self):
                raise AssertionError('reply must not be inspected')
            def __getitem__(self, key):
                raise AssertionError('reply must not be inspected')
        extra = Unreadable()
        for second in (extra, self.valid, None):
            result = a.llm_reply(self.w, 2, [self.valid, second])
            self.assertEqual(result['status'], 'invalid_allocation')
            self.assertEqual(result['attempts'], ['valid'])
            self.assertIsNone(result['groups'])
            self.assertEqual(result['error'], 'extra correction after valid response')
            self.assertIs(result['fallback'], False)
        for replies in ([], [extra, extra, extra]):
            with self.assertRaisesRegex(Invalid, 'at most initial reply plus one structural correction'):
                a.llm_reply(self.w, 2, replies)

    def test_internal_tuple_allocations_unchanged(self):
        value = (('d', 'c'), ('b', 'a'))
        expected = (('a', 'b'), ('c', 'd'))
        self.assertEqual(groups(self.w, 2, value), expected)
        alloc = Allocation(self.w.key, 2, value, 'fixed', 'internal', 0)
        self.assertEqual(alloc.groups, expected)
        self.assertIsInstance(alloc.groups, tuple)
        self.assertTrue(all(isinstance(g, tuple) for g in alloc.groups))
        self.assertEqual(value, (('d', 'c'), ('b', 'a')))


if __name__ == '__main__':
    unittest.main()
