"""Task-free footprint controls with explicit CPU doubles, never model evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments import rr_open_footprint as f
from beyond_consensus.models.base import Generation
from beyond_consensus.util import BCError, digest


class FootprintTests(unittest.TestCase):
    def packet(self, measured=True):
        q = dict(qualification_key='plan', packages={}, thinking_template={'template_hash':'test'})
        lock = {'decoder_qualification':q}
        with patch.object(f.base, 'check_locks'), patch.object(f.base, 'source_revision', return_value='test-source'):
            model = f.base.build(Path('.'), lock, lock, 7, plan_scoped=True)['model']
            proposal = dict(schema='rr-open-engineering-proposal-v1', task_execution_allowed=False,
                campaign_allowed=False, worker_config={'model':model},
                planner_config={'model':dict(model,action_constraint='reporecourse-plan-scoped-v1-pool-7')})
            proposal['proposal_id'] = digest(proposal)
            measure = lambda row,text:dict(input_tokens=300,action_tokens=100,grammar_accepted=True,rendered_input_ids_hash='fake')
            packet = f.prepare(Path('.'), proposal, lock, lock, measure if measured else None)
        packet['measurement_runtime'] = dict(packages={},template={'template_hash':'test'},worker_lock_sha256=digest(lock),
            qualification_keys={'json':'plan','plan':'plan'})
        self.seal(packet,'packet_id')
        return packet, lock

    def seal(self, obj, key): obj[key] = digest({k:v for k,v in obj.items() if k != key})

    def backend(self, packet):
        class Double:
            calls = 0
            def count_input(self, messages): return 300
            def generate(self, messages, cap, seed):
                self.calls += 1
                action = json.loads(messages[-1]['content'].split('no Markdown: ')[1])
                return Generation(json.dumps(action), 100, 5, 0,
                    {'constraint_complete':True,'finish_reason':'eos','rendered_input_tokens':300})
        return Double()

    def memory(self, **kw):
        return dict(peak_allocated_bytes=1,peak_reserved_bytes=2,total_bytes=3)

    def test_cases_real_scope_and_unmeasured_not_admitted(self):
        p,_ = self.packet(False)
        self.assertEqual([r['id'] for r in p['cases']], list(f.CASE_IDS))
        self.assertEqual([len(r['expected']['plan']['units']) for r in p['cases'][:3]], [2,7,24])
        self.assertTrue(p['cases'][-1]['unrelated_read_denied'])
        self.assertEqual(len(p['cases'][-1]['visible_versions']),16)
        self.assertFalse(any(r['measurement']['dispatch_allowed'] for r in p['cases']))
        with self.assertRaises(BCError): f.validate_packet(p, measured=True)

    def test_sequence_all_cases_exact_actions_and_no_task_permission(self):
        p,_ = self.packet(); b = self.backend(p); roles=[]
        rows = f.sequence(p,b,roles.append,self.memory)
        self.assertEqual(b.calls,5)
        self.assertEqual(roles,['plan']*3+['json']*2)
        self.assertTrue(all(r['passed'] for r in rows))
        self.assertFalse(p['task_execution_allowed'])

    def test_overcap_kept_in_denominator_and_not_dispatched(self):
        p,_=self.packet(); m=p['cases'][2]['measurement']
        m.update(action_tokens=2500,action_plus_stop_tokens=2501,status='output_representation_exceeds_cap',dispatch_allowed=False)
        self.seal(p,'packet_id'); b=self.backend(p)
        rows=f.sequence(p,b,lambda _:None,self.memory)
        self.assertEqual(b.calls,4);self.assertEqual(len(rows),5)
        self.assertFalse(rows[2]['passed']);self.assertFalse(rows[2]['dispatched'])
        m['dispatch_allowed']=True;self.seal(p,'packet_id')
        with self.assertRaises(BCError):f.validate_packet(p,True)

    def test_bad_generation_and_unknown_usage_never_pass(self):
        p,_=self.packet()
        for text,finish in [('{"tool":"finish","tool":"finish"}','eos'),('{}','length_limit')]:
            b=self.backend(p)
            b.generate=lambda *args:Generation(text,2048,None,0,{'constraint_complete':False,'finish_reason':finish,'rendered_input_tokens':300})
            self.assertFalse(any(r['passed'] for r in f.sequence(p,b,lambda _:None,self.memory)))
        b=self.backend(p)
        def fail(*args): raise RuntimeError('unknown')
        b.generate=fail
        rows=f.sequence(p,b,lambda _:None,self.memory)
        self.assertEqual(len(rows),5);self.assertEqual(rows[0]['uncertain_tokens'],2348)
        self.assertTrue(all(not r['dispatched'] for r in rows[1:]))

    def test_manifest_integrity_scope_and_task_route(self):
        p,lock=self.packet()
        with patch.object(f,'source_revision',return_value='test-source'),patch.object(f.base,'check_submission'):
            m=f.build(Path('.'),p,lock)
        self.assertEqual(f.validate(m).shards,1)
        with patch.object(f.base,'source_revision',return_value='test-source'),patch.object(f.base,'check_locks'):
            f.check_submission(m,lock,Path('.'),'preflight',1)
            for mode,n in [('run',1),('preflight',2)]:
                with self.assertRaises(BCError):f.check_submission(m,lock,Path('.'),mode,n)
        from beyond_consensus.experiments.runner import run_manifest
        with self.assertRaisesRegex(BCError,'cannot run task'):run_manifest(m,Path('/unused'),Path('.'))
        m['cpu_packet']['cases'].pop()
        with self.assertRaises(BCError):f.validate(m)

    def test_rehashed_visibility_mutation_and_input_admission(self):
        p,_=self.packet();row=p['cases'][-1]
        row['observation']['source_ids']=['hidden']
        row['observation_hash']=digest(row['observation']);self.seal(p,'packet_id')
        with self.assertRaises(BCError):f.validate_packet(p,True)
        p,_=self.packet();b=self.backend(p);b.count_input=lambda _:16000
        rows=f.sequence(p,b,lambda _:None,self.memory)
        self.assertEqual(b.calls,0);self.assertFalse(any(r['passed'] for r in rows))

    def test_contradictory_generation_accounting_reserves_uncertain_usage(self):
        p,_=self.packet();b=self.backend(p)
        b.generate=lambda *args:Generation('{}',10,20,0,
            {'constraint_complete':True,'finish_reason':'eos','rendered_input_tokens':300})
        rows=f.sequence(p,b,lambda _:None,self.memory)
        self.assertEqual(rows[0]['failure_stage'],'accounting')
        self.assertEqual(rows[0]['uncertain_tokens'],2348)
        self.assertFalse(any(r['passed'] for r in rows))

    def test_stdlib_help(self):
        for argv in [['scripts/prepare_rr_open_footprint.py','--help'],['scripts/bc.py','rr-open-footprint-manifest','--help']]:
            r=subprocess.run([sys.executable,'-I','-S',*argv],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
