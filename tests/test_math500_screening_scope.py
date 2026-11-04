"""Synthetic supplement checks; no live data or tokenizer loading."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('screen_scope',Path(__file__).resolve().parents[1]/'scripts/prepare_math500_screening_scope.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class Scope(unittest.TestCase):
    def test_only_one_render_prior_rows_unchanged_block_retained(self):
        import hashlib,copy
        text='Synthetic false-positive fixture'
        records=[{'id':m.CLEARED,'problem':text}]
        old=[{'source_id':f'mock:{i}','input_tokens':10,'reserved_tokens':3082} for i in range(19)]
        prep={'rows':old+[{'source_id':m.CLEARED},{'source_id':m.BLOCKED}]};before=copy.deepcopy(prep)
        view={'input_tokens':20,'payload_digest':'p','rendered_ids_digest':'r'}
        with patch.object(m,'CLEARED_HASH',hashlib.sha256(text.encode()).hexdigest()), \
             patch.object(m.screen,'render_request',return_value=view) as render:
            rows,new=m.supplement(prep,records,object(),'template')
        self.assertEqual(render.call_count,1);self.assertEqual(prep,before)
        self.assertEqual(rows[:19],old);self.assertEqual(len(rows),20)
        self.assertNotIn(m.BLOCKED,[r['source_id'] for r in rows])
        self.assertEqual(new['reserved_tokens'],3092)

    def test_exception_is_exact_statement_not_keyword_bypass(self):
        with patch.object(m.screen,'render_request') as render:
            with self.assertRaises(m.screen.Invalid):
                m.supplement({'rows':[]},[{'id':m.CLEARED,'problem':'changed statement'}],object(),'t')
            render.assert_not_called()

    def test_different_cohort_rejected(self):
        with self.assertRaises(m.screen.Invalid):m.validate({}, {'cohort_digest':'different'}, [])

if __name__=='__main__':unittest.main()
