"""One reviewed synthetic-stock open-planning clean attempt; no fault branches."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import signal
import time

from ..util import BCError, digest, read_json, file_hash, atomic_json, directory_lock
from .manifest import source_revision
from . import rr_open_review as review, rr_v2_preflight as profile
from .rr_v2_competence import task_inputs, check_controls
from reporecourse import v2
from reporecourse.resources import Resources, success_at_budget
from reporecourse.common import Rejected

SCHEMA = 'rr-open-clean-manifest-v1'
LIMITATIONS = ['synthetic_task_independent_review_pending', 'uncalibrated_engineering_caps_not_B0',
               'observed_footprint_only_not_worst_case_fit', 'autonomous_competence_unmeasured',
               'one_clean_attempt_no_faults_no_retry_no_campaign']


CONTROL_FILES = (
    'src/beyond_consensus/experiments/rr_open_clean.py',
    'src/beyond_consensus/experiments/rr_open_review.py',
    'src/beyond_consensus/experiments/cluster.py',
    'src/beyond_consensus/experiments/manifest.py',
    'src/beyond_consensus/experiments/runner.py',
    'src/beyond_consensus/evaluation/aggregate.py',
    'src/beyond_consensus/reporecourse_cli.py',
    'src/beyond_consensus/cli.py',
    'tests/test_rr_open_clean.py', 'scripts/check_rr_open_clean.py',
)


# Trusted operator-owned CPU matrices and proposals can contain all 188 branch
# traces. This is NOT an input allowance for planner/worker actions or tools.
CONTROL_RECORD_BYTES = 128 * 1024 * 1024
CONTROL_RECORD_NODES = 4_000_000
CONTROL_RECORD_DEPTH = 64


def load_control_record(path):
    from reporecourse.common import bounded
    with Path(path).open('rb') as handle:
        raw = handle.read(CONTROL_RECORD_BYTES + 1)
    if len(raw) > CONTROL_RECORD_BYTES:
        raise BCError('Qualification record exceeds the 128 MiB limit')
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out: raise BCError('Duplicate qualification record key')
            out[key] = value
        return out
    try:
        record = json.loads(raw, object_pairs_hook=pairs)
        if not isinstance(record, dict): raise BCError('Qualification record must be an object')
        return bounded(record, size=CONTROL_RECORD_BYTES, depth=CONTROL_RECORD_DEPTH, nodes=CONTROL_RECORD_NODES)
    except (ValueError, RecursionError) as exc:
        raise BCError('Invalid qualification record: '+str(exc)) from exc


def control_hashes(root):
    return {name:file_hash(Path(root)/name) for name in CONTROL_FILES}


def seal(m):
    m.pop('experiment_id', None); m['experiment_id'] = digest(m)
    return m


def config(proposal):
    c = deepcopy(proposal['config']); c['planner_output_cap'] = 6144
    v2.check_config(c)
    review.require(c['pool_size'] == 7 and c['planning_lane'] == 'open_generated' and
                   c['execution_contract'] == 'plan_scoped_v1' and c['max_actions'] == 24 and
                   c['planning_calls'] == 8 and c['planning_revisions'] == 2 and c['max_units'] == 24 and
                   c['resource'] == {'profile':'rr-logical-tokens-cpu-v1', 'token_cap':100000, 'cpu_cap':1200},
                   'Only the reviewed stock engineering scope is supported')
    return c


def approval_template(m):
    return dict(schema='rr-open-clean-approval-v1', proposal_id=m['experiment_id'],
                decision='pending', reviewer=None, reviewed_at=None, source_revision=m['source_revision'],
                evidence_hash=digest(m['footprint_audit']), maximum_clean_branches=1,
                fault_branches=0, limitations_accepted=LIMITATIONS)


def authorize(m, receipt):
    validate(m)
    review.require(m['approval'] is None, 'Already approved; preserve the original record')
    expected = approval_template(m)
    review.require(set(receipt) == set(expected) and receipt.get('decision') == 'approved' and
                   all(isinstance(receipt.get(k), str) and receipt[k].strip() for k in ('reviewer','reviewed_at')),
                   'Explicit attributed clean engineering approval required')
    for key in expected.keys()-{'decision','reviewer','reviewed_at'}:
        review.require(receipt[key] == expected[key], 'Approval scope/binding differs: '+key)
    out = deepcopy(m); out['approval'] = deepcopy(receipt); out['task_execution_allowed'] = True
    return seal(out)


def build(root, sources, worker, planner, qualification, fixtures, adapter_controls, footprint_audit):
    fresh = review.inspect(footprint_audit['run'], footprint_audit['snapshots'])
    review.require(fresh == footprint_audit, 'Footprint audit changed')
    old = read_json(Path(fresh['run'])/'manifest.json')
    proposal = old['cpu_packet']['proposal']
    card, public, private = task_inputs(sources)
    review.require(proposal['task'] == 'synthetic-stock' and proposal['public_hash'] == digest(public), 'Task changed from reviewed proposal')
    base = profile.build(root, worker, planner, 7, plan_scoped=True, planner_output_cap=6144)
    from reporecourse.qualification import implementation_hashes
    m = dict(schema=SCHEMA, source_revision=source_revision(root), sources_root=str(Path(sources).resolve()),
        historical_proposal=proposal, footprint_audit=footprint_audit, backend_profile=base,
        model=base['model'], model_lock_sha256=digest(worker), config=config(proposal),
        task='synthetic-stock', task_hash=digest(card), public_hash=digest(public), private_hash=digest(private),
        implementation_hashes=implementation_hashes(), qualification=qualification, scoped_fixtures=fixtures, adapter_controls=adapter_controls,
        condition='clean', fault_branches=0, maximum_execution_branches=1,
        maximum_planning_sequences=1, shards=1, planned_episodes=1, confirmatory=False,
        campaign_allowed=False, task_execution_allowed=False, approval=None,
        budget_basis='uncalibrated_engineering_cap', limitations=LIMITATIONS)
    m['episodes'] = [dict(episode_id=digest([SCHEMA, m['source_revision'], m['public_hash'], digest(base), digest(m['config'])]), shard=0)]
    seal(m); verify(m, root, worker)
    return m


def validate(m):
    review.require(m.get('schema') == SCHEMA and m.get('experiment_id') == digest({k:v for k,v in m.items() if k!='experiment_id'}), 'Clean manifest integrity')
    c = config(m['historical_proposal'])
    review.require(m['config'] == c and m['model'] == m['backend_profile']['model'] and
        m['model_lock_sha256'] == m['backend_profile']['model_lock_sha256'] and
        m['source_revision'] == m['backend_profile']['source_revision'] and
        m['backend_profile']['schema'] == profile.FOOTPRINT_PROFILE_V3 and
        m['task'] == 'synthetic-stock' and m['condition'] == 'clean' and m['fault_branches'] == 0 and
        m['maximum_execution_branches'] == m['maximum_planning_sequences'] == m['shards'] == m['planned_episodes'] == 1 and
        m['campaign_allowed'] is False and m['confirmatory'] is False and m['limitations'] == LIMITATIONS and
        m['budget_basis'] == 'uncalibrated_engineering_cap', 'Only the bounded clean condition is allowed')
    review.require(m['episodes'] == [dict(episode_id=digest([SCHEMA, m['source_revision'], m['public_hash'], digest(m['backend_profile']), digest(c)]), shard=0)], 'Clean episode binding')
    if m['approval'] is None:
        review.require(m['task_execution_allowed'] is False, 'Approval missing')
    else:
        raw = deepcopy(m); receipt = raw.pop('approval'); raw.update(approval=None, task_execution_allowed=False); seal(raw)
        expected = approval_template(raw)
        review.require(m['task_execution_allowed'] is True and set(receipt) == set(expected) and
                       receipt['decision'] == 'approved' and
                       all(isinstance(receipt[k], str) and receipt[k].strip() for k in ('reviewer','reviewed_at')) and
                       all(receipt[k] == expected[k] for k in expected.keys()-{'decision','reviewer','reviewed_at'}), 'Approval does not bind this proposal')
    return SimpleNamespace(model=profile.validate(m['backend_profile']).model, shards=1, task_kind='rr_open_clean')


def verify(m, root, worker):
    validate(m)
    review.require(source_revision(root) == m['source_revision'] and digest(worker) == m['model_lock_sha256'], 'Source/model lock changed')
    profile.check_submission(m['backend_profile'], worker, root, 'preflight', 1)
    fresh = review.inspect(m['footprint_audit']['run'], m['footprint_audit']['snapshots'])
    review.require(fresh == m['footprint_audit'], 'Historical footprint files changed')
    old = read_json(Path(fresh['run'])/'manifest.json'); report = read_json(Path(fresh['run'])/'preflight.json')
    review.require(old['cpu_packet']['proposal'] == m['historical_proposal'], 'Historical proposal changed')
    old_worker = read_json(Path(fresh['snapshots'])/report['runtime']['snapshot_id']/'resolved/model-lock.json')
    review.require(old['model'] == m['model'], 'Worker settings changed from footprint')
    for key in ('revision','tokenizer_revision','metadata_hashes','weight_hashes'):
        review.require(worker[key] == old_worker[key], 'Frozen model changed')
    # Added adapter/routing code is reviewed separately. Existing execution and
    # decoding contracts must be byte-identical to the observed footprint source.
    marker = read_json(Path(fresh['snapshots'])/report['runtime']['snapshot_id']/'snapshot.json')
    critical = [p for p in marker['files'] if p.startswith(('src/reporecourse/', 'src/restricted_artifacts/', 'src/beyond_consensus/models/'))]
    critical += ['src/beyond_consensus/config.py', 'src/beyond_consensus/experiments/rr_v2_preflight.py', 'src/beyond_consensus/experiments/rr_open_footprint.py']
    review.require(bool(critical) and all(file_hash(Path(root)/p) == marker['files'][p] for p in critical), 'Execution/decoder source differs; renew footprint review')
    from reporecourse.qualification import implementation_hashes, runtime_versions
    from reporecourse.track_f_controls import PINS
    card, public, private = task_inputs(m['sources_root']); q = m['qualification']; fixtures = m['scoped_fixtures']
    review.require([digest(card),digest(public),digest(private)] == [m['task_hash'],m['public_hash'],m['private_hash']], 'Task/evaluator changed')
    check_controls(q, public, private)
    versions = runtime_versions()
    controls = m['adapter_controls']
    review.require(controls.get('schema') == 'rr-open-clean-controls-v1' and controls.get('status') == 'passed' and
        controls.get('source_revision') == m['source_revision'] and controls.get('implementation_hashes') == control_hashes(root) and
        controls.get('runtime_versions') == versions and controls.get('skipped') == controls.get('errors') == controls.get('failures') == 0 and
        type(controls.get('tests')) is int and controls['tests'] >= 12 and controls.get('model_executed') is False,
        'Current clean adapter CPU controls must pass without skips')
    review.require(q.get('task') == 'synthetic-stock' and q.get('task_hash') == digest(card) and
        q.get('status') == 'cpu_qualified_review_pending' and q.get('source_integrity') is True and
        q.get('reset_repeat_identical') is True and q.get('model_executed') is False and
        q.get('implementation_hashes') == m['implementation_hashes'] == implementation_hashes() and
        q.get('runtime_versions') == versions and all(versions.get(k) == v for k,v in PINS.items()), 'Fresh stock controls and pinned CPU runtime required')
    review.require(fixtures.get('status') == 'passed' and fixtures.get('evidence') == 'scripted_reference_only' and
                   fixtures.get('model_executed') is False and fixtures.get('implementation_hashes') == implementation_hashes(), 'Current scoped reference controls required')
    expected = {(task, pool, organization) for task in ('synthetic-stock','synthetic-nullable') for pool in range(2,9)
                for organization in ('independent','shared','grouped','branch_rejoin')}
    rows = fixtures.get('reports', [])
    review.require(len(rows) == len(expected) and {(r['task'],r['pool'],r['outline']) for r in rows} == expected and
        all(r['successes'] == r['branches'] == len(r['results']) and all(x.get('success') is True and
        x.get('execution_contract') == 'plan_scoped_v1' and x.get('contract_conformant') is True for x in r['results']) for r in rows), 'Incomplete or unscoped fixture matrix')


def submission(m, root, worker, mode, concurrency, output):
    review.require(mode == 'run' and concurrency == 1, 'One clean run, concurrency one only')
    verify(m, root, worker)
    review.require(m['approval'] is not None and m['task_execution_allowed'] is True, 'Clean proposal awaits explicit approval')
    output = Path(output); existing = output/'manifest.json'
    review.require(not existing.exists() or read_json(existing) == m, 'Output provenance differs')
    ep = output/'episodes'/m['episodes'][0]['episode_id']
    review.require(not (ep/'started.json').exists() and not (ep/'result.json').exists(), 'Attempt already started; no automatic retry')


def execute(m, public, private, backend, switch, save):
    """Internal allocation adapter; caller owns qualification/approval and journaling."""
    from reporecourse.engine import Engine, ModelWorker
    from reporecourse.evaluator import evaluate
    c = m['config']; switch('plan')
    planning_started = time.process_time()
    req = v2.request(public, c, {'settings': dict(m['model'], action_constraint=profile.grammar(m['backend_profile'],'plan'), max_new_tokens=6144),
                               'qualified_lock_hash': digest(m['backend_profile']['planner_lock'])})
    frozen = v2.PromptedPlanner(backend, 6144).run(req, public, save=lambda x: save('planner-journal', x))
    resources = Resources(**deepcopy(frozen['planning_resources']))
    try:
        resources.parent_overhead('open_clean_planning_parent', planning_started, 0)
    except Rejected:
        frozen.update(status='invalid_plan', error='planning_resource_exhausted', plan=None)
    frozen['planning_resources'] = deepcopy(vars(resources))
    frozen['frozen_id'] = digest({k:v for k,v in frozen.items() if k != 'frozen_id'})
    save('frozen-plan', frozen)
    row = dict(status=frozen['status'], success=False, planning=frozen,
               planning_physical_generations=frozen['physical_generation_count'],
               planning_logical_charges=1, physical_planning_reuse=False, execution_branches=0)
    if frozen['status'] != 'valid':
        if frozen['status'] == 'planning_infrastructure_failure': row['success'] = None
        row['resource_profile'] = resources.summary()
        return row
    # Do not call resolve_branches: it selects fault targets. The legacy
    # environment requires an active identity even for clean runs; pass the
    # first plan owner as an inert value instead of sampling a target.
    switch('json'); engine = None; start = time.process_time(); event_start = len(resources.events)
    try:
        engine = Engine(public, ModelWorker(backend,16384,2048), policy=c['recovery'], plan=frozen['plan'], track='clean',
                        target=frozen['plan']['units'][0]['worker'], seed=c['seeds']['execution'], resources=resources, max_actions=c['max_actions'], v2=c,
                        save=lambda state: save('checkpoint', state))
        row.update(execution_branches=1)
        try:
            row.update(engine.run())
        finally:
            resources.parent_overhead('open_clean_parent', start, event_start)
        row['legacy_inert_environment_identity'] = row.get('target')
        row['target'] = None
        row['evaluation'] = evaluate(public, private, row['state'])
        row['contract_conformant'] = row.get('conformance',{}).get('contract_conformant')
        row['success'] = success_at_budget(row['status'], row['evaluation'].get('success'), resources) and row['contract_conformant'] is True
        if row['evaluation'].get('status') == 'blocked_prerequisite':
            row.update(status='blocked_prerequisite', success=None)
    except BaseException as exc:
        from reporecourse.common import Rejected
        exhausted = isinstance(exc, Rejected) and str(exc) in ('cpu_cap','token_cap','context_limit')
        row.update(status='resource_exhausted' if exhausted else 'interrupted' if isinstance(exc,(InterruptedError,KeyboardInterrupt)) else 'infrastructure_failed',
                   success=False if exhausted else None, error_type=type(exc).__name__)
        for key in list(resources.reservations): resources.reconcile(key)
        for allowance in list(resources.cpu_pending):
            try: resources.reconcile_cpu('interrupted_execution', allowance, None)
            except Rejected: pass
        if engine is not None:
            row.update(state=engine.env.state(), events=engine.env.events, failures=engine.failures)
    finally:
        row['resource_profile'] = resources.summary()
        if engine is not None:
            row['trajectories'] = engine.trajectories
            try: engine.env.close()
            except (Exception, KeyboardInterrupt) as exc: row['cleanup_error_type'] = type(exc).__name__
        save('execution-record', row)
    return row


def run(m, output, root, *, model_lock, shard=None, retry_failures=False):
    review.require(shard in (None,0) and not retry_failures and model_lock is not None, 'One clean attempt; no retry/injected backend')
    worker = read_json(model_lock); output = Path(output)
    submission(m, root, worker, 'run', 1, output)
    from ..models.transformers_backend import require_allocation
    require_allocation()
    ep = output/'episodes'/m['episodes'][0]['episode_id']; ep.mkdir(parents=True,exist_ok=True)
    with directory_lock(ep/'.lock'):
        submission(m, root, worker, 'run', 1, output)
        atomic_json(output/'manifest.json', m); atomic_json(ep/'started.json', {'manifest_hash':digest(m)})
        backend = None; started = time.monotonic(); handlers = {}
        def save(name, data): atomic_json(ep/(name+'.json'), {'manifest_hash':digest(m),'content':data})
        def stop(*_): raise InterruptedError('allocation_termination')
        for sig in (signal.SIGTERM,signal.SIGINT): handlers[sig] = signal.signal(sig,stop)
        try:
            backend, switch, _ = profile.qualified_backend(m['backend_profile'], model_lock, root)
            prior = read_json(Path(m['footprint_audit']['run'])/'preflight.json')['runtime']
            for key in ('hardware','compute_capability','vram_total_bytes','torch_cuda','dependencies'):
                review.require(backend.runtime[key] == prior[key], 'Allocation differs from reviewed footprint: '+key)
            _, public, private = task_inputs(m['sources_root'])
            row = execute(m, public, private, backend, switch, save)
        except (Exception,KeyboardInterrupt) as exc:
            record = ep/'execution-record.json'
            row = read_json(record)['content'] if record.exists() else {}
            row.update(status='interrupted' if isinstance(exc,(InterruptedError,KeyboardInterrupt)) else 'infrastructure_failed', success=None, error_type=type(exc).__name__)
            if 'resource_profile' not in row:
                journal = ep/'planner-journal.json'
                if journal.exists():
                    state = read_json(journal)['content']
                    raw = state.get('resources', state.get('frozen',{}).get('planning_resources'))
                    if raw:
                        r = Resources(**raw)
                        for key in list(r.reservations): r.reconcile(key)
                        for allowance in list(r.cpu_pending):
                            try: r.reconcile_cpu('interrupted_planner',allowance,None)
                            except Exception: pass
                        row['resource_profile'] = r.summary()
        finally:
            for sig,handler in handlers.items(): signal.signal(sig,handler)
        row.update(schema='rr-open-clean-result-v1', experiment_id=m['experiment_id'], episode_id=m['episodes'][0]['episode_id'],
                   provenance={'manifest_hash':digest(m)}, task='synthetic-stock', track='clean', target=None,
                   campaign_allowed=False, confirmatory=False, fault_branches=0, retry_allowed=False,
                   model_executed=any(e['kind'] in ('model_usage','uncertain_interruption') for e in row.get('resource_profile',{}).get('events',[])),
                   runtime=backend.runtime if backend else None, wall_seconds=time.monotonic()-started)
        atomic_json(ep/'result.json', row); atomic_json(output/'open-clean-summary.json', aggregate(m,output))
        return [row]


def aggregate(m, output):
    validate(m); path = Path(output)/'episodes'/m['episodes'][0]['episode_id']/'result.json'
    row = read_json(path) if path.exists() else None
    review.require(row is None or (row.get('provenance',{}).get('manifest_hash') == digest(m) and row.get('experiment_id') == m['experiment_id'] and row.get('episode_id') == m['episodes'][0]['episode_id']), 'Clean result provenance mismatch')
    return dict(schema='rr-open-clean-summary-v1', experiment_id=m['experiment_id'], planned=1, observed=int(row is not None),
                missing=int(row is None), result=row, campaign_allowed=False, confirmatory=False, retry_allowed=False,
                interpretation='One synthetic open-planning clean engineering attempt; no fault or policy comparison.')
