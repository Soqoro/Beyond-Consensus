"""Stdlib byte/token-boundary controls; no native matcher or GPU claims."""
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tests.test_action_constraints import Matrix
from beyond_consensus.models.unique_keys import KeyState, DuplicateKey, UniqueKeyProcessor, synthetic_controls, qualify_unique_keys, MODE
from beyond_consensus.models.action_schema import action_schema, contract, validate_action
from beyond_consensus.models.constrained import ReasoningGate
from beyond_consensus.util import BCError


class UniqueKeys(unittest.TestCase):
    def test_byte_probe_distinguishes_normalization_from_native_mismatch(self):
        import importlib.util
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / 'scripts/probe_unique_token_bytes.py'
        spec = importlib.util.spec_from_file_location('unique_token_probe', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        row = module.compare(4, 'e\u0301', 'é'.encode(), 'é')
        self.assertFalse(row['roundtrip'])
        self.assertTrue(row['native_matches_hf'])
        self.assertTrue(row['native_matches_nfc'])
        row = module.compare(4, 'e\u0301', b'wrong', 'e\u0301')
        self.assertFalse(row['native_matches_hf'])
        self.assertFalse(row['native_matches_nfc'])
        self.assertTrue(row['hf_matches_original'])

    def test_native_controls_survive_nfc_without_collapsing_json_keys(self):
        import unicodedata
        good, bad = synthetic_controls()
        for text in good + bad:
            self.assertEqual(unicodedata.normalize('NFC', text), text)
        text = good[4]
        fields = json.loads(text)['content']['fields']
        self.assertEqual(fields, {'é': 1, 'e\u0301': 2, '😀': 3})
        # Literal decomposed UTF-8 remains valid to the guard too. This local
        # byte test deliberately bypasses tokenizer input normalization.
        raw = text.replace(r'e\u0301', 'e\u0301').encode('utf-8')
        self.assertTrue(KeyState().allows(raw))
        for split in range(len(raw) + 1):
            state = KeyState().feed(raw[:split]).feed(raw[split:])
            self.assertEqual(state.frames, [])

    def test_equivalent_public_schema_distinct_contract(self):
        old = 'reporecourse-json-reliable-v1-pool-7'
        self.assertEqual(action_schema(old), action_schema(MODE))
        self.assertNotEqual(contract(old), contract(MODE))
        self.assertNotIn('duplicate_key_enforcement', contract(old))

    def test_all_byte_splits_unicode_escapes_nested_scopes(self):
        good, bad = synthetic_controls()
        for text in good + bad:
            raw = text.encode()
            for split in range(len(raw) + 1):
                with self.subTest(text=text, split=split):
                    state = KeyState()
                    if text in good:
                        validate_action(text, MODE)
                        state.feed(raw[:split]).feed(raw[split:])
                        self.assertEqual(state.frames, [])
                        self.assertFalse(state.in_string)
                    else:
                        with self.assertRaises(DuplicateKey):
                            state.feed(raw[:split]).feed(raw[split:])
                        with self.assertRaises(BCError):validate_action(text, MODE)

    def test_bytewise_and_single_token_duplicate(self):
        good, bad = synthetic_controls()
        for text in good:
            state = KeyState()
            for byte in text.encode():
                self.assertTrue(state.allows(bytes([byte])))
                state.feed(bytes([byte]))
        for text in bad:
            self.assertFalse(KeyState().allows(text.encode()))
            state = KeyState()
            blocked = False
            for byte in text.encode():
                piece = bytes([byte])
                if not state.allows(piece):
                    blocked = True
                    break
                state.feed(piece)
            self.assertTrue(blocked)

    def test_speculative_candidates_do_not_mutate_scopes(self):
        state = KeyState().feed(b'{"x":1,')
        snapshot = (state.frames.copy(), state.key, state.in_string)
        self.assertFalse(state.allows(b'"x":2}'))
        self.assertTrue(state.allows(b'"xy":2}'))
        self.assertTrue(state.allows(b'"y":{"x":2}}'))
        self.assertEqual(snapshot, (state.frames, state.key, state.in_string))

    def test_duplicate_at_token_boundary_may_extend_to_unique_key(self):
        state = KeyState().feed(b'{"x":1,"x')
        self.assertFalse(state.allows(b'":2}'))
        self.assertTrue(state.allows(b'y":2}'))


# Minimal tensor protocol double for exercising the actual masking wrapper.
class Vector(list):
    def index_select(self, dim, indices):return Vector(self[i] for i in indices)
    def __getitem__(self, key):
        if isinstance(key, Vector):return Vector(v for v, keep in zip(self, key) if keep)
        return super().__getitem__(key)
    def tolist(self):return list(self)
    def any(self):return SimpleNamespace(item=lambda: any(self))


class Scores:
    device = 'cpu'
    def __init__(self, values):self.values = Vector(values)
    def __getitem__(self, key):return self.values if key == 0 else self.values[key[1]]
    def __setitem__(self, key, value):
        for i in key[1]:self.values[i] = value


class IDs(Matrix):
    def __getitem__(self, key):
        if isinstance(key[1], int):return self.row[key[1]]
        return super().__getitem__(key)


TORCH = SimpleNamespace(long=int,
    tensor=lambda ids, **kw: Vector(ids),
    isfinite=lambda scores: Vector(v != float('-inf') for v in (scores.values if isinstance(scores, Scores) else scores)))


class ProcessorTests(unittest.TestCase):
    def processor(self, vocab, inner=None, **kw):
        return UniqueKeyProcessor(inner or (lambda ids, scores: scores), vocab, [len(vocab)-1], **kw)

    def test_mask_intersection_and_reasoning_boundary(self):
        vocab = [b'{"x":1,', b'"x":2}', b'"y":2}', b'never', b'EOS']
        with patch.dict('sys.modules', torch=TORCH):
            processor = self.processor(vocab)
            gate = ReasoningGate(processor, 2, 99)
            initial = Scores([0, 0, 0, float('-inf'), float('-inf')])
            self.assertIs(gate(IDs([99, 1]), initial), initial)
            self.assertIsNone(processor.length)
            gate(IDs([99, 1, 99]), initial)
            masked = gate(IDs([99, 1, 99, 0]), Scores([float('-inf'), 0, 0, float('-inf'), float('-inf')]))
            self.assertEqual(masked.values, [float('-inf'), float('-inf'), 0, float('-inf'), float('-inf')])
            self.assertGreater(processor.blocked_tokens, 0)
            # New generation does not inherit keys.
            fresh = self.processor(vocab)
            self.assertEqual(fresh.state.frames, [])

    def test_committed_violation_no_continuation_and_sequence_are_errors(self):
        vocab = [b'{"x":1,"x":2}', b'EOS']
        with patch.dict('sys.modules', torch=TORCH):
            p = self.processor(vocab)
            with self.assertRaises(BCError):p(IDs([42]), Scores([0, float('-inf')]))
            p = self.processor(vocab)
            p(IDs([42]), Scores([float('-inf'), 0]))
            with self.assertRaises(BCError):p(IDs([42, 0]), Scores([0, 0]))
            p = self.processor(vocab)
            p(IDs([42]), Scores([float('-inf'), 0]))
            with self.assertRaises(BCError):p(IDs([42]), Scores([0, 0]))

    def test_cpu_exhaustion_fails_without_unmasked_fallback(self):
        clock = iter([0., 31., 31.])
        with patch.dict('sys.modules', torch=TORCH), self.assertRaises(BCError):
            self.processor([b'{}', b'"x"', b'EOS'], clock=lambda: next(clock))(IDs([42]), Scores([0, 0, 0]))

    def test_native_roundtrip_failure_identifies_control_without_qualification(self):
        tokenizer = SimpleNamespace(encode=lambda *args, **kwargs: [0])
        constraint = SimpleNamespace(unique_vocab=[b'changed'])
        with self.assertRaises(BCError) as caught:
            qualify_unique_keys(constraint, tokenizer, None, 9, [10], 11)
        details = json.loads(str(caught.exception).split(': ', 1)[1])
        self.assertEqual(details['case'], 0)
        self.assertTrue(details['expected_accepted'])
        self.assertEqual(bytes.fromhex(details['decoded_utf8_hex']), b'changed')
        self.assertEqual(bytes.fromhex(details['expected_utf8_hex']).decode(), synthetic_controls()[0][0])

    def test_bad_vocabulary_is_rejected(self):
        with self.assertRaises(BCError):self.processor(['decoded-as-text', b'EOS'])
