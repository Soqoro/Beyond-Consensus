"""Synthetic source inventories only; no benchmark statements or private keys."""
import hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from bc_phase2.model import Invalid
spec=importlib.util.spec_from_file_location('freeze_aime',Path(__file__).resolve().parents[1]/'scripts/freeze_prospective_aime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CandidateFreeze(unittest.TestCase):
    def setup_sources(self,root):
        pins={}
        for year in [2025,2026]:
            rev=str(year)*10;directory=root/str(year);directory.mkdir()
            rows=[dict(id=f'aime/{year}/{rev}/row/{i}',problem=f'SYNTHETIC ONLY: z + {i} = 99999') for i in range(1,31)]
            raw=json.dumps(rows).encode();(directory/'source.public.json').write_bytes(raw)
            pins[year]=(rev,hashlib.sha256(raw).hexdigest(),m.pipeline.procedure(f'aime{year}')['procedure_digest'])
        return pins
    def test_both_years_fixed_blocks_pending_and_prior_year_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pins=self.setup_sources(root)
            with patch.object(m,'PINNED',pins):r=m.prepare(root)
            self.assertFalse(r['execution_allowed']);self.assertFalse(r['private_keys_read'])
            a,b=r['datasets'];self.assertEqual(len(b['cohort']['excluded']),12)
            seen=[]
            for d in r['datasets']:
                self.assertEqual([len(b['records']) for b in d['cohort']['blocks']],[6,6])
                selected=[x for b in d['cohort']['blocks'] for x in b['records']]
                self.assertTrue(all(x['status']=='blocked' and x['family_review']=='pending' for x in selected))
                seen.append({x['normalized_hash'] for x in selected})
            self.assertFalse(seen[0]&seen[1]);self.assertNotIn('problem',a['inventory'][0])
    def test_wrong_public_bytes_stop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pins=self.setup_sources(root)
            (root/'2025/source.public.json').write_text('[]')
            with patch.object(m,'PINNED',pins),self.assertRaisesRegex(Invalid,'source hash'):m.prepare(root)
    def test_policy_drift_stops(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);pins=self.setup_sources(root);rev,h,_=pins[2025];pins[2025]=(rev,h,'0'*64)
            with patch.object(m,'PINNED',pins),self.assertRaisesRegex(Invalid,'procedure unchanged'):m.prepare(root)
if __name__=='__main__':unittest.main()
