"""CPU doubles for bounded numerical diagnosis; no claims about model outputs."""
from contextlib import nullcontext
from copy import deepcopy
import math
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.models import forward_probe as f,worker_profiles as p
from beyond_consensus.experiments import worker_selection as w
from beyond_consensus.util import BCError,digest


class Vector(list):
    def tolist(self):return list(self)
    def unsqueeze(self,dim):return Matrix([list(self)])

class Matrix:
    device='cuda:0';dtype='torch.int64'
    def __init__(self,rows):self.rows=rows;self.shape=(len(rows),len(rows[0]))
    def __getitem__(self,i):return Vector(self.rows[i])
    def to(self,device):return self

class Scores:
    dtype='torch.bfloat16';device='cuda:3'
    def __init__(self,values):self.values=values;self.shape=(1,len(values))

class Logits:
    def __init__(self,values):self.values=values;self.shape=(1,1,len(values))
    def __getitem__(self,key):return Scores(self.values)

def counted(predicate):
    return lambda scores:SimpleNamespace(sum=lambda:SimpleNamespace(item=lambda:sum(predicate(x) for x in scores.values)))

TORCH=SimpleNamespace(cat=lambda pair,dim:Matrix([pair[0].rows[0]+pair[1].rows[0]]),
    arange=lambda *args,**kw:Vector(range(*args)),ones_like=lambda ids:Matrix([[1]*ids.shape[1]]),
    tensor=lambda rows,**kw:Matrix(rows),device=lambda name:name,inference_mode=nullcontext,
    cuda=SimpleNamespace(synchronize=lambda device:None),isfinite=counted(math.isfinite),
    isnan=counted(math.isnan),isposinf=counted(lambda x:x==math.inf),isneginf=counted(lambda x:x==-math.inf))


