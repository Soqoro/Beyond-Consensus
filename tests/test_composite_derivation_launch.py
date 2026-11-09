import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import composite_derivation_launch as l,composite_derivation_diagnostic as d
from bc_phase2.model import digest,Invalid
from bc_phase2.composite_math import Halt

class LaunchTests(unittest.TestCase):
    def export(self):
        groups=[]
        for sid,tid in d.TARGETS:
            p=dict(source={'id':sid,'problem':'synthetic'},task_id=tid,required_string_fields=['final_answer','justification'])
            groups.append(dict(source_id=sid,task_id=tid,request={'payload':p,'payload_digest':digest(p)}))
        return dict(groups=groups)
    def test_known_invalid_response_continues_without_retry(self):
        class Journal:
            def __init__(self):self.calls=0
            def invoke(self,request,slot,event):
                self.calls+=1
                return dict(id=str(self.calls),actual_tokens=5,observation=dict(finish_reason='length_limit' if self.calls==1 else 'eos',boundary_error=None,final_text='{"justification":"synthetic","final_answer":"x"}'))
            def snapshot(self):return {'totals':{'calls':self.calls}}
        with tempfile.TemporaryDirectory() as t:
            j=Journal();r=l.execute(j,self.export(),t)
            self.assertEqual(j.calls,6);self.assertEqual(r['rows'][0]['status'],'invalid_response')
            self.assertEqual(r['rows'][-1]['status'],'structurally_valid')
    def test_uncertain_dispatch_stops_remaining_tasks(self):
        class Journal:
            def invoke(self,*args):raise Halt('uncertain')
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(Halt):l.execute(Journal(),self.export(),t)
            self.assertEqual(list(Path(t).iterdir()),[])
    def test_changed_rendering_blocks_before_generate(self):
        class Transport:
            binding={}
            def render(self,r):return dict(input_tokens=9,rendered_ids_digest='changed')
            def generate(self,r):raise AssertionError('not called')
        t=l.MeasuredTransport(Transport(),[dict(payload_digest='p',input_tokens=9,rendered_ids_digest='expected')])
        with self.assertRaises(Invalid):t.render({'payload_digest':'p'})
    def test_exact_allocation_partition_and_time(self):
        rec='Partition=HPCAIq NumNodes=1 NumCPUs=4 TimeLimit=01:00:00 ReqTRES=cpu=4,gres/gpu=1,mem=128G'
        l.check_scoped_allocation(rec,{'cluster':{'partition':'HPCAIq'}})
        with self.assertRaises(Invalid):l.check_scoped_allocation(rec,{'cluster':{'partition':'NA100q'}})
        with self.assertRaises(Invalid):l.check_scoped_allocation(rec.replace('01:00:00','04:00:00'),{'cluster':{'partition':'HPCAIq'}})
    def test_pending_and_wrong_scope_approval_rejected(self):
        a=dict(schema='composite-derivation-approval-v1',scope_digest='s',decision='pending',reviewer='r',reviewed_at='date',source_worker_transmission=True,contract_accepted=True,gpu_recipe_authorized=True)
        with patch.object(l,'validate_manifest',return_value={}):
            with self.assertRaises(Invalid):l.approve({'scope_digest':'s','blockers':[]},a)
            a['decision']='approved';a['scope_digest']='other'
            with self.assertRaises(Invalid):l.approve({'scope_digest':'s','blockers':[]},a)
    def test_launcher_reuses_shared_registry_entrypoint(self):
        with patch.object(l.base,'submit',return_value={'dry_run':True}) as call:
            self.assertEqual(l.submit('root',{},dry_run=True),{'dry_run':True})
            self.assertIs(call.call_args.kwargs['protocol'],l)
    def test_release_changes_rejected(self):
        with patch.object(l,'approve',return_value={'release_digest':'expected'}):
            with self.assertRaises(Invalid):l.validate_release({'manifest':{},'approval':{},'release_digest':'changed'})
