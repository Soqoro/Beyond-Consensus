"""P0 workflow planner contracts: supplied mock texts only, no dispatch backend."""
from dataclasses import dataclass
from math import factorial
import json
import re

from .model import Invalid, digest, groups, plain
from .response_boundary import decode_response, MAX_RESPONSE_BYTES

VERSION = 'math500-workflow-planner-v1'
ORIGINAL_IDS = (
    'test/algebra/2743.json', 'test/algebra/101.json',
    'test/counting_and_probability/508.json', 'test/counting_and_probability/666.json',
    'test/geometry/1097.json', 'test/geometry/880.json',
    'test/intermediate_algebra/1210.json', 'test/intermediate_algebra/1555.json',
    'test/number_theory/45.json', 'test/number_theory/914.json',
    'test/prealgebra/1930.json', 'test/prealgebra/1646.json',
    'test/precalculus/675.json', 'test/precalculus/697.json',
)
DIAGRAM_IDS = frozenset(('test/prealgebra/1930.json', 'test/prealgebra/1646.json'))
PROMPT = '''Propose a workflow, not a solution, for the problem and requested number of active agents.
Return exactly one JSON object conforming to the supplied response schema, schema_version "1.0".
Either status "unsupported" with a substantive reason, or status "plan" with tasks and initial ownership.
For a plan use n to 2*n meaningful tasks and exactly n active interchangeable owners named agent_0 through agent_(n-1), each owning one or two tasks. Each task is owned exactly once.
Use unique task IDs, task instructions, concrete expected_artifact descriptions, parent_task_ids and immutable_inputs (only "problem_statement" is allowed). Declare the original problem as input where needed.
Include exactly one counted final-answer/synthesis task named by final_task_id. Every task must lie on a directed path to it. Dependencies refer to explicit parent artifacts, not free-form agent chat.
Sequential derivation, case analysis and checking a specific intermediate claim can be substantive. Do not pad with formatting, tautological checks, repeated complete solutions or voting. Do not hide a whole multi-stage workflow inside one task to manipulate the cap.
Task roles and instructions travel with tasks. Owners share the same worker model and tools, have no hidden memory or special capabilities, and may resume after other owners' tasks. Include all needed dependencies explicitly.
Initial ownership is a neutral planning proposal. Do not solve the problem in the returned plan: no final answer, solved derivation or answer-key material. Strategy descriptions and source constants are allowed.
Explain the usefulness of the stages and dependencies in rationale. If the requested team cannot be supported meaningfully, return unsupported rather than padded work. Do not include additional fields or Markdown.'''


def _string(value, maximum=4000):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise Invalid('nonempty bounded string required')


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise Invalid('unexpected or missing fields')


def _ids(value):
    if type(value) is not list or any(type(x) is not str for x in value) or len(set(value)) != len(value):
        raise Invalid('unique string array required')
    return tuple(value)


@dataclass(frozen=True)
class PlannerTask:
    id: str
    instruction: str
    expected_artifact: str
    parents: tuple
    immutable_inputs: tuple


@dataclass(frozen=True)
class Candidate:
    tasks: tuple
    final_task_id: str
    requested_agents: int
    ownership: tuple
    rationale: str

    @property
    def ids(self):
        return tuple(sorted(t.id for t in self.tasks))

    @property
    def edges(self):
        return tuple((p, t.id) for t in self.tasks for p in t.parents)

    @property
    def graph_digest(self):
        # Ownership and rationale are not task definitions or worker inputs.
        return digest([sorted(self.tasks, key=lambda t: t.id), self.final_task_id])


