import importlib.util
import json
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('common_check',Path(__file__).resolve().parents[1]/'scripts/check_composite_common_derivation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CommonCheckTests(unittest.TestCase):
    def test_fixture_fields_and_escaping(self):
        rows=m.fixtures(['derivation','bound','equality_conditions'])
        self.assertEqual(list(json.loads(rows['derivation_first'])),['derivation','bound','equality_conditions'])
        self.assertEqual(list(json.loads(rows['derivation_last']))[-1],'derivation')
        self.assertIn('"quoted"',json.loads(rows['derivation_first'])['bound'])
        with self.assertRaises(json.JSONDecodeError):json.loads(rows['malformed'])
    def test_complete_controls_and_fail_on_unconstrained_order(self):
        class Tokenizer:
            def encode(self,text,**kwargs):return list(text.encode())
            def decode(self,ids,**kwargs):return bytes(ids).decode()
        fields=['derivation','bound']
        def factory(ordered):
            class Matcher:
                def __init__(self):self.raw=b''
                def valid(self):
                    try:v=json.loads(self.raw)
                    except (ValueError,UnicodeError):return False
                    return isinstance(v,dict) and set(v)==set(fields) and (not ordered or list(v)==fields)
                def accept_string(self,text):self.raw=text.encode();return self.valid()
                def accept_token(self,t):
                    if t in (999,1000):return self.valid()
                    self.raw+=bytes([t]);return True
            return Matcher
        good=m.controls(factory(True),Tokenizer(),fields,[999,1000])
        bad=m.controls(factory(False),Tokenizer(),fields,[999,1000])
        self.assertTrue(all(o['passed'] for o in good))
        self.assertTrue(all(not o['passed'] for o in bad))
