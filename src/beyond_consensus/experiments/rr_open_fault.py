"""Conditional two-owner F diagnostic; historical clean approval never authorizes it."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import math
import re
import signal
import time

from ..util import digest, file_hash, read_json, atomic_json, directory_lock
from . import rr_open_clean as clean, rr_open_review as review
from .manifest import source_revision
from .snapshot import verify_snapshot
from reporecourse import v2
from reporecourse.resources import Resources, success_at_budget
from reporecourse.common import Rejected

SCHEMA = 'rr-open-fault-manifest-v1'
SELECTION = 'conditional-frozen-plan-all-owners-v1'
LIMITATIONS = ['synthetic_task_independent_review_pending', 'uncalibrated_engineering_caps_not_B0',
              'observed_footprint_only_not_worst_case_fit', 'selected_after_clean_success',
              'historical_uniform_request_preserved_new_all_owner_diagnostic',
              'two_F_branches_no_planning_no_clean_rerun_no_retry_no_campaign']
CONTROL_FILES = clean.CONTROL_FILES + ('src/beyond_consensus/experiments/rr_open_fault.py',
                                     'tests/test_rr_open_fault.py', 'scripts/check_rr_open_fault.py')


def control_hashes(root):
    return {p: file_hash(Path(root)/p) for p in CONTROL_FILES}


def check_ledger(raw):
    r = Resources(**deepcopy(raw))
    review.require(not r.reservations and not r.cpu_pending and r.cpu_reserved == 0 and
                   r.uncertain_tokens == r.uncertain_cpu == 0, 'Unsettled historical planning ledger')
    for event in r.events:
        if event['kind']=='model_usage':
            review.require(all(type(event.get(k)) is int and event[k]>=0 for k in ('input_tokens','output_tokens')),
                           'Invalid historical token measurement')
        if event['kind']=='cpu':
            review.require(type(event.get('cap_debit')) in (int,float) and math.isfinite(event['cap_debit']) and
                           event['cap_debit']>=0, 'Invalid historical CPU measurement')
    tokens = sum(e['input_tokens']+e['output_tokens'] for e in r.events if e['kind']=='model_usage')
    cpu = sum(e['cap_debit'] for e in r.events if e['kind']=='cpu')
    review.require(tokens == r.actual_tokens and math.isclose(cpu, r.cpu_seconds, abs_tol=1e-8) and
                   0 < tokens < r.token_cap == 100000 and 0 <= cpu < r.cpu_cap == 1200,
                   'Historical planning charges do not reconcile')
    return r


def check_frozen(frozen, config):
    v2.verify_record(frozen, 'frozen_id'); v2.verify_record(frozen['request'], 'request_id')
    review.require(frozen['status']=='valid' and frozen['mode']=='real_model' and
                   frozen['request']['config']==config and config['target_rule']=='uniform' and config['threat']=='F' and config['recovery']=='delegation_jit', 'Historical request changed')
    check_ledger(frozen['planning_resources'])
    review.require(0 < frozen['physical_generation_count'] <= config['planning_calls'] and
                   frozen['physical_generation_count']==sum(bool(e.get('generation_dispatched')) for e in frozen['planning_events']) and
                   frozen['physical_generation_count']==sum(e['kind']=='model_usage' for e in frozen['planning_resources']['events']),
                   'Historical planner call accounting differs')
    units = frozen['plan']['units']
    review.require([(u['id'],u['worker'],u['outputs']) for u in units] ==
                   [('u0','w0',['stock_report']),('u1','w1',['zero_report'])] and
                   units[0]['depends']==[] and units[1]['depends']==['u0'], 'Only reviewed two-owner stock plan allowed')


def inspect_history(run, snapshots, receipt):
    """Read current bytes and inventory; never import or execute historical source."""
    run, snapshots = Path(run).resolve(), Path(snapshots).resolve()
    m = clean.load_control_record(run/'manifest.json'); clean.validate(m)
    review.require(m['approval'] is not None and m['task_execution_allowed'] is True, 'Historical clean approval missing')
    ep = run/'episodes'/m['episodes'][0]['episode_id']
    result = clean.load_control_record(ep/'result.json')
    sid = result['runtime']['snapshot_id']
    review.require(isinstance(sid,str) and re.fullmatch('[0-9a-f]{64}',sid), 'Invalid snapshot identity')
    snapshot = snapshots/sid
    review.require(not snapshot.is_symlink(), 'Snapshot symlink rejected')
    marker = verify_snapshot(snapshot)
    review.require(clean.load_control_record(snapshot/'resolved/manifest.json')==m and
                   marker['manifest_hash']==digest(m) and marker['source_revision']==m['source_revision'], 'Historical snapshot binding')
    receipt_path = Path(receipt).resolve(); submission = read_json(receipt_path)
    review.require(Path(submission['output']).resolve()==run and Path(submission['snapshot']).resolve()==snapshot and
                   str(submission.get('job_id','')).isdigit(), 'Submission receipt binding')
    review.require(result['experiment_id']==m['experiment_id'] and result['episode_id']==m['episodes'][0]['episode_id'] and
                   result['provenance']['manifest_hash']==digest(m) and result['status']=='completed' and
                   result['success'] is True and result['contract_conformant'] is True and
                   result['execution_branches']==1 and result['fault_branches']==0 and
                   result['evaluation']['success'] is True, 'Successful conformant clean evidence required')
    paths = [run/'manifest.json', ep/'result.json', receipt_path, snapshot/'snapshot.json']
    for name in ('started','frozen-plan','execution-record'):
        path = ep/(name+'.json'); record = clean.load_control_record(path); paths.append(path)
        review.require(record['manifest_hash']==digest(m), 'Journal manifest mismatch')
        if name=='frozen-plan': review.require(record['content']==result['planning'], 'Frozen journal differs')
        if name=='execution-record':
            review.require(all(result.get(k)==v for k,v in record['content'].items()), 'Execution journal differs')
    historical_worker=read_json(snapshot/'resolved/model-lock.json')
    review.require(digest(historical_worker)==m['model_lock_sha256']==result['runtime']['model_lock_hash'] and
                   result['runtime']['settings']==m['model'] and
                   marker['cluster_hash']==digest(read_json(snapshot/'resolved/cluster.json')) and
                   result['runtime']['import_path']==str(snapshot/'src/beyond_consensus/models/transformers_backend.py'),
                   'Historical runtime/source binding differs')
    frozen = result['planning']; check_frozen(frozen,m['config'])
    ledger=result['resource_profile']; events=ledger['events']
    review.require(sum(e['input_tokens']+e['output_tokens'] for e in events if e['kind']=='model_usage')==ledger['actual_tokens'] and
                   math.isclose(sum(e['cap_debit'] for e in events if e['kind']=='cpu'),ledger['cpu_cap_debit'],abs_tol=1e-8) and
                   0 <= ledger['actual_tokens'] <= ledger['token_cap']==100000 and
                   0 <= ledger['cpu_cap_debit'] <= ledger['cpu_cap']==1200 and
                   all(ledger[k]==0 for k in ('reserved_tokens','cpu_reserved','uncertain_tokens','uncertain_cpu')),
                   'Historical total ledger mismatch')
    review.require(result['plan']==frozen['plan'] and result['planning_logical_charges']==1 and
                   result['resource_profile']['events'][:len(frozen['planning_resources']['events'])]==frozen['planning_resources']['events'],
                   'Clean planning prefix changed')
    from reporecourse.conformance import report
    review.require(report(result)['contract_conformant'] is True, 'Clean conformance audit failed')
    return dict(schema='rr-open-fault-history-v1', run=str(run), snapshots=str(snapshots), receipt=str(receipt_path),
                experiment_id=m['experiment_id'], manifest_hash=digest(m), frozen=frozen, config=m['config'],
                public_hash=m['public_hash'], private_hash=m['private_hash'], task_hash=m['task_hash'], model=m['model'],
                implementation_hashes=m['implementation_hashes'], runtime=result['runtime'],
                input_hashes={str(p):file_hash(p) for p in paths}, snapshot_inventory_verified=True,
                scheduler_completion_verified=False, authenticity='internal_file_bindings_only')


def episodes(history):
    return [dict(episode_id=digest([SCHEMA,history['manifest_hash'],history['frozen']['frozen_id'],SELECTION,t]),
                 shard=i, track='F', target=t, weight=0.5) for i,t in enumerate(('w0','w1'))]


def approval_template(m):
    return dict(schema='rr-open-fault-approval-v1', decision='pending', reviewer=None, reviewed_at=None,
                proposal_id=m['experiment_id'], source_revision=m['source_revision'], evidence_hash=digest(m['history']),
                targets=['w0','w1'], fault_branches=2, clean_branches=0, limitations_accepted=LIMITATIONS)


def build(root, qualified_clean, worker, run, snapshots, receipt, controls):
    clean.verify(qualified_clean, root, worker)
    history = inspect_history(run,snapshots,receipt)
    m = dict(schema=SCHEMA, source_revision=source_revision(root), qualification=deepcopy(qualified_clean),
             history=history, controls=controls, model=qualified_clean['model'], config=history['config'],
             model_lock_sha256=digest(worker), shards=2, planned_episodes=2, episodes=episodes(history),
             selection_rule=SELECTION, approval=None, task_execution_allowed=False, campaign_allowed=False,
             confirmatory=False, limitations=LIMITATIONS)
    clean.seal(m); verify(m,root,worker)
    return m


def validate(m):
    review.require(m.get('schema')==SCHEMA and m.get('experiment_id')==digest({k:v for k,v in m.items() if k!='experiment_id'}), 'Fault manifest integrity')
    q = m['qualification']; clean.validate(q)
    h = m['history']; check_frozen(h['frozen'],h['config'])
    review.require(m['source_revision']==q['source_revision'] and m['model']==q['model']==h['model'] and
                   m['model_lock_sha256']==q['model_lock_sha256'] and m['config']==q['config']==h['config'] and
                   all(q[k]==h[k] for k in ('public_hash','private_hash','task_hash','implementation_hashes')) and
                   m['shards']==m['planned_episodes']==2 and m['episodes']==episodes(h) and
                   m['selection_rule']==SELECTION and m['limitations']==LIMITATIONS and
                   m['campaign_allowed'] is False and m['confirmatory'] is False, 'Conditional F scope changed')
    if m['approval'] is None:
        review.require(m['task_execution_allowed'] is False, 'Fault approval missing')
    else:
        proposal = deepcopy(m); proposal.update(approval=None,task_execution_allowed=False); clean.seal(proposal)
        expected = approval_template(proposal); a=m['approval']
        review.require(set(a)==set(expected) and a['decision']=='approved' and
                       all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')) and
                       all(a[k]==expected[k] for k in expected.keys()-{'decision','reviewer','reviewed_at'}) and
                       m['task_execution_allowed'] is True, 'Fault approval binding changed')
    return SimpleNamespace(model=clean.profile.validate(q['backend_profile']).model, shards=2, task_kind='rr_open_fault')


def authorize(m, receipt):
    validate(m); review.require(m['approval'] is None, 'Already approved')
    out=deepcopy(m);out.update(approval=deepcopy(receipt),task_execution_allowed=True);clean.seal(out);validate(out)
    return out


def verify(m, root, worker):
    validate(m); clean.verify(m['qualification'],root,worker)
    h=m['history']
    _,public,_=clean.task_inputs(m['qualification']['sources_root'])
    review.require(h['frozen']['request']['public_hash']==digest(public) and
                   v2.validate_work_plan(h['frozen']['plan'],public,m['config'])==h['frozen']['plan'], 'Historical plan/public inputs differ')
    review.require(inspect_history(h['run'],h['snapshots'],h['receipt'])==h, 'Historical evidence changed')
    from reporecourse.qualification import runtime_versions
    c=m['controls']
    review.require(c.get('schema')=='rr-open-fault-controls-v1' and c.get('status')=='passed' and
                   c.get('source_revision')==m['source_revision'] and c.get('implementation_hashes')==control_hashes(root) and
                   c.get('runtime_versions')==runtime_versions() and c.get('model_executed') is False and
                   c.get('skipped')==c.get('failures')==c.get('errors')==0 and type(c.get('tests')) is int and c['tests']>=10,
                   'Fresh no-skip fault adapter controls required')


def admission(m, output, shard=None):
    review.require(m['approval'] is not None and m['task_execution_allowed'] is True, 'Separate fault approval required')
    output=Path(output)
    if (output/'manifest.json').exists(): review.require(clean.load_control_record(output/'manifest.json')==m,'Output provenance differs')
    for e in m['episodes']:
        if shard is not None and e['shard']!=shard: continue
        p=output/'episodes'/e['episode_id']
        review.require(not (p/'started.json').exists() and not (p/'result.json').exists(), 'Fault attempt already started; no retry')


def submission(m, root, worker, mode, concurrency, output):
    review.require(mode=='run' and concurrency==1, 'Fault diagnostic run-only, concurrency one')
    verify(m,root,worker); admission(m,output)


def execute(m, episode, public, private, backend, save):
    from reporecourse.engine import Engine, ModelWorker
    from reporecourse.evaluator import evaluate
    c=m['config']; frozen=m['history']['frozen']; resources=check_ledger(frozen['planning_resources'])
    row=dict(status='started',success=None,track='F',target=episode['target'],planning=frozen,
             planning_logical_charges=1,planning_physical_generations=0,physical_planning_reuse=True,
             execution_branches=0,fault_branches=1,selection_rule=SELECTION)
    engine=None; start=time.process_time(); first=len(resources.events); overhead_recorded=False
    try:
        engine=Engine(public,ModelWorker(backend,16384,2048),policy=c['recovery'],plan=frozen['plan'],track='F',
                      target=episode['target'],seed=c['seeds']['execution'],resources=resources,max_actions=c['max_actions'],v2=c,
                      save=lambda state:save('checkpoint',state))
        row['execution_branches']=1
        try: row.update(engine.run())
        finally:
            overhead_recorded=True
            resources.parent_overhead('open_fault_parent',start,first)
        row['evaluation']=evaluate(public,private,row['state'])
        row['contract_conformant']=row.get('conformance',{}).get('contract_conformant')
        row['success']=success_at_budget(row['status'],row['evaluation'].get('success'),resources) and row['contract_conformant'] is True
        if row['evaluation'].get('status')=='blocked_prerequisite': row.update(status='blocked_prerequisite',success=None)
    except BaseException as exc:
        if not overhead_recorded:
            try: resources.parent_overhead('open_fault_parent',start,first)
            except Rejected: pass
        exhausted=isinstance(exc,Rejected) and str(exc) in ('cpu_cap','token_cap','context_limit')
        row.update(status='resource_exhausted' if exhausted else 'interrupted' if isinstance(exc,(InterruptedError,KeyboardInterrupt)) else 'infrastructure_failed',
                   success=False if exhausted else None,error_type=type(exc).__name__)
        for key in list(resources.reservations): resources.reconcile(key)
        for allowance in list(resources.cpu_pending):
            try: resources.reconcile_cpu('interrupted_execution',allowance,None)
            except Rejected: pass
        if engine is not None: row.update(state=engine.env.state(),events=engine.env.events,failures=engine.failures)
    finally:
        row['resource_profile']=resources.summary()
        row['model_executed']=any(e['kind'] in ('model_usage','uncertain_interruption') for e in resources.events[first:])
        if engine is not None:
            row['trajectories']=engine.trajectories
            try: engine.env.close()
            except (Exception,KeyboardInterrupt) as exc: row['cleanup_error_type']=type(exc).__name__
        save('execution-record',row)
    return row


def run(m, output, root, *, model_lock, shard=None, retry_failures=False):
    review.require(type(shard) is int and shard in (0,1) and not retry_failures and model_lock is not None, 'One explicit fault shard; no retry')
    worker=read_json(model_lock);verify(m,root,worker);admission(m,output,shard)
    from ..models.transformers_backend import require_allocation
    require_allocation();output=Path(output);episode=m['episodes'][shard]
    ep=output/'episodes'/episode['episode_id'];ep.mkdir(parents=True,exist_ok=True)
    with directory_lock(ep/'.lock'):
        admission(m,output,shard);atomic_json(output/'manifest.json',m)
        atomic_json(ep/'started.json',dict(manifest_hash=digest(m),target=episode['target']))
        backend=None;started=time.monotonic();handlers={}
        def save(name,data): atomic_json(ep/(name+'.json'),dict(manifest_hash=digest(m),content=data))
        def stop(*_): raise InterruptedError('allocation_termination')
        for sig in (signal.SIGTERM,signal.SIGINT): handlers[sig]=signal.signal(sig,stop)
        row=dict(status='infrastructure_failed',success=None,model_executed=False,execution_branches=0,
                 planning_logical_charges=1,physical_planning_reuse=True,planning_physical_generations=0,
                 resource_profile=check_ledger(m['history']['frozen']['planning_resources']).summary())
        try:
            backend,switch,_=clean.profile.qualified_backend(m['qualification']['backend_profile'],model_lock,root)
            for key in ('hardware','compute_capability','vram_total_bytes','torch_cuda','dependencies'):
                review.require(backend.runtime[key]==m['history']['runtime'][key], 'Allocation differs from clean: '+key)
            switch('json');_,public,private=clean.task_inputs(m['qualification']['sources_root'])
            row=execute(m,episode,public,private,backend,save)
        except (Exception,KeyboardInterrupt) as exc:
            record=ep/'execution-record.json'
            if record.exists(): row=clean.load_control_record(record)['content']
            row.update(status='interrupted' if isinstance(exc,(InterruptedError,KeyboardInterrupt)) else 'infrastructure_failed',success=None,error_type=type(exc).__name__)
        finally:
            for sig,handler in handlers.items(): signal.signal(sig,handler)
        row.update(schema='rr-open-fault-result-v1',experiment_id=m['experiment_id'],episode_id=episode['episode_id'],
                   provenance={'manifest_hash':digest(m)},task='synthetic-stock',track='F',target=episode['target'],
                   fault_branches=1,confirmatory=False,campaign_allowed=False,retry_allowed=False,
                   runtime=backend.runtime if backend else None,wall_seconds=time.monotonic()-started)
        atomic_json(ep/'result.json',row)
        return [row]


def aggregate(m, output):
    validate(m); rows=[]
    for e in m['episodes']:
        path=Path(output)/'episodes'/e['episode_id']/'result.json'
        row=clean.load_control_record(path) if path.exists() else None
        if row is not None:
            review.require(row.get('provenance',{}).get('manifest_hash')==digest(m) and
                           row.get('episode_id')==e['episode_id'] and row.get('experiment_id')==m['experiment_id'] and
                           row.get('track')=='F' and row.get('target')==e['target'], 'Fault result provenance differs')
        rows.append(dict(target=e['target'],weight=e['weight'],result=row))
    return dict(schema='rr-open-fault-summary-v1',experiment_id=m['experiment_id'],planned=2,
                observed=sum(x['result'] is not None for x in rows),branches=rows,confirmatory=False,campaign_allowed=False,
                interpretation='Conditional on one previously successful generated plan; no matched fresh clean or policy effect.',
                historical_clean_experiment=m['history']['experiment_id'],retry_allowed=False)
