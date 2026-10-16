"""Bounded synthetic semantic diagnostic through the shared GPU submission path."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import os
import time

from ..config import ModelConfig
from ..util import BCError, digest, file_hash, atomic_json
from ..models.competence import require_qualification, versions
from .manifest import source_revision
from .rr_open_clean import load_control_record as load, seal
from . import rr_unique_review as normal
from . import rr_semantic_diagnostic as design
from reporecourse.common import Rejected
from reporecourse.engine import ModelWorker, worker_messages
from reporecourse.resources import Resources, success_at_budget
from reporecourse.qualification import implementation_hashes, runtime_versions
from reporecourse.sampled_cohort import model_settings, MODE

SCHEMA = 'rr-semantic-run-manifest-v1'
CASES = ('order_grain', 'unpaid_boundary', 'mapping_keys')
PATTERNS = ('test_rr_semantic_diagnostic.py', 'test_rr_semantic_run.py')
FILES = ('src/beyond_consensus/experiments/rr_semantic_run.py',
         'src/beyond_consensus/experiments/rr_semantic_diagnostic.py',
         'src/beyond_consensus/experiments/rr_unique_review.py',
         'src/beyond_consensus/experiments/manifest.py',
         'src/beyond_consensus/experiments/runner.py',
         'src/beyond_consensus/experiments/cluster.py',
         'src/beyond_consensus/evaluation/aggregate.py', 'src/beyond_consensus/cli.py',
         'scripts/prepare_rr_semantic_run.py', 'scripts/check_rr_semantic_run.py',
         'tests/test_rr_semantic_run.py', 'tests/test_rr_semantic_diagnostic.py')
LIMITATIONS = ['post_hoc_synthetic_mechanisms_not_held_out_tasks',
              'one_call_per_case_no_repair_no_retry', 'no_decoder_causal_attribution',
              'observed_memory_only_not_worst_case_fit',
              'public_monitor_unchanged_private_scores_not_worker_feedback']


def require(ok, message):
    if not ok:
        raise BCError(message)


def hashes(root):
    return {**implementation_hashes(), **{p: file_hash(Path(root)/p) for p in FILES}}


def observation(env):
    value = env.observation('w0')
    # Expose fixed caps, not nondeterministic setup timing; actual ledgers unchanged.
    value.pop('cpu_remaining', None)
    value['diagnostic_caps'] = dict(tokens=16384, cpu_seconds=1200)
    value['synthetic_sources'] = deepcopy(env.public['sources'])
    value['diagnostic_instruction'] = 'All synthetic sources are supplied here. Return one publish action for report. No read calls or retries are available.'
    return value


def messages(case_id):
    env = design.environment(case_id, Resources(16384, 1200))
    try:
        return worker_messages(observation(env), [])
    finally:
        env.close()


def footprint(worker):
    from transformers import AutoTokenizer
    from ..models.transformers_backend import verify_thinking_template
    require_qualification(worker, versions(), 16384, MODE, 2048)
    start = time.process_time()
    tokenizer = AutoTokenizer.from_pretrained(worker['tokenizer_path'], local_files_only=True, trust_remote_code=False)
    template = verify_thinking_template(tokenizer, True)
    rows = []
    for case_id in CASES:
        prompt = messages(case_id)
        ids = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True,
            enable_thinking=True, return_dict=True)['input_ids']
        rows.append(dict(id=case_id, messages_hash=digest(prompt), input_tokens=len(ids),
                         rendered_input_ids_hash=digest(ids), passed=0 < len(ids) <= 14336))
    return dict(schema='rr-semantic-footprint-v1', cases=rows, template=template,
                worker_lock_hash=digest(worker), core_hashes=implementation_hashes(),
                adapter_hash=file_hash(Path(__file__)), diagnostic_hash=file_hash(Path(design.__file__)),
                status='passed' if all(r['passed'] for r in rows) else 'failed',
                model_executed=False, task_execution_allowed=False,
                analysis_cpu_seconds=time.process_time()-start)


def check_production(record):
    expected = [('order_grain', None), ('order_grain', 'fanout'), ('order_grain', 'distinct_amount'),
                ('unpaid_boundary', None), ('unpaid_boundary', 'null_row'),
                ('mapping_keys', None), ('mapping_keys', 'wrong_keys')]
    require(record.get('schema') == 'rr-semantic-production-controls-v1' and record.get('status') == 'passed' and
            record.get('implementation_hashes') == implementation_hashes() and
            record.get('diagnostic_sha256') == file_hash(Path(design.__file__)) and
            record.get('runtime_versions') == runtime_versions() and record.get('model_executed') is False and
            record.get('sql_executed') is True and record.get('task_execution_allowed') is False,
            'Production controls missing or incompatible')
    rows = record.get('cases', [])
    require([(r.get('case'), r.get('mutation')) for r in rows] == expected, 'Production cases changed')
    for row in rows:
        require(row.get('status') == 'passed' and row.get('public_monitor_passed') is True and
                row.get('execution_status') == 'ok' and row.get('semantic_correct') is (row['mutation'] is None) and
                all(row['resources'].get(k) == 0 for k in ('uncertain_cpu', 'uncertain_tokens', 'reserved_tokens', 'cpu_reserved')),
                'Incomplete production controls')


def build(root, worker, production, controls, measured, run, snapshots):
    audit = normal.inspect(run, snapshots, root)
    m = dict(schema=SCHEMA, source_revision=source_revision(root), model=model_settings(),
             model_lock_sha256=digest(worker), implementation_hashes=hashes(root),
             evidence=dict(production=production, controls=controls, footprint=measured, normal=audit),
             cases=list(CASES), maximum_calls=3, model_planner_calls=0, seed=0,
             pool=7, context_limit=16384, output_cap=2048, token_cap=16384, cpu_cap=1200,
             evaluator_cpu_cap=1200, shards=1, episodes=[], planned_episodes=0,
             task_execution_allowed=False, approval=None, limitations=LIMITATIONS,
             historical_scores_changed=False, confirmatory=False)
    seal(m)
    verify(m, root, worker)
    return m


def approval_template(m):
    return dict(schema='rr-semantic-run-approval-v1', proposal_id=m['experiment_id'],
                scope_hash=digest({k:v for k,v in m.items() if k not in ('experiment_id','approval','task_execution_allowed')}),
                maximum_calls=3, model_planner_calls=0, limitations_accepted=LIMITATIONS,
                decision='pending', reviewer=None, reviewed_at=None)


def validate(m):
    require(m.get('schema') == SCHEMA and m.get('experiment_id') == digest({k:v for k,v in m.items() if k != 'experiment_id'}), 'Semantic manifest identity changed')
    fixed = dict(cases=list(CASES), maximum_calls=3, model_planner_calls=0, seed=0, pool=7,
                 context_limit=16384, output_cap=2048, token_cap=16384, cpu_cap=1200,
                 evaluator_cpu_cap=1200, shards=1, episodes=[], planned_episodes=0,
                 model=model_settings(), limitations=LIMITATIONS, historical_scores_changed=False, confirmatory=False)
    require(all(type(m.get(k)) is type(v) and m[k] == v for k,v in fixed.items()), 'Semantic scope changed')
    receipt = m.get('approval')
    if receipt is None:
        require(m.get('task_execution_allowed') is False, 'Missing exact approval')
    else:
        proposal = deepcopy(m); proposal.update(approval=None, task_execution_allowed=False); seal(proposal)
        expected = approval_template(proposal)
        require(m.get('task_execution_allowed') is True and set(receipt) == set(expected) and
                receipt.get('decision') == 'approved' and
                all(isinstance(receipt.get(k), str) and receipt[k].strip() for k in ('reviewer','reviewed_at')) and
                all(receipt[k] == v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')), 'Exact three-call approval changed')
    return SimpleNamespace(model=ModelConfig(**m['model']), shards=1, task_kind='rr_semantic_diagnostic')


def verify(m, root, worker):
    validate(m)
    require(m['source_revision'] == source_revision(root) and m['implementation_hashes'] == hashes(root), 'Semantic implementation changed')
    require(digest(worker) == m['model_lock_sha256'], 'Worker lock changed')
    require_qualification(worker, versions(), 16384, MODE, 2048)
    check_production(m['evidence']['production'])
    c = m['evidence']['controls']
    require(c.get('schema') == 'rr-semantic-run-controls-v1' and c.get('status') == 'passed' and
            c.get('source_revision') == m['source_revision'] and c.get('implementation_hashes') == hashes(root) and
            c.get('patterns') == list(PATTERNS) and c.get('runtime_versions') == runtime_versions() and
            c.get('tests', 0) >= 8 and all(c.get(k) == 0 for k in ('skipped','failures','errors')), 'Renewed no-skip adapter controls required')
    f = m['evidence']['footprint']
    require(f.get('schema') == 'rr-semantic-footprint-v1' and f.get('status') == 'passed' and
            f.get('worker_lock_hash') == digest(worker) and f.get('adapter_hash') == file_hash(Path(__file__)) and
            f.get('diagnostic_hash') == file_hash(Path(design.__file__)) and f.get('core_hashes') == implementation_hashes() and
            [(r['id'], r['messages_hash']) for r in f['cases']] == [(i, digest(messages(i))) for i in CASES] and
            all(r['passed'] is True and type(r['input_tokens']) is int and 0 < r['input_tokens'] <= 14336 for r in f['cases']), 'Prompt footprint changed')
    audit = m['evidence']['normal']; fresh = normal.inspect(audit['run'], audit['snapshots'], root)
    saved = deepcopy(audit); saved['current_compatibility']['checked_root'] = fresh['current_compatibility']['checked_root']
    require(saved == fresh and fresh['current_compatibility']['status'] == 'compatible', 'Normal qualification incompatible')
    prior = load(Path(audit['run'])/'manifest.json')
    require(prior['model_lock_sha256'] == digest(worker) and prior['model'] == m['model'], 'Normal model differs')


def authorize(m, receipt, root, worker):
    verify(m, root, worker)
    require(m['approval'] is None, 'Already approved')
    result = deepcopy(m); result.update(approval=deepcopy(receipt), task_execution_allowed=True)
    seal(result); validate(result)
    return result


def submission(m, worker, root, mode, concurrency, output):
    require(mode == 'run' and concurrency == 1, 'Semantic diagnostic is run-only, concurrency one')
    verify(m, root, worker)
    require(m['task_execution_allowed'] is True, 'Exact three-call approval required')
    require(not (Path(output)/'semantic-started.json').exists() and not (Path(output)/'semantic-report.json').exists(), 'Diagnostic already started; no retry')


def sequence(backend, measured, save):
    """One fresh scoped assignment/call per case; private grading after dispatch."""
    rows = []
    for case_id in CASES:
        resources = Resources(16384, 1200); evaluator = Resources(1, 1200)
        row = dict(id=case_id, status='started', dispatched=False, semantic_correct=None,
                   public_monitor_passed=None, complete_in_budget=False)
        rows.append(row); env = None
        def checkpoint():
            row['resources'] = deepcopy(resources.summary())
            row['evaluator_resources'] = deepcopy(evaluator.summary())
            save(deepcopy(rows))
        checkpoint()
        class Recorded:
            def count_input(self, prompt):
                expected = next(r for r in measured['cases'] if r['id'] == case_id)
                require(digest(prompt) == expected['messages_hash'], 'Runtime prompt changed')
                count = backend.count_input(prompt)
                require(count == expected['input_tokens'], 'Runtime token count changed')
                return count
            def generate(self, prompt, cap, seed):
                row['dispatched'] = True; checkpoint()
                generation = backend.generate(prompt, cap, seed)
                row['generation'] = dict(text=generation.text, output_tokens=generation.output_tokens,
                    reasoning_tokens=generation.reasoning_tokens, diagnostics=deepcopy(generation.diagnostics))
                return generation
        try:
            started = time.process_time(); index = len(resources.events)
            try:
                env = design.environment(case_id, resources)
                visible = observation(env)
            finally:
                resources.parent_overhead('diagnostic_setup', started, index)
            started = time.process_time(); index = len(resources.events)
            try:
                action = ModelWorker(Recorded(), 16384, 2048).next_action(env.public, env.assignment['w0'], visible, [], resources, 0, checkpoint)
            finally:
                resources.parent_overhead('diagnostic_response_parsing', started, index)
            row['action'] = deepcopy(action)
            diagnostics = row['generation']['diagnostics']
            if diagnostics.get('finish_reason') != 'eos' or diagnostics.get('constraint_complete') is not True:
                raise Rejected('incomplete_generated_response')
            valid = (isinstance(action, dict) and set(action) == {'tool','name','format','content','bindings','obligations'} and \
                    action['tool'] == 'publish' and action['name'] == 'report' and action['bindings'] == {} and
                    action['obligations'] == ['report'] and action['format'] == env.public['required_outputs'][0]['format'])
            if not valid:
                raise Rejected('diagnostic_action_contract')
            started = time.process_time(); index = len(resources.events)
            try:
                env.action('w0', action)
                row['public_monitor_passed'] = env.check_public()['report']
            finally:
                resources.parent_overhead('diagnostic_publication_and_monitor', started, index)
            checkpoint()
            # Terminal evaluation has its own ledger and cannot trigger model feedback.
            env.resources = evaluator
            started = time.process_time(); index = len(evaluator.events)
            try:
                result = env.execute(env.bound['report'], env.public['examples']['default'])
                row.update(execution_status=result['status'], semantic_correct=design.semantic_check(case_id, result))
            finally:
                evaluator.parent_overhead('diagnostic_terminal_evaluation', started, index)
            row['status'] = 'completed'
            row['complete_in_budget'] = success_at_budget('completed', row['semantic_correct'], resources)
        except Rejected as exc:
            row.update(status='rejected', error_category=str(exc))
            if hasattr(exc, 'response_diagnostic'):
                row['response_diagnostic'] = exc.response_diagnostic
            if resources.uncertain_tokens or resources.uncertain_cpu or str(exc) == 'blocked_prerequisite':
                row['status'] = 'infrastructure_failed'
        except Exception as exc:
            row.update(status='infrastructure_failed', error_type=type(exc).__name__)
        except BaseException as exc:
            row.update(status='interrupted', error_type=type(exc).__name__)
            checkpoint(); raise
        finally:
            if env is not None:
                row['events'] = deepcopy(env.events)
                try:
                    env.close()
                except Exception as exc:
                    row.update(status='infrastructure_failed', cleanup_error_type=type(exc).__name__)
            checkpoint()
        if row['status'] == 'infrastructure_failed':
            break
    return rows


def run(m, output, root, *, model_lock, shard=None, retry_failures=False):
    require(shard in (None, 0) and not retry_failures, 'No extra shard or retry')
    require(os.environ.get('CUDA_LAUNCH_BLOCKING','0') in ('','0'), 'Normal asynchronous mode required')
    worker = load(model_lock); output = Path(output)
    submission(m, worker, root, 'run', 1, output)
    output.mkdir(parents=True, exist_ok=True)
    with (output/'semantic-started.json').open('x') as handle:
        handle.write(m['experiment_id']+'\n')
    start = time.process_time(); wall = time.monotonic()
    report = dict(schema='rr-semantic-run-report-v1', experiment_id=m['experiment_id'], manifest_hash=digest(m),
                  status='started', calls=[], planned_calls=3, model_executed=False,
                  historical_scores_changed=False, worker_feedback=False,
                  accounting='Diagnostic task ledgers and terminal evaluator ledgers separate; process CPU overlaps parent subsets.', limitations=LIMITATIONS)
    def save(rows):
        report.update(calls=rows, model_executed=any(r['dispatched'] for r in rows),
                      missing_cases=[i for i in CASES if i not in [r['id'] for r in rows]],
                      actual_tokens=sum(r['resources']['actual_tokens'] for r in rows),
                      uncertain_tokens=sum(r['resources']['uncertain_tokens'] for r in rows),
                      process_cpu_seconds=time.process_time()-start, wall_seconds=time.monotonic()-wall)
        atomic_json(output/'semantic-report.json', report)
    save([])
    try:
        from ..models.transformers_backend import TransformersBackend
        backend = TransformersBackend(ModelConfig(**m['model']), model_lock)
        prior = load(Path(m['evidence']['normal']['run'])/'preflight.json')['runtime']
        report['runtime'] = backend.runtime
        for key in ('hardware','compute_capability','vram_total_bytes','torch_cuda','dependencies'):
            require(backend.runtime[key] == prior[key], 'Allocation differs from normal qualification: '+key)
        rows = sequence(backend, m['evidence']['footprint'], save)
        report['status'] = 'completed' if len(rows) == 3 and all(r['status'] in ('completed','rejected') for r in rows) else 'incomplete'
        save(rows)
    except BaseException as exc:
        report.update(status='interrupted' if not isinstance(exc, Exception) else 'infrastructure_failed', error_type=type(exc).__name__)
        save(report['calls']); raise
    return [report]


def aggregate(m, output):
    validate(m)
    path = Path(output)/'semantic-report.json'
    if not path.is_file():
        return dict(experiment_id=m['experiment_id'], status='missing', missing_cases=list(CASES))
    report = load(path)
    require(report.get('experiment_id') == m['experiment_id'] and report.get('manifest_hash') == digest(m), 'Semantic result provenance changed')
    ids = [r['id'] for r in report['calls']]
    require(ids == list(CASES[:len(ids)]), 'Unexpected/duplicate diagnostic cases')
    return report
