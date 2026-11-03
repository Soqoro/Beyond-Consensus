"""Pinned local Qwen transport preparation; real entry point is release-disabled.

Standard-library imports only. Component injection is for offline tests, never
qualification evidence. No change to the Phase II worker backend registry.
"""
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from .model import Invalid, digest, plain
from . import planner_first as planner
from .planner_ledger import MockPlannerSession, CONTEXT, OUTPUT, MAX_CALLS

CHECKPOINT = 'Qwen/Qwen3.5-27B'
REVISION = 'fc05daec18b0a78c049392ed2e771dde82bdf654'
# A future reviewed release must implement exact approval/qualification checking
# before changing this gate. Environment variables and JSON flags cannot open it.
_REAL_EXECUTION_RELEASED = False


def _ids(value, *, empty=False):
    if hasattr(value, 'tolist'): value = value.tolist()
    if type(value) is list and len(value) == 1 and type(value[0]) is list:
        value = value[0]
    if (type(value) is not list or (not value and not empty)
            or any(type(i) is not int or i < 0 for i in value)):
        raise Invalid('expected one integer token sequence')
    return value


def _file_hash(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''): value.update(block)
    return value.hexdigest()


def verify_local_inventory(lock):
    """Verify an explicitly supplied inventory; never discover/download weights."""
    if (type(lock) is not dict or lock.get('checkpoint') != CHECKPOINT
            or lock.get('revision') != REVISION):
        raise Invalid('pinned checkpoint/revision required')
    root = Path(lock['local_path'])
    if not root.is_absolute() or root.name != REVISION or not root.is_dir():
        raise Invalid('local pinned snapshot path required')
    inventory = lock.get('files')
    required = {'config.json', 'generation_config.json', 'tokenizer.json',
        'tokenizer_config.json', 'model.safetensors.index.json'}
    if type(inventory) is not dict or not required <= set(inventory):
        raise Invalid('complete local inventory required')
    for name, expected in inventory.items():
        if (type(name) is not str or Path(name).name != name or name in ('.', '..')
                or type(expected) is not str or len(expected) != 64
                or any(c not in '0123456789abcdef' for c in expected)):
            raise Invalid('inventory entry')
        if not (root/name).is_file() or _file_hash(root/name) != expected:
            raise Invalid('local file hash mismatch')
    index = json.loads((root/'model.safetensors.index.json').read_text())
    weights = index.get('weight_map')
    if type(weights) is not dict or not weights:
        raise Invalid('empty weight index')
    if any(type(name) is not str or not name.endswith('.safetensors')
           or name not in inventory for name in weights.values()):
        raise Invalid('unbound weight shard')
    # All snapshot files that a loader could consume must be bound, including
    # optional added/special-token files. HF blob symlinks are hash-verified above.
    if any(p.is_file() and p.name not in inventory for p in root.iterdir()):
        raise Invalid('unbound snapshot file')
    # The loader must not consume a separate unbound template file.
    for name in ('chat_template.jinja',):
        if (root/name).exists() and name not in inventory:
            raise Invalid('unbound chat template')
    if (root/'chat_templates').exists():
        raise Invalid('multiple external templates not supported')
    config = json.loads((root/'config.json').read_text())
    if config.get('architectures') != ['Qwen3_5ForConditionalGeneration']:
        raise Invalid('checkpoint architecture')
    return root


def open_local(lock, *, authorization=None):
    """No imports before the default gate or exact D1 release validation."""
    if not _REAL_EXECUTION_RELEASED:
        if authorization is None:
            raise Invalid('real planner loading disabled: exact execution/qualification release pending')
        from .joint_d1_launch import validate_authorization
        scope = validate_authorization(Path(__file__).resolve().parents[2], authorization)
        report = scope['verification']
        expected = {'checkpoint': CHECKPOINT, 'revision': REVISION,
                    'local_path': report['local_path'], 'files': report['inventory']['files']}
        if lock != expected:
            raise Invalid('D1 authorized inventory mismatch')
    # No CLI or environment switch unlocks arbitrary scopes. Offline tests do
    # not qualify this loader's model competence or worst-case memory fit.
    from beyond_consensus.models.transformers_backend import require_allocation
    require_allocation()
    root = verify_local_inventory(lock)
    import torch
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    if torch.cuda.device_count() != 1:
        raise Invalid('local planner placement requires one visible GPU; no automatic sharding')
    if authorization is not None and torch.cuda.get_device_properties(0).total_memory < 80_000_000_000:
        raise Invalid('D1 requires an 80GB-class GPU before loading')
    tokenizer = AutoTokenizer.from_pretrained(str(root), local_files_only=True, trust_remote_code=False)
    model = Qwen3_5ForConditionalGeneration.from_pretrained(str(root),
        local_files_only=True, trust_remote_code=False, use_safetensors=True,
        dtype=torch.bfloat16, attn_implementation='sdpa')
    # Same single-device transfer as RepoRecourse; no Accelerate device_map.
    model.to(torch.device('cuda:0'))
    model.requires_grad_(False)
    model.eval()
    return QwenTransport(tokenizer, model, torch, evidence='local_runtime_unqualified', lock=lock)


