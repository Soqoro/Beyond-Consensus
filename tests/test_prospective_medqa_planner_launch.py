import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch,Mock
from bc_phase2 import prospective_medqa_planner_launch as p,composite_math_launch as base
from bc_phase2.model import digest,Invalid

class PlannerLaunch(unittest.TestCase):
    def test_exact_cohort_and_limits(self):
        c=p.cohort();self.assertEqual(sum(r['status']=='eligible' for b in c['blocks'] for r in b['records']),8)
        self.assertEqual(p.LIMITS['maximum_calls'],8);self.assertEqual(p.LIMITS['token_cap'],131072)
        self.assertEqual(p.LIMITS['wall_seconds'],3600)
    def test_old_medqa_approval_rejected(self):
        scope={'deployment':{'packages':base.EXPECTED_PACKAGES,'solver_importable':True}}
        m={'scope_digest':'scope','scope':scope,'blockers':[]}
        approval=dict(schema='medqa-planner-v1-approval',decision='approved',scope_digest='scope',reviewer='test',reviewed_at='now',statement_transmission_authorized=True,GPU_spending_authorized=True)
        with patch.object(p,'validate_manifest',return_value=scope):
            with self.assertRaises(Invalid):p.approve(m,approval)

    def test_dispatch_routes_only_block_one(self):
        scope={};journal=Mock();journal.snapshot.return_value={'totals':{'calls':8,'actual_tokens':800,'reserved_tokens':0}}
        with tempfile.TemporaryDirectory() as td,patch.object(p,'validate_release',return_value=scope),patch.object(p,'source_records',return_value={'synthetic':'source'}),patch.object(p,'open_transport',return_value='fake'),patch.object(p.worker,'Journal',return_value=journal),patch.object(p.pipeline,'plan_block',return_value=[]) as plan:
            out=Path(td)/'execution';r=p.dispatch({},out)
            self.assertEqual(plan.call_args.args[2],1)
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
        ids=[r['source_id'] for r in p.cohort()['blocks'][0]['records']]
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
        ids=[r['source_id'] for r in p.cohort()['blocks'][0]['records']]
        by={r['id']:r for r in rows}
        c=deepcopy(p.cohort())
        for r in c['blocks'][0]['records']:
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
        c=dict(dataset='medqa',blocks=[dict(slot=1,records=[dict(source_id=s,status='eligible',exact_hash=p.sources.faithful_identity(r)[0],normalized_hash=p.sources.faithful_identity(r)[1]) for s,r in records.items()])])
        class Fake:
            binding={'evidence':'synthetic'}
            def render(self,req):return dict(input_tokens=100,payload_digest=req['payload_digest'],rendered_ids_digest='2'*64)
            def generate(self,rendered):return dict(input_tokens=100,output_tokens=3072,finish_reason='length_limit',final_text='incomplete',boundary_error=None)
        with tempfile.TemporaryDirectory() as td:
            j=p.worker.Journal(Path(td)/'journal',Fake(),'scope',lambda:None,condition=p.KEY,limits=p.LIMITS)
            result=p.pipeline.plan_block(j,c,1,records,Path(td)/'planning')
            self.assertEqual(len(result),8);self.assertEqual(j.snapshot()['totals']['calls'],8)
            self.assertEqual(j.snapshot()['totals']['reserved_tokens'],0)
            self.assertTrue(all(r['review']['status']=='invalid_or_truncated' for r in result))
        class Uncertain(Fake):
            def generate(self,rendered):raise RuntimeError('unknown dispatch')
        with tempfile.TemporaryDirectory() as td:
            j=p.worker.Journal(Path(td)/'journal',Uncertain(),'scope',lambda:None,condition=p.KEY,limits=p.LIMITS)
            with self.assertRaises(Exception):p.pipeline.plan_block(j,c,1,records,Path(td)/'planning')
            snap=j.snapshot();self.assertEqual(len(snap['attempts']),1)
            self.assertGreater(snap['totals']['reserved_tokens'],0)
