"""Offline planner-adapter double with durable simulated token accounting.

No provider registry or real generation path. This is not GPU qualification or
an execution authorization; numeric token counts are synthetic observations.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import tempfile

from .model import Invalid, digest, plain
from . import planner_first as planner

MAX_LEDGER_BYTES = 8 * 1024 * 1024
CONTEXT = 16384
OUTPUT = 6144
MAX_CALLS = 6


@dataclass(frozen=True)
class MockReply:
    text: str | None
    output_tokens: int | None


def _encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode('utf-8')


class MockPlannerSession:
    """Single-writer, no-replay mock session; process death leaves reservations.

    A ledger is an integrity record, not authenticated evidence. All input IDs
    and output counts are supplied synthetic fixtures, not tokenizer measurements.
    No caller-provided generation function is accepted.
    """
    def __init__(self, directory, requests, *, backend='offline_mock'):
        if backend != 'offline_mock':
            raise Invalid('real planner backends disabled')
        if type(requests) is not list or len(requests) != 3:
            raise Invalid('exactly three frozen requests required')
        canonical = []
        for request in requests:
            if type(request) is not dict or request.get('mechanical_status') != 'NO_RESPONSE':
                raise Invalid('text-complete initial request required')
            try:
                metadata = request['protected_provenance']
                expected = planner.make_request({'id': metadata['source_id'],
                    'problem': request['payload']['problem_statement']}, metadata['source_binding'])
            except (KeyError, TypeError) as exc:
                raise Invalid('request envelope') from exc
            if request != expected:
                raise Invalid('request/prompt binding changed')
            canonical.append(json.loads(_encoded(expected)))
        ids = [r['protected_provenance']['source_id'] for r in canonical]
        if len(set(ids)) != 3:
            raise Invalid('duplicate sources')
        self.binding = {'requests': canonical, 'backend': backend,
            'context': CONTEXT, 'output_cap': OUTPUT, 'maximum_calls': MAX_CALLS,
            'maximum_total_tokens': MAX_CALLS * CONTEXT,
            'gpu_allocation': None, 'real_execution_allowed': False,
            'implementation_hashes': {name: hashlib.sha256(
                (Path(__file__).parent / name).read_bytes()).hexdigest()
                for name in ('planner_ledger.py', 'planner_first.py', 'response_boundary.py',
                             'model.py', 'allocation.py')}}
        if len(_encoded(self.binding)) > MAX_LEDGER_BYTES // 2:
            raise Invalid('binding size')
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        with self._locked():
            if self.path.exists():
                self._read()
            else:
                self._save({'schema': 'phase2-planner-mock-ledger-v1',
                    'binding': self.binding, 'binding_digest': digest(self.binding),
                    'evidence': 'offline_mock_not_real_usage', 'attempts': [],
                    'model_executed': False, 'task_execution_allowed': False})

    @property
    def path(self):
        return self.root / 'ledger.json'

    @contextmanager
    def _locked(self):
        with (self.root / 'ledger.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _save(self, state):
        raw = _encoded({'state': state, 'sha256': digest(state)})
        if len(raw) > MAX_LEDGER_BYTES:
            raise Invalid('ledger byte limit')
        fd, name = tempfile.mkstemp(prefix='.ledger-', dir=self.root)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
            os.replace(name, self.path)
            directory = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(name): os.unlink(name)

    def _read(self):
        try:
            with self.path.open('rb') as handle:
                raw = handle.read(MAX_LEDGER_BYTES + 1)
            if len(raw) > MAX_LEDGER_BYTES: raise Invalid('ledger byte limit')
            wrapper = json.loads(raw)
            state = wrapper['state']
            if (wrapper['sha256'] != digest(state) or state['binding'] != self.binding
                    or state['binding_digest'] != digest(self.binding)):
                raise Invalid('ledger integrity or binding changed')
            return state
        except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
            raise Invalid('unreadable ledger; never reset or replay') from exc

    @staticmethod
    def _totals(state):
        spent = sum(a['actual_tokens'] or 0 for a in state['attempts'])
        reserved = sum(a['reservation_tokens'] for a in state['attempts'] if a['actual_tokens'] is None)
        return {'simulated_actual_tokens': spent, 'simulated_reserved_tokens': reserved,
                'simulated_attempts': len(state['attempts']), 'real_model_calls': 0}

    def snapshot(self):
        with self._locked():
            state = self._read()
            return {**state, 'totals': self._totals(state)}

    def advance(self, source_id, rendered_input_ids, reply):
        """Consume one supplied fixture; never automatically retry or generate.

        Unresolved reservations block every source. Restart after a completed
        valid/unsupported reply is terminal. Only one invalid response can receive
        a second fixture. Input token IDs must cover the full correction payload.
        Their truth is not verified here: this is explicitly a mock boundary.
        """
        with self._locked():
            state = self._read()
            if any(a['state'] != 'completed' for a in state['attempts']):
                raise Invalid('unresolved attempt; dispatch blocked')
            if len(state['attempts']) >= MAX_CALLS:
                raise Invalid('six-call protocol cap')
            request = next((r for r in self.binding['requests']
                if r['protected_provenance']['source_id'] == source_id), None)
            if request is None: raise Invalid('source outside frozen scope')
            previous = [a for a in state['attempts'] if a['source_id'] == source_id]
            outbound = request
            if previous:
                if len(previous) != 1: raise Invalid('at most one correction')
                result = planner.review_transcript(request, [previous[0]['raw']])
                outbound = planner.correction_request(request, result)
            # Check permission before inspecting the supplied extra response.
            if type(reply) is not MockReply: raise Invalid('only built-in mock replies accepted')
            if (type(rendered_input_ids) not in (list, tuple) or not rendered_input_ids
                    or len(rendered_input_ids) + OUTPUT > CONTEXT
                    or any(type(t) is not int or t < 0 for t in rendered_input_ids)):
                raise Invalid('synthetic input IDs/context cap; no truncation')
            reservation = len(rendered_input_ids) + OUTPUT
            if self._totals(state)['simulated_actual_tokens'] + reservation > MAX_CALLS * CONTEXT:
                raise Invalid('token reservation cap')
            attempt = {'source_id': source_id, 'attempt': len(previous), 'state': 'reserved',
                'outbound_payload': outbound['payload'], 'payload_digest': outbound['payload_digest'],
                'rendered_input_ids_digest': digest(rendered_input_ids),
                'input_tokens': len(rendered_input_ids), 'output_cap': OUTPUT,
                'reservation_tokens': reservation, 'actual_tokens': None, 'raw': None,
                'usage_evidence': 'synthetic_fixture_not_tokenizer_verified',
                'reserved_at': datetime.now(timezone.utc).isoformat()}
            state['attempts'].append(attempt)
            self._save(state)  # Must precede response processing; interruption is charged.
            text = reply.text
            if type(text) is str:
                raw_bytes = text.encode('utf-8', errors='replace')
                if len(raw_bytes) <= planner.MAX_RESPONSE_BYTES:
                    attempt['raw'] = text
                else:
                    attempt['raw_sha256'] = digest(text)
                    attempt['retention_note'] = 'oversized response not retained; no correction'
            elif text is not None:
                attempt['retention_note'] = 'nontext response; no correction'
            usage = reply.output_tokens
            if type(usage) is not int or usage < 0:
                attempt['state'] = 'uncertain'
                attempt['error'] = 'missing or malformed output usage'
            elif usage > OUTPUT:
                attempt['state'] = 'usage_violation'
                attempt['actual_tokens'] = len(rendered_input_ids) + usage
                attempt['error'] = 'actual output exceeds reservation; session halted'
            else:
                attempt['actual_tokens'] = len(rendered_input_ids) + usage
                attempt['state'] = 'completed'
                result = planner.review_transcript(request, [a['raw'] for a in previous] + [text])
                attempt['review'] = plain(result)
                if attempt['raw'] is None:
                    attempt['terminal_without_correction'] = True
            attempt['observed_at'] = datetime.now(timezone.utc).isoformat()
            self._save(state)
            return {**attempt, 'totals': self._totals(state), 'model_executed': False}
