"""Offline syntax bridge checks; no real tokenizer, grammar runtime or model."""
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from bc_phase2 import composite_math as c,composite_math_decoder as d
from bc_phase2.d1_natural_screen import NaturalTransport
from bc_phase2.model import Invalid

class DecoderTests(unittest.TestCase):
 def test_flat_contract_and_no_semantic_repair(self):
  for task in c.TASKS:
   s=d.schema(task);self.assertEqual(s['required'],task['fields']);self.assertFalse(s['additionalProperties'])
  text=json.dumps({'bound':'24','derivation':'I claim a different bound: 100','equality_conditions':'unverified'})
  self.assertEqual(json.loads(c.parse_artifact(text,c.TASKS[0]))['bound'],'24')
  malformed='{"bound":"24","derivation":"The text says "minimum".","equality_conditions":"unverified"}'
  with self.assertRaises(Invalid):c.parse_artifact(malformed,c.TASKS[0])
 def test_fresh_matcher_cached_grammar_same_generation(self):
  compiled=[];inners=[];invocations=[]
  class Compiler:
   def __init__(self,*a,**kw):pass
   def compile_json_schema(self,s,**kw):compiled.append(s);return 'grammar'
  class Inner:
   def __init__(self,g):inners.append(self)
  class Model:
   def get_output_embeddings(self):return SimpleNamespace(weight=SimpleNamespace(shape=(100,)))
   def generate(self,**kw):invocations.append(kw);return {'output_tokens':4}
  xgr=SimpleNamespace(TokenizerInfo=SimpleNamespace(from_huggingface=lambda *a,**kw:None),GrammarCompiler=Compiler)
  t=d.TaskTransport.__new__(d.TaskTransport);t.model=Model();original=t.model;t.tokenizer=object();t.tokens={'eos_token_id':[1]};t.compiled={}
  def parent(self,r):return self.model.generate(do_sample=False,max_new_tokens=3072)
  with patch.object(d,'load_xgrammar',return_value=(xgr,Inner)),patch.object(NaturalTransport,'generate',parent):
   for _ in range(2):t.generate({'decoder_task_id':'t0','input_ids':[2,3]})
  self.assertEqual(len(compiled),1);self.assertEqual(len(inners),2);self.assertIsNot(inners[0],inners[1]);self.assertIs(t.model,original)
  self.assertTrue(all(k['max_new_tokens']==3072 and k['do_sample'] is False for k in invocations))
 def test_generation_exception_no_retry_or_fallback(self):
  original=SimpleNamespace();t=d.TaskTransport.__new__(d.TaskTransport);t.model=original;t.compiled={'t0':('g',lambda _:object())}
  with patch.object(NaturalTransport,'generate',side_effect=RuntimeError('GPU failed')) as call:
   with self.assertRaises(RuntimeError):t.generate({'decoder_task_id':'t0','input_ids':[1]})
   self.assertEqual(call.call_count,1)
  self.assertIs(t.model,original)
