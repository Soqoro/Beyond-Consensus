"""Synthetic planner-only bridge qualification. No benchmark/model/scheduler access."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from bc_phase2 import medqa_planner_launch as m
from bc_phase2.model import digest,Invalid
from test_d1_natural_binding import fixtures
from test_phase2_planner_qwen import Tokenizer,Model,Torch
ROOT=Path(__file__).resolve().parents[1]


def records():
    return [dict(id=s,question='Synthetic exam question',options={k:'Choice '+k for k in 'ABCD'}) for s in m.SOURCES]


def fixture():
    v,old,config,partition=fixtures();config['partition']='HPCAIq'
    template=v['template_check'];rows=[]
    for record in records():
        rows.append(dict(source_id=record['id'],payload_digest=m.medqa.planner_request(record)['payload_digest'],
            rendered_ids_digest='a'*64,input_tokens=100,output_cap=3072,reserved_tokens=3172))
    verification=dict(status='initial_requests_fit_observed_no_model',cohort_digest=m.COHORT,
        checkpoint=m.screen.CHECKPOINT,revision=m.screen.REVISION,model_executed=False,execution_allowed=False,
        private_evaluator_read=False,limits=m.medqa.PLAN_LIMITS,template_check=template,metadata=v['files'],
        requests=rows,total_reservation_tokens=38064,
        implementation_hashes={name:m.local.file_hash(ROOT/name) for name in (
            'src/bc_phase2/medqa_development.py','src/bc_phase2/d1_natural_screen.py','scripts/prepare_d1_natural_screen.py')})
    review=dict(cohort_digest=m.COHORT,dataset_sha256='774bbd90103af43badbe8d5294e336443573fc37b918763920b8fc3b3df581d9',
        authors_archive_equivalence='verified',rights_review='permitted_for_scoped_development',
        evidence_reference='synthetic evidence only',reviewer='synthetic',reviewed_at='synthetic')
    return ['/synthetic/public.json',verification,old,config,'PartitionName=HPCAIq State=UP Nodes=node14',review]


def release(args):
    manifest=m.bind(*args);a=m.review(manifest)['approval_template']
    a.update(decision='approved',reviewer='synthetic',reviewed_at='synthetic',
             statement_transmission_authorized=True,GPU_spending_authorized=True)
    return m.approve(manifest,a)


def session_fixture(directory):
    t=m.pilot.CheckedTransport(Tokenizer(),Model(),Torch())
    scope=dict(source_ids=list(m.SOURCES),resources=deepcopy(m.medqa.PLAN_LIMITS),verified_requests=[])
    for r in records():
        view=m.screen.render_request(t.tokenizer,m.medqa.planner_request(r),t.template['template_hash'])
        scope['verified_requests'].append({'source_id':r['id'],**{k:view[k] for k in ('input_tokens','payload_digest','rendered_ids_digest')}})
    t.scope=scope
    return m.Session(Path(directory)/'requests',scope,records(),t,time.time()),t


def observation(view,output=2,finish='eos'):
    return dict(input_tokens=view['input_tokens'],output_tokens=output,finish_reason=finish,final_text='invalid')


class MedqaLaunch(unittest.TestCase):
    def test_binding_and_approval(self):
        with patch.object(m,'source_records',return_value=records()):
            args=fixture();before=deepcopy(args);manifest=m.bind(*args)
            self.assertEqual(args,before);self.assertFalse(manifest['execution_allowed'])
            with self.assertRaises(Invalid):m.approve(manifest,m.review(manifest)['approval_template'])
            value=release(args);self.assertEqual(m.validate_release(value)['source_ids'],list(m.SOURCES))
            a=deepcopy(value['approval']);a['schema']='D1-natural-screen-v1-approval'
            with self.assertRaises(Invalid):m.approve(manifest,a)
            value['manifest']['scope']['resources']['maximum_calls']=13
            with self.assertRaises(Invalid):m.validate_release(value)
        with self.assertRaises((Invalid,KeyError)):m.open_transport({})

    def test_unresolved_source_review_cannot_be_approved(self):
        with patch.object(m,'source_records',return_value=records()):
            for field,value in [('authors_archive_equivalence','not_independently_verified'),
                                ('rights_review','unresolved'),('evidence_reference','')]:
                args=fixture();args[-1][field]=value
                self.assertTrue(m.bind(*args)['blockers'])
                with self.assertRaises(Invalid):release(args)

    def test_explicit_user_mirror_policy_preserves_facts_and_caps(self):
        with patch.object(m,'source_records',return_value=records()):
            args=fixture();r=args[-1]
            r.update(authors_archive_equivalence='not_independently_verified',rights_review='unresolved',
                admission_exception=dict(policy=m.MIRROR_POLICY,authorization_quote=m.MIRROR_AUTHORIZATION,
                                         scope='frozen_12_source_planner_only'))
            value=release(args);scope=m.validate_release(value);summary=m.review(value['manifest'])
            self.assertEqual(scope['source_review']['rights_review'],'unresolved')
            self.assertEqual(scope['source_review']['authors_archive_equivalence'],'not_independently_verified')
            self.assertEqual(scope['resources']['maximum_calls'],12)
            self.assertFalse(scope['worker_execution_allowed'])
            self.assertIn('pinned_mirror_accepted_by_user_not_independently_verified',summary['limitations'])
            self.assertFalse(summary['execution_allowed'])
            for field,bad in [('cohort_digest','changed'),('dataset_sha256','changed'),
                              ('authors_archive_equivalence','verified'),('rights_review','permitted_for_scoped_development')]:
                changed=deepcopy(args);changed[-1][field]=bad
                with self.subTest(field=field),self.assertRaises(Invalid):release(changed)
            for field in ('policy','authorization_quote','scope'):
                changed=deepcopy(args);changed[-1]['admission_exception'][field]='changed'
                with self.subTest(field=field),self.assertRaises(Invalid):release(changed)
            changed=deepcopy(args);changed[-1]['reviewer']=''
            with self.assertRaises(Invalid):release(changed)

    def test_changed_fit_settings_or_prompt_rejected(self):
        with patch.object(m,'source_records',return_value=records()):
            for kind in ('order','payload','render','tokens','sum','thinking','inventory','time','partition','interface'):
                args=fixture();v=args[1]
                if kind=='order':v['requests'].reverse()
                if kind=='payload':v['requests'][0]['payload_digest']='changed'
                if kind=='render':v['requests'][0]['rendered_ids_digest']='invalid'
                if kind=='tokens':v['requests'][0]['input_tokens']=14000
                if kind=='sum':v['total_reservation_tokens']=0
                if kind=='thinking':v['template_check']['enable_thinking']=True
                if kind=='inventory':args[2]['inventory']['files']['config.json']='bad'
                if kind=='time':args[3]['time']='02:00:00'
                if kind=='partition':args[3]['partition']='NA100q'
                if kind=='interface':v['implementation_hashes']={}
                with self.subTest(kind=kind),self.assertRaises(Invalid):m.bind(*args)

    def test_public_boundary_and_source_hash(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'public.json';cohort=dict(records=records())
            cohort['cohort_digest']=digest(cohort);raw=json.dumps(cohort).encode();path.write_bytes(raw)
            h=hashlib.sha256(raw).hexdigest();scope=dict(source_package=dict(path=str(path),sha256=h))
            with patch.object(m,'PUBLIC_HASH',h),patch.object(m,'COHORT',cohort['cohort_digest']):
                self.assertEqual(m.source_records(scope),records())
                path.write_bytes(raw+b' ')
                with self.assertRaises(Invalid):m.source_records(scope)
            for key in ('answer','answer_idx','meta_info','metamap_phrases'):
                r=records()[0];r[key]='PRIVATE'
                with self.assertRaises(Invalid):m.medqa.assert_public(r)

    def test_twelve_invalid_outcomes_continue_no_thirteenth_call(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=observation):result=m.pilot.drive(session,list(m.SOURCES))
            self.assertFalse(result['halted']);self.assertEqual(len(result['ledger']['attempts']),12)
            self.assertEqual(result['ledger']['totals']['reserved_tokens'],0)
            self.assertEqual(result['ledger']['totals']['actual_tokens'],84)
            self.assertEqual(result['ledger']['totals']['model_calls_observed'],0)
            for attempt in result['ledger']['attempts']:
                self.assertEqual(set(attempt['outbound_payload']['source']),{'id','question','options'})
                self.assertEqual(set(attempt['outbound_payload']['source']['options']),set('ABCD'))
            with self.assertRaises(Invalid):session.advance(m.SOURCES[0])

    def test_valid_unsupported_response(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            session,t=session_fixture(d)
            def unsupported(view):
                return {**observation(view),'final_text':json.dumps(dict(schema=m.screen.VERSION,
                    source_id=m.SOURCES[0],status='unsupported',tasks=[],reason='Synthetic unsupported case'))}
            with patch.object(t,'generate',side_effect=unsupported):a=session.advance(m.SOURCES[0])
            self.assertEqual(a['state'],'completed');self.assertTrue(m.screen.reliable_terminal(a))

    def test_truncation_then_unknown_stops(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=lambda v:observation(v,3072,'length_limit')):
                self.assertTrue(m.screen.reliable_terminal(session.advance(m.SOURCES[0])))
            with patch.object(t,'generate',side_effect=lambda v:observation(v,None)):
                self.assertEqual(session.advance(m.SOURCES[1])['state'],'uncertain')
            self.assertEqual(session.snapshot()['totals']['reserved_tokens'],3077)
            with patch.object(t,'generate') as generate,self.assertRaises(Invalid):session.advance(m.SOURCES[2])
            generate.assert_not_called()

    def test_crash_reservation_persisted_no_reopen_or_replay(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            session,t=session_fixture(d)
            with patch.object(t,'generate',side_effect=RuntimeError('crash')),self.assertRaises(RuntimeError):session.advance(m.SOURCES[0])
            self.assertEqual(session.snapshot()['totals']['reserved_tokens'],3077)
            saved=json.loads((Path(d)/'requests'/'ledger.json').read_text())
            self.assertEqual(saved['state']['attempts'][0]['state'],'reserved')
            with self.assertRaises(Invalid):session.advance(m.SOURCES[1])
            with self.assertRaises(FileExistsError):session_fixture(d)

    def test_integrity_wall_render_and_budget_stop_before_generate(self):
        for kind in ('source','wall','render','budget'):
            with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
                session,t=session_fixture(d)
                if kind=='wall':
                    state=session._read();state['started_at']=time.time()-3601;session._save(state)
                if kind=='render':t.scope['verified_requests'][0]['rendered_ids_digest']='changed'
                with patch.object(t,'generate') as generate:
                    if kind=='source':
                        with patch.object(m,'source_records',side_effect=Invalid('integrity')),self.assertRaises(Invalid):session.advance(m.SOURCES[0])
                    elif kind=='budget':
                        with patch.object(m,'CAP',3076),self.assertRaises(Invalid):session.advance(m.SOURCES[0])
                    else:
                        with self.assertRaises(Invalid):session.advance(m.SOURCES[0])
                    generate.assert_not_called()

    def test_uncertain_submission_blocks_rebound_output(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            root=Path(d);reg=root/'registry';reg.mkdir();args=fixture();args[3]['output_root']=str(root/'out')
            value=release(args)
            def command(argv):
                if '--test-only' in argv:return 'ok'
                raise RuntimeError('lost submission response')
            with patch.dict(os.environ,{},clear=True),patch.object(m.cluster,'registry_root',return_value=reg), \
                 patch.object(m.cluster,'guard'),patch.object(m.cluster,'validate_site'), \
                 patch.object(m,'source_revision',return_value='synthetic'),patch.object(m,'create_snapshot',return_value=ROOT), \
                 patch.object(m.cluster,'command',side_effect=command):
                with self.assertRaises(RuntimeError):m.submit(ROOT,value,dry_run=False)
                state=json.loads((reg/'registry.json').read_text());self.assertIsNotNone(state['uncertain_submission'])
                self.assertIn(m.COHORT,state['medqa_planner_attempts'])
                args[3]['output_root']=str(root/'other')
                with self.assertRaises(Invalid):m.submit(ROOT,release(args),dry_run=False)

    def test_dispatch_result_retains_all_sources_and_mock_evidence(self):
        with tempfile.TemporaryDirectory() as d,patch.object(m,'source_records',return_value=records()):
            value=release(fixture());scope=value['manifest']['scope']
            t=m.pilot.CheckedTransport(Tokenizer(),Model(),Torch());t.scope=scope
            scope['verified_requests']=[]
            for r in records():
                v=m.screen.render_request(t.tokenizer,m.medqa.planner_request(r),t.template['template_hash'])
                scope['verified_requests'].append(dict(source_id=r['id'],**{k:v[k] for k in ('input_tokens','payload_digest','rendered_ids_digest')}))
            with patch.object(m,'validate_release',return_value=scope),patch.object(m,'open_transport',return_value=t), \
                 patch.object(t,'generate',side_effect=lambda v:observation(v,None)):
                result=m.dispatch(value,Path(d)/'execution')
            self.assertTrue(result['halted']);self.assertFalse(result['model_executed'])
            self.assertEqual(len(result['rows']),12);self.assertEqual(result['rows'][1]['state'],'unrun')
            self.assertEqual(result['ledger']['totals']['reserved_tokens'],3077)
            self.assertFalse(result['worker_execution_allowed'])

    def test_allocation_resource_changes(self):
        record='Partition=HPCAIq NumNodes=1 NumCPUs=4 TimeLimit=01:00:00 ReqTRES=cpu=4,mem=128G,gres/gpu=1'
        m.check_allocation(record)
        for before,after in [('HPCAIq','NA100q'),('NumNodes=1','NumNodes=2'),('gres/gpu=1','gres/gpu=2'),('128G','256G'),('01:00:00','02:00:00')]:
            with self.assertRaises(Invalid):m.check_allocation(record.replace(before,after))

    def test_argv_and_no_allocation_rejected(self):
        c=m.cluster.ClusterConfig(**fixture()[3]);argv=m.arguments(c,Path('/snapshot'),Path('/output'))
        for flag in ('--partition=HPCAIq','--gres=gpu:1','--time=01:00:00','--mem=128G'):self.assertIn(flag,argv)
        self.assertEqual(argv[-4],'/snapshot/experiments/run_medqa_planner.sbatch')
        with patch.dict(os.environ,{},clear=True),self.assertRaises(Invalid):m.run_allocated(ROOT,Path('/synthetic'))

if __name__=='__main__':unittest.main()
