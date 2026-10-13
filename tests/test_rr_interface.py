"""Public interface revision controls: no task-solution repair or GPU claims."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import interface as I, v2, cohort
from reporecourse.common import Rejected,digest
from reporecourse.action_schema import schema_v2
from reporecourse.runtime import Environment
from reporecourse.resources import Resources
from reporecourse.engine import worker_messages
from beyond_consensus.models.action_schema import validate_action
from beyond_consensus.experiments import rr_cohort as adapter, rr_open_footprint as footprint
from beyond_consensus.util import BCError
from tests.test_reporecourse import optional
ROOT=Path(__file__).resolve().parents[1]


def config():
    return v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1',planner_output_cap=6144,interface_profile=I.PROFILE)


def public():
    return dict(id='neutral',family='api_schema',request='Public neutral contract',sources={},examples=[],required_outputs=[dict(id='report',format='sql')])


class PublicContracts(unittest.TestCase):
    def test_example_and_alternative_graphs(self):
        p=I.example_plan();v2.validate_work_plan(p,public(),config())
        self.assertEqual(p['units'][0]['outputs'],[])
        p['units'][0]['worker']='w6';v2.validate_work_plan(p,public(),config())
        v2.validate_work_plan(v2.requirement_plan(public(),config()),public(),config())
        self.assertNotIn('interface_profile',v2.configuration())

    def test_actionable_output_error_and_unrelated_defects(self):
        p=I.example_plan();p['units'][0]['outputs']=['invented_rows']
        with self.assertRaises(Rejected) as ctx:v2.validate_work_plan(p,public(),config())
        f=ctx.exception.public_feedback['findings'][0]
        self.assertEqual(f['path'],'units[0].outputs[0]');self.assertEqual(f['expected'],{'permitted_terminal_ids':['report']})
        p['units'][0]['outputs']=[];p['units'][1]['consumes']['rows']['artifact']='absent'
        with self.assertRaisesRegex(Rejected,'consumer_interface'):v2.validate_work_plan(p,public(),config())
        p=I.example_plan();p['units'][0].update(depends=['deliver'],consumes={'cycle':dict(unit='deliver',artifact='invented_report',format='sql')})
        with self.assertRaisesRegex(Rejected,'cyclic_plan'):v2.validate_work_plan(p,public(),config())

    def test_typed_envelopes_keep_valid_program_space(self):
        mode=I.mode('json')
        for a in I.publications():validate_action(json.dumps(a),mode)
        for content in (True,False,{'type':'array','items':{'type':'object','properties':{'free_name':{'$ref':'rr:bound'}}}}, {'additionalProperties':False}):
            a=deepcopy(I.publications()[0]);a['content']=content;validate_action(json.dumps(a),mode)
        for a in I.publications()[:2]:
            for content in ('{}',[],None,3):
                a=deepcopy(a);a['content']=content
                with self.assertRaises(BCError):validate_action(json.dumps(a),mode)
        a=deepcopy(I.publications()[1]);a['content']={'fields':{'output_schema':{}}}
        with self.assertRaises(BCError):validate_action(json.dumps(a),mode)
        # Legacy envelopes remain permissive; runtime still rejects these strings.
        a['content']='{}';validate_action(json.dumps(a),'reporecourse-json-scoped-v1-pool-7')

    def test_public_terminal_enum_keeps_helper_artifact_ids_open(self):
        s=schema_v2(I.mode('plan'),['report'])
        unit=s['anyOf'][1]['properties']['plan']['properties']['units']['items']
        self.assertEqual(unit['properties']['outputs']['items'],{'enum':['report']})
        self.assertEqual(unit['properties']['outputs'].get('minItems',0),0)
        self.assertNotIn('enum',unit['properties']['produces'])
        self.assertNotEqual(digest(s),digest(schema_v2(I.mode('plan'),['other'])))
        validate_action(json.dumps({'tool':'submit_plan','plan':I.example_plan()}),I.mode('plan'))

    def test_actual_rejections_and_legacy_categories(self):
        p=public();p['required_outputs']=[]
        for revised in (False,True):
            env=Environment(p,interface_profile=I.PROFILE if revised else None)
            try:
                for fmt,bad,code in [('schema','{}','content_type'),('schema',[],'content_type'),
                    ('schema',{'properties':{'x':{'pattern':'x'}}},'unsupported_schema_keyword'),
                    ('mapping',{'fields':{'output_schema':{}}},'mapping_missing_field')]:
                    with self.assertRaises(Rejected) as ctx:env.publish('w0','neutral',fmt,bad,{},[])
                    self.assertEqual(str(ctx.exception),code if revised else 'schema_keyword' if fmt=='schema' else 'mapping_contract')
                    if revised:
                        f=ctx.exception.public_feedback['findings'][0]
                        if code=='unsupported_schema_keyword':self.assertEqual(f['path'],'content.properties.x.pattern')
                self.assertFalse(env.artifacts)
                for a in I.publications()[:2]:env.action('w0',a)
                self.assertEqual(len(env.artifacts),2)
            finally:env.close()

    def test_shared_worker_contract_primary_and_recovery(self):
        p=public();p['private_canary']='SECRET_EVALUATOR_SENTINEL';c=config()
        self.assertNotIn('SECRET_EVALUATOR_SENTINEL',json.dumps(v2.planner_input(p,c)))
        env=Environment(p,workers=c['workers'],execution_contract='plan_scoped_v1',plan=I.example_plan(),interface_profile=I.PROFILE)
        try:
            u=I.example_plan()['units'][0];systems=[]
            for stage in ('primary','repair'):
                if stage=='repair':env.events.append(dict(type='public_alarm',obligations=['report']))
                env.scopes.begin(u,'w0',stage);env.assignment['w0']=u
                obs=env.observation('w0');systems.append(worker_messages(obs,[])[0])
                self.assertFalse(obs['interface_delivery']['truncated'])
                self.assertNotIn('SECRET_EVALUATOR_SENTINEL',json.dumps(systems[-1]))
            self.assertEqual(*systems)
        finally:env.close()

    def test_assignment_publication_feedback_preserves_denial(self):
        for revised in (False,True):
            env=Environment(public(),workers=config()['workers'],execution_contract='plan_scoped_v1',
                plan=I.example_plan(),interface_profile=I.PROFILE if revised else None)
            try:
                unit=I.example_plan()['units'][0];env.scopes.begin(unit,'w0','primary')
                obs=env.observation('w0')
                self.assertEqual('publication_contract' in obs,revised)
                if revised:self.assertEqual(obs['publication_contract']['artifacts'][0]['permitted_obligations'],[])
                a=dict(tool='publish',name='invented_rows',format='sql',obligations=['invented_rows'],bindings={})
                with self.assertRaises(Rejected) as ctx:env.scopes.authorize('w0',a)
                self.assertEqual(str(ctx.exception),'scope_denied')
                self.assertEqual(hasattr(ctx.exception,'public_feedback'),revised)
                if revised:self.assertEqual(ctx.exception.public_feedback['findings'][0]['code'],'publication_obligation')
                a['obligations']=[];env.scopes.authorize('w0',a)
                a['name']='report'
                with self.assertRaises(Rejected) as ctx:env.scopes.authorize('w0',a)
                if revised:self.assertEqual(ctx.exception.public_feedback['findings'][0]['path'],'name')
                self.assertFalse(env.artifacts)
            finally:env.close()

    def test_checkpoint_diagnostics_never_infer_final_score(self):
        b=dict(status='resource_exhausted',success=False,checkpoint={'engine':dict(status='resource_exhausted',
            environment=dict(triggered=False,bound={},events=[]),failures=[{'category':'cpu_cap'}],
            trajectories=[dict(action=dict(tool='publish',format='schema'),tool_result={'error':'scope_denied'})])})
        before=deepcopy(b);d=cohort.offline_diagnostics(b)
        self.assertEqual(d['trace_source'],'checkpoint');self.assertEqual(d['publication_rejections'],{'scope_denied':1})
        self.assertFalse(d['checkpoint_intervention']);self.assertIsNone(d['conformant'])
        self.assertIsNone(d['final_gated_obligations']);self.assertEqual(b,before)
        b['trajectories']=[]
        self.assertEqual(cohort.offline_diagnostics(b)['publication_attempts'],0)

    def test_new_manifest_bound_scope_and_legacy_task_hashes(self):
        old=adapter.build(ROOT,'/nonexistent',adapter.UNREVIEWED_LANE)
        new=adapter.build(ROOT,'/nonexistent',adapter.UNREVIEWED_LANE,interface_profile=I.PROFILE)
        adapter.validate(new)
        self.assertEqual(old['task_bindings'],new['task_bindings'])
        self.assertNotEqual(old['experiment_id'],new['experiment_id'])
        self.assertEqual(new['maximum_execution_branches'],16)
        self.assertEqual(new['maximum_logical_tokens'],1600000)
        self.assertEqual(new['maximum_charged_cpu_seconds'],19200)
        self.assertFalse(new['task_execution_allowed'])
        for a,b in zip(old['configurations'],new['configurations']):
            c=deepcopy(b['config']);c.pop('interface_profile');self.assertEqual(a['config'],c)
        self.assertTrue(all(r['decision']=='pending' for r in new['evidence']['reviews'].values()))
        bad=deepcopy(new);bad['interface_bindings']['examples']='changed';adapter.seal(bad)
        with self.assertRaises(BCError):adapter.validate(bad)

    def test_target_rule_not_fixed_w1(self):
        p=public();row=cohort.configuration('neutral','requirement_level',interface_profile=I.PROFILE)
        req=v2.request(p,row['config']);plan=I.example_plan()
        for u in plan['units']:u['worker']='w6'
        frozen=v2.freeze(req,p,plan,Resources(100000,1200),[],'scripted_mock')
        schedule=cohort.schedule(row,frozen)
        self.assertEqual([r['target'] for r in schedule['branches']['rows']],[None,'w6'])

    def test_offline_partial_checks_and_unknown_no_score_change(self):
        b=dict(status='completed',success=False,state={'bound':{'a':'v'},'events':[dict(type='publish',obligations=['a'])]},evaluation={'obligations':{'a':False,'b':False},'checks':[{'obligation':'a','passed':True},{'cross_output_consistency':True,'passed':False}]})
        original=deepcopy(b);d=cohort.offline_diagnostics(b)
        self.assertEqual(d['missing_obligations'],['b']);self.assertTrue(d['raw_per_output_checks'][0]['passed'])
        self.assertFalse(d['complete_at_budget']);self.assertEqual(b,original)
        b['evaluation'].pop('checks');self.assertIsNone(cohort.offline_diagnostics(b)['raw_per_output_checks'])

    def test_admission_diagnostic_keeps_rules_and_charge(self):
        r=Resources(100,10,diagnostics=True);r.reconcile_cpu('measured',0,9)
        with self.assertRaisesRegex(Rejected,'cpu_cap'):r.reserve_cpu(2)
        self.assertEqual(r.cpu_seconds,9);self.assertEqual(r.events[-1]['requested'],2)
        self.assertEqual(r.events[-1]['reason'],'insufficient_remaining_allowance')
        self.assertEqual(r.events[-1]['remaining_cpu'],1)

    def test_action_limit_is_recorded_without_changing_dispatch(self):
        from reporecourse.engine import Engine
        class Reader:
            def next_action(self,*args):return {'tool':'list_sources'}
        e=Engine(public(),Reader(),plan=I.example_plan(),v2=config(),max_actions=2)
        try:
            e.unit(e.plan['units'][0],'w0','primary')
            row=next(x for x in e.env.events if x['type']=='unit_end')
            self.assertEqual(row['termination_reason'],'action_limit')
            self.assertEqual(row['actions'],2)
            self.assertEqual(len(e.trajectories),2)
            self.assertFalse(e.env.artifacts)
        finally:e.env.close()

    def test_rejected_response_metadata_preserves_feedback_and_charges(self):
        from reporecourse.engine import Engine,ModelWorker
        for text,finish,category in (
            ('{"secret_key":1,"secret_key":2}','eos','duplicate_object_key'),
            ('{"tool":','length_limit','json_syntax'),
            ('not JSON','eos','json_syntax'),
        ):
            class Backend:
                def count_input(self,m):return 10
                def generate(self,*args):return SimpleNamespace(text=text,output_tokens=8,reasoning_tokens=2,
                    device_seconds=0,diagnostics={'finish_reason':finish,'constraint_complete':True})
            e=Engine(public(),ModelWorker(Backend()),plan=I.example_plan(),v2=config())
            try:
                e.unit(e.plan['units'][0],'w0','primary')
                self.assertEqual(len(e.trajectories),3)
                self.assertEqual(e.env.resources.actual_tokens,54)
                self.assertFalse(e.env.resources.reservations)
                for row in e.trajectories:
                    self.assertEqual(row['tool_result'],{'error':'malformed_json'})
                    d=row['response_diagnostic']
                    self.assertEqual(d['parse_failure'],category)
                    self.assertEqual(d['finish_reason'],finish)
                    self.assertEqual(d['constraint_complete'],True)
                    self.assertNotIn('secret_key',json.dumps(d))
                    self.assertLess(len(json.dumps(d)),1000)
                    self.assertEqual(len(d['response_sha256']),64)
                    self.assertNotIn('response_diagnostic',json.dumps(row['next_observation']))
                self.assertNotIn('response_sha256',json.dumps(e.histories))
                saved=e.checkpoint()
                report=cohort.offline_diagnostics(dict(checkpoint={'engine':saved},status='completed',success=False))
                self.assertEqual(report['rejected_response_categories'],{category:3})
            finally:e.env.close()

    def test_four_probes_only_and_no_task_content(self):
        rows=footprint.reliable_cases();self.assertEqual(len(rows),4)
        self.assertEqual([r['role'] for r in rows],['plan','json','json','json'])
        self.assertEqual(rows,footprint.reliable_cases())
        text=json.dumps(rows)
        for t in adapter.RICH_TASKS:self.assertNotIn(t,text)
        self.assertNotIn('SECRET_EVALUATOR_SENTINEL',text)
        for r in rows:validate_action(json.dumps(r['expected']),I.mode(r['role']))

    def test_revision_cost_and_grammar_binding_no_fallback(self):
        from beyond_consensus.models.base import Generation
        p=public();c=config();req=v2.request(p,c);bad=I.example_plan();bad['units'][0]['outputs']=['wrong']
        class Backend:
            context_limit=16384
            def __init__(self):self.calls=0;self.bindings=[]
            def count_input(self,messages):return 200
            def bind_public_plan(self,task,ids):self.bindings.append((task,ids))
            def generate(self,messages,cap,seed):
                self.calls+=1
                if self.calls==2:self.feedback=json.loads(messages[-1]['content'])
                return Generation(json.dumps({'tool':'submit_plan','plan':bad if self.calls==1 else I.example_plan()}),100,10,0,{})
        backend=Backend();f=v2.PromptedPlanner(backend,6144).run(req,p)
        self.assertEqual(f['status'],'valid');self.assertEqual(backend.bindings,[('neutral',['report'])])
        self.assertEqual(backend.feedback['findings'][0]['path'],'units[0].outputs[0]')
        self.assertEqual(f['planning_resources']['actual_tokens'],600)
        self.assertEqual(f['physical_generation_count'],2)
        with self.assertRaisesRegex(Rejected,'qualified_public_grammar_required'):
            v2.PromptedPlanner(SimpleNamespace(),6144).run(req,p)

    def test_v4_packet_disk_roundtrip_and_sequence(self):
        from unittest.mock import patch
        from tests.test_rr_open_footprint import FootprintTests
        q=dict(qualification_key='plan',packages={},thinking_template={'template_hash':'test'})
        lock={'decoder_qualification':q};model=adapter.model_settings(I.PROFILE)
        proposal=dict(schema='rr-open-engineering-proposal-v1',task_execution_allowed=False,campaign_allowed=False,
            worker_config={'model':model},planner_config={'model':dict(model,action_constraint=I.mode('plan'))})
        proposal['proposal_id']=digest(proposal)
        measure=lambda r,t:dict(input_tokens=300,action_tokens=100,grammar_accepted=True,rendered_input_ids_hash='fake')
        with patch.object(footprint.base,'check_locks'),patch.object(footprint.base,'source_revision',return_value='test-source'):
            packet=footprint.prepare(ROOT,proposal,lock,lock,measure,planner_output_cap=6144,interface_profile=I.PROFILE)
        packet=json.loads(json.dumps(packet,sort_keys=True));footprint.validate_packet(packet,measured=True)
        helper=FootprintTests();backend=helper.backend(packet);calls=[]
        backend.bind_public_plan=lambda task,ids:calls.append((task,ids))
        rows=footprint.sequence(packet,backend,lambda role:None,helper.memory)
        self.assertEqual(len(rows),4);self.assertTrue(all(r['passed'] for r in rows))
        self.assertEqual(calls,[(footprint.reliable_public()['id'],['report'])])
        packet['cases'][0]['expected']['plan']['units'][0]['outputs']=['invalid']
        packet['packet_id']=digest({k:v for k,v in packet.items() if k!='packet_id'})
        with self.assertRaises(BCError):footprint.validate_packet(packet,measured=True)


@unittest.skipUnless(optional(),'pinned compiler/schema child dependencies unavailable')
class CompilerContracts(unittest.TestCase):
    def test_supported_and_unsupported_examples_exact_child_feedback(self):
        from restricted_artifacts.sql_text import lower,capability
        from restricted_artifacts.sqlite_executor import FUNCTIONS
        import sqlite3
        self.assertEqual(set(capability()['function_arities']),set(FUNCTIONS))
        self.assertEqual(capability()['function_arities']['json_extract'],'1..8')
        # Authored literal-only control: SQLite accepts JSON_EXTRACT with no path.
        with sqlite3.connect(':memory:') as db:
            self.assertIsNone(db.execute("SELECT json_extract('{}')").fetchone()[0])
        self.assertEqual(lower("SELECT json_extract('{}') AS value",set(),diagnostics=True)['status'],'ok')
        for sql in capability()['examples']:
            self.assertEqual(lower(sql,{'demo'},diagnostics=True)['status'],'ok')
        for text,code,op in [('SELECT id FROM demo WHERE id IN (1,2)','unsupported_expression','In'),
            ('SELECT id FROM demo WHERE id NOT IN (1,2)','unsupported_expression','Not'),
            ('SELECT id FROM demo WHERE id BETWEEN 1 AND 2','unsupported_expression','Between'),
            ('SELECT CASE WHEN id = 1 THEN 2 END AS x FROM demo','case_else_required','Case')]:
            r=lower(text,{'demo'},diagnostics=True)
            self.assertEqual(r['status'],'rejected');self.assertEqual(r['public_diagnostic']['code'],code)
            self.assertEqual(r['public_diagnostic']['operator'],op)
            self.assertNotIn('public_diagnostic',lower(text,{'demo'}))
        r=lower('SELECT (',{'demo'},diagnostics=True);self.assertEqual(r['public_diagnostic']['code'],'sql_parse_rejected')
        self.assertIsNone(r['public_diagnostic']['operator'])
        self.assertEqual(lower('SELECT 0 AS wrong',set(),diagnostics=True)['status'],'ok')

    def test_schema_and_mapping_examples_execute_without_semantic_repair(self):
        from reporecourse.schema_runtime import execute
        schema=I.publications()[0]['content'];mapping=I.publications()[1]['content']
        self.assertTrue(execute(dict(operation='validate',schema=schema,value={'label':'x'},registry={}))['valid'])
        self.assertFalse(execute(dict(operation='validate',schema=schema,value={'label':5},registry={}))['valid'])
        self.assertEqual(execute(dict(operation='map',program=mapping,value={'name':'x'},registry={}))['output'],{'label':'x'})
