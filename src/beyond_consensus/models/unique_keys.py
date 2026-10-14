"""Opt-in byte-prefix duplicate-key mask; JSON syntax remains XGrammar's job.

No text repair or key normalization. JSON escape decoding matches json.loads;
Unicode normalization is deliberately not applied. No optional imports at load.
"""
import json
import time

from ..util import BCError
from .action_schema import DECODER_CPU_SECONDS

MODE = 'reporecourse-json-unique-v1-pool-7'


class DuplicateKey(ValueError):
    pass


class KeyState:
    """Lexical state for a syntactically valid JSON prefix, including split UTF-8.

    Frames are immutable (kind, expecting_key, keys), so speculative token
    checks never mutate committed scopes. Arrays and sibling objects are distinct.
    """
    def __init__(self):
        self.frames = []
        self.in_string = False
        self.is_key = False
        self.escaped = False
        self.key = b''

    def copy(self):
        result = KeyState()
        result.frames = self.frames.copy()
        result.in_string, result.is_key = self.in_string, self.is_key
        result.escaped, result.key = self.escaped, self.key
        return result

    def feed(self, piece):
        for byte in piece:
            if self.in_string:
                if self.escaped:
                    if self.is_key:
                        self.key += bytes([byte])
                    self.escaped = False
                elif byte == 92:
                    if self.is_key:
                        self.key += b'\\'
                    self.escaped = True
                elif byte == 34:
                    if self.is_key:
                        name = json.loads(b'"' + self.key + b'"')
                        kind, _, keys = self.frames[-1]
                        if name in keys:
                            raise DuplicateKey('Duplicate JSON object key')
                        self.frames[-1] = (kind, False, keys | {name})
                    self.in_string = self.is_key = False
                    self.key = b''
                elif self.is_key:
                    self.key += bytes([byte])
            elif byte == 34:
                self.in_string = True
                self.is_key = bool(self.frames and self.frames[-1][0] == 'object' and self.frames[-1][1])
                self.key = b''
                self.escaped = False
            elif byte == 123:  # {
                self.frames.append(('object', True, frozenset()))
            elif byte == 91:  # [
                self.frames.append(('array', False, frozenset()))
            elif byte in (125, 93):
                if not self.frames:
                    raise ValueError('Invalid JSON nesting')
                self.frames.pop()
            elif byte == 44 and self.frames and self.frames[-1][0] == 'object':
                kind, _, keys = self.frames[-1]
                self.frames[-1] = (kind, True, keys)
            elif byte == 58 and self.frames and self.frames[-1][0] == 'object':
                kind, _, keys = self.frames[-1]
                self.frames[-1] = (kind, False, keys)
        return self

    def allows(self, piece):
        # Duplicate detection occurs only at an unescaped closing key quote.
        # No quote => cannot complete any new duplicate key in this token.
        if b'"' not in piece:
            return True
        try:
            self.copy().feed(piece)
            return True
        except (ValueError, UnicodeError):
            return False


class UniqueKeyProcessor:
    """Intersect native masks with duplicate-key validity, never unmask tokens."""
    def __init__(self, inner, decoded_vocab, stop_ids, *, clock=time.process_time):
        if not decoded_vocab or not all(isinstance(p, bytes) for p in decoded_vocab):
            raise BCError('Unique-key decoding requires native decoded vocabulary bytes')
        self.inner = inner
        self.vocab = decoded_vocab
        self.stops = frozenset(stop_ids)
        self.quote_ids = [i for i, p in enumerate(decoded_vocab) if b'"' in p and i not in self.stops]
        self.state = KeyState()
        self.length = None
        self.clock = clock
        self.cpu_seconds = 0.0
        self.blocked_tokens = 0
        self.device_indices = None

    def __call__(self, input_ids, scores):
        import torch
        start = self.clock()
        try:
            size = input_ids.shape[1]
            if input_ids.shape[0] != 1 or (self.length is not None and size != self.length + 1):
                raise BCError('Unique-key decoding requires one append-only sequence')
            if self.length is not None:
                token = int(input_ids[0, -1])
                if token in self.stops:
                    raise BCError('Generation continued after EOS')
                try:
                    self.state.feed(self.vocab[token])
                except (ValueError, UnicodeError, IndexError) as exc:
                    raise BCError('Invalid committed unique-key prefix') from exc
            # First invocation is after ReasoningGate activates. Everything
            # before this position is prompt/reasoning, never JSON state.
            self.length = size
            masked = self.inner(input_ids, scores)
            if self.device_indices is None:
                self.device_indices = torch.tensor(self.quote_ids, dtype=torch.long, device=masked.device)
            finite = torch.isfinite(masked[0].index_select(0, self.device_indices))
            candidates = self.device_indices[finite].tolist()
            blocked = []
            for index, token in enumerate(candidates):
                if index % 128 == 0 and self.cpu_seconds + self.clock() - start >= DECODER_CPU_SECONDS:
                    raise BCError('Unique-key decoder CPU allowance exhausted')
                if not self.state.allows(self.vocab[token]):
                    blocked.append(token)
            if blocked:
                masked[0, blocked] = float('-inf')
                self.blocked_tokens += len(blocked)
            if not torch.isfinite(masked).any().item():
                raise BCError('Unique-key decoder has no valid continuation')
            return masked
        finally:
            self.cpu_seconds += max(0.0, self.clock() - start)
            if self.cpu_seconds > DECODER_CPU_SECONDS:
                raise BCError('Unique-key decoder CPU allowance exhausted')


