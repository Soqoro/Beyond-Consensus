"""No external calls: narrow release, ledger and scheduler-double controls."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from bc_phase2 import d1_natural_launch as l, d1_natural_binding as b, d1_natural_screen as n
from bc_phase2.model import Invalid,digest
from test_d1_natural_binding import fixtures
from test_phase2_planner_qwen import Tokenizer,Model,Torch

ROOT=Path(__file__).resolve().parents[1]


def release(output=None):
    v,o,c,p=fixtures()
    if output:c['output_root']=str(output)
    m=b.bind(v,o,c,p)
    a=b.review(m)['approval_template']
    a.update(decision='approved',reviewer='synthetic-test',reviewed_at='synthetic-test',
             statement_transmission_authorized=True,GPU_spending_authorized=True)
    return l.approve(m,a)


class Launch(unittest.TestCase):
    def test_approval_binding_and_no_legacy_activation(self):
        v=release();self.assertEqual(l.validate_release(v)['source_ids'],list(n.SMOKE))
        for key in ('GPU_spending_authorized','statement_transmission_authorized'):
            changed=copy.deepcopy(v);changed['approval'][key]=False
            with self.assertRaises(Invalid):l.validate_release(changed)
        changed=copy.deepcopy(v);changed['manifest']['scope']['resources']['maximum_calls']=4
        with self.assertRaises(Invalid):l.validate_release(changed)
        with self.assertRaises(Invalid):l.open_transport({})
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(Invalid):l.run_allocated(ROOT,Path('/synthetic'))

    def test_allocated_resources_cannot_expand(self):
        record='Partition=NA100q NumNodes=1 NumCPUs=4 TimeLimit=01:00:00 ReqTRES=cpu=4,mem=128G,gres/gpu=1'
        l.check_allocation_record(record)
        for old,new in [('NumCPUs=4','NumCPUs=8'),('01:00:00','02:00:00'),('128G','256G'),('gpu=1','gpu=2')]:
            with self.assertRaises(Invalid):l.check_allocation_record(record.replace(old,new))

    def test_single_gpu_one_hour_no_requeue_argv(self):
        v=release();c=l.cluster.ClusterConfig(**v['manifest']['scope']['cluster'])
        a=l.arguments(c,Path('/snapshot'),Path('/output'))
        for token in ('--gres=gpu:1','--array=0-0%1','--time=01:00:00','--mem=128G','--cpus-per-task=4','--no-requeue'):
            self.assertIn(token,a)
        self.assertEqual(a[-4],'/snapshot/experiments/run_d1_natural.sbatch')

    def test_submission_exception_preserves_reservation_no_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);v=release(root/'outputs');reg=root/'registry';reg.mkdir()
            def command(argv):
                if '--test-only' in argv:return 'ok'
                raise RuntimeError('synthetic lost sbatch response')
            with patch.dict(os.environ,{},clear=True),patch.object(l.local,'statement_records',return_value=[]), \
                 patch.object(l.cluster,'registry_root',return_value=reg),patch.object(l.cluster,'guard'), \
                 patch.object(l.cluster,'validate_site'),patch.object(l,'source_revision',return_value='synthetic'), \
                 patch.object(l,'create_snapshot',return_value=ROOT),patch.object(l.cluster,'command',side_effect=command):
                with self.assertRaises(RuntimeError):l.submit(ROOT,v,dry_run=False)
                state=json.loads((reg/'registry.json').read_text())
                self.assertIsNotNone(state['uncertain_submission'])
                self.assertEqual(len(state['d1_natural_scopes']),1)
                with self.assertRaises(Invalid):l.submit(ROOT,v,dry_run=False)

    def test_bound_session_uses_one_shot_accounting_and_continues_invalid(self):
        records=[{'id':f'mock:{i}','problem':'Synthetic relation'} for i in range(3)]
        transport=l.CheckedTransport(Tokenizer(),Model(),Torch())
        scope={'source_ids':[r['id'] for r in records], 'source_package':{'path':'/synthetic/statements'},'verified_requests':[]}
        for r in records:
            req=n.request(r);view=n.render_request(transport.tokenizer,req,transport.template['template_hash'])
            scope['verified_requests'].append({'source_id':r['id'],**{k:view[k] for k in ('payload_digest','rendered_ids_digest','input_tokens')}})
        transport.scope=scope
        hashes={r['id']:hashlib.sha256(r['problem'].encode()).hexdigest() for r in records}
        def generate(rendered):
            return {'input_tokens':rendered['input_tokens'],'output_tokens':2,'finish_reason':'eos','final_text':'invalid'}
        with tempfile.TemporaryDirectory() as d,patch.object(l.local,'STATEMENT_HASHES',hashes), \
             patch.object(l.local,'statement_records',return_value=records),patch.object(transport,'generate',side_effect=generate):
            session=l.Session(Path(d)/'requests',scope,records,transport,time.time())
            result=l.drive(session,scope['source_ids'])
            self.assertFalse(result['halted']);self.assertEqual(len(result['sources']),3)
            self.assertTrue(all(r['status']=='invalid_response' for r in result['sources']))
            totals=result['ledger']['totals']
            self.assertEqual(totals['model_calls_observed'],3);self.assertEqual(totals['reserved_tokens'],0)
            self.assertNotIn('simulated_actual_tokens',totals)
            with self.assertRaises(Invalid):session.advance(records[0]['id'])

    def test_gpu_count_and_vram_rejected_before_weights(self):
        from types import SimpleNamespace
        import sys
        from beyond_consensus.models import transformers_backend as backend
        from unittest.mock import Mock
        for count,vram in ((2,85000000000),(1,40000000000)):
            weights=Mock()
            torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:count,
                    get_device_properties=lambda _:SimpleNamespace(total_memory=vram)))
            transformers=SimpleNamespace(AutoTokenizer=Mock(),Qwen3_5ForConditionalGeneration=weights)
            with patch.dict(sys.modules,{'torch':torch,'transformers':transformers}), \
                 patch.object(backend,'require_allocation'),patch.object(l,'verify_local_inventory',return_value=Path('/synthetic')):
                with self.assertRaises(Invalid):l.open_transport(release())
            weights.from_pretrained.assert_not_called()

    def test_drive_uncertain_stops_and_retains_unrun(self):
        class Fake:
            calls=0
            def advance(self,s):
                self.calls+=1
                return {'state':'uncertain','actual_tokens':None}
            def snapshot(self):return {'reserved_tokens':3172}
        s=Fake();r=l.drive(s,['mock:0','mock:1','mock:2'])
        self.assertTrue(r['halted']);self.assertEqual(s.calls,1)
        self.assertEqual([x['status'] for x in r['sources']],['uncertain','unrun','unrun'])
        self.assertEqual(r['ledger']['reserved_tokens'],3172)

if __name__=='__main__':unittest.main()
