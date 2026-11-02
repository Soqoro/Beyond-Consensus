"""Synthetic durability/adapter checks; no real generation or tokenizer use."""
import copy
import fcntl
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.model import Invalid
from bc_phase2.planner_first import make_request
from bc_phase2.planner_ledger import MockPlannerSession, MockReply, OUTPUT

UNSUPPORTED = json.dumps({'schema_version': '1.0', 'status': 'unsupported',
    'requested_agents': 4, 'reason': 'Synthetic fixture has insufficient substantive operations.'})


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'session'
        self.requests = [make_request({'id': f'synthetic:{i}', 'problem': 'Synthetic statement.',
            'answer': 'SECRET', 'solution': 'SECRET'}, 'synthetic-only') for i in range(3)]
        for name in ('socket.socket.connect', 'socket.create_connection', 'subprocess.Popen',
                     'bc_phase2.runtime.MockWorker.invoke', 'bc_phase2.allocation.solve'):
            guard = patch(name, side_effect=AssertionError('offline only'))
            guard.start(); self.addCleanup(guard.stop)
        self.session = MockPlannerSession(self.root, self.requests)

    def run_reply(self, text=UNSUPPORTED, count=20, source='synthetic:0', ids=(1, 2, 3)):
        return self.session.advance(source, ids, MockReply(text, count))

    def test_completed_usage_and_restart_terminal(self):
        row = self.run_reply()
        self.assertEqual(row['review']['mechanical_status'], 'UNSUPPORTED')
        self.assertEqual(row['totals']['simulated_actual_tokens'], 23)
        self.assertEqual(row['totals']['simulated_reserved_tokens'], 0)
        resumed = MockPlannerSession(self.root, self.requests)
        with self.assertRaises(Invalid): resumed.advance('synthetic:0', [1], object())
        self.assertEqual(resumed.snapshot()['totals']['simulated_attempts'], 1)

    def test_only_invalid_allows_one_correction(self):
        self.run_reply('{')
        row = self.run_reply()
        correction = row['outbound_payload']['planning_instructions']['structural_correction']
        self.assertEqual(correction['prior_response'], '{')
        self.assertEqual(row['attempt'], 1)
        self.assertEqual(row['totals']['simulated_actual_tokens'], 46)
        with self.assertRaises(Invalid): self.run_reply()

    def test_two_invalid_not_retried(self):
        self.run_reply('{'); self.run_reply('{')
        with self.assertRaises(Invalid): self.run_reply()

    def test_six_calls_across_exact_three_sources(self):
        for i in range(3):
            for unused in range(2): self.run_reply('{', source=f'synthetic:{i}')
        self.assertEqual(self.session.snapshot()['totals']['simulated_attempts'], 6)
        with self.assertRaises(Invalid): self.run_reply(source='synthetic:2')
        with self.assertRaises(Invalid): self.run_reply(source='synthetic:3')

    def test_unknown_usage_preserves_reservation(self):
        row = self.run_reply(count=None)
        self.assertEqual(row['state'], 'uncertain')
        self.assertEqual(row['totals']['simulated_reserved_tokens'], 3 + OUTPUT)
        self.assertEqual(row['raw'], UNSUPPORTED)
        resumed = MockPlannerSession(self.root, self.requests)
        with self.assertRaises(Invalid): resumed.advance('synthetic:1', [1], MockReply(UNSUPPORTED, 10))

    def test_interruption_before_reconcile_never_replays(self):
        original = self.session._save
        def interrupt(state):
            if state['attempts'][-1]['state'] == 'completed': raise KeyboardInterrupt()
            return original(state)
        with patch.object(self.session, '_save', side_effect=interrupt):
            with self.assertRaises(KeyboardInterrupt): self.run_reply()
        resumed = MockPlannerSession(self.root, self.requests)
        self.assertEqual(resumed.snapshot()['attempts'][0]['state'], 'reserved')
        with self.assertRaises(Invalid): resumed.advance('synthetic:0', [1], MockReply(UNSUPPORTED, 10))

    def test_failed_reservation_write_has_no_attempt(self):
        with patch('bc_phase2.planner_ledger.os.replace', side_effect=OSError('write failure')):
            with self.assertRaises(OSError): self.run_reply()
        self.assertEqual(self.session.snapshot()['attempts'], [])
        self.assertEqual(list(self.root.glob('.ledger-*')), [])

    def test_actual_overrun_saved_and_halts(self):
        row = self.run_reply(count=OUTPUT+1)
        self.assertEqual(row['state'], 'usage_violation')
        self.assertEqual(row['actual_tokens'], OUTPUT+4)
        with self.assertRaises(Invalid): self.run_reply(source='synthetic:1')

    def test_context_overflow_not_truncated_or_charged(self):
        for ids in ([1]*10241, [], [True], [-1], '1'):
            with self.subTest(ids=str(ids)[:20]), self.assertRaises(Invalid): self.run_reply(ids=ids)
        self.assertEqual(self.session.snapshot()['attempts'], [])
        self.assertEqual(self.run_reply(ids=[1]*10240)['input_tokens'], 10240)

    def test_correction_overflow_does_not_erase_initial(self):
        self.run_reply('{')
        with self.assertRaises(Invalid): self.run_reply(ids=[1]*10241)
        self.assertEqual(self.session.snapshot()['totals']['simulated_attempts'], 1)

    def test_empty_nontext_oversize_terminal(self):
        for i, text in enumerate((None, object(), ' '*65537)):
            self.run_reply(text, source=f'synthetic:{i}')
            with self.assertRaises(Invalid): self.run_reply(source=f'synthetic:{i}')
        self.assertEqual(self.session.snapshot()['totals']['simulated_attempts'], 3)

    def test_tamper_and_binding_change_fail_closed(self):
        self.run_reply()
        state = json.loads(self.session.path.read_text()); state['state']['attempts'] = []
        self.session.path.write_text(json.dumps(state))
        with self.assertRaises(Invalid): MockPlannerSession(self.root, self.requests)
        with self.assertRaises(Invalid): self.session.snapshot()

    def test_changed_frozen_source_or_prompt(self):
        changed = copy.deepcopy(self.requests)
        changed[0] = make_request({'id': 'synthetic:0', 'problem': 'Different.'}, 'synthetic-only')
        with self.assertRaises(Invalid): MockPlannerSession(self.root, changed)
        changed = copy.deepcopy(self.requests); changed[0]['payload']['gold'] = 'SECRET'
        with self.assertRaises(Invalid): MockPlannerSession(self.root, changed)

    def test_blocked_input_and_real_backend_rejected(self):
        for backend in ('transformers', 'api', 'qwen'):
            with self.assertRaises(Invalid): MockPlannerSession(self.root, self.requests, backend=backend)
        blocked = make_request({'id': 'test/prealgebra/1930.json', 'problem': 'Diagram.'}, 'fixture')
        with self.assertRaises(Invalid): MockPlannerSession(self.root, [blocked] + self.requests[1:])
        with self.assertRaises(Invalid): self.session.advance('synthetic:0', [1], lambda: 'no')

    def test_secrets_absent_and_mock_evidence_explicit(self):
        self.run_reply()
        raw = self.session.path.read_text()
        self.assertNotIn('SECRET', raw)
        self.assertIn('offline_mock_not_real_usage', raw)
        self.assertFalse(self.session.snapshot()['model_executed'])
        self.assertIsNone(self.session.snapshot()['binding']['gpu_allocation'])

    def test_valid_plan_terminal_and_unmodified(self):
        plan = {'schema_version': '1.0', 'status': 'plan', 'requested_agents': 4,
            'tasks': [{'task_id': f't{i}', 'instruction': f'Derive claim {i}.',
                'expected_artifact': f'Justified claim {i}.',
                'parent_task_ids': [f't{i-1}'] if i else [],
                'immutable_inputs': ['problem_statement']} for i in range(4)],
            'ownership': [{'agent_id': f'agent_{i}', 'task_ids': [f't{i}']} for i in range(4)],
            'final_task_id': 't3', 'rationale': 'Sequential fixture.'}
        raw = json.dumps(plan)
        row = self.run_reply(raw)
        self.assertEqual(row['review']['mechanical_status'], 'PLAN_VALID')
        self.assertEqual(row['raw'], raw)
        self.assertIn('NO_OWNERSHIP_CHOICE', row['review']['flags'])
        with self.assertRaises(Invalid): self.run_reply('{')

    def test_invalid_usage_not_coerced(self):
        self.run_reply(count=True)
        self.assertEqual(self.session.snapshot()['attempts'][0]['state'], 'uncertain')
        self.assertEqual(self.session.snapshot()['totals']['simulated_actual_tokens'], 0)
        with self.assertRaises(Invalid): self.run_reply(source='synthetic:1')

    def test_single_writer_lock(self):
        with (self.root/'ledger.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                with self.assertRaises(BlockingIOError): self.run_reply()
            finally: fcntl.flock(lock, fcntl.LOCK_UN)
        self.assertEqual(self.session.snapshot()['attempts'], [])


if __name__ == '__main__': unittest.main()
