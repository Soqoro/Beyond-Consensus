"""Prospective sampled schedules retain semantic failures, unknowns and gates."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse import sampled_cohort as sampled,v2,cohort
from reporecourse.common import digest,Rejected
from reporecourse.tasks import load_task,private_task
from reporecourse.engine import ScriptedWorker


def fixture():
    public=load_task('synthetic-nullable',Path('/missing'))[1]
    config=v2.configuration(7,planning_lane='authored_diagnostic',execution_contract='plan_scoped_v1',planner_output_cap=6144,interface_profile=sampled.PROFILE)
    return public,[v2.authored_plan(public,config,x) for x in ('independent','grouped','shared')]


def catalog_fixture():
    public,plans=fixture();publics={};rows=[]
    for task in sampled.TASKS:
        pub=deepcopy(public);pub['id']=task;publics[task]=pub
        candidates=[dict(candidate_id=digest(p),plan=p,recipe='test_fixture',canonical_key=digest(p),
            qualification={'status':'cpu_qualified_reference'}) for p in plans]
        rows.append(dict(task=task,source_group='test-fixture-only',public_hash=digest(pub),
            candidates=candidates,selected=[p['candidate_id'] for p in candidates]))
    catalog=dict(schema='rr-organization-catalog-v1',tasks=rows,offline_costs={'cpu_seconds':1})
    return {**catalog,'catalog_id':digest(catalog)},publics


class SampledSchedule(unittest.TestCase):
    def setUp(self):
        # Synthetic contracts exercise scheduling, not real-task certification.
        checker=patch.object(sampled,'qualified_candidate',side_effect=lambda c,*args:
            c.get('qualification',{}).get('status')=='cpu_qualified_reference')
        checker.start();self.addCleanup(checker.stop)

    def test_fixed_full_scope_and_meaningful_targets(self):
        catalog,publics=catalog_fixture();p=sampled.proposal(catalog,publics)
        self.assertEqual(len(p['configurations']),6);self.assertEqual(p['planned_conditions'],12)
        self.assertEqual(p['maximum_logical_tokens'],1200000)
        self.assertEqual(p['maximum_charged_cpu_seconds'],14400)
        self.assertFalse(p['task_execution_allowed']);self.assertEqual(p['status'],'blocked')
        for item in p['configurations']:
            c=item['configuration'];s=item['schedule'];cohort.check_schedule(c,s)
            self.assertEqual(c['config']['reserve_rule'],'none')
            self.assertEqual(s['frozen']['physical_generation_count'],0)
            rows=s['branches']['rows'];self.assertEqual([r['track'] for r in rows],['clean','F'])
            self.assertIn(rows[1]['target'],rows[1]['eligible'])
            self.assertNotIn('w6',rows[1]['eligible'])
            self.assertNotIn('target',s['frozen']['request']['planner_input'])
        a=sampled.approval_template(p)
        self.assertEqual(a['decision'],'pending');self.assertEqual(a['maximum_execution_branches'],12)

    def test_missing_or_unqualified_slots_never_shrink_denominator(self):
        catalog,publics=catalog_fixture()
        catalog['tasks'][0]['selected'].pop()
        catalog['tasks'][1]['candidates'][0]['qualification']['status']='blocked_prerequisite'
        catalog['catalog_id']=digest({k:v for k,v in catalog.items() if k!='catalog_id'})
        p=sampled.proposal(catalog,publics)
        self.assertEqual(len(p['missing_slots']),2);self.assertEqual(p['planned_conditions'],12)
        self.assertEqual(len(p['configurations']),4)
        report=sampled.analyze(p,{})
        self.assertEqual(report['by_task'][sampled.TASKS[0]]['clean']['planned'],3)
        self.assertIsNone(report['by_task'][sampled.TASKS[0]]['clean']['complete_rate'])

    def test_ordinary_clean_failure_preserves_fault_and_pause_retains_unrun(self):
        public,plans=fixture();c=sampled.configuration(public['id'],plans[0]);s=sampled.schedule(c,public)
        calls=[]
        def execute(manifest,branch):
            calls.append(branch['track'])
            return dict(status='completed',success=False,contract_conformant=True)
        r=cohort.run_scheduled(c,s,execute,lambda *args:None)
        self.assertEqual(calls,['clean','F']);self.assertEqual(r['status'],'completed')
        def fail(manifest,branch):raise RuntimeError('injected')
        r=cohort.run_scheduled(c,s,fail,lambda *args:None)
        self.assertEqual([b['status'] for b in r['branches']],['infrastructure_failed','unrun'])

    def test_actual_engine_receives_scoped_assignments(self):
        public,plans=fixture();c=sampled.configuration(public['id'],plans[1]);s=sampled.schedule(c,public)
        worker=ScriptedWorker({'organization':'grouped','actions':[]})
        saved=[]
        r=sampled.run_reference_schedule(c,s,public,private_task('synthetic-nullable'),worker,
            lambda name,value:saved.append(name))
        self.assertEqual(len(r['branches']),2)
        for b in r['branches']:
            self.assertEqual(b['execution_contract'],'plan_scoped_v1')
            assignments=[e for e in b['events'] if e['type']=='assignment_start' and e['stage']=='primary']
            self.assertEqual(len(assignments),1)
            self.assertEqual(assignments[0]['unit'],plans[1]['units'][0]['id'])
        self.assertEqual(saved[0],'schedule')
        worker.mode='model'
        with self.assertRaisesRegex(Rejected,'gpu_execution_adapter_pending'):
            sampled.run_reference_schedule(c,s,public,{},worker,lambda *args:None)

    def test_tampering_unknown_records_and_pending_evidence_remain_closed(self):
        catalog,publics=catalog_fixture();p=sampled.proposal(catalog,publics,
            worker_lock={'status':'passed'},normal_qualification={'status':'passed_observed_cases'})
        self.assertFalse(p['task_execution_allowed'])
        self.assertIn('guarded_normal_gpu_evidence_requires_exact_compatibility_review',p['blockers'])
        with self.assertRaises(Rejected):sampled.analyze(p,{'unknown':{}})
        row=deepcopy(p['configurations'][0]['configuration']);row['config']['reserve_rule']='tuned'
        with self.assertRaises(Rejected):cohort.check_configuration(row)
        catalog['tasks'][0]['selected'][1]=catalog['tasks'][0]['selected'][0]
        catalog['catalog_id']=digest({k:v for k,v in catalog.items() if k!='catalog_id'})
        with self.assertRaises(Rejected):sampled.proposal(catalog,publics)

    def test_read_only_metrics_include_failures_unknowns_and_fault_identity(self):
        catalog,publics=catalog_fixture();p=sampled.proposal(catalog,publics)
        item=p['configurations'][0];c=item['configuration'];s=item['schedule']
        record=cohort.run_scheduled(c,s,lambda m,b:dict(status='completed',success=False,
            task_correct=False,contract_conformant=True,resource_profile={'actual_tokens':100,'cpu_cap_debit':1}),lambda *args:None)
        report=sampled.analyze(p,{c['configuration_id']:record})
        self.assertEqual(report['configurations'][0]['branch_metrics'][1]['total_tokens'],100)
        self.assertEqual(report['by_task'][c['task']]['F']['known'],1)
        self.assertIsNone(report['by_task'][c['task']]['F']['complete_rate'])
        record['branches'][1]['target']='w6'
        with self.assertRaises(Rejected):sampled.analyze(p,{c['configuration_id']:record})


class EvidenceBindings(unittest.TestCase):
    def test_exact_reference_binding_and_each_negative_required(self):
        from reporecourse.organization_sampler import sample,reference_witness
        from reporecourse.tasks import ROOT
        from reporecourse.common import load
        from reporecourse.qualification import implementation_hashes
        from reporecourse.track_f_controls import PINS
        task=sampled.TASKS[0];public=load(ROOT/'rich'/'public'/(task+'.json'))
        entry=sample(task,public);candidate=entry['candidates'][0];private=private_task(task)
        from reporecourse.tasks import catalog as task_catalog
        card=next(x for x in task_catalog(ROOT/'rich')['tasks'] if x['id']==task)
        entry.update(source_available=True,public_hash=digest(public),card_hash=digest(card),source_group=card['source_group'])
        obligations={r['id']:True for r in public['required_outputs']}
        candidate['qualification']=dict(status='cpu_qualified_reference',evidence='scripted_reference_only',
            plan_id=digest(candidate['plan']),private_binding_hash=digest(reference_witness(candidate,private)),
            reference_implementation_hashes=implementation_hashes(),private_task_hash=digest(private),
            runtime_versions=dict(PINS),model_executed=False,task_execution_allowed=False,
            execution_status='completed',contract_conformant=True,source_integrity=True,reset_repeat_identical=True,
            evaluation={'status':'available','success':True,'obligations':obligations},
            negative_controls=[dict(obligation=o,mutation=m,detected=True) for o in obligations for m in ('missing','wrong_semantics')])
        cat={'implementation_hashes':implementation_hashes()}
        with patch.object(sampled,'runtime_versions',return_value=dict(PINS)):
            self.assertTrue(sampled.qualified_candidate(candidate,task,public,entry,cat))
            candidate['qualification']['negative_controls'].pop()
            self.assertFalse(sampled.qualified_candidate(candidate,task,public,entry,cat))

    def test_status_alone_or_rehashed_changed_plan_does_not_qualify(self):
        from reporecourse.organization_sampler import sample
        from reporecourse.tasks import ROOT
        from reporecourse.common import load
        from reporecourse.qualification import implementation_hashes
        task=sampled.TASKS[0];public=load(ROOT/'rich'/'public'/(task+'.json'))
        candidate=sample(task,public)['candidates'][0]
        candidate['qualification']={'status':'cpu_qualified_reference'}
        catalog={'implementation_hashes':implementation_hashes()}
        self.assertFalse(sampled.qualified_candidate(candidate,task,public,{},catalog))
        candidate['plan']['units'][0]['description']='Changed public instruction'
        candidate['plan_id']=digest(candidate['plan'])
        self.assertFalse(sampled.qualified_candidate(candidate,task,public,{},catalog))

class SavedRecordCLI(unittest.TestCase):
    def test_large_catalog_proposal_and_result_records_round_trip(self):
        import json
        import subprocess
        from tempfile import TemporaryDirectory
        from reporecourse.common import load,write_new
        root=Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            directory=Path(directory)
            # Synthetic offline evidence exercises serialization, not task qualification.
            catalog=dict(schema='rr-organization-catalog-v1',tasks=[],
                offline_costs={'synthetic_record_padding':'x'*(3*1024*1024)})
            catalog['catalog_id']=digest(catalog)
            path=directory/'catalog.json';write_new(path,catalog)
            with self.assertRaisesRegex(Rejected,'file_size'):load(path)
            proposal_path=directory/'proposal.json'
            result=subprocess.run([sys.executable,'-I','-S',str(root/'scripts/prepare_rr_sampled_cohort.py'),
                '--catalog',str(path),'--sources',str(directory/'missing-sources'),
                '--output',str(proposal_path),'--approval-template',str(directory/'approval.json')],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            proposal=json.loads(proposal_path.read_text())
            self.assertEqual(proposal['catalog'],catalog)
            self.assertEqual(proposal['planned_conditions'],12)
            self.assertFalse(proposal['task_execution_allowed'])
            self.assertEqual(len(proposal['missing_slots']),6)
            self.assertGreater(proposal_path.stat().st_size,2097152)
            records=directory/'records.json'
            records.write_text('{}'+' '*(3*1024*1024))
            output=directory/'analysis.json'
            result=subprocess.run([sys.executable,'-I','-S',str(root/'scripts/analyze_rr_sampled_cohort.py'),
                '--proposal',str(proposal_path),'--records',str(records),'--output',str(output)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(output.read_text())
            self.assertEqual(len(report['missing_slots']),6)
            self.assertTrue(all(t['clean']['complete_rate'] is None for t in report['by_task'].values()))

    def test_saved_record_cli_keeps_strict_json_rejections(self):
        import subprocess
        from tempfile import TemporaryDirectory
        root=Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as directory:
            directory=Path(directory);path=directory/'catalog.json'
            for raw in ('{"tasks":[],"tasks":[]}', '{"value":NaN}', '{"value":Infinity}', '[]'):
                path.write_text(raw)
                result=subprocess.run([sys.executable,'-I','-S',str(root/'scripts/prepare_rr_sampled_cohort.py'),
                    '--catalog',str(path),'--sources',str(directory/'missing'),
                    '--output',str(directory/'proposal.json'),'--approval-template',str(directory/'approval.json')],
                    capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((directory/'proposal.json').exists())


if __name__=='__main__':unittest.main()