def response_schema():
    string = {'type': 'string', 'minLength': 1, 'maxLength': 4000}
    identifier = {'type': 'string', 'pattern': '^[A-Za-z][A-Za-z0-9_-]{0,63}$'}
    def obj(properties):
        return {'type': 'object', 'properties': properties, 'required': list(properties), 'additionalProperties': False}
    task = obj({'task_id': identifier, 'instruction': string, 'expected_artifact': string,
                'parent_task_ids': {'type': 'array', 'items': identifier, 'uniqueItems': True, 'maxItems': 8},
                'immutable_inputs': {'type': 'array', 'items': {'const': 'problem_statement'}, 'uniqueItems': True, 'maxItems': 1}})
    owner = obj({'agent_id': {'enum': [f'agent_{i}' for i in range(4)]},
                 'task_ids': {'type': 'array', 'minItems': 1, 'maxItems': 2, 'uniqueItems': True, 'items': identifier}})
    common = {'schema_version': {'const': '1.0'}, 'requested_agents': {'const': 4, 'type': 'integer'}}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'oneOf': [
        obj({**common, 'status': {'const': 'plan'},
             'tasks': {'type': 'array', 'minItems': 4, 'maxItems': 8, 'items': task},
             'ownership': {'type': 'array', 'minItems': 4, 'maxItems': 4, 'items': owner},
             'final_task_id': identifier, 'rationale': string}),
        obj({**common, 'status': {'const': 'unsupported'}, 'reason': string})]}


def parse_response(text, requested_agents=4):
    if type(requested_agents) is not int or requested_agents != 4:
        raise Invalid('P0/P1 initial scope is n=4 only')
    row = decode_response(text)
    if type(row) is not dict or row.get('schema_version') != '1.0':
        raise Invalid('planner schema version')
    if type(row.get('requested_agents')) is not int or row['requested_agents'] != requested_agents:
        raise Invalid('requested agent count mismatch')
    if row.get('status') == 'unsupported':
        _keys(row, ('schema_version', 'status', 'requested_agents', 'reason'))
        _string(row['reason'])
        return 'UNSUPPORTED', None, row['reason']
    _keys(row, ('schema_version', 'status', 'requested_agents', 'tasks', 'ownership', 'final_task_id', 'rationale'))
    if row['status'] != 'plan':
        raise Invalid('plan/unsupported discriminator')
    _string(row['rationale'])
    if type(row['tasks']) is not list or not 4 <= len(row['tasks']) <= 8:
        raise Invalid('n <= m <= 2n')
    tasks = []
    for task in row['tasks']:
        _keys(task, ('task_id', 'instruction', 'expected_artifact', 'parent_task_ids', 'immutable_inputs'))
        identity = task['task_id']
        if type(identity) is not str or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', identity):
            raise Invalid('task ID')
        _string(task['instruction']); _string(task['expected_artifact'])
        parents = _ids(task['parent_task_ids']); inputs = _ids(task['immutable_inputs'])
        if set(inputs) - {'problem_statement'}:
            raise Invalid('undeclared immutable input')
        tasks.append(PlannerTask(identity, task['instruction'], task['expected_artifact'], parents, inputs))
    ids = {t.id for t in tasks}
    if len(ids) != len(tasks):
        raise Invalid('duplicate task IDs')
    if type(row['final_task_id']) is not str or row['final_task_id'] not in ids:
        raise Invalid('one counted final task required')
    if any(set(t.parents) - ids for t in tasks):
        raise Invalid('unknown parent')
    pending = {t.id: set(t.parents) for t in tasks}
    while pending:
        ready = sorted(k for k, v in pending.items() if not v)
        if not ready:
            raise Invalid('cyclic task DAG')
        for identity in ready:
            del pending[identity]
            for parents in pending.values(): parents.discard(identity)
    ancestors = set(); stack = [row['final_task_id']]
    by_id = {t.id: t for t in tasks}
    while stack:
        identity = stack.pop()
        if identity not in ancestors:
            ancestors.add(identity); stack.extend(by_id[identity].parents)
    if ancestors != ids:
        raise Invalid('all tasks must contribute to final synthesis')
    if type(row['ownership']) is not list or len(row['ownership']) != 4:
        raise Invalid('exactly n active owners')
    labels = []; assigned = []
    for owner in row['ownership']:
        _keys(owner, ('agent_id', 'task_ids'))
        if type(owner['agent_id']) is not str:
            raise Invalid('owner label')
        labels.append(owner['agent_id']); assigned.append(_ids(owner['task_ids']))
    if set(labels) != {f'agent_{i}' for i in range(4)}:
        raise Invalid('owner identities')
    candidate = Candidate(tuple(tasks), row['final_task_id'], 4, (), row['rationale'])
    canonical = groups(candidate, 4, tuple(assigned))
    return 'PLAN_VALID', Candidate(candidate.tasks, candidate.final_task_id, 4, canonical, candidate.rationale), None


