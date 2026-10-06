"""CPU doubles for the separate planner-output qualification, not GPU evidence."""
import copy
import tempfile
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import test_rr_open_footprint as prior
from beyond_consensus.experiments import rr_open_footprint as f
from beyond_consensus.models.competence import qualification_key, require_qualification
from beyond_consensus.util import BCError, digest


class PlannerCapacityTests(unittest.TestCase):
    def packet(self):
        helper = prior.FootprintTests()
        old, lock = helper.packet()
        def measure(row, text):
            return dict(input_tokens=300, action_tokens=2124 if row['role']=='plan' else 11,
                        grammar_accepted=True, rendered_input_ids_hash='fake')
        with patch.object(f.base, 'check_locks'), patch.object(f.base, 'source_revision', return_value='test-source'):
            p = f.prepare(Path('.'), old['proposal'], lock, lock, measure, planner_output_cap=4096)
        p['measurement_runtime'] = old['measurement_runtime']
        helper.seal(p, 'packet_id')
        return helper, p, lock

    def test_saved_packet_and_manifest_round_trip_preserve_measured_messages(self):
        from reporecourse.common import write_new, load
        for packet, lock in (prior.FootprintTests().packet(), self.packet()[1:]):
            with self.subTest(schema=packet['schema']), tempfile.TemporaryDirectory() as temp:
                path=Path(temp)/'packet.json'
                write_new(path, packet)
                saved=load(path)
                f.validate_packet(saved, measured=True)
                self.assertEqual([r['messages'] for r in saved['cases']],
                                 [r['messages'] for r in packet['cases']])
                with patch.object(f.base,'check_submission'), patch.object(f,'source_revision',return_value='test-source'):
                    manifest=f.build(Path('.'),saved,lock)
                dest=Path(temp)/'manifest.json'
                write_new(dest,manifest)
                f.validate(load(dest))
                # Hash-consistent text changes must still fail exact validation.
                saved['cases'][0]['messages'][-1]['content']+=' '
                saved['cases'][0]['prompt_hash']=digest(saved['cases'][0]['messages'])
                prior.FootprintTests().seal(saved,'packet_id')
                with self.assertRaises(BCError):f.validate_packet(saved,measured=True)

    def test_separate_version_and_role_caps(self):
        h,p,_ = self.packet()
        f.validate_packet(p, measured=True)
        self.assertEqual(p['schema'], f.PACKET_V2)
        self.assertEqual(p['base_manifest']['model']['max_new_tokens'], 2048)
        self.assertEqual(p['proposal']['planner_config']['model']['max_new_tokens'], 2048)
        self.assertEqual(p['status'], 'passed_cpu_cases')
        backend = h.backend(p); seen=[]; generate=backend.generate
        def recording(messages, cap, seed):
            seen.append(cap)
            return generate(messages, cap, seed)
        backend.generate=recording
        rows=f.sequence(p,backend,lambda role:None,h.memory)
        self.assertTrue(all(r['passed'] for r in rows))
        self.assertEqual(seen,[4096]*3+[2048]*2)
        self.assertFalse(p['task_execution_allowed'])
        # Relabeling a new packet as the old protocol cannot reuse its evidence.
        p.update(schema=f.PACKET,protocol=f.PROTOCOL);h.seal(p,'packet_id')
        with self.assertRaises(BCError): f.validate_packet(p, measured=True)

    def test_input_reservation_and_worker_output_unchanged(self):
        h,p,_=self.packet()
        for index, cap in ((0,4096),(3,2048)):
            good=copy.deepcopy(p);m=good['cases'][index]['measurement']
            m['input_tokens']=16384-cap;h.seal(good,'packet_id')
            f.validate_packet(good,measured=True)
            m['input_tokens']+=1;h.seal(good,'packet_id')
            with self.assertRaises(BCError): f.validate_packet(good,measured=True)
        bad=copy.deepcopy(p);m=bad['cases'][3]['measurement']
        m.update(action_tokens=2048,action_plus_stop_tokens=2049);h.seal(bad,'packet_id')
        with self.assertRaises(BCError): f.validate_packet(bad,measured=True)

    def test_uncertain_planner_reservation_and_stop(self):
        h,p,_=self.packet();backend=h.backend(p)
        def broken(*args): raise RuntimeError('explicit CPU double')
        backend.generate=broken
        rows=f.sequence(p,backend,lambda role:None,h.memory)
        self.assertEqual(rows[0]['uncertain_tokens'],300+4096)
        self.assertTrue(all(not r['dispatched'] for r in rows[1:]))

    def test_output_bound_qualification_keys(self):
        mode='reporecourse-plan-scoped-v1-pool-7'
        lock=dict(checkpoint='test',revision='test',tokenizer_revision='test',metadata_hashes={})
        k2=qualification_key(lock,{},16384,mode)
        k4=qualification_key(lock,{},16384,mode,4096)
        self.assertNotEqual(k2,k4)
        lock['decoder_qualification']=dict(status='passed',qualification_key=k4,
                                          model_executed=False,sql_executed=False)
        require_qualification(lock,{},16384,mode,4096)
        with self.assertRaises(BCError): require_qualification(lock,{},16384,mode)
        for context, grammar in ((8192,mode),(16384,'reporecourse-json-scoped-v1-pool-7'),
                                 (16384,'reporecourse-plan-scoped-v1-pool-6')):
            with self.assertRaises(BCError): qualification_key(lock,{},context,grammar,4096)

    def test_profile_not_legacy_probe_or_task(self):
        h,p,lock=self.packet()
        with patch.object(f.base,'check_submission'),patch.object(f,'source_revision',return_value='test-source'):
            m=f.build(Path('.'),p,lock)
        self.assertEqual(m['schema'],f.SCHEMA_V2)
        from beyond_consensus.experiments.manifest import validate_manifest
        validate_manifest(m)
        from beyond_consensus.experiments.runner import run_manifest
        with self.assertRaises(BCError):run_manifest(m,Path('/unused'),Path('.'))
        with self.assertRaises(BCError):f.base.run(p['base_manifest'],Path('/unused'),Path('.'))
        with self.assertRaises(BCError):f.base.check_submission(p['base_manifest'],lock,Path('.'),'run',1)
        with self.assertRaises(BCError):f.base.check_submission(p['base_manifest'],lock,Path('.'),'preflight',2)

    def test_lock_checks_use_each_roles_cap(self):
        _,p,_=self.packet()
        lock=dict(checkpoint='test',revision='test',tokenizer_revision='test',model_path='test',
                  tokenizer_path='test',metadata_hashes={'a':'b'},weight_hashes={'c':'d'})
        profile=copy.deepcopy(p['base_manifest'])
        profile.update(model_lock_sha256=digest(lock),planner_lock=lock)
        with patch('beyond_consensus.models.competence.require_qualification') as check:
            f.base.check_locks(profile,lock)
        self.assertEqual([c.args[-1] for c in check.call_args_list],[2048,4096])


if __name__=='__main__':unittest.main()
