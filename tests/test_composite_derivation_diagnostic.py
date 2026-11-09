import unittest
from copy import deepcopy
from bc_phase2 import composite_derivation_diagnostic as d
from bc_phase2.model import digest,Invalid
from bc_phase2.composite_math import parse_artifact
import json

class DerivationDiagnosticTests(unittest.TestCase):
    def request(self):
        p={'instruction':'unchanged','responsibility':'solve assigned task','source':{'id':'synthetic','problem':'synthetic'},'parent_artifacts':{'t0':{'equation':'synthetic'}},'required_string_fields':['final_answer','justification']}
        return {'payload':p,'payload_digest':digest(p)}
    def test_only_field_order_changes_and_input_is_not_mutated(self):
        old=self.request();saved=deepcopy(old);new=d.candidate_request(old)
        self.assertEqual(old,saved)
        self.assertEqual(new['payload']['required_string_fields'],['justification','final_answer'])
        for k in old['payload']:
            if k!='required_string_fields':self.assertEqual(old['payload'][k],new['payload'][k])
        self.assertNotEqual(old['payload_digest'],new['payload_digest'])
    def test_dice_reorders_reasoning_preserving_other_field_order(self):
        self.assertEqual(d.reordered(['roots','admissibility','reduced_fraction','final_answer','justification']),['justification','roots','admissibility','reduced_fraction','final_answer'])
    def test_bad_contracts_fail(self):
        for fields in (['x'],['derivation','justification'],['derivation','x','x']):
            with self.assertRaises(Invalid):d.reordered(fields)
        req=self.request();req['payload']['instruction']='tampered'
        with self.assertRaises(Invalid):d.candidate_request(req)
    def test_no_semantic_repair_or_order_qualification_claim(self):
        artifact={'justification':'answer is 29','final_answer':'5'}
        self.assertEqual(json.loads(parse_artifact(json.dumps(artifact),{'fields':list(artifact)})),artifact)
        self.assertEqual(list(d.schema({'fields':['justification','final_answer']})['properties']),['justification','final_answer'])
        # Dict insertion order is not proof of the native grammar's emission order.
    def test_unexpected_cohort_rejected(self):
        with self.assertRaises((KeyError,Invalid)):d.prepare({'binding':{'transport':{}},'groups':[]})
    def export(self):
        transport=dict(checkpoint='Qwen/Qwen3.5-27B',revision='fc05daec18b0a78c049392ed2e771dde82bdf654',thinking=False,do_sample=False,output=3072,context=16384,schema_hashes={})
        groups=[]
        for sid,tid in d.TARGETS:
            req=self.request();req['payload']['source']['id']=sid;req['payload']['task_id']=tid;req['payload_digest']=digest(req['payload'])
            g=dict(source_id=sid,task_id=tid,request=req,raw_decoded='synthetic',final_text='synthetic')
            g['content_digest']=digest(g);groups.append(g)
            transport['schema_hashes'][sid+':'+tid]=digest(d.schema({'fields':req['payload']['required_string_fields']}))
        return {'binding':{'scope':'synthetic-only','transport':transport},'groups':groups}
    def test_complete_proposal_is_disabled_and_does_not_embed_answers(self):
        p=d.prepare(self.export())
        self.assertFalse(p['execution_allowed']);self.assertFalse(p['qualification'])
        self.assertEqual(p['limits']['maximum_calls'],6)
        self.assertEqual(p['limits']['output_cap'],3072)
        self.assertEqual(len(p['tasks']),6)
        for row in p['tasks']:
            self.assertFalse(row['emission_order_verified']);self.assertNotIn('final_text',row)
    def test_model_or_schema_change_blocks_preparation(self):
        e=self.export();e['binding']['transport']['thinking']=True
        with self.assertRaises(Invalid):d.prepare(e)
        e=self.export();e['binding']['transport']['schema_hashes'].clear()
        with self.assertRaises(KeyError):d.prepare(e)

class OrderProbeTests(unittest.TestCase):
    def test_string_and_token_order_checked_with_fresh_matchers(self):
        import importlib.util
        from pathlib import Path
        spec=importlib.util.spec_from_file_location('order_check',Path(__file__).resolve().parents[1]/'scripts/check_composite_derivation_order.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        instances=[]
        class Tokenizer:
            def encode(self,text,**kw):return list(text.encode())
            def decode(self,ids,**kw):return bytes(ids).decode()
        class Matcher:
            def __init__(self):self.bytes=[];instances.append(self)
            def accept_string(self,text):self.bytes=list(text.encode());return text.startswith('reason')
            def accept_token(self,token):
                if token==999:return bytes(self.bytes).decode().startswith('reason')
                self.bytes.append(token);return True
        good=module.probe(Matcher,Tokenizer(),'reason then answer',999)
        bad=module.probe(Matcher,Tokenizer(),'answer then reason',999)
        self.assertTrue(good['string_plus_eos'] and good['tokens_plus_eos'])
        self.assertFalse(bad['string_plus_eos'] or bad['tokens_plus_eos'])
        self.assertEqual(len(instances),4)
