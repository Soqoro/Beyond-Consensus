"""Exact matched-arm scope, fresh-process dispatch, and host-only failure capture."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import json
import os
import unittest

from tests.support import ROOT
from tests.test_rr_unique_preflight import Backend
from beyond_consensus.experiments import rr_decoder_diagnostic as probe
from beyond_consensus.experiments import rr_unique_preflight as normal
from beyond_consensus.models.base import Generation
from beyond_consensus.util import BCError,digest


def manifest():
    m=dict(schema=probe.SCHEMA,protocol=probe.PROTOCOL,model=asdict(normal.model()),cases=probe.selected_cases(),arms=list(probe.ARMS),
        maximum_calls=4,maximum_calls_per_arm=2,maximum_logical_tokens=65536,shards=1,episodes=[],planned_episodes=0,
        task_inputs_used=False,task_execution_allowed=False,sql_executed=False,parent_experiment=probe.PARENT,
        debug_environment={'CUDA_LAUNCH_BLOCKING':'1'},models={a:asdict(probe.model(a)) for a in probe.ARMS},
        source_revision='test',native_lock={},model_lock_sha256=digest({}),controls={},parent_cases=[],approval=None)
    m['experiment_id']=digest(m);return m


def approved():
    m=manifest();a=probe.approval_template(m);a.update(decision='approved',reviewer='test',reviewed_at='2026-10-15')
    return probe.approve(m,a)


class FakeCuda:
    def synchronize(self):pass
    def reset_peak_memory_stats(self,_):pass
    def mem_get_info(self,_):return 20_000_000_000,80_000_000_000
    def max_memory_allocated(self,_):return 60_000_000_000
    def max_memory_reserved(self,_):return 62_000_000_000

class DiagnosticBackend(Backend):
    runtime={'vram_total_bytes':80_000_000_000,'hardware':'synthetic-test-double'}
    torch=SimpleNamespace(cuda=FakeCuda())
    config=normal.model()
    def generate(self,messages,cap,seed):
        result=super().generate(messages,cap,seed)
        result.diagnostics['rendered_input_ids_hash']=digest([1,2])
        return result
    def diagnostic_inputs(self,messages):return dict(rendered_input_ids=[1,2],rendered_input_ids_hash=digest([1,2]),rendered_input_tokens=self.count_input(messages))


class MatchedDiagnostic(unittest.TestCase):
    def test_exact_scope_and_approval_cannot_expand_or_change_model(self):
        m=approved();probe.validate(m)
        for key,value in [('maximum_calls',5),('cases',normal.cases()),('debug_environment',{}),('arms',['guarded']),('task_inputs_used',True)]:
            changed=deepcopy(m);changed[key]=value;changed['experiment_id']=digest({k:v for k,v in changed.items() if k!='experiment_id'})
            with self.subTest(key=key),self.assertRaises(BCError):probe.validate(changed)
        a=probe.approval_template(manifest());a.update(decision='approved',reviewer='r',reviewed_at='now',maximum_calls=5)
        with self.assertRaises(BCError):probe.approve(manifest(),a)

    def test_arms_share_prompts_settings_except_mode_and_native_schema(self):
        from beyond_consensus.models.action_schema import decoder_schema
        models=[asdict(probe.model(a)) for a in probe.ARMS]
        self.assertEqual({k:v for k,v in models[0].items() if k!='action_constraint'},
                         {k:v for k,v in models[1].items() if k!='action_constraint'})
        self.assertEqual(decoder_schema(probe.NATIVE),decoder_schema(normal.MODE))
        self.assertEqual([c['id'] for c in probe.selected_cases()],['nested_mapping','escaped_keys'])
        self.assertFalse(any(c['long_context'] for c in probe.selected_cases()))

    def test_pending_approval_and_started_attempt_do_not_dispatch(self):
        with TemporaryDirectory() as tmp,patch.object(probe,'check'):
            with self.assertRaises(BCError):probe.submission(manifest(),ROOT,{},'preflight',1,tmp)
            probe.submission(approved(),ROOT,{},'preflight',1,tmp)
            (Path(tmp)/'decoder-diagnostic-started.json').write_text('{}')
            with self.assertRaises(BCError):probe.submission(approved(),ROOT,{},'preflight',1,tmp)

    def test_accelerator_error_through_real_arm_adapter_retains_uncertain_and_unrun(self):
        AcceleratorError=type('AcceleratorError',(RuntimeError,),{})
        backend=DiagnosticBackend(error=AcceleratorError('injected synthetic accelerator failure'))
        with TemporaryDirectory() as tmp,patch.dict(os.environ,{'CUDA_LAUNCH_BLOCKING':'1','SLURM_JOB_ID':'test'}),patch('beyond_consensus.models.transformers_backend.TransformersBackend',return_value=backend):
            output=Path(tmp)/'arm.json'
            report=probe.arm_run(approved(),'guarded',Path(tmp)/'lock',ROOT,output)
            saved=json.loads(output.read_text())
            self.assertEqual(saved['calls'][0]['accelerator_status'],'exception')
            self.assertEqual(saved['calls'][0]['error_type'],'AcceleratorError')
            self.assertEqual(saved['calls'][0]['failure_stage'],'generation')
            self.assertGreater(saved['calls'][0]['resources']['uncertain_tokens'],0)
            self.assertEqual(saved['calls'][1]['status'],'not_attempted')
            self.assertEqual(len(backend.calls),1)
            self.assertTrue(report['command_failed'])
            self.assertIn('rendered_input_ids_hash',saved['calls'][0]['pre_dispatch'])

    def test_native_duplicate_parse_failure_not_accelerator_failure_no_text_export(self):
        backend=DiagnosticBackend(text='{"tool":"finish","tool":"finish"}')
        rows=normal.sequence(backend,lambda reset:{},lambda rows:None,selected_cases=probe.selected_cases(),mode=probe.NATIVE,diagnostic=True)
        self.assertEqual(len(backend.calls),2)
        self.assertTrue(all(r['strict_parser_valid'] is False and r['accelerator_status']=='no_exception_observed' for r in rows))
        self.assertTrue(all('text' not in r['generation'] for r in rows))
        self.assertTrue(all(r['generation_completion']=='eos' for r in rows))

    def test_parent_uses_two_sequential_fresh_processes_same_launchblocking(self):
        calls=[]
        def subprocess_run(argv,env,check):
            calls.append((argv,env.copy()));arm=argv[argv.index('--arm')+1];path=Path(argv[argv.index('--output')+1])
            path.write_text(json.dumps(dict(arm=arm,status='completed',command_failed=arm=='native',calls=[],runtime={'hardware':'same-test-GPU'})))
            return SimpleNamespace(returncode=1 if arm=='native' else 0)
        with TemporaryDirectory() as tmp,patch.object(probe,'submission'),patch.object(probe.subprocess,'run',side_effect=subprocess_run):
            root=Path(tmp);lock=root/'lock';lock.write_text('{}')
            result=probe.run(approved(),lock,ROOT,root/'preflight.json')
            self.assertEqual(len(calls),2)
            self.assertEqual([args[args.index('--arm')+1] for args,_ in calls],['native','guarded'])
            self.assertTrue(all(env['CUDA_LAUNCH_BLOCKING']=='1' for _,env in calls))
            self.assertTrue(all('run_rr_decoder_diagnostic.py' in ' '.join(args) for args,_ in calls))
            self.assertTrue(result['command_failed'])
            self.assertTrue(result['same_hardware_model'])

    def test_normal_gate_blocks_unreviewed_failed_pair_and_debug_environment(self):
        with self.assertRaises(BCError):normal.normal_gate(None,None)
        with patch.dict(os.environ,{'CUDA_LAUNCH_BLOCKING':'1'}),self.assertRaisesRegex(BCError,'launch blocking disabled'):
            normal.run({},None,ROOT,Path('/unused'))

    def test_native_parse_rejection_can_be_reviewed_but_accelerator_or_length_failure_cannot(self):
        arms=[]
        for index,arm in enumerate(probe.ARMS):
            backend=DiagnosticBackend();backend.config=probe.model(arm)
            rows=normal.sequence(backend,lambda reset:{},lambda rows:None,
                selected_cases=probe.selected_cases(),mode=probe.model(arm).action_constraint,diagnostic=True)
            arms.append(dict(arm=arm,calls=rows,process_id=index+1,launch_blocking='1',process_exit_code=0,status='completed'))
        report=dict(schema='rr-decoder-diagnostic-report-v1',protocol=probe.PROTOCOL,status='completed',arms=arms)
        report['arms'][0]['calls'][0]['passed']=False
        report['arms'][0]['calls'][0]['strict_parser_valid']=False
        self.assertTrue(probe.normal_eligible(report))
        report['arms'][1]['calls'][0]['generation_completion']='length_limit'
        self.assertFalse(probe.normal_eligible(report))

class InterruptedChild(unittest.TestCase):
    def test_parent_interruption_keeps_uncertain_reservations_and_unrun_arm(self):
        from reporecourse.resources import Resources
        usage=Resources(16384,1200);usage.reserve_cpu(31);usage.reserve(95,2048)
        saved=dict(arm='native',status='started',calls=[dict(id='nested_mapping',status='started',dispatched=True,resources=usage.summary()),
            dict(id='escaped_keys',status='not_attempted',dispatched=False,resources=Resources(16384,1200).summary())])
        def interrupted(argv,**kwargs):
            Path(argv[argv.index('--output')+1]).write_text(json.dumps(saved))
            raise KeyboardInterrupt()
        with TemporaryDirectory() as tmp,patch.object(probe,'submission'),patch.object(probe.subprocess,'run',side_effect=interrupted) as child:
            root=Path(tmp);lock=root/'lock';lock.write_text('{}');output=root/'preflight.json'
            with self.assertRaises(KeyboardInterrupt):probe.run(approved(),lock,ROOT,output)
            report=json.loads(output.read_text());row=report['arms'][0]['calls'][0]
            self.assertEqual(row['resources']['uncertain_tokens'],2143)
            self.assertEqual(row['resources']['uncertain_cpu'],31)
            self.assertEqual(row['resources']['reserved_tokens'],0)
            self.assertEqual(row['resources']['cpu_reserved'],0)
            self.assertEqual(report['arms'][1]['status'],'not_attempted')
            self.assertEqual(child.call_count,1)
        terminal=probe.reconcile_interrupted_arm(saved)
        self.assertEqual(terminal['uncertain_tokens'],2143)
        self.assertEqual(probe.reconcile_interrupted_arm(terminal),terminal)
