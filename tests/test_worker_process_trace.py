"""CPU-only launch observations, not model qualification."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from beyond_consensus.models import process_trace as t


class ProcessTrace(unittest.TestCase):
    def test_real_short_lived_child_records_caller_without_arguments(self):
        with t.process_launch_trace() as record:
            subprocess.run([sys.executable, '-c', 'pass', 'secret-argument'],
                           env=dict(os.environ, PRIVATE_TEST_VALUE='secret-environment'), check=True)
        launches = [r for r in record['events'] if r['event'] == 'subprocess.Popen']
        self.assertEqual(len(launches), 1)
        self.assertEqual(launches[0]['executable'], os.path.basename(sys.executable))
        self.assertTrue(any(f['function'] == 'test_real_short_lived_child_records_caller_without_arguments'
                            for f in launches[0]['callers']))
        text = json.dumps(record)
        self.assertNotIn('secret-argument', text)
        self.assertNotIn('secret-environment', text)
        self.assertNotIn('PRIVATE_TEST_VALUE', text)

    def test_thread_events_captured_and_hook_inactive_after_exit(self):
        with t.process_launch_trace() as record:
            thread = threading.Thread(target=lambda: sys.audit('os.system', 'secret-shell'))
            thread.start(); thread.join()
        sys.audit('os.system', 'outside')
        self.assertEqual(len(record['events']), 1)
        self.assertIsNone(record['events'][0]['executable'])
        self.assertNotIn('secret-shell', json.dumps(record))
        with t.process_launch_trace() as fresh:
            self.assertEqual(fresh['events'], [])

    def test_bounds_and_exception_cleanup(self):
        with self.assertRaisesRegex(ValueError, 'original'):
            with t.process_launch_trace() as record:
                for _ in range(70):sys.audit('os.fork')
                raise ValueError('original')
        self.assertEqual(len(record['events']), 64)
        self.assertTrue(record['truncated'])
        self.assertIsNone(t._ACTIVE)

    def test_failed_launch_is_an_attempt_not_success(self):
        with t.process_launch_trace() as record:
            with self.assertRaises(FileNotFoundError):
                subprocess.run(['/nonexistent-rr-launch-test/executable'], check=True)
        self.assertTrue(record['events'])
        self.assertIn('attempts', record['attribution'])

    def test_nested_scope_rejected_without_losing_outer_record(self):
        with t.process_launch_trace() as record:
            with self.assertRaises(RuntimeError):
                with t.process_launch_trace():pass
            sys.audit('os.fork')
        self.assertEqual(len(record['events']), 1)
