import json,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import composite_derivation_interface as i,composite_scaling as s
from bc_phase2.model import digest,Invalid

class CommonInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank=json.loads((Path(__file__).resolve().parents[1]/'configs/phase2/composite_scaling_bank_v2.json').read_text())
        cls.components=s.reviewed(cls.bank)
    def test_freeze_preserves_historical_bank_and_all_sources(self):
        before=deepcopy(self.bank);v=i.freeze(self.bank)
        self.assertEqual(self.bank,before);self.assertFalse(v['execution_allowed'])
        self.assertEqual(v['methods'],['NEUTRAL','JOINT'])
        self.assertEqual(len(v['transport_tasks']),14);self.assertEqual(len(v['profile_coverage']),16)
        self.assertEqual({t['source_id'] for t in v['transport_tasks']},{c['source_id'] for c in self.components})
    def test_only_task_field_order_changes(self):
        for c in self.components:
            for t in c['tasks']:
                new=i.task(t)
                for k in t:
                    if k!='fields':self.assertEqual(t[k],new[k])
                self.assertEqual(set(t['fields']),set(new['fields']))
                self.assertIn(new['fields'][0],('derivation','justification'))
    def test_all_modes_need_distinct_fresh_prices(self):
        for e in i.coverage(self.components):
            self.assertNotEqual(e['key'],e['historical_key'])
            for kind in ('historical_profile','evaluation','diagnostic'):
                with self.assertRaises(Invalid):i.check_profile({'kind':kind},e)
            r=dict(kind='new_profile',key=e['key'],descriptor=e['descriptor'],tokens=20,invocation='synthetic',ledger_digest='synthetic')
            i.check_profile(r,e);r['key']=e['historical_key']
            with self.assertRaises(Invalid):i.check_profile(r,e)
    def test_engine_request_overlay_keeps_inputs_without_method_labels(self):
        p=dict(instruction='synthetic',responsibility='synthetic',source={'id':'synthetic'},parent_artifacts={'t0':{'value':'synthetic'}},required_string_fields=['bound','derivation'])
        r=dict(payload=p,payload_digest=digest(p))
        with patch.object(i.runtime.Engine,'make_request',return_value=r):
            # No journal/transport/model is needed to inspect this request path.
            e=object.__new__(i.Engine);new=e.make_request({},{});self.assertEqual(new['payload']['parent_artifacts'],p['parent_artifacts'])
            self.assertEqual(new['payload']['required_string_fields'],['derivation','bound'])
            self.assertEqual(set(new['payload']),set(p))
