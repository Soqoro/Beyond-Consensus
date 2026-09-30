"""Explicit synthetic tensor-shape stress; never a worker generation policy.

The normal backend and its qualified decoder are unchanged. This diagnostic
forces an inert token, disables EOS stopping, and executes no output as a tool.
"""
import time

from ..util import BCError, digest
from .base import Generation

INPUT = 14336
OUTPUT = 2048
PROTOCOL = 'rr-forced-token-full-budget-v1'


class ForceInertToken:
    def __init__(self, token):
        self.token = token
        self.calls = 0

    def __call__(self, input_ids, scores):
        self.calls += 1
        scores.fill_(float('-inf'))
        scores[:, self.token] = 0
        return scores


def verified(diagnostics, output_tokens):
    """A short response or unavailable cache evidence never passes geometry."""
    return (output_tokens == OUTPUT
        and diagnostics.get('rendered_input_tokens') == INPUT
        and diagnostics.get('observed_cache_sequence_length') == INPUT + OUTPUT - 1
        and diagnostics.get('forced_token_verified') is True
        and diagnostics.get('force_mask_calls') == OUTPUT)


def generate(backend, messages, max_new_tokens, seed):
    from .transformers_backend import require_allocation, cache_dtypes
    require_allocation()
    if (backend.config.context_limit != INPUT + OUTPUT or max_new_tokens != OUTPUT
            or backend.config.checkpoint != 'Qwen/Qwen3.5-27B'
            or backend.config.dtype != 'bfloat16'):
        raise BCError('Stress requires the fixed 16K/2048 BF16 profile')
    torch = backend.torch
    encoded = backend.encode(messages)
    if set(encoded) != {'input_ids', 'attention_mask'}:
        raise BCError('Stress supports text input_ids/attention_mask only')
    ids = encoded['input_ids']
    size = int(ids.shape[-1])
    if ids.shape[0] != 1 or not 14080 <= size <= INPUT:
        raise BCError('Unexpected synthetic stress input shape')
    candidates = backend.tokenizer.encode('x', add_special_tokens=False)
    if len(candidates) != 1 or candidates[0] in backend.generation_tokens['eos_token_id']:
        raise BCError('Cannot select a single inert non-EOS token')
    token = candidates[0]
    # Padding is a labelled tensor-shape intervention before the synthetic prompt,
    # not silent truncation or a change to task histories. Attention stays enabled.
    prefix = torch.full((1, INPUT-size), token, dtype=ids.dtype, device=ids.device)
    ids = torch.cat((prefix, ids), dim=-1).to(torch.device('cuda:0'))
    mask = torch.ones_like(ids)
    processor = ForceInertToken(token)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
    wall = time.monotonic()
    start.record()
    with torch.inference_mode():
        output = backend.model.generate(input_ids=ids, attention_mask=mask,
            max_new_tokens=OUTPUT, min_new_tokens=OUTPUT, do_sample=False,
            use_cache=True, return_dict_in_generate=True,
            eos_token_id=None, forced_eos_token_id=None,
            pad_token_id=backend.generation_tokens['pad_token_id'],
            logits_processor=[processor])
    end.record()
    torch.cuda.synchronize()
    result = output.sequences[0, INPUT:].tolist()
    cache = getattr(output, 'past_key_values', None)
    try:
        length = int(cache.get_seq_length()) if cache is not None else None
    except (AttributeError, TypeError, ValueError):
        length = None
    diagnostics = dict(stress_protocol=PROTOCOL, rendered_input_tokens=INPUT,
        original_rendered_input_tokens=size, inert_prefix_tokens=INPUT-size,
        rendered_input_ids_hash=digest(ids[0].tolist()), forced_token_id=token,
        forced_token_verified=len(result) == OUTPUT and all(t == token for t in result),
        force_mask_calls=processor.calls, observed_cache_sequence_length=length,
        state_dtypes=cache_dtypes(cache), finish_reason='synthetic_fixed_length',
        constraint_complete=None, normal_decoder_applied=False,
        generation_wall_seconds=time.monotonic()-wall)
    return Generation('', len(result), None, start.elapsed_time(end)/1000, diagnostics)
