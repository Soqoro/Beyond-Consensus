"""Bounded, synthetic-only decoder metadata; imports remain standard-library only."""
from collections import deque
import hashlib
import math
import re
import traceback
from ..util import BCError


class MaskDiagnosticError(BCError):
    pass


def safe_message(value, limit=2048):
    # Terminal controls and common credential-shaped values are never persisted.
    text = ''.join(c if c in '\n\t' or ord(c) >= 32 else '?' for c in str(value))
    text = re.sub(r'(?i)(token|password|secret|api[_-]?key)\s*[=:]\s*\S+', r'\1=<redacted>', text)
    return text[:limit]


def exception_record(exc):
    chain=[];seen=set();current=exc
    while current is not None and id(current) not in seen and len(chain)<4:
        seen.add(id(current))
        frames=list(traceback.walk_tb(current.__traceback__))[-12:]
        chain.append(dict(type=type(current).__name__, message=safe_message(current),
            frames=[dict(file=f.f_code.co_filename[-512:],line=n,function=f.f_code.co_name[:128]) for f,n in frames]))
        current=current.__cause__ or (None if current.__suppress_context__ else current.__context__)
    return chain


class UniquePrefixEvidence:
    """Explicit synthetic-only action bytes; prompt/reasoning are never fed here."""
    def __init__(self):
        self.tokens=deque(maxlen=64);self.tail=b'';self.count=0;self.byte_count=0
        self.hash=hashlib.sha256()
    def feed(self, token, piece):
        self.count+=1;self.byte_count+=len(piece);self.hash.update(piece)
        self.tokens.append(token);self.tail=(self.tail+piece)[-2048:]
    def snapshot(self):
        return dict(action_tokens_committed=self.count,action_bytes_committed=self.byte_count,
            action_prefix_sha256=self.hash.hexdigest(),action_tail_hex=self.tail.hex(),
            action_tail_truncated=self.byte_count>2048,action_token_tail=list(self.tokens),
            action_token_tail_truncated=self.count>64,
            meaning='JSON action prefix only; not total generated tokens or completed response')


def native_allowed_snapshot(inner, vocab_size):
    # ObservedProcessor wraps the native matcher. Inspect CPU metadata only.
    native=getattr(inner,'inner',inner)
    mask=getattr(native,'token_bitmask',None)
    if mask is None or str(mask.device)!='cpu':
        return dict(status='unavailable',reason='no_cpu_native_bitmask')
    words=mask[0].tolist();count=0;sample=[]
    for index,word in enumerate(words):
        width=min(32,max(0,vocab_size-index*32))
        bits=int(word)&((1<<width)-1)
        count+=bits.bit_count()
        if len(sample)<64:
            sample.extend(index*32+i for i in range(width) if bits&(1<<i))
            sample=sample[:64]
    return dict(status='observed',allowed_count=count,token_ids=sample,truncated=count>64,
                meaning='native grammar bitmask; does not establish finite model scores')


def unique_failure_snapshot(state, candidates, blocked, vocab, inner, size):
    def sample(ids):
        return [dict(token_id=i,piece_hex=vocab[i][:128].hex(),piece_truncated=len(vocab[i])>128)
                for i in ids[:64]]
    return dict(input_sequence_length=size,
        finite_quote_candidates_count=len(candidates),finite_quote_candidates=sample(candidates),
        finite_quote_candidates_truncated=len(candidates)>64,
        blocked_count=len(blocked),blocked=sample(blocked),blocked_truncated=len(blocked)>64,
        native_grammar=native_allowed_snapshot(inner,len(vocab)),
        state=dict(depth=len(state.frames),in_string=state.in_string,is_key=state.is_key,
            escaped=state.escaped,key_tail_hex=state.key[-256:].hex(),key_truncated=len(state.key)>256,
            top_scope_key_count=len(state.frames[-1][2]) if state.frames else 0),
        interpretation='no finite score after unique mask; candidates are finite quote tokens before unique mask, not all grammar tokens')


