"""Synthetic AIME intake and existing rich-artifact recovery path; no real questions."""
import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from bc_phase2 import prospective_pipeline as p,prospective_sources as s,prospective_adapters as a,composite_math as worker,composite_scaling_runtime as rt
from bc_phase2.model import Invalid,digest
from test_medqa_worker_launch import Fake,alternate
spec=importlib.util.spec_from_file_location('aime_intake',Path(__file__).resolve().parents[1]/'scripts/prepare_prospective_aime.py')
intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)

class AimePreparation(unittest.TestCase):
    def fixture(self,year=2025):
        rows=[dict(problem='Synthetic x + 2 = 9',problem_idx=1,answer='007',problem_type='Synthetic')]
        raw=json.dumps(rows).encode();receipt=dict(dataset=f'aime{year}',year=year,repository=f'MathArena/aime_{year}',revision='a'*40,format='json',upstream_path='synthetic.json',split='train',sha256=hashlib.sha256(raw).hexdigest(),read_authorized=True,authorization_reference='Synthetic test only')
        return raw,receipt
    def test_denied_before_source_open(self):
        with self.assertRaisesRegex(Invalid,'authorization'):intake.inspect('/absent',{})
    def test_identity_public_private_and_missing_metadata(self):
        raw,r=self.fixture()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'source';path.write_bytes(raw)
            pub,key,meta,proc,summary=intake.inspect(path,r)
            self.assertEqual(set(pub[0]),{'id','problem'});self.assertEqual(key[0]['integer'],7)
            self.assertIsNone(meta[0]['sitting']);self.assertIsNone(meta[0]['original_contest_id'])
            self.assertFalse(summary['execution_allowed']);self.assertFalse(summary['cohort_selected'])
            rr=deepcopy(r);rr.update(year=2026,dataset='aime2026',repository='MathArena/aime_2026')
            pub2,_,_,_,_=intake.inspect(path,rr);self.assertNotEqual(pub2[0]['id'],pub[0]['id'])
            for k,v in [('sha256','0'*64),('revision','main'),('format','parquet'),('repository','unreviewed')]:
                bad=deepcopy(r);bad[k]=v
                with self.assertRaises(Invalid):intake.inspect(path,bad)
    def test_cli_writes_separate_private_artifact_and_refuses_overwrite(self):
        raw,r=self.fixture()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'source.json').write_bytes(raw);(root/'receipt.json').write_text(json.dumps(r))
            cmd=[sys.executable,'-I','-B',str(Path(intake.__file__)), '--source',str(root/'source.json'),'--receipt',str(root/'receipt.json'),'--output',str(root/'out')]
            x=subprocess.run(cmd,capture_output=True,text=True);self.assertEqual(x.returncode,0,x.stderr)
            report=json.loads((root/'out/inspection.json').read_text())
            self.assertFalse(report['execution_allowed']);self.assertFalse(report['cohort_selected'])
            public=json.loads((root/'out/source.public.json').read_text());self.assertEqual(set(public[0]),{'id','problem'})
            private=root/'out/evaluator.private.json';self.assertEqual(private.stat().st_mode & 0o077,0)
            before=private.read_bytes();x=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(x.returncode,0);self.assertEqual(private.read_bytes(),before)

    def test_unknown_key_not_worker_failure_and_strict_final(self):
        pub,key,_=a.aime(dict(problem='Synthetic',problem_idx=2,answer=True),2026,'r',1)
        self.assertEqual(a.grade_aime('{"justification":"synthetic","final_integer":"007"}',key,pub)['status'],'unknown_grade')
        for bad in ['7 or 8','1000','-7','７','7.0',True,7]:
            self.assertEqual(a.grade_aime(json.dumps(dict(justification='synthetic',final_integer=bad)),key,pub)['status'],'invalid_answer')
    def test_rich_intermediate_and_all_owner_mock(self):
        pubs={};records=[]
        for i in range(12):
            pub,_,_=a.aime(dict(problem=f'Synthetic x + {i} = 90',problem_idx=i,answer=7),2025,'synthetic',i+1)
            pubs[pub['id']]=pub;e,n=s.faithful_identity(pub)
            records.append(dict(source_id=pub['id'],canonical_id=pub['id'],exact_hash=e,normalized_hash=n,family_id='',status='eligible'))
        exp=dict(cutoff='synthetic',records=[],aliases=[])
        review=dict(dataset='aime2025',revision='synthetic',inventory_digest=digest(records),reviewer='synthetic',reviewed_at='synthetic',decisions={k:'clear' for k in pubs})
        c=s.freeze(records,'aime2025','synthetic',exp,p.procedure('aime2025'),review)
        self.assertEqual([len(b['records']) for b in c['blocks']],[6,6])
        ids=[r['source_id'] for r in c['blocks'][0]['records']];ds={sid:dict(status='unsupported') for sid in ids}
        for sid,length in zip(ids,[3,3]):
            raw=json.dumps(dict(schema=p.natural.VERSION,source_id=sid,status='decomposed',tasks=[dict(id='T'+str(i+1),responsibility='Synthetic operation',required_inputs=['problem_statement'] if i==0 else ['T'+str(i)],produces='synthetic proof artifact') for i in range(length)],final_assembly='[T3]'))
            rev=dict(decision='admitted',reviewer='synthetic',reviewer_kind='AI-assisted',reviewed_at='synthetic',public_digest=digest(pubs[sid]),plan_digest=digest(raw),substantive_no_answer_leakage=True,tasks=[dict(id='t'+str(i),responsibility='Synthetic operation',parents=[] if i==0 else ['t'+str(i-1)],fields=['justification','final_integer'] if i==2 else ['derivation','equations','constraints']) for i in range(3)],outputs=['t2'])
            ds[sid]=p.admit('aime2025',c,pubs[sid],raw,rev)
        wave=p.wave(c,1,ds)
        class Transport(Fake):
            def generate(self,r):
                v=super().generate(r);obj=json.loads(v['final_text'])
                if 'final_integer' in obj:obj['final_integer']='007'
                v['final_text']=json.dumps(obj);return v
        with tempfile.TemporaryDirectory() as td:
            f=Transport();j=worker.Journal(Path(td)/'journal',f,wave['wave_id'],lambda:None,limits=wave['limits'])
            result=rt.run_wave(j,pubs,td,wave,alternate,interface=p)
            self.assertEqual(result['conditions'][0]['status'],'completed_comparison')
            for m in result['conditions'][0]['methods'].values():self.assertEqual(len(m['repairs']),4)
            for req in f.calls:
                self.assertEqual(set(req['source']),{'id','problem'})
                self.assertFalse(set(req)&{'method','owner','answer','integer','score','prices'})
                if 'constraints' in req['required_string_fields']:self.assertNotIn('final_integer',req['required_string_fields'])
            self.assertEqual(j.snapshot()['totals']['reserved_tokens'],0)

if __name__=='__main__':unittest.main()
