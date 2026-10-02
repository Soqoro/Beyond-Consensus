"""Adapter tests use fabricated evidence/backends; never model competence evidence."""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments import rr_v2_competence as c
from beyond_consensus.experiments.manifest import validate_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.util import BCError, digest, atomic_json
from beyond_consensus.config import ModelConfig
from dataclasses import asdict


class CompetenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.card,self.public,self.private=c.task_inputs(self.root)
        from beyond_consensus.models.competence import CHECKPOINT, REVISION
        self.model=asdict(ModelConfig(backend='transformers',checkpoint=CHECKPOINT,revision=REVISION,
            tokenizer_revision=REVISION,context_limit=16384,max_new_tokens=2048,thinking=True,
            action_constraint='reporecourse-json-v2-pool-7'))
        self.binding=dict(model=self.model,hardware='test-only device',compute_capability=[9,0],
                          vram_total_bytes=80,torch_cuda='test',dependencies={})
        with patch.object(c,'verify'),patch.object(c,'evidence_check',return_value=self.binding):
            self.m=c.build(self.root,self.root,{}, {}, {'evidence':[{'comparison_binding':self.binding}]})
        self.lock=self.root/'lock.json';atomic_json(self.lock,{})

    def rehash(self,m):
        m['experiment_id']=digest({k:v for k,v in m.items() if k!='experiment_id'});return m

    def controls(self):
        return dict(schema='rr-cpu-qualification-v1',
            witnesses=[dict(organization=w['organization'],success=True) for w in self.private['witnesses']],
            negative_controls=[dict(control=k,obligation=r['id'],detected=True)
                for r in self.public['required_outputs']
                for k in ('missing','semantic_mutation','wrong_alias','wrong_type')])

    def test_complete_control_matrix_required(self):
        q=self.controls();c.check_controls(q,self.public,self.private)
        for section in ('witnesses','negative_controls'):
            for mutation in ('missing','duplicate','false','wrong'):
                broken=deepcopy(q)
                if mutation=='missing':broken[section].pop()
                elif mutation=='duplicate':broken[section].append(deepcopy(broken[section][0]))
                elif mutation=='false':broken[section][0]['success' if section=='witnesses' else 'detected']=False
                else:broken[section][0]['organization' if section=='witnesses' else 'obligation']='unknown'
                with self.subTest(section=section,mutation=mutation), self.assertRaises(BCError):
                    c.check_controls(broken,self.public,self.private)

    def test_scope_rejects_widening_even_with_new_hash(self):
        self.assertEqual(validate_manifest(self.m).shards,1)
        for field,value in [('task','synthetic-nullable'),('condition','loss_w0'),('seed',1),
                            ('planned_episodes',2),('shards',2),('campaign_allowed',True),
                            ('planner_evidence','real_model')]:
            m=deepcopy(self.m);m[field]=value
            with self.subTest(field=field),self.assertRaises(BCError):c.validate(self.rehash(m))
        for field,value in [('pool_size',8),('max_actions',30),('lane','open')]:
            m=deepcopy(self.m);m['config'][field]=value
            with self.subTest(field=field),self.assertRaises(BCError):c.validate(self.rehash(m))
        m=deepcopy(self.m);m['config']['resource']['token_cap']=200000
        with self.assertRaises(BCError):c.validate(self.rehash(m))
        with self.assertRaises(BCError):run_manifest(self.m,self.root,self.root,backend=object())
        for shard,retry in [(1,False),(0,True)]:
            with self.assertRaises(BCError):c.run(self.m,self.root,self.root,model_lock=self.lock,shard=shard,retry_failures=retry)

    def test_evidence_pair_and_changed_files_fail_closed(self):
        for evidence in ({},{'status':'passed'}, {'status':'verified_internal_bindings_review_pending',
            'errors':[],'cross_run_binding_differences':[],'changed_source_files':c.CHANGES,
            'evidence':[{'experiment_id':'other'}]}):
            with self.assertRaises(BCError):c.evidence_check(evidence)

    def test_submission_and_output_guard(self):
        out=self.root/'output'
        with patch.object(c,'verify'):
            for mode,n in [('preflight',1),('run',2)]:
                with self.assertRaises(BCError):c.submission(self.m,self.root,{},mode,n,out)
            c.submission(self.m,self.root,{},'run',1,out)
            atomic_json(out/'manifest.json',{'other':True})
            with self.assertRaises(BCError):c.submission(self.m,self.root,{},'run',1,out)
            atomic_json(out/'manifest.json',self.m)
            ep=out/'episodes'/self.m['episodes'][0]['episode_id']
            atomic_json(ep/'started.json',{})
            with self.assertRaises(BCError):c.submission(self.m,self.root,{},'run',1,out)

    def adapter(self, engine_type, *, backend_error=None):
        stack=ExitStack();self.addCleanup(stack.close)
        stack.enter_context(patch.object(c,'verify'))
        stack.enter_context(patch('beyond_consensus.models.transformers_backend.require_allocation'))
        stack.enter_context(patch('beyond_consensus.models.transformers_backend.TransformersBackend',
            side_effect=backend_error,return_value=SimpleNamespace(runtime=self.binding)))
        stack.enter_context(patch('reporecourse.engine.Engine',engine_type))
        score=stack.enter_context(patch('reporecourse.evaluator.evaluate',return_value={'status':'available','success':True}))
        return score

    def engine(self, *, fail=False, cleanup=False, checkpoint=False):
        owner=self
        class FakeEngine:
            def __init__(self,public,worker,**kw):
                owner.assertNotIn('witnesses',public);owner.assertNotIn('oracle',public)
                owner.assertEqual(kw['track'],'clean');owner.assertEqual(kw['v2']['pool_size'],7)
                owner.assertEqual(worker.mode,'model')
                self.resources=kw['resources'];self.failures=[];self.trajectories=[]
                self.env=SimpleNamespace(resources=self.resources,events=[],state=lambda:{},close=self.close)
            def run(self):
                key=self.resources.reserve(20,10)
                if fail:
                    self.resources.reconcile(key)
                    raise InterruptedError('test-only interruption')
                self.resources.reconcile(key,5,2)
                return dict(status='completed',state={})
            def close(self):
                if cleanup:raise OSError('test-only cleanup error')
            def checkpoint(self):
                if checkpoint:raise OSError('test-only checkpoint error')
        return FakeEngine

    def test_success_and_cleanup_failure_persist_and_do_not_rerun(self):
        score=self.adapter(self.engine(cleanup=True))
        out=self.root/'output'
        row=run_manifest(self.m,out,self.root,model_lock=self.lock)[0]
        self.assertTrue(row['success']);self.assertEqual(row['mode'],'real_model')
        self.assertEqual(row['resource_profile']['actual_tokens'],25)
        self.assertEqual(row['cleanup_error_type'],'OSError');score.assert_called_once()
        self.assertEqual(c.aggregate(self.m,out)['success'],True)
        with self.assertRaises(BCError):run_manifest(self.m,out,self.root,model_lock=self.lock)

    def test_interruption_with_checkpoint_and_cleanup_errors_retains_usage(self):
        score=self.adapter(self.engine(fail=True,checkpoint=True,cleanup=True))
        out=self.root/'output';row=c.run(self.m,out,self.root,model_lock=self.lock)[0]
        self.assertEqual(row['status'],'interrupted');self.assertIsNone(row['success'])
        self.assertEqual(row['resource_profile']['uncertain_tokens'],30)
        self.assertEqual(row['checkpoint_error_type'],'OSError')
        self.assertEqual(row['cleanup_error_type'],'OSError');score.assert_not_called()
        self.assertEqual(c.aggregate(self.m,out)['status'],'interrupted')

    def test_load_failure_and_missing_report_not_scientific_failure(self):
        self.assertEqual(c.aggregate(self.m,self.root)['missing'],1)
        self.adapter(self.engine(),backend_error=RuntimeError('test-only load error'))
        row=c.run(self.m,self.root/'output',self.root,model_lock=self.lock)[0]
        self.assertEqual(row['status'],'infrastructure_failed');self.assertIsNone(row['success'])
        self.assertFalse(row['model_executed'])
        path=self.root/'output'/'episodes'/row['episode_id']/'result.json'
        row['provenance']['manifest_hash']='changed';atomic_json(path,row)
        with self.assertRaises(BCError):c.aggregate(self.m,self.root/'output')

    def test_missing_shard_visible_but_retry_still_rejected(self):
        from beyond_consensus.experiments.cluster import failed_shard_ids
        self.assertEqual(failed_shard_ids(self.m,self.root),[0])
        with self.assertRaises(BCError):
            c.run(self.m,self.root,self.root,model_lock=self.lock,retry_failures=True)

    def test_cluster_scope_checked_before_scheduler(self):
        from beyond_consensus.experiments.cluster import submit
        config=SimpleNamespace(output_root=str(self.root))
        with patch('beyond_consensus.experiments.cluster.os.environ',{}),patch.object(c,'verify'):
            for opts in ({'concurrency':2},{'concurrency':1,'mode':'preflight'},
                         {'concurrency':1,'serialize':True},{'concurrency':1,'failed_shards':[0]},
                         {'concurrency':1,'condition':'clean'}):
                with self.subTest(opts=opts),self.assertRaises(BCError):submit(self.root,config,self.m,{},**opts)

if __name__=='__main__':unittest.main()
