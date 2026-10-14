"""Synthetic CPU controls; these do not claim native XGrammar validation."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace

from tests.test_action_constraints import Matrix
from beyond_consensus.models.constrained import ReasoningGate
from reporecourse.engine import ModelWorker
from reporecourse.resources import Resources
from reporecourse.common import Rejected

spec = importlib.util.spec_from_file_location('decoder_boundary_audit', Path(__file__).resolve().parents[1] / 'scripts/probe_decoder_boundary.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class BoundaryAuditTests(unittest.TestCase):
    def test_strict_parser_rejects_nested_and_escaped_duplicate_keys(self):
        for name, text in audit.cases().items():
            with self.subTest(name=name):
                self.assertEqual(audit.parser_accepts(text), name == 'valid_mapping')

    def test_gate_delegates_eos_mask_after_close_without_consuming_delimiter(self):
        seen = []
        # HF processor starts at its first invocation; subsequent calls consume
        # one generated token. No prompt/reasoning token enters the matcher.
        def inner(ids, scores):
            if seen:
                seen.append(ids.row[-1])
            else:
                seen.append('initialized')
            return 'eos-masked' if len(seen) < 3 else 'eos-allowed'
        gate = ReasoningGate(inner, 2, 9)
        self.assertEqual(gate(Matrix([9, 1]), 'raw'), 'raw')
        self.assertEqual(gate(Matrix([9, 1, 8]), 'raw'), 'raw')
        self.assertEqual(gate(Matrix([9, 1, 8, 9]), 'raw'), 'eos-masked')
        self.assertEqual(gate(Matrix([9, 1, 8, 9, 4]), 'raw'), 'eos-masked')
        self.assertEqual(gate(Matrix([9, 1, 8, 9, 4, 5]), 'raw'), 'eos-allowed')
        self.assertEqual(seen, ['initialized', 4, 5])

    def test_eos_and_incomplete_validation_do_not_override_strict_parser(self):
        for name in ('duplicate_nested', 'escaped_duplicate_nested', 'incomplete_action'):
            text = audit.cases()[name]
            class Backend:
                def count_input(self, messages):return 10
                def generate(self, *args):
                    return SimpleNamespace(text=text, output_tokens=20, reasoning_tokens=2,
                        device_seconds=0, diagnostics={'finish_reason':'eos', 'constraint_complete':False})
            resources = Resources(10000, 1200)
            with self.subTest(name=name), self.assertRaises(Rejected) as caught:
                ModelWorker(Backend()).next_action({}, {}, {}, [], resources, 0, lambda: None)
            diagnostic = caught.exception.response_diagnostic
            self.assertEqual(diagnostic['parse_failure'], 'json_syntax' if name == 'incomplete_action' else 'duplicate_object_key')
            self.assertEqual(diagnostic['finish_reason'], 'eos')
            self.assertFalse(diagnostic['constraint_complete'])
            self.assertEqual(resources.actual_tokens, 30)
            self.assertFalse(resources.reservations)