def render_qwen_request(tokenizer, request, template_hash):
    if digest(tokenizer.chat_template) != template_hash:
        raise Invalid('template changed after binding')
    payload = request['payload']
    messages = [{'role': 'user', 'content': json.dumps(payload, ensure_ascii=False, sort_keys=True)}]
    text = tokenizer.apply_chat_template(messages, tokenize=False,
        add_generation_prompt=True, enable_thinking=True)
    if type(text) is not str or not text.rstrip().endswith('<think>'):
        raise Invalid('template must open reasoning at end of generation prefix')
    encoded = tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=True, enable_thinking=True, return_dict=True, return_tensors=None)
    ids = _ids(encoded.get('input_ids') if isinstance(encoded, Mapping) else encoded)
    if ids != tokenizer.encode(text, add_special_tokens=False):
        raise Invalid('rendered text/token binding mismatch')
    if len(ids) + OUTPUT > CONTEXT:
        raise Invalid('context overflow; no prompt truncation')
    return {'messages': messages, 'rendered_text': text, 'input_ids': ids,
            'input_tokens': len(ids), 'payload_digest': request['payload_digest']}


class QwenTransport:
    """Shared measured-token plumbing, exercised only with injected doubles here."""
    def __init__(self, tokenizer, model, torch, *, evidence='injected_offline_double', lock=None):
        from beyond_consensus.models.transformers_backend import generation_tokens, verify_thinking_template
        self.tokenizer, self.model, self.torch = tokenizer, model, torch
        self.evidence = evidence
        self.template = verify_thinking_template(tokenizer, True)
        self.tokens = generation_tokens(tokenizer, model.generation_config)
        closing = tokenizer.convert_tokens_to_ids('</think>')
        if type(closing) is not int or closing < 0 or tokenizer.encode('</think>', add_special_tokens=False) != [closing]:
            raise Invalid('single verified thinking-close token required')
        if closing in self.tokens['eos_token_id']:
            raise Invalid('thinking close cannot be EOS')
        self.closing = closing
        self.binding = {'checkpoint': CHECKPOINT, 'revision': REVISION,
            'inventory_digest': digest(lock) if lock else None, 'template': self.template,
            'tokens': self.tokens, 'closing_id': closing, 'evidence': evidence,
            'do_sample': False, 'thinking': True, 'context_limit': CONTEXT, 'output_cap': OUTPUT}

    def render(self, request):
        return render_qwen_request(self.tokenizer, request, self.template['template_hash'])

    def generate(self, rendered):
        torch = self.torch
        ids = rendered['input_ids']
        inputs = torch.tensor([ids], dtype=torch.long, device='cuda:0')
        mask = torch.ones_like(inputs)
        start = time.monotonic()
        with torch.inference_mode():
            result = self.model.generate(input_ids=inputs, attention_mask=mask,
                max_new_tokens=OUTPUT, do_sample=False, use_cache=True,
                num_beams=1, num_return_sequences=1,
                return_dict_in_generate=True, **self.tokens)
        torch.cuda.synchronize()
        sequence = _ids(result.sequences)
        if sequence[:len(ids)] != ids:
            raise Invalid('generation prefix mismatch; usage unresolved')
        generated = sequence[len(ids):]
        # Preserve all generated IDs: reasoning, delimiters and EOS are charged.
        observation = {'input_tokens': len(ids), 'output_tokens': len(generated),
            'generated_ids': generated, 'input_ids_digest': digest(ids),
            'raw_decoded': self.tokenizer.decode(generated, skip_special_tokens=False,
                clean_up_tokenization_spaces=False), 'final_text': None,
            'reasoning_tokens': None, 'boundary_error': None,
            'wall_seconds': time.monotonic()-start, 'evidence': self.evidence}
        eos = self.tokens['eos_token_id']
        observation['finish_reason'] = ('eos' if generated and generated[-1] in eos else
            'length_limit' if len(generated) >= OUTPUT else 'unknown')
        if len(generated) > OUTPUT:
            observation['boundary_error'] = 'output_usage_overrun'
        elif generated.count(self.closing) != 1:
            observation['boundary_error'] = 'exactly_one_generated_thinking_close_required'
        else:
            boundary = generated.index(self.closing)+1
            observation['reasoning_tokens'] = boundary
            final = generated[boundary:]
            if final and final[-1] in eos: final = final[:-1]
            if any(i in eos for i in generated[:-1]):
                observation['boundary_error'] = 'unexpected_interior_eos'
            else:
                # No strip/Markdown extraction/JSON repair or general special-token removal.
                observation['final_text'] = self.tokenizer.decode(final, skip_special_tokens=False,
                    clean_up_tokenization_spaces=False)
        return observation