class ForwardProbeTests(unittest.TestCase):
    def test_raw_hook_runs_before_generation_processors_and_is_removed(self):
        from beyond_consensus.models.transformers_backend import TransformersBackend
        from beyond_consensus.models.decoder_trace import Trace,MaskDiagnosticError
        handles=[];hooks={}
        class Model:
            def register_forward_pre_hook(self, fn, **kw):
                hooks['before']=fn
                return SimpleNamespace(remove=lambda:handles.append('before'))
            def register_forward_hook(self, fn, **kw):
                hooks['after']=fn
                return SimpleNamespace(remove=lambda:handles.append('after'))
        backend=TransformersBackend.__new__(TransformersBackend);backend.model=Model()
        trace=Trace();trace.capture_raw_logits=True;backend.diagnostic_trace=trace
        def generate(*args):
            hooks['after'](backend.model,(),{},SimpleNamespace(logits=Logits([math.nan,1.])))
            self.fail('Nonfinite raw output must stop before logits processors')
        backend._generate=generate
        with patch.dict('sys.modules',torch=TORCH):
            with self.assertRaisesRegex(MaskDiagnosticError,'nonfinite_raw_model_logits'):
                backend.generate([],4096,0)
        self.assertEqual(handles,['before','after'])
        self.assertEqual(trace.snapshot()['events'][-1]['stage'],'raw_model_logits')
        self.assertEqual(trace.snapshot()['events'][-1]['nan'],1)

    def test_raw_counts_do_not_sanitize_nonfinite_or_cast_dtype(self):
        with patch.dict('sys.modules',torch=TORCH):
            report=f.raw_logits_summary(Logits([1.,math.nan,math.inf,-math.inf]))
        self.assertEqual((report['finite'],report['nan'],report['positive_infinity'],report['negative_infinity']),(1,1,1,1))
        self.assertFalse(report['all_finite']);self.assertEqual(report['dtype'],'torch.bfloat16')

    def test_fixed_cached_and_uncached_inputs_and_cache_isolation(self):
        ids=Matrix([[1,2,3]]);prefix=Matrix([[90]]);cache=object()
        a=f.forward_kwargs('cache_prefill',ids,prefix,None,TORCH)
        b=f.forward_kwargs('cached_token',ids,prefix,cache,TORCH)
        c=f.forward_kwargs('full_prefix',ids,prefix,cache,TORCH)
        self.assertEqual(a['cache_position'],[0,1,2]);self.assertIsNone(a['past_key_values'])
        self.assertEqual(b['input_ids'].rows,[[90]]);self.assertIs(b['past_key_values'],cache)
        self.assertEqual(b['position_ids'].rows,[[3]]);self.assertEqual(b['attention_mask'].shape,(1,4))
        self.assertEqual(c['input_ids'].rows,[[1,2,3,90]])
        self.assertFalse(c['use_cache']);self.assertIsNone(c['past_key_values'])
        with self.assertRaises(BCError):f.forward_kwargs('cached_token',ids,prefix,None,TORCH)

    def backend(self, fail=False):
        calls=[];cache=object()
        def model(**kwargs):
            calls.append(kwargs)
            if len(calls)==2 and fail:raise RuntimeError('device failure')
            return SimpleNamespace(logits=Logits([math.nan if len(calls)==2 else 1.,2.]),
                                   past_key_values=cache if kwargs['use_cache'] else None)
        return SimpleNamespace(profile=p.profile('coder'),torch=TORCH,model=model,
            tokenizer=SimpleNamespace(encode=lambda *a,**k:[90]),
            encode=lambda m:{'input_ids':Matrix([[1,2,3]])}),calls

    def test_three_forwards_nonfinite_is_observation_not_qualification(self):
        backend,calls=self.backend();saved=[]
        with patch.dict('sys.modules',torch=TORCH):
            rows=f.run(backend,dict(id='cache_prefill',input_tokens=3,messages=[],rendered_ids_hash=digest([1,2,3]),fixed_prefix_ids=[90]),lambda r:saved.append(deepcopy(r)))
        self.assertEqual(len(calls),3)
        self.assertEqual([r['raw_logits']['all_finite'] for r in rows],[True,False,True])
        self.assertEqual([r['resources']['actual_tokens'] for r in rows],[3,4,8])
        self.assertEqual([r['generated_tokens'] for r in rows],[0]*3)
        self.assertTrue(all(r['qualification_passed'] is False and r['cpu_accounting_complete'] is False for r in rows))
        self.assertLess(len(rows[0]['resources']['events']),len(rows[2]['resources']['events']))

    def test_exception_stops_without_retry_retains_uncertain_input(self):
        backend,calls=self.backend(fail=True)
        with patch.dict('sys.modules',torch=TORCH):
            rows=f.run(backend,dict(id='cache_prefill',input_tokens=3,messages=[],rendered_ids_hash=digest([1,2,3]),fixed_prefix_ids=[90]))
        self.assertEqual(len(calls),2)
        self.assertEqual(rows[-1]['status'],'infrastructure_failed')
        self.assertEqual(rows[-1]['resources']['uncertain_tokens'],1)

    def candidate(self):
        from tests.support import ROOT
        def footprint(profile,lock,stage,rows,*args):
            return dict(stage=stage,profile='coder',lock_hash=digest(lock),status='passed',implementation=w.hashes(),
                cases=[dict(id=r['id'],input_tokens=3,forward_input_tokens=1 if r['id']=='cached_token' else 3+(r['id']=='full_prefix'),passed=True,messages=[],rendered_ids_hash=digest([1,2,3]),fixed_prefix_ids=[90]) for r in rows])
        with patch.object(p,'require_qualified'),patch.object(w,'footprint',side_effect=footprint):
            return w.build(ROOT,'coder',{},'N')

    def test_exact_separate_scope_task_route_and_qualification_rejected(self):
        from beyond_consensus.experiments.runner import run_manifest
        m=self.candidate();a=w.approval_template(m)
        self.assertEqual(a['maximum_calls'],3);self.assertEqual(a['maximum_branches'],0)
        a.update(decision='approved',reviewer='test',reviewed_at='test')
        with patch.object(w,'verify'):approved=w.authorize(m,a,Path('.'),{})
        self.assertFalse(approved['task_execution_allowed'])
        with self.assertRaises(BCError):run_manifest(approved,Path('/unused'),Path('.'))
        changed=deepcopy(approved);changed['footprint']['cases'][1]['fixed_prefix_ids']=[91];w.seal(changed)
        with self.assertRaises(BCError):w.validate(changed)
        with self.assertRaises(BCError):w.compare([approved]*2,[{}]*2)

    def test_stage_n_cannot_supply_stage_a_qualification(self):
        from tests.support import ROOT
        study=w.study(ROOT)
        controls=dict(status='passed',implementation=w.hashes(),case_set_id=study['case_set_id'],
            runtime_versions={},cases=[dict(case=c['id'],negative=n,status='passed',evaluation={'correct':not n})
                for c in w.design.cases() for n in (False,True)])
        qualification=dict(stage='N',status='completed',rows=[{'passed':True}]*3)
        with patch.object(p,'require_qualified'),patch.object(w,'runtime_versions',return_value={}):
            with self.assertRaisesRegex(BCError,'four-call normal qualification'):
                w.build(ROOT,'coder',{},'A',controls_record=controls,qualification=qualification)

    def test_wrong_approval_count_and_task_authorization_are_rejected(self):
        m=self.candidate();a=w.approval_template(m)
        a.update(decision='approved',reviewer='test',reviewed_at='test',maximum_calls=4)
        with patch.object(w,'verify'),self.assertRaises(BCError):w.authorize(m,a,Path('.'),{})
        changed=deepcopy(m);changed['task_execution_allowed']=True;w.seal(changed)
        with self.assertRaises(BCError):w.validate(changed)
