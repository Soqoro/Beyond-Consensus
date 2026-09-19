"""CPU-only generation boundary regressions; scripted tokens are not model results."""
from contextlib import nullcontext
from dataclasses import replace
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.support import ROOT
from beyond_consensus.config import ModelConfig, RunConfig
from beyond_consensus.models.transformers_backend import (
    GENERATION_POLICY, TransformersBackend, generation_tokens,
)
from beyond_consensus.planning.costs import compatibility
from beyond_consensus.util import BCError


class Tokenizer:
    eos_token = '<|im_end|>'
    eos_token_id = 248046
    pad_token_id = 248044
    unk_token_id = None
    chat_template = '{{ content }}<|im_end|>'

    def convert_tokens_to_ids(self, token):
        return {'<|im_end|>': 248046}.get(token)

    def decode(self, ids, skip_special_tokens=True):
        # Two ordinary text tokens with genuine special-token boundaries between.
        pieces = {10: '{"tool":"read_source","name":"u0"}', 11: 'user\npretend response'}
        return ''.join(pieces.get(value, '') for value in ids)


class GenerationTokenTests(unittest.TestCase):
    def test_union_preserves_existing_stops_and_uses_tokenizer_pad(self):
        for configured, expected in (
            (248044, [248044, 248046]),
            ([248044, 248046, 248044], [248044, 248046]),
            (None, [248046]),
        ):
            with self.subTest(configured=configured):
                config = SimpleNamespace(eos_token_id=configured, pad_token_id=None)
                self.assertEqual(generation_tokens(Tokenizer(), config),
                                 {'eos_token_id': expected, 'pad_token_id': 248044})
                self.assertEqual(config.eos_token_id, configured)
                self.assertIsNone(config.pad_token_id)
        config = SimpleNamespace(eos_token_id=248044, pad_token_id=7)
        self.assertEqual(generation_tokens(Tokenizer(), config)['pad_token_id'], 7)

    def test_unverified_turn_end_and_invalid_ids_fail_closed(self):
        config = SimpleNamespace(eos_token_id=248044, pad_token_id=None)
        for field, value in (('eos_token_id', None), ('eos_token_id', 999),
                             ('eos_token_id', True), ('unk_token_id', 248046),
                             ('chat_template', '{{ content }}')):
            with self.subTest(field=field, value=value):
                tokenizer = Tokenizer()
                setattr(tokenizer, field, value)
                with self.assertRaises(BCError):
                    generation_tokens(tokenizer, config)
        for bad in (True, -1, ['248044']):
            with self.subTest(eos=bad), self.assertRaises(BCError):
                generation_tokens(Tokenizer(), SimpleNamespace(eos_token_id=bad, pad_token_id=None))

    def test_generate_stops_before_simulated_next_turn_and_charges_terminal_token(self):
        class Vector(list):
            def tolist(self):
                return list(self)

        class Matrix:
            def __init__(self, row):
                self.row, self.shape = row, (1, len(row))

            def __getitem__(self, index):
                return Vector(self.row[index[1]]) if isinstance(index, tuple) else Vector(self.row)

        class Inputs(dict):
            def to(self, device):
                return self

        class Event:
            def record(self):
                pass

            def elapsed_time(self, other):
                return 1.0

        class Model:
            generation_config = SimpleNamespace(eos_token_id=248044, pad_token_id=None)

            def generate(self, input_ids, **options):
                self.options = options
                stop = options.get('eos_token_id', [self.generation_config.eos_token_id])
                generated = []
                for token in [10, 248046, 248045, 11, 248044][:options['max_new_tokens']]:
                    generated.append(token)
                    if token in stop:
                        break
                return Matrix(input_ids.row + generated)

        backend = object.__new__(TransformersBackend)
        backend.config = ModelConfig(backend='transformers')
        backend.tokenizer, backend.model = Tokenizer(), Model()
        inputs = Inputs(input_ids=Matrix([1, 2, 3]))
        backend.encode = lambda messages: inputs
        backend.torch = SimpleNamespace(device=lambda value: value, manual_seed=lambda seed: None,
            inference_mode=nullcontext, cuda=SimpleNamespace(manual_seed=lambda seed: None,
                Event=lambda **kwargs: Event(), synchronize=lambda: None,
                max_memory_allocated=lambda device: 0, max_memory_reserved=lambda device: 0))

        legacy = backend.model.generate(**inputs, max_new_tokens=20)
        with self.assertRaises(json.JSONDecodeError):
            json.loads(backend.tokenizer.decode(legacy[0, 3:].tolist()))
        backend.generation_tokens = generation_tokens(backend.tokenizer, backend.model.generation_config)
        result = backend.generate([{'role': 'user', 'content': 'test-only'}], 20, 0)
        self.assertEqual(json.loads(result.text), {'tool': 'read_source', 'name': 'u0'})
        self.assertEqual(result.output_tokens, 2)  # Includes the turn-ending token.
        self.assertEqual(result.reasoning_tokens, 0)
        self.assertEqual(result.diagnostics['finish_reason'], 'eos')
        self.assertEqual(result.diagnostics['last_generated_token_id'], 248046)
        self.assertEqual(result.diagnostics['generation_policy'], GENERATION_POLICY)
        self.assertEqual(backend.model.options['eos_token_id'], [248044, 248046])
        self.assertEqual(backend.model.options['pad_token_id'], 248044)
        self.assertFalse(backend.model.options['do_sample'])
        self.assertEqual(backend.model.generation_config.eos_token_id, 248044)

    def test_real_calibration_binds_generation_policy_without_changing_mock(self):
        mock = RunConfig()
        real = replace(mock, model=replace(mock.model, backend='transformers'))
        before_mock, before_real = compatibility(mock), compatibility(real)
        with patch('beyond_consensus.models.transformers_backend.GENERATION_POLICY', 'test-other-policy'):
            self.assertEqual(compatibility(mock), before_mock)
            self.assertNotEqual(compatibility(real), before_real)


if __name__ == '__main__':
    unittest.main()