class QwenPlannerSession(MockPlannerSession):
    """Reuses atomic persistence/locking only, with separate schema/evidence.

    The only constructible transport in this release uses injected doubles.
    It is never labelled a real model call or a GPU qualification.
    """
    def __init__(self, directory, requests, transport):
        if type(transport) is not QwenTransport or transport.evidence != 'injected_offline_double':
            raise Invalid('this release only permits injected offline transport doubles')
        # Reuse request validation without creating an intermediate mock ledger.
        if type(requests) is not list or len(requests) != 3:
            raise Invalid('three frozen requests required')
        frozen = []
        for request in requests:
            try:
                provenance = request['protected_provenance']
                expected = planner.make_request({'id': provenance['source_id'],
                    'problem': request['payload']['problem_statement']}, provenance['source_binding'])
            except (KeyError, TypeError) as exc:
                raise Invalid('request envelope') from exc
            if expected != request: raise Invalid('request binding')
            frozen.append(json.loads(json.dumps(expected)))
        if len({r['protected_provenance']['source_id'] for r in frozen}) != 3:
            raise Invalid('duplicate sources')
        self.transport = transport
        self.binding = {'requests': frozen, 'transport': json.loads(json.dumps(transport.binding)),
            'maximum_calls': MAX_CALLS, 'maximum_total_tokens': CONTEXT*MAX_CALLS,
            'gpu_allocation': None, 'real_execution_allowed': False,
            'implementation': {name: _file_hash(Path(__file__).parent/name) for name in
                ('planner_qwen.py', 'planner_ledger.py', 'planner_first.py', 'response_boundary.py', 'model.py')},
            'shared_transformers_helpers_sha256': _file_hash(Path(__file__).parents[1] /
                'beyond_consensus/models/transformers_backend.py')}
        self.root = Path(directory); self.root.mkdir(parents=True, exist_ok=True)
        with self._locked():
            if self.path.exists(): self._read()
            else: self._save({'schema': 'phase2-qwen-adapter-offline-ledger-v1',
                'binding': self.binding, 'binding_digest': digest(self.binding),
                'evidence': 'injected_offline_double', 'attempts': [],
                'model_executed': False, 'task_execution_allowed': False})

    def advance(self, source_id):
        if (self.transport.evidence != 'injected_offline_double'
                or self.transport.binding != self.binding['transport']):
            raise Invalid('transport binding/evidence changed')
        with self._locked():
            state = self._read()
            if any(a['state'] != 'completed' for a in state['attempts']):
                raise Invalid('unresolved or violated attempt; no replay')
            if len(state['attempts']) >= MAX_CALLS: raise Invalid('six-call protocol cap')
            request = next((r for r in self.binding['requests'] if
                r['protected_provenance']['source_id'] == source_id), None)
            if request is None: raise Invalid('source outside frozen scope')
            previous = [a for a in state['attempts'] if a['source_id'] == source_id]
            outbound = request
            if previous:
                if len(previous) != 1 or previous[0].get('boundary_error'):
                    raise Invalid('no further correction')
                outbound = planner.correction_request(request,
                    planner.review_transcript(request, [previous[0]['raw']]))
            rendered = self.transport.render(outbound)
            reservation = rendered['input_tokens'] + OUTPUT
            if self._totals(state)['simulated_actual_tokens'] + reservation > CONTEXT*MAX_CALLS:
                raise Invalid('total token cap')
            attempt = {'source_id': source_id, 'attempt': len(previous), 'state': 'reserved',
                'outbound_payload': outbound['payload'], 'rendered': rendered,
                'reservation_tokens': reservation, 'actual_tokens': None, 'raw': None,
                'reserved_at': datetime.now(timezone.utc).isoformat()}
            state['attempts'].append(attempt); self._save(state)
            # Exceptions leave a durable reservation. No automatic fallback/retry.
            observed = self.transport.generate(rendered)
            # Bound decoded evidence without altering the parser input. Token
            # IDs remain the exact generated sequence, including reasoning/EOS.
            saved_observation = dict(observed)
            for key in ('raw_decoded', 'final_text'):
                value = saved_observation[key]
                if type(value) is str and len(value.encode('utf-8', errors='replace')) > planner.MAX_RESPONSE_BYTES:
                    saved_observation[key] = None
                    saved_observation[key+'_digest'] = digest(value)
                    saved_observation[key+'_retention'] = 'oversized_text_digest_only'
            attempt['observation'] = saved_observation
            attempt['actual_tokens'] = observed['input_tokens'] + observed['output_tokens']
            attempt['boundary_error'] = observed['boundary_error']
            attempt['state'] = 'usage_violation' if observed['output_tokens'] > OUTPUT else 'completed'
            text = observed['final_text']
            if type(text) is str and len(text.encode('utf-8', errors='replace')) <= planner.MAX_RESPONSE_BYTES:
                attempt['raw'] = text
            else:
                attempt['boundary_error'] = attempt['boundary_error'] or 'missing_or_oversized_final_response'
            attempt['review'] = plain(planner.review_transcript(request,
                [a['raw'] for a in previous] + [attempt['raw']]))
            attempt['observed_at'] = datetime.now(timezone.utc).isoformat()
            self._save(state)
            return {**attempt, 'totals': self._totals(state), 'model_executed': False}