class Trace:
    def __init__(self, limit=32, *, capture_unique_prefix=False):
        self.unique_prefix = UniquePrefixEvidence() if capture_unique_prefix else None
        self.forward_inputs=[]
        self.events=deque(maxlen=limit);self.count=0;self.last_started=None;self.last_completed=None;self.steps=0
    def begin(self, stage, **metadata):
        self.last_started=stage;self._event(stage,'started',metadata)
    def end(self, stage, **metadata):
        self.last_completed=stage;self._event(stage,'completed',metadata)
    def _event(self, stage, status, metadata):
        self.count+=1;self.events.append(dict(sequence=self.count,stage=stage,status=status,**metadata))
    def snapshot(self):
        return dict(forward_inputs=self.forward_inputs,unique_key_failure=getattr(self,'unique_key_failure',None),
            unique_prefix=self.unique_prefix.snapshot() if self.unique_prefix else None,
            last_started_stage=self.last_started,last_completed_stage=self.last_completed,
            observed_token_steps=self.steps,token_step_observation='completed_forward_count; emitted tokens unknown until generation returns',events=list(self.events),events_seen=self.count,event_buffer_limit=self.events.maxlen,
            native_completion=getattr(self,'native_completion',None),
            native_completion_basis='native CPU stop-token bitmask acceptance before choice, not strict parsing or matcher termination',
            observation='Host metadata only; unavailable post-error device counters remain unknown')


def score_summary(values, vocab_size, indices=()):
    """CPU semantics used in tests: -inf masks are valid, NaN/+inf are not."""
    if len(values)!=vocab_size:raise MaskDiagnosticError('vocabulary_alignment')
    if any(type(i) is not int or not 0<=i<vocab_size for i in indices):raise MaskDiagnosticError('token_index_bounds')
    if any(math.isnan(v) for v in values):raise MaskDiagnosticError('nan_logits')
    if any(v==math.inf for v in values):raise MaskDiagnosticError('positive_infinity_logits')
    usable=sum(math.isfinite(v) for v in values)
    if not usable:raise MaskDiagnosticError('empty_allowed_intersection')
    return dict(vocabulary_size=vocab_size,usable_scores=usable,masked_negative_infinity=len(values)-usable)


def tensor_summary(scores, vocab_size):
    # Only called before an exception; never query a device from error handling.
    import torch
    metadata=dict(shape=list(scores.shape),dtype=str(scores.dtype),device=str(scores.device),vocabulary_size=vocab_size)
    if len(scores.shape)!=2 or tuple(scores.shape)!=(1,vocab_size):raise MaskDiagnosticError('vocabulary_alignment')
    if torch.isnan(scores).any().item():raise MaskDiagnosticError('nan_logits')
    if torch.isposinf(scores).any().item():raise MaskDiagnosticError('positive_infinity_logits')
    usable=int(torch.isfinite(scores).sum().item());metadata['usable_scores']=usable
    metadata['masked_negative_infinity']=int(torch.isneginf(scores).sum().item())
    if not usable:raise MaskDiagnosticError('empty_allowed_intersection')
    return metadata


class ObservedProcessor:
    def __init__(self, inner, trace, vocab_size, stage='native_mask', stop_ids=()):
        self.inner,self.trace,self.vocab_size,self.stage=inner,trace,vocab_size,stage
        self.stop_ids=tuple(stop_ids)
    def __call__(self, input_ids, scores):
        self.trace.begin(self.stage)
        self.trace.end(self.stage+'_input_metadata',**tensor_summary(scores,self.vocab_size))
        last=int(input_ids[0,-1])
        if not 0<=last<self.vocab_size:raise MaskDiagnosticError('token_index_bounds')
        self.trace.end(self.stage+'_token_bounds',last_input_token_id=last,in_bounds=True)
        result=self.inner(input_ids,scores)
        self.trace.end(self.stage,**tensor_summary(result,self.vocab_size))
        mask=getattr(self.inner,'token_bitmask',None)
        if mask is not None and str(mask.device)=='cpu' and self.stop_ids:
            allowed=[]
            for token in self.stop_ids:
                if not 0<=token<self.vocab_size:raise MaskDiagnosticError('stop_token_index_bounds')
                allowed.append(bool(int(mask[0,token//32].item()) & (1 << (token%32))))
            self.trace.native_completion=any(allowed)
        return result
