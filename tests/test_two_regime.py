import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from bc_phase2 import two_regime as g, two_regime_launch as launch, two_regime_results as results
from bc_phase2.model import Invalid,digest
from test_medqa_worker_launch import Fake
import test_prospective_cohort as fixtures


class TwoRegime(unittest.TestCase):
    def test_reservations_and_budget(self):
        frozen=g.frozen()
        self.assertEqual(frozen,g.reserve())
        slots=frozen['slots']
        self.assertEqual([len(slots),sum(len(s['candidates']) for s in slots[:12]),sum(len(s['candidates']) for s in slots)],[28,106,240])
        for ds in g.LABELS:
            ids=[v for s in slots if s['dataset']==ds for v in s['candidates']]
            self.assertEqual(len(set(ids)),120)
            self.assertTrue(set(ids).isdisjoint(frozen['historical_ids'][ds]))

    def example(self,n=4,regime='extra'):
        pubs,_,dis=fixtures.Prospective().contracts()
        dis={k:v for k,v in dis.items() if v['status']=='admitted'}
        slot=dict(id='math500-n4-extra',dataset='math500',n=n,regime=regime,target_m=n if regime=='equal' else (3*n+1)//2,candidates=list(dis))
        return pubs,dis,slot

    def test_prefix_exhaustion_and_freeze(self):
        _,dis,slot=self.example()
        first=next(iter(dis))
        self.assertEqual(g.select(slot,{first:dis[first]})['status'],'next_candidate')
        self.assertEqual(g.select(slot,dis)['m'],5)
        more=dict(slot,candidates=slot['candidates']+['unrun'])
        self.assertEqual(g.select(more,dis)['status'],'next_candidate')
        equal=dict(slot,regime='equal',target_m=4)
        self.assertEqual(g.select(equal,dis)['status'],'construction_gap')
        with patch.object(g,'neutral',side_effect=TimeoutError):
            self.assertEqual(g.select(slot,dis)['status'],'construction_unresolved')
        with self.assertRaises(Invalid):
            g.select(dict(more,target_m=5),dict(dis,unrun=dict(status='invalid')))

    def test_variant_binding_and_shared_control(self):
        pubs,dis,slot=self.example(n=5,regime='equal')
        chosen=g.select(slot,dis)
        none=[dict(source_id=s,decision='outside_domain',rationale='fixture',reviewer='fixture') for s in dis]
        w=g.wave(slot,chosen,none)
        procedures={t['id']:t['responsibility'] for t in chosen['components'][0]['tasks']}
        procedures['t0']+=' Use an inequality proof.'
        a=g.wave(slot,chosen,[dict(none[0],decision='admit_procedure',provenance='reviewer-authored',
                                  preserves_responsibilities=True,solution_free=True,procedures=procedures)])
        self.assertEqual(a['bundles'][0]['neutral_seed'],chosen['neutral_seed'])
        def owners(w):
            return {(c['source_id'],t['id']):w['bundles'][0]['neutral']['ownership'][c['namespace']+'_'+t['id']]
                    for c in w['components'] for t in c['tasks']}
        self.assertEqual(owners(a),owners(w))
        c=a['components'][0]
        p=g.worker_request(c,g.mode_task(c,c['tasks'][0],'A1'),'A1',pubs,{})
        self.assertIn('inequality proof',p['payload']['responsibility'])
        self.assertEqual(len(a['profile_coverage']),8)
        with tempfile.TemporaryDirectory() as tmp:
            journal=launch.worker.Journal(Path(tmp)/'journal',Fake(),w['wave_id'],lambda:None,limits=w['limits'])
            def tied(domain,**kwargs):
                return dict(status='MOCK',candidate=kwargs['seed'])
            r=g.run_wave(journal,pubs,tmp,w,tied)
        cond=r['conditions'][0]
        self.assertTrue(cond['shared_observations'])
        self.assertEqual(cond['paired_saving'],'0')
        self.assertEqual(len(cond['methods']['NEUTRAL']['repairs']),5)
        self.assertEqual(r['totals']['calls'],5+5+cond['methods']['NEUTRAL']['repair_calls'])
        summary=results.summarize(dict(wave=w,cell=slot['id'],planning_overhead=dict(calls=2,actual_tokens=40)),r)
        self.assertIsNone(summary['methods']['JOINT']['repair_accuracy'])
        failed=deepcopy(cond['methods']['NEUTRAL']['repairs'][0])
        failed.update(store={},status='unusable_artifact',full_cost=None,complete=False)
        row=results.session(failed,w['components'],lambda *_:None)
        self.assertEqual((row['accuracy'],row['denominator'],row['full_cost']),(0,2,None))
        self.assertIsNone(results.session(dict(status='no_clean_snapshot'),w['components'],None)['accuracy'])

    def test_requires_exact_permission(self):
        m=dict(scope_digest='frozen',scope={})
        p=launch.Stage(dict(key='prefix'))
        with patch.object(p,'validate_manifest',return_value={'family_review':{'decision':'clear'}}):
            a=dict(schema='prefix-approval',scope_digest='frozen',decision='approved',reviewer='fixture',
                   reviewed_at='test',statement_transmission_authorized=True,GPU_spending_authorized=True)
            self.assertTrue(p.approve(m,a)['release_digest'])
            for update in (dict(scope_digest='previous'),dict(GPU_spending_authorized=False)):
                with self.assertRaises(Invalid):
                    p.approve(m,dict(a,**update))

    def test_first_scoped_prepare_without_gpu(self):
        from contextlib import ExitStack
        import json
        import sys
        slot=launch.cell('math500-n4-extra')
        with tempfile.TemporaryDirectory() as tmp,ExitStack() as stack:
            root=Path(tmp)
            path=root/'public.json'
            records=[dict(id=s,problem='Synthetic question '+str(i)) for i,s in enumerate(slot['candidates'])]
            path.write_text(json.dumps(records))
            parent=dict(model={'non_thinking_verification':{'template_hash':'fake'}},
                source_package=dict(path=str(path),sha256=launch.local.file_hash(path)),
                scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},
                cluster=dict(partition='HPCAIq',memory_gb=128,python=sys.executable))
            stack.enter_context(patch.object(launch,'anchor',return_value=parent))
            stack.enter_context(patch.object(launch,'load_tokenizer',return_value=object()))
            stack.enter_context(patch.object(launch,'identity',return_value={'synthetic':'hash'}))
            stack.enter_context(patch.object(launch.screen,'render_request',side_effect=lambda tok,req,h:dict(
                payload_digest=req['payload_digest'],rendered_ids_digest='a'*64,input_tokens=100)))
            dep=dict(packages=launch.base.EXPECTED_PACKAGES,solver_importable=True,python=str(Path(sys.executable).resolve()))
            stack.enter_context(patch.object(launch.base,'deployment',return_value=dep))
            manifest=launch.prepare(root,slot,[],None,[],root/'scope','PartitionName=HPCAIq State=UP')
            s=manifest['scope']
            stage=launch.Stage(s)
            self.assertEqual(s['source_ids'],slot['candidates'][:1])
            self.assertEqual(s['limits']['maximum_calls'],1)
            a=dict(schema=stage.KEY+'-approval',scope_digest=manifest['scope_digest'],decision='approved',
                   statement_transmission_authorized=True,GPU_spending_authorized=True,reviewer='fixture',reviewed_at='now',
                   family_review=dict(card_digest=s['card_digest'],decision='blocked',reviewer='fixture',rationale='fixture'))
            with self.assertRaises(Invalid):
                stage.approve(manifest,a)
            a['family_review']['decision']='clear'
            release=stage.approve(manifest,a)
            self.assertEqual(stage.validate_release(release),s)
            stage.submission_check(release,{})
            with self.assertRaises(Invalid):
                stage.submission_check(release,{'composite_math_attempts':{stage.KEY:{'state':'submission_uncertain'}}})

    def test_binary_profile_prices_and_selected_requests(self):
        pubs,dis,slot=self.example()
        chosen=g.select(slot,dis)
        c=chosen['components'][0]
        procedures={t['id']:t['responsibility']+' Alternative procedure.' for t in c['tasks']}
        w=g.wave(slot,chosen,[dict(source_id=c['source_id'],rationale='fixture',reviewer='fixture',
            decision='admit_procedure',preserves_responsibilities=True,solution_free=True,
            provenance='reviewer-authored',procedures=procedures)])
        with tempfile.TemporaryDirectory() as tmp:
            f=Fake()
            j=launch.worker.Journal(Path(tmp)/'journal',f,w['wave_id'],lambda:None,limits=w['limits'])
            def select_a1(domain,**kwargs):
                seed=kwargs['seed']
                self.assertEqual(domain['unit'],'profile_input_plus_generated_tokens')
                candidate=g.spec.explicit_selection(domain,dict.fromkeys(seed['A'],'A1'),{},seed['ownership'])
                return dict(status='MOCK',candidate=candidate)
            r=g.run_wave(j,pubs,tmp,w,select_a1)
        cond=r['conditions'][0]
        self.assertTrue(cond['changed']['A'])
        self.assertFalse(cond['shared_observations'])
        self.assertFalse(cond['changed']['topology'])
        attempts=f.calls
        self.assertTrue(any('Alternative procedure.' in a['responsibility'] for a in attempts))
        self.assertFalse(any('owner' in a or 'method' in a for a in attempts))
        self.assertEqual(len(cond['methods']['JOINT']['repairs']),4)

    def test_original_plan_journals_drive_first_exact_pair(self):
        import json
        slot=launch.cell('math500-n4-extra')
        ids=slot['candidates']
        public={sid:dict(id=sid,problem='Synthetic statement '+str(i)) for i,sid in enumerate(ids)}
        entries=[]
        with tempfile.TemporaryDirectory() as tmp:
            for rank,sid in enumerate(ids[:2]):
                card=launch.review_card(slot,sid,public)
                family=dict(card_digest=card['card_digest'],decision='clear',reviewer='fixture',rationale='fixture')
                run=Path(tmp)/str(rank)
                execution=run/'execution'
                execution.mkdir(parents=True)
                scope=dict(key=launch.key(slot,sid),history=deepcopy(entries),family_review=None)
                release=dict(manifest=dict(scope=scope,scope_digest=digest(scope)),approval=dict(family_review=family))
                (run/'manifest.json').write_text(json.dumps(dict(release=release)))
                tasks=[dict(id='T'+str(i+1),responsibility='Synthetic computation',
                            required_inputs=['problem_statement'] if not i else ['T'+str(i)],produces='synthetic result') for i in range(3)]
                raw=json.dumps(dict(schema=g.pipeline.natural.VERSION,source_id=sid,status='decomposed',
                                    tasks=tasks,final_assembly='[T3]'))
                class Planner:
                    binding={'evidence':'synthetic_mock'}
                    def render(self,req):
                        return dict(payload=req['payload'],input_tokens=80)
                    def generate(self,rendered):
                        return dict(input_tokens=80,output_tokens=30,finish_reason='eos',boundary_error=None,final_text=raw)
                journal=launch.worker.Journal(execution/'journal',Planner(),digest(scope),lambda:None,
                                              limits=dict(maximum_calls=1,wall_seconds=3600,token_cap=16384))
                c=launch.cohort(slot,public)
                c['blocks'][0]['records']=[c['blocks'][0]['records'][rank]]
                rows=g.pipeline.plan_block(journal,c,1,public,execution/'planning')
                # Fixture uses the production on-disk shape; it never enters the live registry.
                (execution/'result.json').write_text(json.dumps(dict(evidence='real_prospective_planner',rows=rows,
                                                                  totals=journal.snapshot()['totals'])))
                contract=dict(decision='admitted',reviewer='fixture',reviewer_kind='human',reviewed_at='fixture',
                              public_digest=digest(public[sid]),plan_digest=digest(raw),substantive_no_answer_leakage=True,
                              tasks=[dict(id='t'+str(i),responsibility='Synthetic operation',parents=['t'+str(i-1)] if i else [],
                                    fields=['derivation','artifact'] if i<2 else ['justification','final_answer']) for i in range(3)],
                              outputs=['t2'])
                entries.append(dict(source_id=sid,family_review=family,run=str(run),decision='admitted',contract=contract))
                step,overhead=launch.history(slot,public,entries)
                self.assertEqual(overhead,dict(calls=rank+1,actual_tokens=(rank+1)*110))
            self.assertEqual((step['status'],step['n'],step['m'],step['q']),('bundle_frozen',4,6,2))
            with self.assertRaises(Invalid):
                launch.history(slot,public,entries+[dict(source_id=ids[2])])