def task_payloads(candidate, ownership):
    """Assignment invariance fixture only; does not execute mathematical workers."""
    groups(candidate, candidate.requested_agents, ownership)
    return tuple({'task_id': t.id, 'instruction': t.instruction,
                  'expected_artifact': t.expected_artifact, 'parent_task_ids': t.parents,
                  'immutable_inputs': t.immutable_inputs} for t in sorted(candidate.tasks, key=lambda t: t.id))


def make_request(row, provenance, n=4):
    if type(n) is not int or n != 4: raise Invalid('initial n=4 only')
    if type(row) is not dict: raise Invalid('source record')
    identity = row.get('unique_id', row.get('id'))
    _string(identity); _string(row.get('problem'), 16000)
    if identity in DIAGRAM_IDS or '[asy]' in row['problem'].casefold():
        return {'mechanical_status': 'INPUT_BLOCKED', 'payload': None,
                'source_id': identity, 'reason': 'reviewed immutable diagram representation unavailable'}
    payload = {'problem_statement': row['problem'], 'requested_agents': n,
               'planning_instructions': {'version': VERSION, 'text': PROMPT, 'response_schema': response_schema()}}
    if len(json.dumps(payload).encode()) > MAX_RESPONSE_BYTES:
        raise Invalid('request byte limit')
    return {'mechanical_status': 'NO_RESPONSE', 'payload': payload, 'payload_digest': digest(payload),
            'protected_provenance': {'source_id': identity, 'source_binding': provenance,
                                     'problem_digest': digest(row['problem'])},
            'execution_allowed': False}


def review_transcript(request, texts):
    """A supplied transcript is not a model call; never resample or dispatch."""
    result = {'mechanical_status': 'NO_RESPONSE', 'qualitative_status': 'NOT_REVIEWED',
              'attempts': [], 'candidate': None, 'flags': [], 'actual_planning_expenditure': None,
              'physical_model_calls': 0, 'evidence': 'P0_supplied_mock_responses',
              'execution_allowed': False, 'empirically_admitted': False}
    if request['mechanical_status'] == 'INPUT_BLOCKED':
        return {**result, 'mechanical_status': 'INPUT_BLOCKED'}
    if type(texts) not in (list, tuple): raise Invalid('transcript container')
    if len(texts) > 2:
        return {**result, 'mechanical_status': 'PLAN_INVALID', 'error': 'at most two supplied responses; none inspected'}
    for index in range(len(texts)):
        if result['mechanical_status'] in ('PLAN_VALID', 'UNSUPPORTED'):
            return {**result, 'mechanical_status': 'PLAN_INVALID', 'candidate': None,
                    'error': 'impermissible extra reply; extra not inspected'}
        text = texts[index]
        if text is None:
            result['attempts'].append({'attempt': index, 'raw': None, 'status': 'NO_RESPONSE', 'usage': None})
            return {**result, 'mechanical_status': 'NO_RESPONSE', 'error': 'no response; no automatic retry'}
        raw = text if type(text) is str and len(text.encode('utf-8', errors='replace')) <= MAX_RESPONSE_BYTES else None
        attempt = {'attempt': index, 'raw': raw, 'usage': None, 'usage_verified': False}
        if raw is None:
            attempt['retention_note'] = 'nontext or oversized input not retained as raw'
            if type(text) is str: attempt['raw_digest'] = digest(text)
        try:
            status, candidate, reason = parse_response(text)
            attempt.update(status=status, reason=reason)
            result.update(mechanical_status=status, candidate=candidate)
        except Invalid as exc:
            attempt.update(status='PLAN_INVALID', reason=str(exc))
            result['mechanical_status'] = 'PLAN_INVALID'
        result['attempts'].append(attempt)
    if result['candidate'] is not None:
        candidate = result['candidate']; m = len(candidate.tasks); k = m - 4
        result['feasible_ownership_partitions'] = factorial(m) // (2**k * factorial(k) * factorial(8-m))
        if m == 4: result['flags'].append('NO_OWNERSHIP_CHOICE')
        # A strategy may contain source constants. Only verbal answer/solved-result
        # cues trigger this conservative reviewer flag; it is not an acceptance gate.
        returned = ' '.join([candidate.rationale] + [t.instruction+' '+t.expected_artifact for t in candidate.tasks])
        if re.search(r'(?i)(final answer\s+is|answer\s*[:=]|\\boxed\s*\{)', returned):
            result['flags'].append('ANSWER_LEAKAGE_FLAG')
        result['initial_ownership_role'] = 'neutral_planner_baseline_not_cost_informed'
        result['future_cost_informed_baseline'] = {'frozen_graph_digest': candidate.graph_digest,
            'requires_common_pre_execution_costs': True, 'implemented': False}
    return result


