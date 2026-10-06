"""Capacity arithmetic on explicitly fabricated test packets, not model results."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments.rr_planner_capacity import review
from beyond_consensus.util import BCError, digest
from tests import test_rr_open_footprint as footprint_controls


def packet():
    p,_ = footprint_controls.FootprintTests().packet()
    for r, action, inp in zip(p['cases'], (188,628,2124,11,69), (749,1189,2685,968,3859)):
        m=r['measurement']
        m.update(action_tokens=action,action_plus_stop_tokens=action+1,input_tokens=inp,
                 status='passed' if action+1<=2048 else 'output_representation_exceeds_cap',
                 dispatch_allowed=action+1<=2048)
    p['status']='failed_cpu_cases';seal(p)
    return p


def seal(p): p['packet_id']=digest({k:v for k,v in p.items() if k!='packet_id'})


class CapacityTests(unittest.TestCase):
    def test_measured_arithmetic_keeps_qualifications_and_selection_false(self):
        p=packet();original=copy.deepcopy(p);r=review(p)
        self.assertEqual(p,original)
        self.assertEqual([c['cases'][2]['action_headroom_tokens'] for c in r['comparisons']],[-77,947,1971])
        self.assertEqual([c['maximum_planner_input_tokens'] for c in r['comparisons']],[14336,13312,12288])
        self.assertEqual(r['worker_output_cap_unchanged'],2048)
        self.assertIsNone(r['measured_reasoning_tokens']);self.assertIsNone(r['selected_planner_output_cap'])
        self.assertFalse(r['task_execution_allowed']);self.assertFalse(r['GPU_submission_allowed'])
        self.assertFalse(r['comparisons'][1]['cases'][2]['scenarios'][2]['arithmetic_fit'])
        self.assertTrue(r['comparisons'][2]['cases'][2]['scenarios'][2]['arithmetic_fit'])
        self.assertFalse(r['comparisons'][2]['cases'][2]['scenarios'][3]['arithmetic_fit'])

    def test_context_reservation_is_independent_of_action_fit(self):
        p=packet();p['cases'][0]['measurement']['input_tokens']=14000;seal(p)
        r=review(p,[4096],[0])
        c=r['comparisons'][0]['cases'][0]
        self.assertGreater(c['action_headroom_tokens'],0)
        self.assertFalse(c['observed_prompt_fits_reservation'])
        self.assertFalse(c['scenarios'][0]['arithmetic_fit'])

    def test_malformed_unmeasured_or_changed_records_rejected(self):
        mutations=[lambda p:p.update(packet_id='changed'),
            lambda p:p['cases'].pop(),
            lambda p:p['cases'][0]['measurement'].update(action_tokens=None),
            lambda p:p['cases'][2]['measurement'].update(dispatch_allowed=True),
            lambda p:p.update(status='passed_cpu_cases'),
            lambda p:p['measurement_runtime']['qualification_keys'].update(plan='wrong')]
        for i,fn in enumerate(mutations):
            p=packet();fn(p)
            if i:seal(p)
            with self.subTest(i=i),self.assertRaises((BCError,KeyError)):review(p)
        for caps,reserves in [([], [0]),([True],[0]),([16384],[0]),([2048,2048],[0]),([2048],[-1])]:
            with self.assertRaises(BCError):review(packet(),caps,reserves)

    def test_cli_stdlib_no_overwrite_or_input_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'packet.json';output=Path(tmp)/'review.json'
            source.write_text(json.dumps(packet()));before=source.read_bytes()
            cmd=[sys.executable,'-I','-S','scripts/review_rr_planner_capacity.py','--packet',str(source),'--output',str(output)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(source.read_bytes(),before)
            saved=output.read_bytes()
            self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
            self.assertEqual(output.read_bytes(),saved)
            report=json.loads(saved)
            self.assertFalse(report['tokenizer_executed'])
            self.assertEqual(report['report_id'],digest({k:v for k,v in report.items() if k!='report_id'}))