def synthetic_controls():
    """Fixed qualification-only controls; no task names or model prompt content."""
    prefix = '{"tool":"publish","name":"demo","format":"mapping","content":'
    suffix = ',"bindings":{},"obligations":[]}'
    good = [
        '{"fields":{"x":1},"output_schema":{}}',
        '{"fields":{"x":{"x":1},"y":{"x":2}},"output_schema":{}}',
        '{"fields":{"x":[{"id":1},{"id":2}]},"output_schema":{}}',
        '{"fields":{"x":"quoted \\"x\\" and braces {}","y":"x"},"output_schema":{}}',
        '{"fields":{"é":1,"é":2,"😀":3},"output_schema":{}}',
    ]
    bad = [
        '{"fields":{"x":1,"x":2},"output_schema":{}}',
        r'{"fields":{"x":1,"\u0078":2},"output_schema":{}}',
        r'{"fields":{"é":1,"\u00e9":2},"output_schema":{}}',
        r'{"fields":{"😀":1,"\ud83d\ude00":2},"output_schema":{}}',
        r'{"fields":{"a\"b":1,"a\u0022b":2},"output_schema":{}}',
        '{"fields":{"x":[{"id":1,"id":2}]},"output_schema":{}}',
    ]
    return [prefix + text + suffix for text in good], [prefix + text + suffix for text in bad]


def qualify_unique_keys(constraint, tokenizer, torch, closing, stops, vocab):
    """Native CPU/tokenizer controls required before issuing this mode's lock."""
    from ..util import digest
    good, bad = synthetic_controls()
    rows = []
    for index, text in enumerate(good + bad):
        expected = index < len(good)
        ids = tokenizer.encode(text, add_special_tokens=False)
        if b''.join(constraint.unique_vocab[t] for t in ids) != text.encode('utf-8'):
            raise BCError('Unique-key token bytes do not round trip')
        for stop in stops:
            for reasoning in (False, True):
                prefix = [closing]
                processor = constraint.processor(1, closing if reasoning else None)
                scores = torch.zeros((1, vocab), dtype=torch.float32)
                if reasoning:
                    before = processor(torch.tensor([prefix]), scores.clone())
                    if processor.active or not torch.equal(scores, before):
                        raise BCError('Prompt delimiter activated unique-key guard')
                    prefix.append(closing)
                accepted = True
                blocked_index = None
                for position, token in enumerate([*ids, stop]):
                    masked = processor(torch.tensor([prefix]), scores.clone())
                    if not torch.isfinite(masked[0, token]).item():
                        accepted = False
                        blocked_index = position
                        break
                    prefix.append(token)
                if accepted != expected:
                    raise BCError(f'Unique-key native control failed: case={index}, stop={stop}, reasoning={reasoning}')
                rows.append(dict(case=index, expected=expected, accepted=accepted,
                                 stop_token_id=stop, reasoning=reasoning, blocked_index=blocked_index,
                                 decoder_cpu_seconds=processor.cpu_seconds))
    return dict(schema='rr-unique-key-controls-v1', status='passed',
                controls_hash=digest([good, bad]), cases=rows, model_executed=False,
                task_inputs_used=False, sql_executed=False)