def attach_review(result, status, rationale, reviewer):
    if status not in ('PLAUSIBLE', 'WEAK_OR_PADDED', 'REQUIRES_EXECUTION_TO_ASSESS', 'NOT_REVIEWED'):
        raise Invalid('qualitative review status')
    if result['mechanical_status'] != 'PLAN_VALID': raise Invalid('no valid plan to review')
    _string(rationale); _string(reviewer)
    return {**result, 'qualitative_status': status, 'reviewer_rationale': rationale,
            'reviewer': reviewer, 'empirically_admitted': False}


def correction_request(request, result):
    """Prepare, never send, the single permitted structural correction payload."""
    attempts = result['attempts']
    if (request.get('correction_index', 0) != 0 or result['mechanical_status'] != 'PLAN_INVALID'
            or len(attempts) != 1 or attempts[0]['status'] != 'PLAN_INVALID'
            or attempts[0]['raw'] is None):
        raise Invalid('no structural correction permitted')
    payload = json.loads(json.dumps(request['payload']))
    payload['planning_instructions']['structural_correction'] = {
        'instruction': 'Correct only the reported structural contract failure. This is the only correction allowed.',
        'prior_response': attempts[0]['raw'], 'validator_reason': attempts[0]['reason']}
    if len(json.dumps(payload).encode()) > MAX_RESPONSE_BYTES:
        raise Invalid('correction payload byte limit')
    return {**request, 'payload': payload, 'payload_digest': digest(payload), 'correction_index': 1}


def smoke_manifest(cards, labels, binding):
    by_id = {c['source_id']: c for c in cards}
    if len(by_id) != 14 or len(cards) != 14 or set(by_id) != set(ORIGINAL_IDS):
        raise Invalid('preserve exact fourteen-source denominator')
    if set(labels) != set(ORIGINAL_IDS): raise Invalid('original review labels required')
    rows = []
    for identity in ORIGINAL_IDS:
        row = by_id[identity]
        problem = row.get('problem')
        complete = type(problem) is str and bool(problem.strip())
        blocked = identity in DIAGRAM_IDS or not complete or '[asy]' in problem.casefold()
        rows.append({'source_id': identity, 'original_review_label': labels[identity],
                     'source_text_available': complete,
                     'mechanical_status': 'INPUT_BLOCKED' if blocked else 'NO_RESPONSE',
                     'qualitative_status': 'NOT_REVIEWED', 'development_only': True})
    smoke = [r['source_id'] for r in rows if r['mechanical_status'] == 'NO_RESPONSE'][:3]
    return {'schema': 'phase2-planner-first-P0-manifest-v1', 'source_binding': binding,
            'rows': rows, 'smoke_ids': smoke, 'smoke_rule': 'first_three_text_complete_in_original_selection_order',
            'requested_agents': 4, 'stage': 'P0', 'real_model_calls_enabled': False,
            'smoke_authorized': False, 'max_future_initial_calls': 3, 'max_future_total_calls': 6,
            'model_snapshot': None, 'sampling': None, 'token_limits': None, 'expenditure_cap': None,
            'qualitative_or_optimizer_gains_used_for_selection': False,
            'family_review': 'pending_not_a_P0_blocker', 'task_execution_allowed': False}
