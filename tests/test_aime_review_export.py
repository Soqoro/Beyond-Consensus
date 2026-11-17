import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aime_review_export',ROOT/'scripts/export_prospective_aime_review.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AimeReviewExportTests(unittest.TestCase):
    def test_public_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'public.json'
            for rows,accepted in [([{'id':'x','problem':'a'}],True),([{'id':'x','problem':'a','answer':1}],False),([{'id':'x','problem':'a'}]*2,False)]:
                p.write_text(json.dumps(rows));h=hashlib.sha256(p.read_bytes()).hexdigest()
                if accepted:self.assertEqual(set(m.public_rows(p,h)),{'x'})
                else:
                    with self.assertRaises(ValueError):m.public_rows(p,h)
            with self.assertRaises(ValueError):m.public_rows(p,'0'*64)
    def test_no_dispatch_evidence(self):
        with self.assertRaises(ValueError):m.build({'status':'approved'},Path('/absent'),Path('/absent'))
    def test_retrieval_is_deterministic_and_excludes_self(self):
        p={x:{'id':x,'problem':'x + 1'} for x in ('z','b','a')}
        rows,count=m.comparisons(p,['z'],list(p),[])
        self.assertEqual([r['source_id'] for r in rows[0]['nearest']['historical']],['a','b'])
        self.assertEqual(count,2)
if __name__=='__main__':unittest.main()
