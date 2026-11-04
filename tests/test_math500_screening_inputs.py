"""Synthetic source projection and request-fit tests; no dataset/tokenizer/model load."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('screen_inputs',Path(__file__).resolve().parents[1]/'scripts/prepare_math500_screening_inputs.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from test_phase2_planner_qwen import Tokenizer


class Inputs(unittest.TestCase):
    def test_projection_only_requested_id_and_statement(self):
        raw='\n'.join(json.dumps({'unique_id':s,'problem':'Synthetic relation','answer':'SECRET','solution':'SECRET',
                                  'reviewer_notes':'SECRET'}) for s in ('mock:0','mock:1','mock:2')).encode()
        rows=m.project(raw,['mock:2','mock:0'])
        self.assertEqual([r['id'] for r in rows],['mock:2','mock:0'])
        self.assertTrue(all(set(r)=={'id','problem'} for r in rows));self.assertNotIn('SECRET',json.dumps(rows))
        with self.assertRaises(m.Invalid):m.project(raw,['absent'])
        with self.assertRaises(m.Invalid):m.project(raw+b'\n'+raw,['mock:0'])

    def test_attachment_flags_block_no_invented_clearance(self):
        tokenizer=Tokenizer();check=m.screen.verify_non_thinking(tokenizer)
        rows=[{'id':f'mock:{i}','problem':text} for i,text in enumerate(('[asy] code [/asy]',r'\includegraphics{x}',
              'See the diagram.','![image](x)','https://example.invalid/file'))]
        with patch.object(tokenizer,'apply_chat_template',side_effect=AssertionError('flagged content must not render')):
            result=m.measure(rows,tokenizer,check['template_hash'])
        self.assertTrue(all(r['status']=='attachment_review_required_not_rendered' for r in result))
        self.assertTrue(all(r['input_tokens'] is None for r in result))

    def test_render_reuses_prompt_cap_and_does_not_accept_semantics(self):
        tokenizer=Tokenizer();check=m.screen.verify_non_thinking(tokenizer)
        rows=m.measure([{'id':'mock:1','problem':'Synthetic relation'}],tokenizer,check['template_hash'])
        self.assertEqual(rows[0]['reserved_tokens'],rows[0]['input_tokens']+3072)
        self.assertEqual(rows[0]['attachment_review'],'pending');self.assertFalse(rows[0]['execution_allowed'])
        with self.assertRaises(m.Invalid):m.measure([{'id':'mock:1','problem':'x','answer':'secret'}],tokenizer,check['template_hash'])

    def test_overflow_is_retained_not_truncated_or_replaced(self):
        with patch.object(m.screen,'render_request',side_effect=m.Invalid('input overflow')):
            row=m.measure([{'id':'mock:1','problem':'synthetic'}],object(),'hash')[0]
        self.assertEqual(row['source_id'],'mock:1');self.assertEqual(row['status'],'render_rejected_no_truncation')
        self.assertIsNone(row['input_tokens']);self.assertFalse(row['execution_allowed'])

if __name__=='__main__':unittest.main()
