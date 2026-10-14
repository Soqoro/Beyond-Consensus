"""Three task-free unique-key generation probes; no tools, scoring or retries."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import time
from types import SimpleNamespace

from ..config import ModelConfig
from ..models.competence import CHECKPOINT, REVISION, require_qualification
from ..models.unique_keys import MODE, synthetic_controls
from ..models.action_schema import validate_action
from ..util import BCError, digest, read_json, atomic_json
from .manifest import source_revision

SCHEMA = 'rr-unique-preflight-manifest-v1'
PROTOCOL = 'rr-unique-three-synthetic-calls-v1'


def require(value, message):
    if not value:raise BCError(message)


def model():
    return ModelConfig(backend='transformers', checkpoint=CHECKPOINT, revision=REVISION,
        tokenizer_revision=REVISION, dtype='bfloat16', context_limit=16384,
        max_new_tokens=2048, thinking=True, do_sample=False, action_constraint=MODE)


def cases():
    good, _ = synthetic_controls()
    return [dict(id='nested_mapping', text=good[1], long_context=False),
            dict(id='escaped_keys', text=good[4], long_context=False),
            dict(id='long_context_mapping', text=good[1], long_context=True)]


def check_controls(root, controls):
    from .rr_response_probe import check_controls as common
    common(root, controls)
    require('test_rr_unique_preflight.py' in controls.get('patterns', []), 'Unique preflight adapter controls missing')


def build(root, lock, controls):
    check_controls(root, controls)
    m = dict(schema=SCHEMA, protocol=PROTOCOL, model=asdict(model()),
        model_lock_sha256=digest(lock), source_revision=source_revision(root), controls=controls,
        cases=cases(), maximum_calls=3, maximum_logical_tokens=49152,
        cpu_cap_per_call=1200, shards=1, episodes=[], planned_episodes=0,
        task_inputs_used=False, task_execution_allowed=False, worst_case_fit_established=False)
    m['experiment_id'] = digest(m)
    check(m, root, lock)
    return m


def validate(m):
    require(m.get('schema') == SCHEMA and m.get('protocol') == PROTOCOL and
            m.get('experiment_id') == digest({k:v for k,v in m.items() if k != 'experiment_id'}), 'Unique preflight identity changed')
    for key, expected in dict(model=asdict(model()), cases=cases(), maximum_calls=3,
        maximum_logical_tokens=49152, cpu_cap_per_call=1200, shards=1, episodes=[],
        planned_episodes=0, task_inputs_used=False, task_execution_allowed=False,
        worst_case_fit_established=False).items():
        require(type(m.get(key)) is type(expected) and m[key] == expected, 'Unique preflight scope changed: '+key)
    return SimpleNamespace(model=model(), shards=1, task_kind='rr_unique_preflight')


def check(m, root, lock):
    validate(m)
    require(m['source_revision'] == source_revision(root), 'Unique preflight source changed')
    check_controls(root, m['controls'])
    require(m['model_lock_sha256'] == digest(lock), 'Unique worker lock changed')
    require_qualification(lock, lock.get('decoder_qualification', {}).get('packages', {}), 16384, MODE, 2048)
    q = lock['decoder_qualification'].get('unique_key_controls', {})
    good, bad = synthetic_controls()
    stops = lock['decoder_qualification'].get('effective_generation_tokens', {}).get('eos_token_id', [])
    rows = q.get('cases', [])
    expected = {(i, stop, reasoning) for i in range(len(good)+len(bad)) for stop in stops for reasoning in (False,True)}
    require(q.get('schema') == 'rr-unique-key-controls-v1' and q.get('status') == 'passed' and
            q.get('controls_hash') == digest([good,bad]) and len(expected) == 44 and len(rows) == 44 and
            {(r.get('case'),r.get('stop_token_id'),r.get('reasoning')) for r in rows} == expected and
            all(type(r.get('reasoning')) is bool and r.get('accepted') is (r['case'] < len(good)) and
                r.get('expected') is (r['case'] < len(good)) for r in rows), 'Native unique-key controls missing')


def submission(m, root, lock, mode, concurrency, output):
    check(m, root, lock)
    require(mode == 'preflight' and concurrency == 1, 'Unique preflight requires preflight mode and concurrency one')
    require(not (Path(output)/'unique-preflight-started.json').exists(), 'Unique preflight already started; no retry')


def messages(case, count):
    system = 'Synthetic decoder probe only. Return exactly this JSON action, no Markdown: ' + case['text']
    def render(n):
        return [{'role':'system', 'content':system}, {'role':'user', 'content':
            '<inert_records>\n' + ''.join(f'record {i:05d}: inert synthetic data\n' for i in range(n)) +
            '</inert_records>\nReturn the requested action.'}]
    if not case['long_context']:return render(0)
    require(count(render(0)) <= 14336, 'Synthetic instruction exceeds input allowance')
    lo, hi = 0, 16384
    while lo < hi:
        mid = (lo+hi+1)//2
        if count(render(mid)) <= 14336:lo=mid
        else:hi=mid-1
    result = render(lo)
    require(14080 <= count(result) <= 14336, 'Long-input band not reached')
    return result


def sequence(backend, memory, save):
    from reporecourse.resources import Resources
    rows = []
    for case in cases():
        resource = Resources(16384, 1200)
        row = dict(id=case['id'], status='started', passed=False, dispatched=False, output_cap=2048)
        rows.append(row)
        def checkpoint():
            row['resources'] = resource.summary()
            save(rows)
        checkpoint()
        pending = None
        cpu_pending = False
        start = time.process_time()
        try:
            resource.reserve_cpu(31);cpu_pending=True
            prompt = messages(case, backend.count_input)
            size = backend.count_input(prompt)
            require(size + 2048 <= 16384, 'Context limit exceeded')
            row.update(input_tokens=size, prompt_hash=digest(prompt), memory_before=memory(True))
            pending = resource.reserve(size, 2048)
            checkpoint()
            row['dispatched'] = True;checkpoint()
            generation = backend.generate(deepcopy(prompt), 2048, 0)
            resource.reconcile(pending, generation.output_tokens, generation.reasoning_tokens,
                finish_reason=generation.diagnostics.get('finish_reason'))
            pending = None
            cpu_pending=False
            resource.reconcile_cpu('synthetic_model_host_including_decoder',31,time.process_time()-start,
                decoder_cpu_seconds=generation.diagnostics.get('constraint_cpu_seconds'))
            row.update(generation=asdict(generation), memory_after=memory(False))
            validate_action(generation.text, MODE)
            row['passed'] = (json.loads(generation.text) == json.loads(case['text']) and
                generation.diagnostics.get('finish_reason') == 'eos' and
                generation.diagnostics.get('constraint_complete') is True and
                isinstance(generation.diagnostics.get('constraint_cpu_seconds'), (int,float)) and
                0 <= generation.diagnostics['constraint_cpu_seconds'] <= 30)
            row['status'] = 'passed' if row['passed'] else 'failed_response'
        except BaseException as exc:
            if pending is not None:resource.reconcile(pending)
            if cpu_pending:
                resource.reconcile_cpu('synthetic_model_host_including_decoder',31,time.process_time()-start)
            row.update(status='error', error_type=type(exc).__name__)
            checkpoint()
            if not isinstance(exc, Exception):raise
            break
        finally:checkpoint()
    return rows


def run(m, lock_path, root, output):
    output = Path(output)
    submission(m, root, read_json(lock_path), 'preflight', 1, output.parent)
    require(not output.exists(), 'Use a fresh preflight output')
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent/'unique-preflight-started.json').open('x') as handle:
        json.dump({'experiment_id':m['experiment_id']}, handle)
    start = time.process_time(); wall = time.monotonic()
    report = dict(schema='rr-unique-preflight-report-v1', protocol=PROTOCOL,
        experiment_id=m['experiment_id'], manifest_hash=digest(m), source_revision=m['source_revision'], status='started', command_failed=True,
        model_executed=False, model_instances=0, task_inputs_used=False, sql_executed=False,
        task_execution_allowed=False, worst_case_fit_established=False, task_competence_measured=False,
        maximum_calls=3, calls=[], accounting='Separate synthetic qualification; no historical/task ledger changes')
    def save(rows):
        report.update(calls=deepcopy(rows), model_executed=any(r.get('dispatched') for r in rows),
            actual_tokens=sum(r['resources']['actual_tokens'] for r in rows),
            uncertain_tokens=sum(r['resources']['uncertain_tokens'] for r in rows),
            total_process_cpu_seconds=time.process_time()-start, total_wall_seconds=time.monotonic()-wall)
        atomic_json(output, report)
    save([])
    try:
        from ..models.transformers_backend import TransformersBackend
        backend = TransformersBackend(model(), lock_path)
        report.update(runtime=backend.runtime, model_instances=1)
        def memory(reset):
            cuda=backend.torch.cuda
            cuda.synchronize()
            if reset:cuda.reset_peak_memory_stats(0)
            free,total=cuda.mem_get_info(0)
            return dict(peak_allocated_bytes=cuda.max_memory_allocated(0),
                peak_reserved_bytes=cuda.max_memory_reserved(0), free_bytes=free,total_bytes=total)
        rows = sequence(backend, memory, save)
        passed = len(rows)==3 and all(r['passed'] for r in rows)
        report.update(status='passed_observed_cases' if passed else 'failed', command_failed=not passed)
        save(rows)
    except BaseException as exc:
        report.update(status='error',error_type=type(exc).__name__);save(report['calls'])
        raise
    return report


def aggregate(m, output):
    validate(m)
    path = Path(output)/'preflight.json'
    if not path.is_file():return dict(experiment_id=m['experiment_id'], status='missing', model_executed=False)
    report = read_json(path)
    require(report.get('experiment_id') == m['experiment_id'] and report.get('manifest_hash') == digest(m),
            'Unique preflight report provenance changed')
    return report
