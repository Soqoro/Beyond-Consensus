import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch,Mock
from bc_phase2 import prospective_medqa_block3_launch as p,composite_math_launch as base
from bc_phase2.model import digest,Invalid

class PlannerLaunch(unittest.TestCase):
    def test_exact_cohort_and_limits(self):
        c=p.cohort();self.assertEqual(sum(r['status']=='eligible' for b in c['blocks'] for r in b['records']),22)
        self.assertEqual(p.LIMITS['maximum_calls'],8);self.assertEqual(p.LIMITS['token_cap'],131072)
        self.assertEqual(p.LIMITS['wall_seconds'],3600)
    def test_old_medqa_approval_rejected(self):
        scope={'deployment':{'packages':base.EXPECTED_PACKAGES,'solver_importable':True}}
        m={'scope_digest':'scope','scope':scope,'blockers':[]}
        approval=dict(schema='medqa-planner-v1-approval',decision='approved',scope_digest='scope',reviewer='test',reviewed_at='now',statement_transmission_authorized=True,GPU_spending_authorized=True)
        with patch.object(p,'validate_manifest',return_value=scope):
            with self.assertRaises(Invalid):p.approve(m,approval)
            approval['schema']='prospective-medqa-block1-planner-v1-approval'
            with self.assertRaises(Invalid):p.approve(m,approval)

    def test_dispatch_routes_only_block_three(self):
        scope={};journal=Mock();journal.snapshot.return_value={'totals':{'calls':8,'actual_tokens':800,'reserved_tokens':0}}
        with tempfile.TemporaryDirectory() as td,patch.object(p,'validate_release',return_value=scope),patch.object(p,'source_records',return_value={'synthetic':'source'}),patch.object(p,'open_transport',return_value='fake'),patch.object(p.worker,'Journal',return_value=journal),patch.object(p.pipeline,'plan_block',return_value=[]) as plan:
            out=Path(td)/'execution';r=p.dispatch({},out)
            self.assertEqual(plan.call_args.args[2],3)
            self.assertEqual(plan.call_args.args[3],{'synthetic':'source'})
            self.assertFalse(r['worker_execution_allowed'])
            self.assertEqual(r['totals']['calls'],8)

    def test_approval_exact_and_pending_rejected(self):
        s={'deployment':{'packages':base.EXPECTED_PACKAGES,'solver_importable':True}}
        m={'scope_digest':'scope','scope':s,'blockers':[]}
        a=dict(schema=p.KEY+'-approval',decision='pending',scope_digest='scope',reviewer='test',reviewed_at='now',statement_transmission_authorized=True,GPU_spending_authorized=True)
        with patch.object(p,'validate_manifest',return_value=s):
            with self.assertRaises(Invalid):p.approve(m,a)
            a['decision']='approved';v=p.approve(m,a)
            self.assertEqual(p.validate_release(v),s)
            a['scope_digest']='old'
            with self.assertRaises(Invalid):p.approve(m,a)
    def test_shared_registry_dry_run_and_no_retry(self):
        with tempfile.TemporaryDirectory() as td:
            c=SimpleNamespace(output_root=td+'/out',snapshot_root=td+'/snap')
            s=dict(cluster={},scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4})
            v={'manifest':{'scope_digest':'scope'}}
            with patch.dict('os.environ',{},clear=True),patch.object(p,'validate_release',return_value=s),patch.object(p,'source_records'),patch.object(p,'arguments',return_value=['sbatch','synthetic']),patch.object(base.cluster,'ClusterConfig',return_value=c),patch.object(base.cluster,'registry_root',return_value=Path(td)),patch.object(base.cluster,'guard'),patch.object(base.cluster,'validate_site'),patch.object(base.cluster,'command') as cmd:
                self.assertFalse(p.submit(Path(td),v)['submitted']);cmd.assert_not_called()
                (Path(td)/'registry.json').write_text(json.dumps({'composite_math_attempts':{p.KEY:{'state':'submission_uncertain'}}}))
                with self.assertRaises(Invalid):p.submit(Path(td),v)
    def test_bad_release_cannot_load(self):
        with patch.object(p,'validate_release',side_effect=Invalid('bad approval')):
            with self.assertRaises(Invalid):p.open_transport({})
    def test_factory_uses_existing_checked_natural_transport(self):
        fake=SimpleNamespace()
        with patch.object(p.pilot,'CheckedTransport',return_value=fake) as ctor:
            result=p.make_transport('tokenizer','model','torch',{'verified_requests':[]})
            ctor.assert_called_once_with('tokenizer','model','torch');self.assertIs(result,fake)
            self.assertEqual(result.scope,{'verified_requests':[]})
    def test_common_loader_selects_planner_transport(self):
        model=Mock();tok=Mock();transport=SimpleNamespace(tokens={'eos':1},binding={})
        torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:1,get_device_properties=lambda i:SimpleNamespace(total_memory=80000000000)),bfloat16='bf16',device=lambda s:s)
        tf=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=tok)),Qwen3_5ForConditionalGeneration=SimpleNamespace(from_pretrained=Mock(return_value=model)))
        dep={'solver_importable':True,'packages':base.EXPECTED_PACKAGES}
        scope={'deployment':dep,'model':{'non_thinking_verification':{'ok':True},'generation_tokens':{'eos':1}}}
        proto=SimpleNamespace(validate_release=lambda v:scope,make_transport=Mock(return_value=transport),TRANSPORT_EVIDENCE='real_prospective_planner')
        with patch.dict('sys.modules',{'torch':torch,'transformers':tf}),patch.object(base,'deployment',return_value=dep),patch.object(base,'verify_local_inventory',return_value=Path('/synthetic')),patch.object(base.pilot,'lock_for',return_value={}),patch.object(base.screen,'verify_non_thinking',return_value={'ok':True}),patch('beyond_consensus.models.transformers_backend.require_allocation'),patch('bc_phase2.composite_math_decoder.TaskTransport') as constrained:
            result=base.open_transport({},protocol=proto)
            self.assertIs(result,transport);constrained.assert_not_called()
            proto.make_transport.assert_called_once_with(tok,model,torch,scope)
            self.assertEqual(result.binding['evidence'],'real_prospective_planner')
    def test_prepare_with_fake_tokenizer_and_changed_payload_rejected(self):
        import sys
        ids=[r['source_id'] for r in p.cohort()['blocks'][2]['records'] if r['status']=='eligible']
        records={sid:{'id':sid,'question':'Synthetic exam question','options':dict(zip('ABCD',['One','Two','Three','Four']))} for sid in ids}
        template={'enable_thinking':False,'template_hash':p.local.TEMPLATE_HASH,'on_off_switch':{'reasoning_support_verified':True}}
        files=dict(p.local.METADATA);shards=[f'weight-{i}.safetensors' for i in range(11)];files.update({k:'1'*64 for k in shards})
        inventory=dict(schema='joint-d1-local-verification-v1',checkpoint=p.screen.CHECKPOINT,revision=p.screen.REVISION,
            local_path='/synthetic/'+p.screen.REVISION,inventory=dict(files=files,weight_shards=shards),generation_tokens={'eos_token_id':[248046,248044],'pad_token_id':248044})
        dep=dict(python=str(Path(sys.executable).resolve()),packages=base.EXPECTED_PACKAGES,solver_importable=True)
        cfg=dict(partition='HPCAIq',time='01:00:00',memory_gb=128,python=dep['python'],storage_root='/synthetic',cache_root='/synthetic/cache',snapshot_root='/synthetic/snap',output_root='/synthetic/out')
        actual_hash=p.local.file_hash
        def hash_file(path):return p.local.METADATA[Path(path).name] if str(path).startswith('/synthetic/') else actual_hash(path)
        def render(tok,req,template):return {'payload_digest':req['payload_digest'],'rendered_ids_digest':'2'*64,'input_tokens':100}
        tf=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=Mock(return_value=object())))
        with patch.dict('sys.modules',{'transformers':tf}),patch.object(p,'source_records',return_value=records),patch.object(p.pipeline,'planning_packet',return_value={'requests':[p.pipeline.adapters.planner_request('medqa',r) for r in records.values()]}),patch.object(p.local,'file_hash',side_effect=hash_file),patch.object(p.screen,'verify_non_thinking',return_value=template),patch.object(p.screen,'render_request',side_effect=render),patch.object(base,'deployment',return_value=dep):
            m=p.prepare('/synthetic/public.json',inventory,cfg,'PartitionName=HPCAIq State=UP')
            self.assertFalse(m['execution_allowed']);self.assertEqual(len(m['scope']['verified_requests']),8)
            self.assertEqual(m['blockers'],[])
            m['scope']['verified_requests'][0]['payload_digest']='0'*64;m['scope_digest']=digest(m['scope'])
            with self.assertRaises(Invalid):p.validate_manifest(m)
    def test_unapproved_dispatch_no_directory(self):
        with tempfile.TemporaryDirectory() as td,patch.object(p,'validate_release',side_effect=Invalid('pending')):
            path=Path(td)/'execution'
            with self.assertRaises(Invalid):p.dispatch({},path)
            self.assertFalse(path.exists())

    def test_public_package_exact_block_options_and_private_rejection(self):
        import hashlib
        rows=[dict(id=f'test/row/{i}',question=f'Synthetic question {i}',options=dict(zip('ABCD',['One','Two','Three','Four']))) for i in range(1,1274)]
        ids=[r['source_id'] for r in p.cohort()['blocks'][2]['records'] if r['status']=='eligible']
        by={r['id']:r for r in rows}
        c=deepcopy(p.cohort())
        for r in c['blocks'][2]['records']:
            r['exact_hash'],r['normalized_hash']=p.sources.faithful_identity(by[r['source_id']])
        with tempfile.TemporaryDirectory() as td,patch.object(p,'cohort',return_value=c):
            path=Path(td)/'public.json'
            def read_current():
                raw=json.dumps(rows).encode();path.write_bytes(raw)
                h=hashlib.sha256(raw).hexdigest()
                with patch.object(p,'PUBLIC_HASH',h):return p.source_records({'source_package':{'path':str(path),'sha256':h}})
            selected=read_current();self.assertEqual(list(selected),ids)
            for r in selected.values():
                req=p.pipeline.adapters.planner_request('medqa',r)
                self.assertEqual(req['payload']['source'],r)
                self.assertEqual(list(req['payload']['source']['options']),'A B C D'.split())
            by[ids[0]]['answer_idx']='A'
            with self.assertRaises(Invalid):read_current()
            del by[ids[0]]['answer_idx']
            by[ids[0]]['options']['D']='One'
            with self.assertRaises(Invalid):read_current()

    def test_real_journal_continues_invalid_but_stops_uncertain(self):
        records={f'mock:{i}':dict(id=f'mock:{i}',question='Synthetic exam',options=dict(zip('ABCD',['One','Two','Three','Four']))) for i in range(8)}
        c=dict(dataset='medqa',blocks=[dict(slot=3,records=[dict(source_id=s,status='eligible',exact_hash=p.sources.faithful_identity(r)[0],normalized_hash=p.sources.faithful_identity(r)[1]) for s,r in records.items()]+[dict(source_id=s,status='blocked') for s in p.BLOCKED_IDS])])
        class Fake:
            binding={'evidence':'synthetic'}
            def render(self,req):return dict(input_tokens=100,payload_digest=req['payload_digest'],rendered_ids_digest='2'*64)
            def generate(self,rendered):return dict(input_tokens=100,output_tokens=3072,finish_reason='length_limit',final_text='incomplete',boundary_error=None)
        with tempfile.TemporaryDirectory() as td:
            j=p.worker.Journal(Path(td)/'journal',Fake(),'scope',lambda:None,condition=p.KEY,limits=p.LIMITS)
            result=p.pipeline.plan_block(j,c,3,records,Path(td)/'planning')
            self.assertEqual([r['source_id'] for r in result if r['status']=='blocked'],p.BLOCKED_IDS)
            self.assertEqual(len(result),8);self.assertEqual(j.snapshot()['totals']['calls'],8)
            self.assertEqual(j.snapshot()['totals']['reserved_tokens'],0)
            self.assertTrue(all(r['review']['status']=='invalid_or_truncated' for r in result if r['status']=='completed'))
        class Uncertain(Fake):
            def generate(self,rendered):raise RuntimeError('unknown dispatch')
        with tempfile.TemporaryDirectory() as td:
            j=p.worker.Journal(Path(td)/'journal',Uncertain(),'scope',lambda:None,condition=p.KEY,limits=p.LIMITS)
            with self.assertRaises(Exception):p.pipeline.plan_block(j,c,3,records,Path(td)/'planning')
            snap=j.snapshot();self.assertEqual(len(snap['attempts']),1)
            self.assertGreater(snap['totals']['reserved_tokens'],0)

    def test_campaign_transition_reuses_consent_and_rejects_scope_expansion(self):
        expected='d085a9e10104e39fbb4827772b49df1ac193d9f85b18d8cb33f0d7917de383fe'
        scope=dict(procedure_digest=p.cohort()['procedure_digest'],source_review_digest='review',model={'pinned':True},source_package={'pinned':True},source_ids=['synthetic'],limits=p.LIMITS)
        proposal=dict(proposal_digest=expected,procedure_digest=scope['procedure_digest'],model=scope['model'],source_package=scope['source_package'],stages=[dict(scope_digest='prior'),dict(stage='block3_planner',source_ids=['synthetic'],maximum_calls=8,token_cap=131072,wall_seconds=3600)],total_limits={'maximum_calls':134},restrictions=['no retries'])
        consent=dict(schema='remaining-medqa-campaign-consent-v1',decision='approved',proposal_digest=expected,source_transmission_authorized=True,GPU_spending_authorized=True,frozen_procedure_review_delegation_authorized=True,stages=deepcopy(proposal['stages']),total_limits=deepcopy(proposal['total_limits']),restrictions=proposal['restrictions'],block3_source_review_bundle_digest='review',reviewer='original user',reviewed_at='original approval time')
        prior=dict(status='completed_wave_recipe',totals=dict(actual_tokens=22657,calls=32,reserved_tokens=0))
        files={'CAMPAIGN_PROPOSAL.disabled.json':proposal,'approval.json':consent,'block2-submission.json':dict(scope_digest='prior',output='/synthetic/prior',job_id='synthetic'),'result.json':prior}
        original_digest=p.digest
        def hashed(v):return expected if v=={k:x for k,x in proposal.items() if k!='proposal_digest'} else original_digest(v)
        def filehash(path):return '284ae82c2832d9e2c678842bd335429bae4370eb78e735785985aece4872d66b' if Path(path).name=='result.json' else 'consent-hash'
        with patch.object(p,'validate_manifest',return_value=scope),patch.object(p,'digest',side_effect=hashed),patch.object(p.local,'file_hash',side_effect=filehash),patch('bc_phase2.joint_d1_release.read_evidence',side_effect=lambda path:deepcopy(files[Path(path).name])),patch.object(p,'approve',return_value={'release_digest':'release'}):
            a,r,e=p.campaign_approval('/synthetic',{'scope_digest':'new'})
            self.assertEqual(a['reviewer'],'original user');self.assertEqual(a['reviewed_at'],'original approval time')
            self.assertFalse(e['new_user_approval_requested']);self.assertFalse(e['submitted'])
            consent['GPU_spending_authorized']=False
            with self.assertRaises(Invalid):p.campaign_approval('/synthetic',{'scope_digest':'new'})
            consent['GPU_spending_authorized']=True
            scope['source_ids']=['different']
            with self.assertRaises(Invalid):p.campaign_approval('/synthetic',{'scope_digest':'new'})
            scope['source_ids']=['synthetic']
            prior['totals']['reserved_tokens']=10
            with self.assertRaises(Invalid):p.campaign_approval('/synthetic',{'scope_digest':'new'})
