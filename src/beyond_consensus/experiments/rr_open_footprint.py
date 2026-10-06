"""Task-free scoped representation qualification. No task execution permission."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json
import time

from ..util import BCError, digest, read_json, file_hash
from .manifest import source_revision
from . import rr_v2_preflight as base
from reporecourse import v2
from reporecourse.engine import worker_messages
from reporecourse.common import Rejected

SCHEMA = 'rr-open-footprint-manifest-v1'
PACKET = 'rr-open-footprint-cpu-v1'
PROTOCOL = 'rr-open-footprint-five-cases-v1'
SCHEMA_V2 = 'rr-open-footprint-manifest-v2'
PACKET_V2 = 'rr-open-footprint-cpu-v2'
PROTOCOL_V2 = base.FOOTPRINT_PROTOCOL
CASE_IDS = ('plan_02', 'plan_07', 'plan_24', 'scope_empty', 'scope_imports16')
FLAGS = dict(task_execution_allowed=False, campaign_allowed=False,
             task_competence_measured=False, autonomous_planning_competence_measured=False,
             worst_case_fit_established=False)


def require(value, message):
    if not value:
        raise BCError(message)


def public_contract():
    return dict(id='footprint-probe', family='api_schema',
        request='Synthetic qualification only; reproduce the requested public interface.',
        sources={'probe_source': 'Synthetic qualification source; no task implementation.'},
        required_outputs=[{'id': 'probe_result', 'format': 'schema'}], examples=[])


def config(planner_output_cap=2048):
    return v2.configuration(7, planning_lane='open_generated', execution_contract='plan_scoped_v1',
                            planner_output_cap=planner_output_cap)


def unit(i, terminal=False):
    name = f'artifact_{i:02d}'
    return dict(id=f'unit_{i:02d}', worker=f'w{i % 7}',
        outputs=['probe_result'] if terminal else [], depends=[],
        description='Carry the synthetic interface forward.', produces={name: 'schema'},
        consumes={}, sources=['probe_source'], interfaces={name: 'Synthetic schema artifact.'},
        terminal_bindings={'probe_result': name} if terminal else {})


def plan(n, chain=True):
    units = [unit(i, i == n-1) for i in range(n)]
    if chain:
        for i in range(1, n):
            units[i]['depends'] = [units[i-1]['id']]
            units[i]['consumes'] = {'input': dict(unit=units[i-1]['id'], artifact=f'artifact_{i-1:02d}', format='schema')}
    return dict(schema='rr-work-plan-v2', id=f'plan_{n:02d}', units=units)


def instruction(expected):
    return ('Task-free authored qualification, not autonomous planning. Return exactly this '
            'JSON action, no Markdown: ' + json.dumps(expected, separators=(',', ':')))


def case(name, role, messages, expected, **extra):
    messages = deepcopy(messages)
    messages.append({'role': 'user', 'content': instruction(expected)})
    return dict(id=name, role=role, messages=messages, prompt_hash=digest(messages),
                expected=expected, expected_hash=digest(expected), **extra)


def cases(planner_output_cap=2048):
    """Use actual scoped observations and publications, no database or execution."""
    public = public_contract(); c = config(planner_output_cap); result = []
    for n in (2, 7, 24):
        p = plan(n)
        v2.validate_work_plan(p, public, c)
        result.append(case(f'plan_{n:02d}', 'plan',
            v2.planner_messages({'planner_input': v2.planner_input(public, c)}),
            {'tool': 'submit_plan', 'plan': p}, structural_valid=True))
    from reporecourse.runtime import Environment
    from reporecourse.resources import Resources
    for populated in (False, True):
        p = plan(18 if populated else 1, chain=False)
        consumer = p['units'][-1]
        if populated:
            consumer['depends'] = [u['id'] for u in p['units'][:16]]
            consumer['consumes'] = {f'input_{i:02d}': dict(unit=f'unit_{i:02d}',
                artifact=f'artifact_{i:02d}', format='schema') for i in range(16)}
        v2.validate_work_plan(p, public, c)
        env = Environment(public, Resources(100000, 1200), workers=c['workers'],
                          execution_contract='plan_scoped_v1', plan=p)
        try:
            versions = []
            for u in p['units'][:-1]:
                w = u['worker']; env.scopes.begin(u, w, 'primary'); env.assignment[w] = deepcopy(u)
                versions.append(env.action(w, dict(tool='publish', name=next(iter(u['produces'])),
                    format='schema', content=True, bindings={}, obligations=[]))['version'])
            w = consumer['worker']; env.scopes.begin(consumer, w, 'primary'); env.assignment[w] = deepcopy(consumer)
            observation = env.observation(w)
            visible = sorted(a['version'] for a in observation['artifacts'])
            require(visible == sorted(versions[:16]), 'Scoped artifact visibility failed')
            require(observation['messages'] == [] and observation['bound'] == {}, 'Unexpected scoped delivery')
            denied = None
            if populated:
                try:
                    env.action(w, {'tool': 'read_artifact', 'version': versions[16]})
                except Rejected as exc:
                    denied = str(exc)
                require(denied == 'scope_denied', 'Unrelated artifact read was not denied')
            expected = ({'tool': 'read_artifact', 'version': versions[0]} if populated
                        else {'tool': 'read_source', 'name': 'probe_source'})
            result.append(case('scope_imports16' if populated else 'scope_empty', 'json',
                worker_messages(observation, []), expected, structural_valid=True,
                observation=observation, observation_hash=digest(observation),
                visible_versions=visible, unrelated_version=versions[16] if populated else None,
                unrelated_read_denied=populated and denied == 'scope_denied',
                visibility_passed=True, preparation_resources=deepcopy(vars(env.resources))))
        finally:
            env.close()
    return result


def proposal_check(proposal, model):
    require(proposal.get('schema') == 'rr-open-engineering-proposal-v1' and
            proposal.get('proposal_id') == digest({k:v for k,v in proposal.items() if k != 'proposal_id'}),
            'Invalid engineering proposal')
    require(proposal.get('task_execution_allowed') is False and proposal.get('campaign_allowed') is False,
            'Proposal must remain blocked')
    require(proposal['worker_config']['model'] == model, 'Proposal worker model differs')
    expected = dict(model, action_constraint='reporecourse-plan-scoped-v1-pool-7')
    require(proposal['planner_config']['model'] == expected, 'Proposal planner model differs')


def prepare(root, proposal, worker, planner, measure=None, *, planner_output_cap=2048):
    start = time.process_time()
    frozen = base.build(root, worker, planner, 7, plan_scoped=True, planner_output_cap=planner_output_cap)
    proposal_check(proposal, frozen['model'])
    rows = cases(planner_output_cap)
    for row in rows:
        cap = base.output_cap(frozen, row['role'])
        text = json.dumps(row['expected'], separators=(',', ':'))
        row['measurement'] = dict(input_tokens=None, action_tokens=None, action_plus_stop_tokens=None,
            grammar_accepted=None, utf8_bytes=len(text.encode()), status='unmeasured', dispatch_allowed=False)
        if measure is not None:
            values = measure(row, text)
            i, a = values['input_tokens'], values['action_tokens']
            require(type(i) is int and i > 0 and type(a) is int and a > 0, 'Invalid tokenizer measurement')
            status = ('grammar_rejected' if values['grammar_accepted'] is not True else
                      'output_representation_exceeds_cap' if a+1 > cap else
                      'input_reservation_exceeds_context' if i+cap > 16384 else 'passed')
            row['measurement'].update(values, action_plus_stop_tokens=a+1, status=status,
                                      dispatch_allowed=status == 'passed')
    report = dict(schema=PACKET_V2 if planner_output_cap == 4096 else PACKET,
        protocol=PROTOCOL_V2 if planner_output_cap == 4096 else PROTOCOL, source_revision=frozen['source_revision'],
        proposal=proposal, base_manifest=frozen, public=public_contract(), cases=rows,
        model_executed=False, sql_executed=False, task_inputs_used=False,
        status='prepared_unmeasured' if measure is None else
               'passed_cpu_cases' if all(r['measurement']['dispatch_allowed'] for r in rows) else 'failed_cpu_cases',
        analysis_cpu_seconds=time.process_time()-start, **FLAGS)
    report['packet_id'] = digest(report)
    return report


def validate_packet(packet, measured=False):
    special = packet.get('schema') == PACKET_V2
    require((packet.get('schema'), packet.get('protocol')) in ((PACKET, PROTOCOL), (PACKET_V2, PROTOCOL_V2)) and
        packet.get('packet_id') == digest({k:v for k,v in packet.items() if k != 'packet_id'}), 'CPU packet integrity mismatch')
    require(packet.get('model_executed') is False and packet.get('sql_executed') is False and
            packet.get('task_inputs_used') is False, 'CPU packet evidence scope mismatch')
    for k, value in FLAGS.items():
        require(packet.get(k) is value, 'CPU packet changed permission')
    require(packet['public'] == public_contract(), 'Synthetic public contract changed')
    base.validate(packet['base_manifest'])
    require(packet['base_manifest']['schema'] == (base.FOOTPRINT_PROFILE if special else base.SCHEMA),
            'Footprint profile/version mismatch')
    planner_cap = base.output_cap(packet['base_manifest'], 'plan')
    require(packet['base_manifest'].get('execution_contract') == 'plan_scoped_v1' and
            packet['base_manifest']['pool'] == 7 and packet['source_revision'] == packet['base_manifest']['source_revision'], 'Packet scope mismatch')
    proposal_check(packet['proposal'], packet['base_manifest']['model'])
    regenerated = cases(planner_cap)
    require([r['id'] for r in packet['cases']] == list(CASE_IDS), 'Incomplete/changed case coverage')
    for index, row in enumerate(packet['cases']):
        require(row['prompt_hash'] == digest(row['messages']) and row['expected_hash'] == digest(row['expected']), 'Case hash mismatch')
        require(row['role'] == ('plan' if index < 3 else 'json'), 'Case grammar mismatch')
        if index < 3:
            expected = {'tool':'submit_plan','plan':plan((2,7,24)[index])}
            v2.validate_work_plan(row['expected']['plan'], public_contract(), config(planner_cap))
            require(row['expected'] == expected, 'Authored plan changed')
            messages = v2.planner_messages({'planner_input':v2.planner_input(public_contract(),config(planner_cap))})
        else:
            o = row['observation']; visible = row['visible_versions']
            expected_observation = deepcopy(regenerated[index]['observation'])
            # CPU debit is actually measured when the packet is prepared. It is
            # the only nondeterministic field of this fresh synthetic observation.
            expected_observation['cpu_remaining'] = o['cpu_remaining']
            require(type(o['cpu_remaining']) in (float, int) and 0 <= o['cpu_remaining'] <= 1200, 'Invalid CPU balance')
            require(o == expected_observation, 'Synthetic observation changed')
            require(row['unrelated_version'] == regenerated[index]['unrelated_version'], 'Unrelated version changed')
            require(row['observation_hash'] == digest(o) and row['visibility_passed'] is True,
                    'Observation evidence mismatch')
            require(sorted(a['version'] for a in o['artifacts']) == visible and
                    not o['messages'] and not o['bound'], 'Unexpected visible content')
            require(len(visible) == (0 if index == 3 else 16), 'Import count mismatch')
            if index == 4:
                require(row['unrelated_read_denied'] is True and row['unrelated_version'] not in visible,
                        'Negative visibility control failed')
                require(row['expected'] == {'tool':'read_artifact','version':o['execution_scope']['imports']['input_00']}, 'Wrong version read')
            else:
                require(row['expected'] == {'tool':'read_source','name':'probe_source'}, 'Wrong source read')
            # write_new sorts dictionary keys on disk. Reconstruct the original
            # insertion order, retaining the measured CPU balance, so validation
            # checks the exact prepared prompt rather than a reordered rendering.
            messages = worker_messages(expected_observation, [])
        messages.append({'role':'user','content':instruction(regenerated[index]['expected'])})
        require(messages == row['messages'], 'Rendered messages changed')
        cap = base.output_cap(packet['base_manifest'], row['role'])
        m = row['measurement']
        if measured:
            require(type(m['input_tokens']) is int and m['input_tokens'] > 0 and
                    type(m['action_tokens']) is int and m['action_tokens'] > 0 and
                    m['action_plus_stop_tokens'] == m['action_tokens']+1, 'Unmeasured CPU case')
            status = ('grammar_rejected' if m['grammar_accepted'] is not True else
                      'output_representation_exceeds_cap' if m['action_plus_stop_tokens'] > cap else
                      'input_reservation_exceeds_context' if m['input_tokens']+cap > 16384 else 'passed')
            require(m['status'] == status and m['dispatch_allowed'] == (status == 'passed'), 'Invalid admission decision')


def measurement_binding(packet):
    runtime = packet.get('measurement_runtime', {})
    require(runtime, 'CPU tokenizer/grammar provenance missing')
    b = packet['base_manifest']
    require(runtime.get('worker_lock_sha256') == b['model_lock_sha256'], 'CPU worker lock mismatch')
    q = b['planner_lock']['decoder_qualification']
    require(runtime['qualification_keys']['plan'] == q['qualification_key'] and
            runtime['packages'] == q['packages'], 'CPU grammar/package binding mismatch')
    require(runtime['template']['template_hash'] == q['thinking_template']['template_hash'], 'CPU template mismatch')


def build(root, packet, worker):
    validate_packet(packet, measured=True)
    require(packet.get('model_executed') is False and packet.get('sql_executed') is False, 'Invalid CPU evidence scope')
    if packet['schema'] == PACKET_V2:
        require(all(r['measurement']['dispatch_allowed'] for r in packet['cases']),
                'Planner-4096 footprint requires all fresh CPU cases to pass')
    require(packet['source_revision'] == source_revision(root), 'Source changed since CPU preparation')
    m = deepcopy(packet['base_manifest'])
    base.check_submission(m, worker, root, 'preflight', 1)
    measurement_binding(packet)
    m.update(schema=SCHEMA_V2 if packet['schema'] == PACKET_V2 else SCHEMA,
             protocol=packet['protocol'], rounds=1, cpu_packet=packet)
    m['experiment_id'] = digest({k:v for k,v in m.items() if k != 'experiment_id'})
    validate(m)
    check_submission(m, worker, root, 'preflight', 1)
    return m


def validate(m):
    require((m.get('schema'), m.get('protocol')) in ((SCHEMA, PROTOCOL), (SCHEMA_V2, PROTOCOL_V2)) and
            m.get('experiment_id') == digest({k:v for k,v in m.items() if k != 'experiment_id'}), 'Footprint manifest integrity mismatch')
    packet = m['cpu_packet']; validate_packet(packet, measured=True)
    if packet['schema'] == PACKET_V2:
        require(all(r['measurement']['dispatch_allowed'] for r in packet['cases']),
                'Planner-4096 footprint requires all fresh CPU cases to pass')
    measurement_binding(packet)
    expected = deepcopy(packet['base_manifest']); expected.update(schema=SCHEMA_V2 if packet['schema'] == PACKET_V2 else SCHEMA,
        protocol=packet['protocol'], rounds=1, cpu_packet=packet)
    expected['experiment_id'] = digest({k:v for k,v in expected.items() if k != 'experiment_id'})
    require(m == expected, 'Footprint/base binding mismatch')
    return base.validate(packet['base_manifest'])


def check_submission(m, worker, root, mode, concurrency):
    validate(m)
    base.check_submission(m['cpu_packet']['base_manifest'], worker, root, mode, concurrency)
    q = worker['decoder_qualification']
    r = m['cpu_packet']['measurement_runtime']
    require(r['qualification_keys']['json'] == q['qualification_key'] and r['packages'] == q['packages'], 'CPU worker grammar binding mismatch')


def parse(text):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result: raise ValueError('duplicate key')
            result[k] = v
        return result
    return json.loads(text, object_pairs_hook=pairs)


def sequence(packet, backend, switch, memory):
    validate_packet(packet, measured=True)
    rows = []
    for case_row in packet['cases']:
        cap = base.output_cap(packet['base_manifest'], case_row['role'])
        row = dict(id=case_row['id'], passed=False, dispatched=False,
                   output_cap=cap, input_tokens=case_row['measurement']['input_tokens'], output_tokens=0, uncertain_tokens=0)
        rows.append(row)
        if not case_row['measurement']['dispatch_allowed']:
            row['status'] = case_row['measurement']['status']; continue
        start = time.process_time(); wall = time.monotonic(); generated = None
        stage = 'runtime_admission'
        try:
            switch(case_row['role'])
            actual_input = backend.count_input(case_row['messages'])
            if hasattr(backend, 'encode'):
                ids = backend.encode(case_row['messages'])['input_ids'][0].tolist()
                require(digest(ids) == case_row['measurement']['rendered_input_ids_hash'], 'Rendered token IDs changed')
            require(actual_input == row['input_tokens'] and actual_input+cap <= 16384, 'Runtime prompt count mismatch')
            memory(reset=True)
            row['dispatched'] = True
            stage = 'generation'
            generated = backend.generate(deepcopy(case_row['messages']), cap, 0)
            stage = 'accounting'
            require(type(generated.output_tokens) is int and 0 < generated.output_tokens <= cap, 'Invalid output accounting')
            row.update(generation=asdict(generated), output_tokens=generated.output_tokens)
            d = generated.diagnostics
            require(d.get('rendered_input_tokens') == actual_input, 'Generation input accounting mismatch')
            require(generated.reasoning_tokens is None or
                    (type(generated.reasoning_tokens) is int and 0 <= generated.reasoning_tokens <= generated.output_tokens),
                    'Invalid reasoning token accounting')
            stage = 'response_validation'
            action = parse(generated.text)
            if case_row['role'] == 'plan':
                v2.validate_work_plan(action['plan'], public_contract(), config(base.output_cap(packet['base_manifest'], 'plan')))
            row['passed'] = (action == case_row['expected'] and d.get('constraint_complete') is True and d.get('finish_reason') == 'eos')
            row['status'] = 'passed' if row['passed'] else 'response_failed'
        except Exception as exc:
            row.update(status='error', error_type=type(exc).__name__, failure_stage=stage)
            if row['dispatched'] and (stage == 'accounting' or generated is None or not row['output_tokens']):
                row['uncertain_tokens'] = row['input_tokens']+cap
        finally:
            row.update(process_cpu_seconds=time.process_time()-start, wall_seconds=time.monotonic()-wall,
                       memory=memory(reset=False))
            mem = row['memory']
            if not (0 < mem.get('peak_allocated_bytes', 0) <= mem.get('peak_reserved_bytes', 0) <= mem.get('total_bytes', 0)):
                row.update(passed=False, status='memory_evidence_failed')
        # No retry. A backend exception ends dispatch; retain all remaining cases.
        if row.get('uncertain_tokens'):
            for remaining in packet['cases'][len(rows):]:
                rows.append(dict(id=remaining['id'], passed=False, dispatched=False,
                                 status='not_dispatched_after_error', input_tokens=0, output_tokens=0, uncertain_tokens=0))
            break
    return rows


def measure_cpu(root, proposal, worker, planner, *, planner_output_cap=2048):
    """Optional offline CPU tokenizer/grammar stack; never load model weights."""
    start = time.process_time(); wall = time.monotonic()
    from ..models.competence import check_output_allowance
    check_output_allowance(16384, 'reporecourse-plan-scoped-v1-pool-7', planner_output_cap)
    import os
    require(bool(os.environ.get('SLURM_JOB_ID')), 'Tokenizer measurement requires a CPU batch allocation')
    for lock in (worker, planner):
        for relative, expected in lock['metadata_hashes'].items():
            require(file_hash(Path(lock['model_path'])/relative) == expected, 'Staged model metadata changed')
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from transformers import AutoTokenizer
    from ..models.transformers_backend import verify_thinking_template
    from ..models.constrained import ActionConstraint
    from ..models.competence import versions, require_qualification
    packages = versions()
    tokenizer = AutoTokenizer.from_pretrained(worker['tokenizer_path'], local_files_only=True, trust_remote_code=False)
    template = verify_thinking_template(tokenizer, True)
    metadata = read_json(Path(worker['model_path'])/'config.json')
    vocab = metadata.get('text_config', metadata)['vocab_size']
    constraints = {}
    for role, lock in (('json', worker), ('plan', planner)):
        mode = f'reporecourse-{role}-scoped-v1-pool-7'
        require_qualification(lock, packages, 16384, mode, planner_output_cap if role == 'plan' else 2048)
        q = lock['decoder_qualification']
        require(template['template_hash'] == q['thinking_template']['template_hash'], 'Tokenizer template changed')
        require(q['vocab_size'] == vocab, 'Qualified vocabulary changed')
        require(q['effective_generation_tokens'] == worker['decoder_qualification']['effective_generation_tokens'], 'Worker/planner stop tokens differ')
        constraints[role] = ActionConstraint(tokenizer, vocab, q['effective_generation_tokens']['eos_token_id'], mode)
    def measure(row, text):
        constraint = constraints[row['role']]
        ids = tokenizer.encode(text, add_special_tokens=False)
        matcher = constraint.xgr.GrammarMatcher(constraint.compiled)
        eos = worker['decoder_qualification']['effective_generation_tokens']['eos_token_id'][0]
        accepted = all(matcher.accept_token(t) for t in [*ids, eos])
        encoded = tokenizer.apply_chat_template(row['messages'], tokenize=True, add_generation_prompt=True,
                                                return_dict=True, enable_thinking=True)
        return dict(input_tokens=len(encoded['input_ids']), action_tokens=len(ids),
                    grammar_accepted=accepted, rendered_input_ids_hash=digest(encoded['input_ids']))
    report = prepare(root, proposal, worker, planner, measure, planner_output_cap=planner_output_cap)
    report.update(measurement_runtime=dict(packages=packages, template=template, worker_lock_sha256=digest(worker),
        qualification_keys={role:lock['decoder_qualification']['qualification_key']
                            for role,lock in (('json',worker),('plan',planner))}),
        measurement_cpu_seconds=time.process_time()-start, measurement_wall_seconds=time.monotonic()-wall)
    report['packet_id'] = digest({k:v for k,v in report.items() if k != 'packet_id'})
    return report


def run(m, lock_path, root):
    start = time.process_time(); wall = time.monotonic()
    worker = read_json(lock_path)
    check_submission(m, worker, root, 'preflight', 1)
    packet = m['cpu_packet']
    from ..models.competence import versions
    require(packet['measurement_runtime']['packages'] == versions(), 'CPU/runtime dependency mismatch')
    require(any(r['measurement']['dispatch_allowed'] for r in packet['cases']), 'No eligible cases; do not load model')
    backend, switch, memory = base.qualified_backend(packet['base_manifest'], lock_path, root)
    rows = sequence(packet, backend, switch, memory)
    passed = len(rows) == 5 and all(r['passed'] for r in rows)
    return dict(schema='rr-open-footprint-report-v2' if packet['schema'] == PACKET_V2 else 'rr-open-footprint-report-v1',
        protocol=packet['protocol'], role_output_caps={r:base.output_cap(packet['base_manifest'], r) for r in ('json','plan')}, experiment_id=m['experiment_id'],
        manifest_hash=digest(m), source_revision=m['source_revision'], packet_id=packet['packet_id'],
        proposal_id=packet['proposal']['proposal_id'], status='passed_observed_cases' if passed else 'failed',
        command_failed=not passed, model_executed=any(r['dispatched'] for r in rows), sql_executed=False,
        task_inputs_used=False, pool=7, model_instances=1, runtime=backend.runtime, calls=rows,
        actual_tokens=sum(r['input_tokens']+r['output_tokens'] for r in rows if r['dispatched'] and not r['uncertain_tokens']),
        uncertain_tokens=sum(r['uncertain_tokens'] for r in rows),
        total_process_cpu_seconds=time.process_time()-start, total_wall_seconds=time.monotonic()-wall,
        qualification_keys=packet['measurement_runtime']['qualification_keys'],
        accounting='Separate task-free qualification; historical and task ledgers unchanged',
        limitation='Supplied-plan reproduction and selected observations only; no autonomous planning competence or universal fit.',
        **FLAGS)
