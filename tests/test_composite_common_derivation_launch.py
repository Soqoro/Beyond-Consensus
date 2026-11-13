"""Focused fake-transport recipe controls, no solver or model execution."""
from copy import deepcopy
import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import composite_common_derivation_launch as l, composite_scaling_launch as old
from bc_phase2 import composite_scaling_runtime as runtime, composite_scaling as spec, composite_math as worker
from bc_phase2.model import digest,Invalid
from test_composite_scaling import Fake,alternate,retain,BANK

class CommonWave(unittest.TestCase):
    def setUp(self):
        self.parent=old.make_wave(json.loads(BANK.read_text()),{})
        self.wave=l.make_wave(self.parent)
    def test_frozen_baseline_and_workload_unchanged(self):
        before=deepcopy(self.parent);w=l.make_wave(self.parent)
        self.assertEqual(before,self.parent)
        self.assertEqual(w['limits']['maximum_calls'],192)
        self.assertEqual(w['limits']['token_cap'],3145728)
        self.assertEqual(w['reused_profiles'],{})
        self.assertEqual(sum(s['calls'] for s in w['profile_schedule']),16)
        for a,b in zip(self.parent['bundles'],w['bundles']):
            for k in ('neutral','components','sources','call_bounds','work_id'):self.assertEqual(a[k],b[k])
            self.assertNotEqual(a['preprice_id'],b['preprice_id'])
    def test_prices_translate_without_changing_choices(self):
        b=self.wave['bundles'][2];cov=l.coverage(b['components']);prices={e['key']:i+1 for i,e in enumerate(cov)}
        d=l.domain(b['components'],b['n'],prices)
        expected=spec.domain(b['components'],b['n'],{e['historical_key']:prices[e['key']] for e in cov})
        self.assertEqual(d,expected)
        with self.assertRaises(KeyError):l.domain(b['components'],b['n'],{e['historical_key']:1 for e in cov})
    def run_mock(self,fault=None,solver=alternate):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);out=Path(tmp.name)
        w=deepcopy(self.wave);w['bundles']=w['bundles'][:1];b=w['bundles'][0]
        w['components']=b['components'];w['profile_coverage']=l.coverage(b['components'])
        w['profile_schedule']=runtime.schedule_profiles(b['components'],{})
        fake=Fake(fault);j=worker.Journal(out/'journal',fake,'synthetic',lambda:None,condition=l.KEY,limits=w['limits'])
        result=runtime.run_wave(j,{c['source_id']:'synthetic source' for c in w['components']},out,w,solver,interface=l)
        return result,j,fake,out
    def test_fresh_profiles_two_methods_all_owners_and_common_wire(self):
        result,j,fake,out=self.run_mock();c=result['conditions'][0]
        self.assertEqual(c['status'],'completed_comparison');self.assertFalse(c['shared_observations'])
        receipts=json.loads((out/'prices.frozen.json').read_text())['receipts']
        self.assertEqual(len(receipts),3)
        for e in l.coverage(self.wave['bundles'][0]['components']):l.check_profile(receipts[e['key']],e)
        profile_ids={r['invocation'] for r in receipts.values()}
        for method in ('NEUTRAL','JOINT'):
            m=c['methods'][method];self.assertEqual(len(m['repairs']),2)
            self.assertTrue(profile_ids.isdisjoint(m['clean']['invocations']))
        for p in fake.calls:
            self.assertIn(p['required_string_fields'][0],('derivation','justification'))
            self.assertNotIn('method',p);self.assertNotIn('prices',p)
        self.assertEqual(j.snapshot()['totals']['calls'],len(fake.calls))
    def test_invalid_profile_blocks_dependents_not_retried(self):
        result,j,fake,out=self.run_mock(lambda p,n:{'final_text':'not JSON'} if n==1 else None)
        self.assertEqual(result['conditions'][0]['status'],'blocked_profile_coverage')
        self.assertTrue(all(a['slot'].startswith('profile/') for a in j.snapshot()['attempts']))
    def test_pending_approval_cannot_dispatch(self):
        with patch.object(l,'validate_manifest',return_value={'deployment':{'packages':l.base.EXPECTED_PACKAGES,'solver_importable':True}}):
            a=dict(schema=l.KEY+'-approval',scope_digest='x',decision='pending',reviewer='test',reviewed_at='now',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
            with self.assertRaises(Invalid):l.approve({'blockers':[],'scope_digest':'x'},a)
    def test_exact_allocation(self):
        record='Partition=HPCAIq NodeList=node14 NumNodes=1 NumCPUs=4 TimeLimit=04:00:00 ReqTRES=cpu=4,gres/gpu=1,mem=128G'
        l.check_scoped_allocation(record,{'cluster':{'partition':'HPCAIq'}})
        with self.assertRaises(Invalid):l.check_scoped_allocation(record.replace('gpu=1','gpu=2'),{'cluster':{'partition':'HPCAIq'}})
