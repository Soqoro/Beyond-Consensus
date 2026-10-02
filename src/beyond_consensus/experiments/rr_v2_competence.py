"""Exact synthetic-stock clean competence exception; never a policy campaign."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import signal
import time

from ..config import ModelConfig
from ..util import BCError, atomic_json, digest, read_json, file_hash, directory_lock
from .manifest import source_revision
from .rr_v2_evidence import audit

SCHEMA = 'rr-v2-stock-competence-v1'
TASK = 'synthetic-stock'
NORMAL = '78419528eb91d65c58517565ad196ff82c7f84f76a1e240c80ce7d4996c6cc79'
STRESS = 'b67a0fa3e511f82a1f3120dedd70a3f6a06e34daca2dd9a4bbf8507d855c6939'
CHANGES = ['src/beyond_consensus/experiments/rr_v2_preflight.py',
           'src/beyond_consensus/models/rr_memory_stress.py',
           'src/beyond_consensus/reporecourse_cli.py']


def evidence_check(evidence):
    if (evidence.get('status') != 'verified_internal_bindings_review_pending'
            or evidence.get('errors') != [] or evidence.get('cross_run_binding_differences') != []
            or evidence.get('changed_source_files') != CHANGES
            or [r['experiment_id'] for r in evidence.get('evidence', [])] != [NORMAL, STRESS]):
        raise BCError('Exact reviewed pool-7 probe pair required')
    runs=[]; roots=[]
    for row in evidence['evidence']:
        files=row['input_files']
        for name, expected in files.items():
            if file_hash(Path(name)) != expected: raise BCError('Historical evidence file changed')
        reports=[Path(p) for p in files if Path(p).name=='preflight.json']
        markers=[Path(p) for p in files if Path(p).name=='snapshot.json']
        if len(reports)!=1 or len(markers)!=1: raise BCError('Ambiguous evidence paths')
        runs.append(reports[0].parent); roots.append(markers[0].parent.parent)
    if roots[0]!=roots[1]: raise BCError('Different snapshot roots')
    fresh=audit(*runs, roots[0])
    comparable=lambda x:{k:v for k,v in x.items() if k!='analysis_cpu_seconds'}
    if comparable(fresh)!=comparable(evidence): raise BCError('Historical audit changed; review new evidence')
    return evidence['evidence'][0]['comparison_binding']


def task_inputs(sources):
    from reporecourse.tasks import load_task, private_task
    card, public=load_task(TASK,sources)
    private=private_task(TASK)
    if card['grounding']!='synthetic_diagnostic':raise BCError('Only synthetic task permitted')
    return card,public,private


def scope(public):
    from reporecourse.v2 import configuration, authored_plan
    c=configuration(pool_size=7,lane='fixed_plan',seed=0,token_cap=100000,cpu_cap=1200)
    return c,authored_plan(public,c,'independent')


def build(root,sources,lock,qualification,evidence):
    from reporecourse.qualification import implementation_hashes
    binding=evidence_check(evidence)
    card,public,private=task_inputs(sources)
    config,plan=scope(public)
    m=dict(schema=SCHEMA,source_revision=source_revision(root),sources_root=str(Path(sources).resolve()),
        model=binding['model'],model_lock_sha256=digest(lock),qualification=qualification,
        preflight_evidence=evidence,task=TASK,task_hash=digest(card),public_hash=digest(public),
        private_hash=digest(private),implementation_hashes=implementation_hashes(),
        config=config,plan=plan,condition='clean',seed=0,shards=1,planned_episodes=1,
        budget_basis='uncalibrated_engineering_cap',planner_evidence='authored_independent',
        confirmatory=False,campaign_allowed=False)
    m['episodes']=[dict(episode_id=digest([SCHEMA,m['source_revision'],m['public_hash'],m['model_lock_sha256']]),shard=0)]
    m['experiment_id']=digest(m)
    verify(m,root,lock)
    return m


def validate(m):
    if m.get('schema')!=SCHEMA or digest({k:v for k,v in m.items() if k!='experiment_id'})!=m.get('experiment_id'):
        raise BCError('Competence manifest integrity mismatch')
    _,public,_=task_inputs(m['sources_root']);c,p=scope(public)
    if (m['task']!=TASK or m['config']!=c or m['plan']!=p or m['condition']!='clean' or m['seed']!=0
            or m['planned_episodes']!=1 or m['shards']!=1 or m['confirmatory'] is not False
            or m['campaign_allowed'] is not False or m['budget_basis']!='uncalibrated_engineering_cap'
            or m['planner_evidence']!='authored_independent'
            or m['episodes'] != [dict(episode_id=digest([SCHEMA,m['source_revision'],m['public_hash'],m['model_lock_sha256']]),shard=0)]):
        raise BCError('Only one fixed pool-7 synthetic-stock independent clean condition is allowed')
    model=ModelConfig(**m['model'])
    if m['model']!=m['preflight_evidence']['evidence'][0]['comparison_binding']['model']:
        raise BCError('Model differs from reviewed preflight')
    return SimpleNamespace(model=model,shards=1,task_kind='rr_v2_competence')


def check_controls(q, public, private):
    """Require the complete frozen stock control matrix, without exposing it."""
    witnesses = Counter(w['organization'] for w in private['witnesses'])
    negatives = Counter((r['id'], control) for r in public['required_outputs']
                        for control in ('missing', 'semantic_mutation', 'wrong_alias', 'wrong_type'))
    if (q.get('schema') != 'rr-cpu-qualification-v1'
            or Counter(w.get('organization') for w in q.get('witnesses', [])) != witnesses
            or any(w.get('success') is not True for w in q.get('witnesses', []))
            or Counter((n.get('obligation'), n.get('control')) for n in q.get('negative_controls', [])) != negatives
            or any(n.get('detected') is not True for n in q.get('negative_controls', []))):
        raise BCError('Complete stock witness and per-obligation negative-control matrix required')


def verify(m,root,lock):
    validate(m)
    from reporecourse.qualification import implementation_hashes,runtime_versions
    from reporecourse.track_f_controls import PINS
    from ..models.competence import require_qualification
    if source_revision(root)!=m['source_revision'] or digest(lock)!=m['model_lock_sha256']:
        raise BCError('Source/model lock changed')
    binding=evidence_check(m['preflight_evidence'])
    if (lock['metadata_hashes']!=binding['model_metadata'] or lock['weight_hashes']!=binding['model_weights']
            or lock['decoder_qualification']['qualification_key']!=binding['qualification_keys']['json']):
        raise BCError('Qualified model does not match reviewed probes')
    require_qualification(lock,lock['decoder_qualification']['packages'],16384,'reporecourse-json-v2-pool-7')
    card,public,private=task_inputs(m['sources_root'])
    if [digest(card),digest(public),digest(private)]!=[m['task_hash'],m['public_hash'],m['private_hash']]:
        raise BCError('Task/evaluator inputs changed')
    q=m['qualification']; versions=runtime_versions()
    check_controls(q, public, private)
    if (q.get('status')!='cpu_qualified_review_pending' or q.get('task')!=TASK
            or q.get('task_hash')!=digest(card) or q.get('model_executed') is not False
            or q.get('source_integrity') is not True or q.get('reset_repeat_identical') is not True
            or not q.get('witnesses') or not all(w['success'] for w in q['witnesses'])
            or not q.get('negative_controls') or not all(n['detected'] for n in q['negative_controls'])
            or q.get('implementation_hashes')!=implementation_hashes()
            or m['implementation_hashes']!=implementation_hashes()
            or q.get('runtime_versions')!=versions or any(versions.get(k)!=v for k,v in PINS.items())):
        raise BCError('Current synthetic-stock CPU reference/negative controls and pinned children required')


def submission(m,root,lock,mode,concurrency,output):
    if mode!='run' or concurrency!=1:raise BCError('Competence diagnostic requires run mode and concurrency one')
    verify(m,root,lock)
    existing=Path(output)/'manifest.json'
    if existing.exists() and read_json(existing)!=m:
        raise BCError('Output directory belongs to different provenance')
    ep=Path(output)/'episodes'/m['episodes'][0]['episode_id']
    if (ep/'started.json').exists() or (ep/'result.json').exists():
        raise BCError('Diagnostic already attempted; preserve evidence and review before retry')


def run(m,output,root,*,model_lock,shard=None,retry_failures=False):
    if shard not in (None,0) or retry_failures:raise BCError('One diagnostic shard only; no automatic retry')
    if model_lock is None:raise BCError('Qualified model lock required')
    lock=read_json(model_lock);verify(m,root,lock)
    from ..models.transformers_backend import require_allocation,TransformersBackend
    require_allocation()
    from reporecourse.common import Rejected
    from reporecourse.engine import Engine,ModelWorker
    from reporecourse.evaluator import evaluate
    from reporecourse.resources import Resources,success_at_budget
    _,public,private=task_inputs(m['sources_root'])
    output=Path(output);ep=output/'episodes'/m['episodes'][0]['episode_id'];ep.mkdir(parents=True,exist_ok=True)
    with directory_lock(ep/'.lock'):
        submission(m,root,lock,'run',1,output)
        atomic_json(output/'manifest.json',m)
        atomic_json(ep/'started.json',dict(manifest_hash=digest(m),status='started'))
        backend=None;engine=None;old={};start=time.monotonic()
        resources=Resources(token_cap=100000,cpu_cap=1200)
        row=dict(status='interrupted',success=None)
        def stop(*_):raise InterruptedError('allocation_termination')
        for sig in (signal.SIGINT,signal.SIGTERM):old[sig]=signal.signal(sig,stop)
        try:
            backend=TransformersBackend(validate(m).model,model_lock)
            expected=m['preflight_evidence']['evidence'][0]['comparison_binding']
            for key in ('hardware','compute_capability','vram_total_bytes','torch_cuda','dependencies'):
                if backend.runtime[key]!=expected[key]:raise BCError('Allocation/runtime differs from reviewed evidence: '+key)
            def save(state):atomic_json(ep/'checkpoint.json',dict(manifest_hash=digest(m),engine=state))
            # Separate exact diagnostic adapter; the generic v2.run_branch gate
            # and its scripted-only result labels are deliberately untouched.
            engine=Engine(public,ModelWorker(backend,16384,2048),policy='delegation_jit',
                plan=deepcopy(m['plan']),track='clean',seed=m['config']['seeds']['execution'],
                resources=resources,max_actions=24,save=save,v2=m['config'])
            started_cpu=time.process_time();event_start=len(resources.events)
            try:row=engine.run()
            finally:
                # Normal Engine completion already charges its orchestration.
                # On an unexpected failure, retain the remaining measured CPU too.
                resources.parent_overhead('competence_runtime_parent',started_cpu,event_start)
            row['evaluation']=evaluate(public,private,row['state'])
            row['success']=success_at_budget(row['status'],row['evaluation'].get('success'),resources)
            if row['evaluation']['status']=='blocked_prerequisite':row.update(status='blocked_prerequisite',success=None)
        except (Exception,KeyboardInterrupt) as exc:
            exhausted=isinstance(exc,Rejected) and str(exc) in ('cpu_cap','token_cap','context_limit')
            status=('resource_exhausted' if exhausted else 'interrupted'
                    if isinstance(exc,(InterruptedError,KeyboardInterrupt)) else 'infrastructure_failed')
            row=dict(status=status,success=False if exhausted else None,error_type=type(exc).__name__)
            if engine is not None:
                try:engine.checkpoint()
                except Exception as checkpoint_error:
                    row['checkpoint_error_type']=type(checkpoint_error).__name__
                row.update(state=engine.env.state(),resource_profile=engine.env.resources.summary(),
                           events=engine.env.events,failures=engine.failures,trajectories=engine.trajectories)
        finally:
            # Cleanup failures must not suppress the recorded outcome or usage.
            # Restore handlers even when cleanup fails.
            try:
                if engine is not None:engine.env.close()
            except (Exception, KeyboardInterrupt) as cleanup_error:
                row['cleanup_error_type']=type(cleanup_error).__name__
            finally:
                for sig,handler in old.items():signal.signal(sig,handler)
        row['resource_profile']=resources.summary()
        if engine is not None:row['trajectories']=engine.trajectories
        row.update(schema='rr-v2-stock-competence-result-v1',experiment_id=m['experiment_id'],
            episode_id=m['episodes'][0]['episode_id'],provenance={'manifest_hash':digest(m)},
            mode='real_model',model_executed=bool(engine and any(e['kind'] in ('model_usage','uncertain_interruption') for e in engine.env.resources.events)),
            planner_evidence='authored_independent',planning_model_executed=False,
            task=TASK,track='clean',N_pool=7,budget_basis=m['budget_basis'],confirmatory=False,
            campaign_allowed=False,runtime=backend.runtime if backend else None,wall_seconds=time.monotonic()-start)
        atomic_json(ep/'result.json',row)
        atomic_json(output/'competence-summary.json', aggregate(m,output))
        return [row]


def aggregate(m, output):
    validate(m)
    path=Path(output)/'episodes'/m['episodes'][0]['episode_id']/'result.json'
    row=read_json(path) if path.exists() else None
    if row and (row.get('provenance',{}).get('manifest_hash')!=digest(m)
                or row.get('episode_id')!=m['episodes'][0]['episode_id']
                or row.get('experiment_id')!=m['experiment_id']):
        raise BCError('Competence result provenance mismatch')
    return dict(schema='rr-v2-stock-competence-summary-v1', experiment_id=m['experiment_id'],
        planned=1, observed=int(row is not None), missing=int(row is None),
        status=row['status'] if row else 'missing', success=row.get('success') if row else None,
        model_executed=row.get('model_executed',False) if row else False,
        mode='real_model', confirmatory=False, campaign_allowed=False,
        resource_profile=row.get('resource_profile') if row else None,
        evaluation=row.get('evaluation') if row else None,
        cleanup_error_type=row.get('cleanup_error_type') if row else None,
        retry_allowed=False,
        interpretation='Single synthetic worker competence diagnostic; authored plan; no planner or recovery comparison')
