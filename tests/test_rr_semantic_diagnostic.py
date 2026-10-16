"""Counterexample and separation controls for the unsubmitted design packet."""
import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from beyond_consensus.experiments.rr_semantic_diagnostic import fixtures, reference, controls, packet


class SemanticDesign(unittest.TestCase):
    def test_duplicate_payment_changes_money_not_order_count(self):
        data = fixtures()
        before = reference(data)
        data['payments'].append(copy.deepcopy(data['payments'][0]))
        after = reference(data)
        self.assertEqual(after[0][1], before[0][1])
        self.assertEqual(after[0][2], before[0][2]+1)
        self.assertEqual(after[0][3], before[0][3]+7)
        self.assertEqual(after[0][4:], before[0][4:])

    def test_no_orders_and_zero_payment(self):
        rows = reference(fixtures())
        self.assertEqual(rows[2], [30, 0, 0, 0, 0, 0])
        self.assertEqual(rows[1][3:], [0, 1, 0])

    def test_order_and_customer_permutation(self):
        data = fixtures()
        before = reference(data)
        for value in data.values():
            value.reverse()
        self.assertEqual(sorted(reference(data)), sorted(before))

    def test_packet_stability_and_no_execution_authority(self):
        first, second = packet(), packet()
        self.assertEqual(first['design_id'], second['design_id'])
        self.assertFalse(first['task_execution_allowed'])
        self.assertTrue(first['blockers'])
        self.assertEqual(first['intended_model_calls'], 3)
        for case in first['cases']:
            self.assertNotIn('expected', case)
            self.assertNotIn('controls', case)
        self.assertTrue(all(controls()['checks'].values()))
        first['cases'][0]['tables']['customers'].clear()
        self.assertEqual(len(packet()['cases'][0]['tables']['customers']), 3)


class ProductionControls(unittest.TestCase):
    def test_public_tasks_have_no_reference_program_or_oracle(self):
        from beyond_consensus.experiments.rr_semantic_diagnostic import task, environment
        import json
        for case in ('order_grain', 'unpaid_boundary', 'mapping_keys'):
            public = task(case)
            self.assertNotIn('expected', public)
            self.assertNotIn('witnesses', public)
            with self.subTest(case=case):
                env = environment(case)
                try:
                    observation = json.dumps(env.observation('w0'))
                    self.assertNotIn('COUNT(DISTINCT', observation)
                    self.assertNotIn('semantic_correct', observation)
                    self.assertEqual(env.workers, tuple('w'+str(i) for i in range(7)))
                finally:
                    env.close()

    def test_oracle_rejects_execution_error_and_wrong_keys(self):
        from beyond_consensus.experiments.rr_semantic_diagnostic import semantic_check
        self.assertFalse(semantic_check('order_grain', {'status': 'semantic_error'}))
        from beyond_consensus.experiments.rr_semantic_diagnostic import task, reference, fixtures
        self.assertFalse(semantic_check('order_grain', {'status': 'ok', 'outputs': [{
            'columns': task('order_grain')['required_outputs'][0]['columns'],
            'rows': [[float(v) for v in row[:4]] for row in reference(fixtures())]}]}))
        self.assertFalse(semantic_check('mapping_keys', {'status': 'ok', 'output':
            {'errors': ['alpha'], 'errors_bytes': {'X': 4}}}))
        self.assertTrue(semantic_check('mapping_keys', {'status': 'ok', 'output':
            {'labels': ['alpha'], 'size_bytes': {'X': 4}}}))

    def test_prerequisite_failure_is_recorded_not_passed(self):
        from unittest.mock import patch
        from reporecourse.common import Rejected
        from beyond_consensus.experiments.rr_semantic_diagnostic import production_controls
        with patch('beyond_consensus.experiments.rr_semantic_diagnostic.inspect_action',
                   side_effect=Rejected('blocked_prerequisite')):
            report = production_controls()
        self.assertEqual(report['status'], 'blocked_prerequisite')
        self.assertEqual(len(report['cases']), 7)
        self.assertFalse(report['sql_executed'])
        self.assertFalse(report['task_execution_allowed'])

    def test_actual_production_paths(self):
        from tests.test_reporecourse import optional
        if not optional():
            self.skipTest('pinned SQLGlot/jsonschema/referencing required')
        from beyond_consensus.experiments.rr_semantic_diagnostic import production_controls
        report = production_controls()
        self.assertEqual(report['status'], 'passed', report)
        self.assertTrue(report['sql_executed'])
        self.assertEqual(sum(r['semantic_correct'] for r in report['cases']), 3)
        self.assertTrue(all(r['public_monitor_passed'] for r in report['cases']))
        for row in report['cases']:
            self.assertGreater(row['resources']['cpu_cap_debit'], 0)
            self.assertEqual(row['resources']['uncertain_cpu'], 0)


if __name__ == '__main__':
    unittest.main()
