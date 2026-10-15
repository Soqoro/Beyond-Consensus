"""Mask support checks and bounded diagnostics without optional GPU imports."""
import math
import unittest
from tests.support import ROOT
from beyond_consensus.models.decoder_trace import Trace,score_summary,MaskDiagnosticError,exception_record
from beyond_consensus.models.unique_keys import KeyState,synthetic_controls

class TraceTests(unittest.TestCase):
    def test_negative_infinity_is_mask_not_failure(self):
        self.assertEqual(score_summary([-math.inf,0.,-2.],3)['usable_scores'],2)
    def test_empty_invalid_bounds_nan_and_positive_infinity_fail_closed(self):
        for values,vocab,indices,code in [([-math.inf]*2,2,(),'empty_allowed_intersection'),
            ([0.],2,(),'vocabulary_alignment'),([0.],1,(-1,),'token_index_bounds'),
            ([0.],1,(1,),'token_index_bounds'),([math.nan],1,(),'nan_logits'),
            ([math.inf],1,(),'positive_infinity_logits')]:
            with self.subTest(code=code),self.assertRaisesRegex(MaskDiagnosticError,code):score_summary(values,vocab,indices)
    def test_bounded_buffer_retains_started_completed_stages(self):
        trace=Trace(4)
        for i in range(100):trace.begin('native_mask',step=i);trace.end('native_mask')
        trace.begin('unique_key_mask')
        out=trace.snapshot()
        self.assertEqual(len(out['events']),4);self.assertEqual(out['events_seen'],201)
        self.assertEqual(out['last_started_stage'],'unique_key_mask');self.assertEqual(out['last_completed_stage'],'native_mask')
    def test_exception_chain_redacts_credentials_and_controls(self):
        try:
            try:raise ValueError('token=secret-value\x00')
            except ValueError as cause:raise RuntimeError('x'*9000) from cause
        except RuntimeError as error:chain=exception_record(error)
        self.assertEqual(len(chain),2);self.assertEqual(len(chain[0]['message']),2048)
        self.assertNotIn('secret-value',chain[1]['message']);self.assertNotIn('\x00',chain[1]['message'])
    def test_nfc_stable_keys_and_escape_equivalent_duplicates_unchanged(self):
        import unicodedata
        good,bad=synthetic_controls()
        self.assertTrue(all(unicodedata.normalize('NFC',text)==text for text in good+bad))
        for text in good:KeyState().feed(text.encode())
        for text in bad:
            with self.assertRaises(ValueError):KeyState().feed(text.encode())

class TensorMetadataTests(unittest.TestCase):
    def test_real_metadata_adapter_rejects_bad_support_with_cpu_tensor_double(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from beyond_consensus.models.decoder_trace import tensor_summary,ObservedProcessor
        class Scores:
            dtype='float32';device='cpu'
            def __init__(self,values):self.values=values;self.shape=(1,len(values))
        def result(values):
            return SimpleNamespace(any=lambda:SimpleNamespace(item=lambda:any(values)),
                sum=lambda:SimpleNamespace(item=lambda:sum(values)))
        torch=SimpleNamespace(isnan=lambda x:result([math.isnan(v) for v in x.values]),
            isposinf=lambda x:result([v==math.inf for v in x.values]),
            isneginf=lambda x:result([v==-math.inf for v in x.values]),
            isfinite=lambda x:result([math.isfinite(v) for v in x.values]))
        class IDs:
            def __getitem__(self,key):return 0
        with patch.dict('sys.modules',torch=torch):
            trace=Trace();wrapper=ObservedProcessor(lambda ids,scores:Scores([-math.inf,-math.inf]),trace,2)
            with self.assertRaisesRegex(MaskDiagnosticError,'empty_allowed_intersection'):wrapper(IDs(),Scores([1.,2.]))
            self.assertEqual(trace.last_started,'native_mask')
            for values in ([math.nan,0.],[math.inf,0.]):
                with self.assertRaises(MaskDiagnosticError):tensor_summary(Scores(values),2)
            self.assertEqual(tensor_summary(Scores([-math.inf,0.]),2)['usable_scores'],1)
