"""Bounded synthetic expanded-scope checks; never call a model or scheduler."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from bc_phase2 import math500_screen_launch as m
from bc_phase2.model import digest,Invalid
from test_d1_natural_binding import fixtures
from test_phase2_planner_qwen import Tokenizer,Model,Torch
ROOT=Path(__file__).resolve().parents[1]


def proposal_fixture():
    v,old,config,partition=fixtures()
    rows=[{'source_id':s,'statement_sha256':'a'*64,'payload_digest':'b'*64,'rendered_ids_digest':'c'*64,
           'input_tokens':1212+(i>=10),'reserved_tokens':4284+(i>=10),'output_cap':3072} for i,s in enumerate(m.SOURCES)]
    scope={'cohort_digest':m.COHORT,'source_ids':list(m.SOURCES),'blocked_retained':m.BLOCKED,
           'completed_no_rerun':list(m.screen.SMOKE),'verified_requests':rows,
           'model_binding':v,'snapshot_path':old['local_path'],'prompt_hash':digest(m.screen.PROMPT),
           'schema_hash':digest(m.screen.response_schema()),'thinking':False,'do_sample':False,
           'statement_file':'/synthetic/statements.json','statement_file_sha256':'d'*64,
           'attachment_review_digest':'e'*64,'retry_policy':'no_retry',
           'stop_policy':m.screen.disabled_manifest()['scope']['stop_policy'],
           'resources_proposed':{'maximum_calls':20,'calls_per_source':1,'output_cap':3072,'context_limit':16384,
             'aggregate_token_cap':85690,'campaign_wall_seconds':3600,'physical_gpus':1,'concurrency':1,
             'cpus':4,'host_memory_gb':128,'minimum_vram_bytes':80000000000,'partition':'NA100q','scheduler_config_bound':False}}
    p={'schema':'math500-screening-scope-proposal-v1','scope':scope,'scope_digest':digest(scope),'approval':None,'execution_allowed':False}
    return p,old,config,partition


def make_release(args):
    manifest=m.bind(*args);a=m.review(manifest)['approval_template']
    a.update(decision='approved',reviewer='synthetic',reviewed_at='synthetic',
             statement_transmission_authorized=True,GPU_spending_authorized=True)
    return m.approve(manifest,a)


def session_fixture(directory):
    records=[{'id':s,'problem':'Synthetic relation'} for s in m.SOURCES]
    t=m.pilot.CheckedTransport(Tokenizer(),Model(),Torch())
    scope={'source_ids':list(m.SOURCES),'resources':{'maximum_calls':20,'aggregate_token_cap':m.CAP},
           'source_package':{'path':'/synthetic','statement_hashes':{r['id']:hashlib.sha256(r['problem'].encode()).hexdigest() for r in records}},
           'verified_requests':[]}
    for r in records:
        view=m.screen.render_request(t.tokenizer,m.screen.request(r),t.template['template_hash'])
        scope['verified_requests'].append({'source_id':r['id'],**{k:view[k] for k in ('input_tokens','payload_digest','rendered_ids_digest')}})
    t.scope=scope
    return m.Session(Path(directory)/'requests',scope,records,t,time.time()),t


def observation(view,output=2,finish='eos'):
    return {'input_tokens':view['input_tokens'],'output_tokens':output,'finish_reason':finish,
            'final_text':'invalid','generated_ids':[1]*output if output is not None else None}


class Expanded(unittest.TestCase):
    def test_disabled_binding_and_distinct_approval(self):
        args=proposal_fixture()
        with patch.object(m,'PARENT',args[0]['scope_digest']):
            manifest=m.bind(*args);review=m.review(manifest)
            self.assertFalse(review['execution_allowed']);self.assertEqual(len(review['source_ids']),20)
            self.assertFalse(set(review['source_ids'])&set(m.screen.SMOKE));self.assertFalse(set(review['source_ids'])&set(m.BLOCKED))
            a=review['approval_template']
            with self.assertRaises(Invalid):m.approve(manifest,a)
            release=make_release(args);self.assertEqual(m.validate_release(release)['resources']['aggregate_token_cap'],85690)
            old=deepcopy(release['approval']);old['schema']='D1-natural-screen-v1-approval'
            with self.assertRaises(Invalid):m.approve(manifest,old)
            tampered=deepcopy(manifest);tampered['scope']['resources']['maximum_calls']=21
            with self.assertRaises(Invalid):m.validate_manifest(tampered)
        with self.assertRaises((Invalid,KeyError)):m.open_transport({})

    def test_parent_resource_or_source_changes_rejected(self):
        for kind in ('hash','calls','order','output','model','time'):
            args=list(proposal_fixture());parent=args[0]['scope_digest']
            if kind=='hash':args[0]['scope_digest']='x'
            if kind=='calls':args[0]['scope']['resources_proposed']['maximum_calls']=21
            if kind=='order':args[0]['scope']['source_ids'].reverse()
            if kind=='output':args[0]['scope']['resources_proposed']['output_cap']=4096
            if kind=='model':args[1]['revision']='wrong'
            if kind=='time':args[2]['time']='02:00:00'
            with patch.object(m,'PARENT',parent),self.assertRaises(Invalid):m.bind(*args)

    def test_twenty_invalid_calls_continue_and_twenty_first_rejected(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=[]):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=observation):result=m.pilot.drive(session,list(m.SOURCES))
            self.assertFalse(result['halted']);self.assertEqual(len(result['ledger']['attempts']),20)
            self.assertTrue(all(r['status']=='invalid_response' for r in result['sources']))
            self.assertEqual(result['ledger']['totals']['reserved_tokens'],0)
            self.assertEqual(result['ledger']['totals']['actual_tokens'],140)
            with self.assertRaises(Invalid):session.advance(m.SOURCES[0])

    def test_truncation_continues_but_uncertain_usage_stops(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=[]):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=lambda v:observation(v,3072,'length_limit')):
                first=session.advance(m.SOURCES[0])
            self.assertTrue(m.screen.reliable_terminal(first))
            with patch.object(t,'generate',side_effect=lambda v:observation(v,None)):
                second=session.advance(m.SOURCES[1])
            self.assertEqual(second['state'],'uncertain')
            self.assertEqual(session.snapshot()['totals']['reserved_tokens'],3077)
            with self.assertRaises(Invalid):session.advance(m.SOURCES[2])

    def test_crash_source_integrity_and_time_fail_closed(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=[]):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=RuntimeError('synthetic crash')):
                with self.assertRaises(RuntimeError):session.advance(m.SOURCES[0])
            self.assertEqual(session.snapshot()['totals']['reserved_tokens'],3077)
            with self.assertRaises(Invalid):session.advance(m.SOURCES[1])
        for kind in ('source','wall','render'):
            with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=[]):
                session,t=session_fixture(d)
                if kind=='wall':
                    state=session._read();state['started_at']=time.time()-3601;session._save(state)
                if kind=='render':t.scope['verified_requests'][0]['rendered_ids_digest']='changed'
                with patch.object(t,'generate') as generate:
                    if kind=='source':
                        with patch.object(m,'source_records',side_effect=Invalid('integrity')),self.assertRaises(Invalid):session.advance(m.SOURCES[0])
                    else:
                        with self.assertRaises(Invalid):session.advance(m.SOURCES[0])
                    generate.assert_not_called()

    def test_aggregate_limit_blocks_before_dispatch(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=[]):
            session,t=session_fixture(d)
            # Artificial reliable spend exercises admission without a real generation.
            state=session._read()
            state['attempts']=[{'state':'completed','source_id':m.SOURCES[i],'input_tokens':13312,
                'reservation_tokens':16384,'actual_tokens':16384,
                'observation':{'input_tokens':13312,'output_tokens':3072,'finish_reason':'eos'}} for i in range(6)]
            session._save(state)
            with patch.object(t,'generate') as generate,self.assertRaises(Invalid):session.advance(m.SOURCES[6])
            generate.assert_not_called()

    def test_submission_ambiguity_retained_even_after_rebinding(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);reg=root/'registry';reg.mkdir();args=list(proposal_fixture());args[2]['output_root']=str(root/'out')
            with patch.object(m,'PARENT',args[0]['scope_digest']):
                value=make_release(args)
                def command(argv):
                    if '--test-only' in argv:return 'ok'
                    raise RuntimeError('lost submit response')
                with patch.dict(os.environ,{},clear=True),patch.object(m,'source_records',return_value=[]), \
                     patch.object(m.cluster,'registry_root',return_value=reg),patch.object(m.cluster,'guard'), \
                     patch.object(m.cluster,'validate_site'),patch.object(m,'source_revision',return_value='synthetic'), \
                     patch.object(m,'create_snapshot',return_value=ROOT),patch.object(m.cluster,'command',side_effect=command):
                    with self.assertRaises(RuntimeError):m.submit(ROOT,value,dry_run=False)
                    state=json.loads((reg/'registry.json').read_text())
                    self.assertIsNotNone(state['uncertain_submission']);self.assertIn(m.COHORT,state['math500_screen_attempts'])
                    args[2]['output_root']=str(root/'other')
                    rebound=make_release(args)
                    with self.assertRaises(Invalid):m.submit(ROOT,rebound,dry_run=False)

    def test_submission_argv_and_unallocated_entry(self):
        c=m.cluster.ClusterConfig(**proposal_fixture()[2])
        argv=m.arguments(c,Path('/snapshot'),Path('/output'))
        self.assertIn('--gres=gpu:1',argv);self.assertIn('--time=01:00:00',argv)
        self.assertEqual(argv[-4],'/snapshot/experiments/run_math500_screen.sbatch')
        with patch.dict(os.environ,{},clear=True),self.assertRaises(Invalid):m.run_allocated(ROOT,Path('/synthetic'))

if __name__=='__main__':unittest.main()
