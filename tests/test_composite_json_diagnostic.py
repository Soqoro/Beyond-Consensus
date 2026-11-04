import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('diagnostic',Path(__file__).resolve().parents[1]/'scripts/diagnose_composite_json.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Tokens:
 def decode(self,ids,**kw):return str(ids)
class DiagnosticTests(unittest.TestCase):
 def test_content_vs_eos_and_no_further_accepts(self):
  for reject,expected in [(2,'content'),(9,'eos'),(-1,None)]:
   calls=[]
   class Matcher:
    def accept_token(self,t):calls.append(t);return t!=reject
   r=d.trace_tokens(Matcher,[1,2,3],9,Tokens())
   self.assertEqual(r['rejection_stage'],expected)
   self.assertEqual(calls,[1,2] if reject==2 else [1,2,3,9])
 def test_fresh_matcher_per_trace(self):
  instances=[]
  class Matcher:
   def __init__(self):instances.append(self)
   def accept_token(self,t):return True
  for _ in range(2):self.assertTrue(d.trace_tokens(Matcher,[1],9,Tokens())['accepted'])
  self.assertEqual(len(instances),2)
