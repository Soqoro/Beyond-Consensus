"""Finite worker comparison boundaries; model doubles are not competence evidence."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments import worker_selection as w
from beyond_consensus.experiments.worker_presentation import render,audit,PresentedBackend
from beyond_consensus.models import worker_profiles as p
from beyond_consensus.models.base import Generation
from beyond_consensus.experiments.cluster import sbatch_arguments,active_gpu_jobs,guard
from beyond_consensus.experiments.cluster import ClusterConfig
from beyond_consensus.util import BCError,digest
from reporecourse import worker_cases as d
from reporecourse.resources import Resources,success_at_budget
from reporecourse.common import Rejected


class PromptFootprints(unittest.TestCase):
    def test_extracts_mapping_list_and_single_batch_without_counting_keys(self):
        from collections import UserDict
        ids=[101,102,103,104]
        tensor=SimpleNamespace(tolist=lambda:[ids])
        for encoded in (ids,[ids],UserDict(input_ids=ids,attention_mask=[1]*4),
                        UserDict(input_ids=tensor,attention_mask=[[1]*4])):
            for name in ('control','coder'):
                with self.subTest(encoded=type(encoded).__name__,profile=name):
                    def apply(messages,**kwargs):
                        self.assertTrue(kwargs['return_dict'])
                        self.assertIsNone(kwargs['return_tensors'])
                        self.assertEqual(kwargs.get('enable_thinking'),True if name=='control' else None)
                        return encoded
                    result=w.prompt_token_ids(SimpleNamespace(apply_chat_template=apply),p.profile(name),[])
                    self.assertEqual(result,ids)
                    self.assertEqual(digest(result),digest(ids))

    def test_bad_or_multiple_sequences_rejected(self):
        for encoded in ({'attention_mask':[1]},[],[[1],[2]],[True],[1.5],[-1],'123'):
            with self.subTest(encoded=encoded):
                with self.assertRaises(BCError):
                    w.prompt_token_ids(SimpleNamespace(apply_chat_template=lambda *a,**k:encoded),p.profile('coder'),[])

    def test_full_q_footprint_uses_ids_for_long_search_counts_and_hashes(self):
        from collections import UserDict
        class Tokenizer:
            def apply_chat_template(self,messages,**kwargs):
                count=20+10*messages[-1]['content'].count('Record ')
                return UserDict(input_ids=list(range(count)),attention_mask=[1]*count)
        tokenizer=Tokenizer()
        module=SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a,**k:tokenizer))
        with patch.dict('os.environ',{'SLURM_JOB_ID':'cpu-test'}),patch.dict(sys.modules,{'transformers':module}),\
             patch.object(p,'require_qualified'):
            result=w.footprint(p.profile('coder'),{'tokenizer_path':'/unused'},'Q',w.grid('Q'))
        self.assertEqual(result['status'],'passed')
        self.assertEqual([row['id'] for row in result['cases']],['sql','schema','mapping','long'])
        for row in result['cases']:
            ids=tokenizer.apply_chat_template(row['messages'])['input_ids']
            self.assertEqual(row['input_tokens'],len(ids))
            self.assertEqual(row['rendered_ids_hash'],digest(ids))
        long=result['cases'][-1]
        self.assertEqual(long['input_tokens'],12280)
        self.assertGreater(long['input_tokens']+10,12288)


class Design(unittest.TestCase):
    def test_disjoint_inventory_domain_family_membership(self):
        cases=d.cases();self.assertEqual(len(cases),24);self.assertEqual(len({x['id'] for x in cases}),24)
        for split in ('screen','confirm'):
            rows=[c for c in cases if c['split']==split]
            self.assertEqual(len(rows),12)
            self.assertEqual({domain:sum(c['domain']==domain for c in rows) for domain in ('sql','api')},{'sql':6,'api':6})
            self.assertEqual(len({c['family'] for c in rows}),9)
        self.assertFalse({x['template'] for x in cases if x['split']=='screen'} & {x['template'] for x in cases if x['split']=='confirm'})
        self.assertEqual(d.inventory()['case_set_id'],d.inventory()['case_set_id'])
    def test_parity_and_no_private_solution_for_every_case(self):
        for c in d.cases():
            with self.subTest(case=c['id']):
                original=w.messages(c);r=audit(original);minimal=render(original,'P_minimal')
                self.assertTrue(r['observation_equal']);self.assertTrue(r['history_equal'])
                self.assertEqual(json.loads(original[-1]['content']),json.loads(minimal[-1]['content']))
                self.assertNotIn('private',json.loads(minimal[-1]['content']))
                self.assertIn('explicit ELSE',minimal[0]['content'])
                self.assertIn('publication_rules',minimal[0]['content'])
                self.assertIn('tool',minimal[0]['content'])
                self.assertEqual(render(original,'P_current'),original)
    def test_dynamic_repair_context_preserved(self):
        obs={'interface_delivery':True,'public_alarm':['x'],'bindings':{'x':'frozen'},'scope':{'imports':['a']},'messages':[{'x':1}]}
        history=[{'role':'assistant','content':'{"tool":"read_source","name":"a"}'},{'role':'user','content':'recorded feedback'}]
        messages=w.worker_messages(obs,history);value=render(messages,'P_minimal')
        self.assertEqual(value[1:-1],history);self.assertEqual(json.loads(value[-1]['content']),obs)
        with self.assertRaises(BCError):render([{'role':'system','content':'injected'},messages[-1]],'P_minimal')
    def test_exact_grids_balanced_and_single_common_confirmation(self):
        a=w.grid('A');b=w.grid('B','P_minimal');self.assertEqual((len(a),len(b)),(48,24))
        self.assertEqual(len({r['id'] for r in a+b}),72)
        self.assertEqual({r['presentation'] for r in b},{'P_minimal'})
        cs=[dict(configuration_id=str(i)) for i in range(6)]
        c=w.grid('C','P_minimal',cs);self.assertEqual(len(c),24)
        for name in w.MODELS:self.assertEqual(sum(r['model']==name for r in c),12)
    def test_meaningful_mutants_and_isolated_oracle(self):
        for c in d.cases():self.assertNotEqual(d.action(c),d.action(c,True))
        c=next(c for c in d.cases() if c['id']=='screen-api-nested-fields')
        env=SimpleNamespace(bound={'report':'v'},execute=lambda *a:dict(status='ok',output={'wrong':7,'title':'A'}))
        self.assertFalse(d.evaluate(c,env)['correct'])
        env.execute=lambda *a:dict(status='ok',output={'item_id':7,'title':'A'})
        self.assertTrue(d.evaluate(c,env)['correct'])
    def test_blocked_prerequisites_never_cpu_pass(self):
        with patch.object(d,'environment',side_effect=Rejected('blocked_prerequisite')):r=w.controls()
        self.assertEqual(r['status'],'failed');self.assertEqual(len(r['cases']),48)
        self.assertTrue(all(x['error_category']=='blocked_prerequisite' for x in r['cases']))
    def test_actual_restricted_reference_mutants(self):
        from tests.test_reporecourse import optional
        if not optional():self.skipTest('Pinned SQLGlot/jsonschema/referencing unavailable')
        r=w.controls()
        self.assertEqual(r['status'],'passed',[(x['case'],x['negative'],x.get('error_category'),x.get('evaluation')) for x in r['cases'] if x['status']!='passed'])


class Deployments(unittest.TestCase):
    def test_exact_routes_and_layer_map(self):
        control=p.profile('control');coder=p.profile('coder')
        self.assertEqual(control['model']['revision'],p.CONTROL);self.assertEqual(coder['model']['revision'],p.CODER)
        self.assertEqual(p.template_options(control),{'enable_thinking':True});self.assertEqual(p.template_options(coder),{})
        self.assertEqual(p.device_map(control,64),{'':0})
        mapping=p.device_map(coder,48);self.assertEqual({mapping['model.layers.'+str(i)] for i in range(48)},{0,1,2,3})
        self.assertEqual(mapping['model.rotary_emb'],0)
        with self.assertRaises(BCError):p.device_map(coder,49)
        for value in (control,coder):self.assertEqual(value['model']['max_new_tokens'],4096)
    def test_no_hidden_offload(self):
        class Tensor:
            device='cpu';dtype='torch.bfloat16'
            def is_floating_point(self):return True
            def numel(self):return 1
        model=SimpleNamespace(named_parameters=lambda:[('p',Tensor())],named_buffers=lambda:[])
        with self.assertRaises(BCError):p.check_placement(model,p.profile('coder'))
    def test_physical_request_defaults_and_four_gpu(self):
        c=ClusterConfig("test", "02:00:00", 256, sys.executable,"/tmp/store","/tmp/cache","/tmp/snap","/tmp/out");args=sbatch_arguments(c,Path('/src'),Path('/out'),[0],1)
        self.assertIn('--gres=gpu:1',args)
        args=sbatch_arguments(c,Path('/src'),Path('/out'),[0],1,physical_gpus=4,mode='preflight')
        self.assertIn('--gres=gpu:4',args);self.assertIn('--nodes=1',args);self.assertIn('--ntasks=1',args)
        with self.assertRaises(BCError):sbatch_arguments(c,Path('/src'),Path('/out'),[0,1],2,physical_gpus=4)
    def test_array_tres_and_cross_campaign_guard(self):
        def command(argv):
            if argv[0]=='squeue':return '123_0\n123_1'
            return 'JobId='+argv[-1]+' JobState=RUNNING ReqTRES=cpu=4,gres/gpu=4,gres/gpu:a100=4'
        with patch('beyond_consensus.experiments.cluster.command',side_effect=command):
            jobs=active_gpu_jobs();self.assertTrue(jobs)
            with self.assertRaises(BCError):guard({'jobs':[]})
    def test_frozen_generation_multidevice_occupancy(self):
        b=p.WorkerBackend.__new__(p.WorkerBackend);b.profile=p.profile('coder')
        b.model=SimpleNamespace(_cache=object())
        synced=[];b.torch=SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda i:synced.append(i),max_memory_reserved=lambda i:1))
        g=Generation('{}',2,0,0.1,{})
        with patch('beyond_consensus.models.transformers_backend.TransformersBackend.generate',return_value=g):result=b.generate([],4096,0)
        self.assertIsNone(result.device_seconds);self.assertEqual(synced,[0,1,2,3]*2)
        self.assertEqual(result.diagnostics['actual_gpus'],4);self.assertIsNone(b.model._cache)

    def test_reaped_child_cpu_blocks_and_survives_qualification_report(self):
        b=p.WorkerBackend.__new__(p.WorkerBackend);b.profile=p.profile('coder')
        b.count_input=lambda messages:63
        b.torch=SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda i:None))
        g=Generation('{}',2,0,None,{})
        def generated(*args):
            sys.audit('subprocess.Popen', '/bin/diagnostic-test', ['private'], None, {})
            return g
        usage=[SimpleNamespace(ru_utime=1.,ru_stime=2.),SimpleNamespace(ru_utime=1.25,ru_stime=2.5)]
        with patch('resource.getrusage',side_effect=usage), patch.object(p,'inference_processes',return_value={}), patch.object(p,'child_process_observation',return_value={'children':[]}):
            with patch('beyond_consensus.models.transformers_backend.TransformersBackend.generate',side_effect=generated):
                row=w.qualification_call(b,dict(id='sql',messages=[],input_tokens=63))
        self.assertFalse(row['passed']);self.assertFalse(row['cpu_accounting_complete'])
        self.assertEqual(row['inference_child_cpu']['reaped_child_cpu_delta_seconds'],.75)
        self.assertEqual(row['resources']['uncertain_tokens'],4159)
        self.assertNotIn('generation',row)

        self.assertEqual(row['inference_child_cpu']['process_launch_trace']['events'][0]['executable'],'diagnostic-test')

    def test_generation_failure_keeps_original_error_and_child_observation(self):
        b=p.WorkerBackend.__new__(p.WorkerBackend);b.profile=p.profile('coder')
        b.torch=SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda i:None))
        with patch.object(p,'inference_processes',return_value={}):
            with patch('beyond_consensus.models.transformers_backend.TransformersBackend.generate',side_effect=RuntimeError('accelerator')):
                with self.assertRaisesRegex(RuntimeError,'accelerator') as caught:b.generate([],4096,0)
        self.assertEqual(caught.exception.inference_child_cpu['schema'],'rr-inference-child-cpu-observation-v1')

    def test_live_child_guard_remains_with_zero_reaped_delta(self):
        b=p.WorkerBackend.__new__(p.WorkerBackend);b.profile=p.profile('coder')
        b.torch=SimpleNamespace(cuda=SimpleNamespace(synchronize=lambda i:None))
        usage=SimpleNamespace(ru_utime=0.,ru_stime=0.)
        with patch('resource.getrusage',return_value=usage), patch.object(p,'inference_processes',side_effect=[{},BCError('live child')]):
            with patch('beyond_consensus.models.transformers_backend.TransformersBackend.generate',return_value=Generation('{}',2)):
                with self.assertRaisesRegex(BCError,'live child') as caught:b.generate([],4096,0)
        self.assertEqual(caught.exception.inference_child_cpu['reaped_child_cpu_delta_seconds'],0)


class Attempts(unittest.TestCase):
    def test_qualification_trace_survives_failure_and_restores_backend(self):
        prior=object()
        class Backend:
            diagnostic_trace=prior
            def count_input(self,m):return 63
            def generate(self,*args):
                self.diagnostic_trace.unique_prefix.feed(3,b'{')
                self.diagnostic_trace.begin('unique_key_mask')
                raise BCError('Unique-key empty_allowed_intersection')
        backend=Backend()
        row=w.qualification_call(backend,dict(id='sql',messages=[],input_tokens=63))
        self.assertIs(backend.diagnostic_trace,prior)
        self.assertFalse(row['passed'])
        self.assertEqual(row['decoder_trace']['unique_prefix']['action_token_tail'],[3])
        self.assertEqual(row['resources']['uncertain_tokens'],4159)

    def test_wrong_tool_one_call_and_no_retry(self):
        class Backend:
            calls=0
            def count_input(self,m):return 100
            def generate(self,m,cap,seed):
                self.calls+=1;return Generation('{"tool":"list_sources"}',7,0,None,dict(finish_reason='eos',constraint_complete=True))
        backend=Backend();saved=[];r=w.attempt(backend,d.cases()[0],'P_minimal',saved.append)
        self.assertEqual(backend.calls,1);self.assertEqual(r['error_category'],'unexpected_action')
        self.assertFalse(r['complete_in_budget']);self.assertIsNone(r['semantic_correct'])
        self.assertEqual(r['resources']['actual_tokens'],107);self.assertTrue(saved)
    def test_interruption_retains_unknown_usage_and_stops(self):
        class Backend:
            def count_input(self,m):return 100
            def generate(self,*a):raise RuntimeError('accelerator')
        r=w.attempt(Backend(),d.cases()[0],'P_current',lambda r:None)
        self.assertEqual(r['status'],'infrastructure_failed');self.assertEqual(r['resources']['uncertain_tokens'],4196)
    def test_output_truncation_is_observed_not_infrastructure_retry(self):
        class Backend:
            def count_input(self,m):return 100
            def generate(self,*a):return Generation('{"tool":"list_sources"}',4096,4000,None,dict(finish_reason='length_limit',constraint_complete=False))
        r=w.attempt(Backend(),d.cases()[0],'P_current',lambda r:None)
        self.assertEqual(r['status'],'rejected');self.assertEqual(r['error_category'],'incomplete_response')
    def test_cpu_overrun_cannot_be_success(self):
        r=Resources(16384,1)
        with self.assertRaises(Rejected):r.reconcile_cpu('host',0,2)
        self.assertFalse(success_at_budget('completed',True,r))
    def test_qualification_strict_duplicate_parser(self):
        class Backend:
            def count_input(self,m):return 10
            def generate(self,*a):return Generation('{"tool":"list_sources","tool":"list_sources"}',10,0,None,dict(finish_reason='eos',constraint_complete=True))
        r=w.qualification_call(Backend(),dict(id='long',messages=[],input_tokens=10))
        self.assertFalse(r['passed']);self.assertEqual(r['resources']['actual_tokens'],20)
    def test_presentation_backend_counts_and_generates_identical_render(self):
        seen=[]
        backend=SimpleNamespace(count_input=lambda m:seen.append(m) or 5,generate=lambda m,*a:seen.append(m) or Generation('{}',1))
        b=PresentedBackend(backend,'P_minimal');m=w.messages(d.cases()[0]);b.count_input(m);b.generate(m,4096,0)
        self.assertEqual(seen[0],seen[1])


class Decisions(unittest.TestCase):
    def records(self,stage='A',presentation=None):
        st={'confirmation_case_ids':[c['id'] for c in d.cases() if c['split']=='confirm']}
        ms=[];rs=[]
        for name in w.MODELS:
            m={'study':st,'stage':stage,'profile':{'name':name},'presentation':presentation,'prior':{'selected_presentation':presentation}}
            rows=[dict(x,status='completed',semantic_correct=False,complete_in_budget=False,resources={'actual_tokens':100}) for x in w.grid(stage,presentation) if x['model']==name]
            ms.append(m);rs.append(dict(manifest_hash=digest(m),rows=rows))
        return ms,rs
    def test_tie_keeps_current_and_missing_blocks_selection(self):
        ms,rs=self.records()
        with patch.object(w,'validate'):
            r=w.compare(ms,rs);self.assertEqual(r['selected_presentation'],'P_current');self.assertEqual(r['status'],'complete')
            empty=[dict(manifest_hash=digest(m),status='missing',rows=[]) for m in ms]
            missing=w.compare(ms,empty);self.assertEqual(missing['status'],'incomplete');self.assertEqual(len(missing['rows']),48);self.assertIsNone(missing['selected_presentation'])
            rs[0]['rows'].pop();r=w.compare(ms,rs);self.assertIsNone(r['selected_presentation']);self.assertEqual(len(r['rows']),48)
    def test_minimum_domain_tie_breaker_and_total_priority(self):
        ms,rs=self.records()
        # Current: four successes in one cell. Minimal: one in each cell.
        current=[r for r in rs[0]['rows'] if r['presentation']=='P_current' and r['domain']=='sql'][:4]
        minimal=[next(r for r in block['rows'] if r['presentation']=='P_minimal' and r['domain']==domain) for block in rs for domain in ('sql','api')]
        for r in current+minimal:r['semantic_correct']=True
        with patch.object(w,'validate'):
            r=w.compare(ms,rs);self.assertEqual(r['selected_presentation'],'P_minimal')
            extra=next(r for r in rs[0]['rows'] if r['presentation']=='P_current' and not r['semantic_correct']);extra['semantic_correct']=True
            self.assertEqual(w.compare(ms,rs)['selected_presentation'],'P_current')
    def test_confirmation_adequacy_domain_and_all_costs(self):
        ms,rs=self.records('B','P_current')
        for r in rs[0]['rows']:r.update(semantic_correct=True,complete_in_budget=True)
        with patch.object(w,'validate'):r=w.compare(ms,rs)
        self.assertTrue(r['models']['control']['adequate']);self.assertFalse(r['models']['coder']['adequate'])
        self.assertEqual(r['models']['coder']['total_tokens'],1200);self.assertEqual(len(r['pairs']),12)
        self.assertIn('review_required',r['decision'])
    def test_approval_mutation_and_old_lock_rejected(self):
        with self.assertRaises(BCError):w.validate({'schema':w.SCHEMA,'experiment_id':'false'})
        with self.assertRaises(BCError):p.verify_lock(p.profile('coder'),dict(checkpoint='Qwen/Qwen3.5-27B'))


class Workflow(unittest.TestCase):
    def test_same_frozen_owner_for_each_model_and_no_clean_filter(self):
        from tests.test_rr_sampled_cohort import fixture
        from reporecourse import sampled_cohort
        from beyond_consensus.experiments import rr_cohort
        public,plans=fixture()
        for plan in plans:
            c=sampled_cohort.configuration(public['id'],plan)
            schedules=[sampled_cohort.schedule(c,public,{'profile':p.profile(n)}) for n in w.MODELS]
            self.assertEqual([x['target'] for x in schedules[0]['branches']['rows']],[x['target'] for x in schedules[1]['branches']['rows']])
            calls=[]
            def execute(branches,bid,public,private,worker,save):
                self.assertEqual(worker.output_cap,4096)
                calls.append(bid)
                return dict(status='completed',success=False,contract_conformant=True)
            with patch.object(rr_cohort.v2,'_execute_branch',side_effect=execute):
                r=rr_cohort.execute_schedule(c,schedules[0],public,{},object(),lambda _:None,lambda *a:None,output_cap=4096)
            self.assertEqual(len(calls),2);self.assertEqual(r['status'],'completed')
            self.assertEqual(r['planning']['physical_generation_count'],0)
    def test_real_common_scoped_engine_with_fresh_model_double(self):
        from tests.test_rr_sampled_cohort import fixture
        from reporecourse import sampled_cohort
        from reporecourse.tasks import private_task
        from beyond_consensus.experiments import rr_cohort
        public,plans=fixture();c=sampled_cohort.configuration(public['id'],plans[0]);seen=[]
        class Backend:
            def count_input(self,m):seen.append(json.loads(m[-1]['content']));return 100
            def generate(self,m,cap,seed):
                self_cap=cap
                if self_cap!=4096:raise AssertionError('old cap')
                return Generation('{"tool":"finish"}',7,0,None,{'finish_reason':'eos','constraint_complete':True})
        r=rr_cohort.execute_schedule(c,sampled_cohort.schedule(c,public),public,private_task('synthetic-nullable'),
            PresentedBackend(Backend(),'P_minimal'),lambda _:None,lambda *a:None,output_cap=4096)
        self.assertEqual(len(r['branches']),2);self.assertTrue(seen)
        self.assertTrue(all(b['execution_contract']=='plan_scoped_v1' for b in r['branches']))
        self.assertTrue(all(b['resource_profile']['actual_tokens']>0 for b in r['branches']))
    def test_distributed_cpu_not_silently_coordinator_only(self):
        import os
        with patch.dict(os.environ,{'WORLD_SIZE':'4'}):
            with self.assertRaises(BCError):p.inference_processes()
    def test_approval_no_started_attempt_or_automatic_stage_chain(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(w,'verify'):
            m={'approval':None,'stage':'A'}
            with self.assertRaises(BCError):w.submission(m,Path(temp),{},'run',1,temp)
            m['approval']={'test_only':True};w.submission(m,Path(temp),{},'run',1,temp)
            with self.assertRaises(BCError):w.submission(m,Path(temp),{},'preflight',1,temp)
            (Path(temp)/'worker-started.json').write_text('{}')
            with self.assertRaises(BCError):w.submission(m,Path(temp),{},'run',1,temp)


class ManifestScope(unittest.TestCase):
    def candidate(self):
        from tests.support import ROOT
        def measured(p,lock,stage,rows,*args):
            return dict(stage=stage,profile=p['name'],lock_hash=digest(lock),status='passed',implementation=w.hashes(),
                cases=[dict(id=r['id'],input_tokens=100,passed=True) for r in rows])
        with patch.object(p,'require_qualified'),patch.object(w,'footprint',side_effect=measured):
            return w.build(ROOT,'control',{},'Q')
    def test_four_call_scope_cannot_expand_after_approval(self):
        m=self.candidate();a=w.approval_template(m);a.update(decision='approved',reviewer='CPU test only',reviewed_at='test')
        with patch.object(w,'verify'):approved=w.authorize(m,a,Path('.'),{})
        self.assertFalse(approved['task_execution_allowed'])
        self.assertEqual(w.validate(approved).shards,1)
        for mutation in (lambda m:m['footprint']['cases'].append(copy.deepcopy(m['footprint']['cases'][0])),
            lambda m:m['footprint']['cases'][0].update(input_tokens=12289),
            lambda m:m['rows'].pop(),lambda m:m['profile']['model'].update(thinking=False)):
            changed=copy.deepcopy(approved);mutation(changed);w.seal(changed)
            with self.assertRaises(BCError):w.validate(changed)
    def test_stage_a_cannot_reuse_old_normal_qualification(self):
        from tests.support import ROOT
        with patch.object(p,'require_qualified'):
            with self.assertRaisesRegex(BCError,'controls'):
                w.build(ROOT,'control',{},'A',controls_record={'status':'passed'})
    def test_new_preflight_rejects_task_route_and_backend_injection(self):
        from beyond_consensus.experiments.runner import run_manifest
        m=self.candidate()
        with self.assertRaises(BCError):run_manifest(m,Path('/unused'),Path('.'),backend=object())
    def test_staging_dry_run_is_exact_and_does_not_download(self):
        from beyond_consensus.models.worker_staging import stage
        assets=dict(profile=p.profile('coder'),checkpoint_bytes=123,files=[],license='apache-2.0')
        assets['metadata_id']=digest(assets)
        r=stage(assets,Path('/not-created'))
        self.assertEqual(r['maximum_bytes'],123);self.assertEqual(r['decision'],'pending')
        with self.assertRaises(BCError):stage(assets,Path('/not-created'),r)
    def test_preflight_failure_has_nonzero_cli_outcome_and_standard_report(self):
        from beyond_consensus import cli
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'preflight.json'
            args=SimpleNamespace(command='gpu-preflight',manifest=Path('/manifest'),model_lock=Path('/lock'),output=target)
            with patch.object(cli,'read_json',return_value={'schema':w.SCHEMA,'stage':'Q'}),patch.object(w,'run',return_value=[{'status':'incomplete'}]):
                result=cli.dispatch(args)
            self.assertTrue(result['command_failed']);self.assertTrue(json.loads(target.read_text())['command_failed'])
    def test_allocation_uses_parent_once_and_marks_unknown_gpus(self):
        m=self.candidate();receipt={'output':'/run','job_id':'123'}
        text='123_0|COMPLETED|0:0|10|cpu=4,gres/gpu=1|00:00:04|\n123_0.batch|COMPLETED|0:0|10|cpu=4,gres/gpu=1|00:00:04|\n'
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=text)):
            r=w.allocation(m,receipt,'/run');self.assertEqual(r['whole_allocation_gpu_seconds'],10);self.assertEqual(len(r['rows']),1)
        with patch('subprocess.run',return_value=SimpleNamespace(stdout=text.replace(',gres/gpu=1',''))):
            self.assertEqual(w.allocation(m,receipt,'/run')['status'],'incomplete')


if __name__=='__main__':unittest.main()
