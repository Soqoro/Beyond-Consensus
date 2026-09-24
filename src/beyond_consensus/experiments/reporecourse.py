"""BC model/journal/scheduler adapters; benchmark core never imports this module."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import json
import signal
import time

from ..util import BCError,read_json,atomic_json,digest,directory_lock
from ..config import ModelConfig
from .manifest import source_revision
from ..runtime.persistence import EpisodeJournal
from reporecourse.common import Rejected
from reporecourse.tasks import load_task,private_task
from reporecourse.experiments import validate,require_run
from reporecourse.engine import Engine,ModelWorker
from reporecourse.resources import Resources
from reporecourse.evaluator import evaluate


def select_plan(plans, public, calibration, mode, compatibility, resources, *, reserve=0):
    """Optional BC finite selector plugin, same neutral JIT and eligibility.

    Reuses the existing finite selector's objective and tie break. The legacy
    route-allocation solver and surrogate calibrations are NOT ported as costs.
    No compatible RepoRecourse empirical calibration has yet been produced.
    """
    from ..planning.decomposition import rank_costed
    from reporecourse.policies import select_calibrated
    resources.reserve_cpu(1);start=time.process_time()
    try:
        return select_calibrated(plans,public,calibration,mode,compatibility,
            cap=resources.remaining,reserve=reserve,ranker=rank_costed)
    finally:resources.reconcile_cpu('finite_selection',1,time.process_time()-start)


def config_namespace(m):
    try:validate(m)
    except Rejected as e:raise BCError(str(e)) from e
    return SimpleNamespace(model=ModelConfig(**m['model']),shards=m['shards'],task_kind='reporecourse')


def verify_inputs(m,root):
    if source_revision(root)!=m['source_revision']:raise BCError('RepoRecourse source changed; rebuild manifest')
    from reporecourse.qualification import implementation_hashes
    if m.get('qualification',{}).get('implementation_hashes')!=implementation_hashes():
        raise BCError('RepoRecourse CPU qualification implementation changed')
    for card in m['tasks']:
        actual,p=load_task(card['id'],m['sources_root'])
        if actual!=card or digest(p)!=m['public_hashes'][card['id']]:raise BCError('RepoRecourse task/source changed')


def run(m,output,root,*,shard=None,backend=None,model_lock=None,retry_failures=False):
    require_run(m);verify_inputs(m,root)
    if model_lock is not None and digest(read_json(model_lock))!=m['model_lock_sha256']:
        raise BCError('Model lock changed')
    if shard is not None and shard!=0:raise BCError('RepoRecourse shard out of range')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    with directory_lock(output/'.manifest.lock'):
        if (output/'manifest.json').exists() and read_json(output/'manifest.json')!=m:raise BCError('Output provenance mismatch')
        atomic_json(output/'manifest.json',m)
    if backend is None:
        preflight=read_json(Path(str(output)+'-preflight')/'preflight.json')
        if preflight.get('experiment_id')!=m['experiment_id'] or preflight.get('command_failed') is not False:
            raise BCError('Matching actual-allocation preflight required')
        from ..models.transformers_backend import TransformersBackend
        backend=TransformersBackend(config_namespace(m).model,model_lock)
    rows=[];old={}
    def stop(*_):raise InterruptedError('allocation_termination')
    for s in (signal.SIGINT,signal.SIGTERM):old[s]=signal.signal(s,stop)
    try:
        for e in m['episodes']:
            journal=EpisodeJournal(output,e['episode_id'])
            with directory_lock(journal.path/'.lock'):
                result_path=journal.path/'result.json'
                if result_path.exists():
                    row=read_json(result_path)
                    if row.get('provenance')!={'manifest_hash':digest(e)}:raise BCError('Result provenance mismatch')
                    if row['status'] not in ('interrupted','infrastructure_failed') or not retry_failures:rows.append(row);continue
                _,p=load_task(e['task_id'],m['sources_root'])
                private=private_task(e['task_id'])
                resources=Resources(m['resource']['token_cap'],m['resource']['cpu_cap'])
                attempt=journal.begin(digest(e))
                def save(state):journal.checkpoint({'manifest_hash':digest(e),'engine':state})
                engine=Engine(p,ModelWorker(backend,m['model']['context_limit'],m['model']['max_new_tokens']),
                    policy=e['policy'],plan=e['plan'],track=e['track'],target=e['target'],seed=e['seed'],resources=resources,save=save)
                previous=journal.previous(digest(e))
                if previous:engine.restore(previous['engine'])
                try:
                    row=engine.run();row['evaluation']=evaluate(p,private,row['state'])
                    row['success']=row['evaluation']['success'] is True and engine.env.resources.actual_tokens+engine.env.resources.uncertain_tokens<=engine.env.resources.token_cap and engine.env.resources.cpu_seconds<=engine.env.resources.cpu_cap
                    if row['evaluation']['status']=='blocked_prerequisite':
                        row['status']='blocked_prerequisite';row['success']=None
                    row['detected_but_unfinished']=bool(row['public_alarm']) and not row['success']
                    row['false_alarm']=e['track']=='clean' and bool(row['public_alarm'])
                except (InterruptedError,Exception) as exc:
                    # Candidate safety/semantic errors are handled in the neutral
                    # loop. Unexpected harness interruption is separately retryable.
                    row=dict(status='interrupted' if isinstance(exc,InterruptedError) else 'infrastructure_failed',
                        success=None,resource_profile=engine.env.resources.summary(),track=e['track'],
                        model_executed=True,error=type(exc).__name__)
                    engine.checkpoint()
                finally:engine.env.close()
                row.update(experiment_id=m['experiment_id'],episode_id=e['episode_id'],attempt_id=attempt,provenance={'manifest_hash':digest(e)})
                atomic_json(result_path,row);journal.event('attempt_finished',attempt_id=attempt,status=row['status'])
                rows.append(row)
                if row['status'] in ('interrupted','infrastructure_failed'):break
    finally:
        for s,h in old.items():signal.signal(s,h)
    return rows


def preflight(m,lock,root):
    require_run(m);verify_inputs(m,root)
    if digest(read_json(lock))!=m['model_lock_sha256']:raise BCError('Model lock changed')
    from ..models.transformers_backend import TransformersBackend
    backend=TransformersBackend(config_namespace(m).model,lock)
    from reporecourse.tasks import tool_contract
    prompts=[{'role':'system','content':'One JSON action, no Markdown. '+json.dumps(tool_contract())},
        {'role':'user','content':'Synthetic probe only. Publish SQL SELECT 1 AS id with name demo, format sql, bindings {}, obligations [].'}]
    first=backend.generate(prompts,2048,0)
    # Long input tests the actual allocation; early EOS is not worst-case proof.
    long=[{'role':'system','content':'One JSON action: {"tool":"list_sources"}.'},{'role':'user','content':''}]
    lo,hi=0,16384
    while lo<hi:
        mid=(lo+hi+1)//2;long[-1]['content']='synthetic datum '*mid+' Reply with list_sources.'
        if backend.count_input(long)<=m['model']['context_limit']-2048:lo=mid
        else:hi=mid-1
    long[-1]['content']='synthetic datum '*lo+' Reply with list_sources.'
    second=backend.generate(long,2048,0)
    _,p=load_task('synthetic-stock',m['sources_root'])
    from reporecourse.runtime import Environment
    env=Environment(p)
    try:
        action=json.loads(first.text);v=env.action('w0',action)['version'];sql=env.execute(v)
        ok=sql['status']=='ok' and sql['outputs'][0]['rows']==[[1]] and json.loads(second.text)=={'tool':'list_sources'}
    except Exception:ok=False;sql={'status':'failed_probe'}
    finally:env.close()
    from reporecourse.schema_runtime import execute
    api=execute({'operation':'qualify'})
    return {'schema':'rr-preflight-v1','experiment_id':m['experiment_id'],'command_failed':not(ok and api['status']=='ok'),
        'model_executed':True,'runtime':backend.runtime,'sql_probe':sql,'schema_probe':api,
        'generation':asdict(first),'long_context_generation':asdict(second),
        'long_context_input_tokens':backend.count_input(long),'worst_case_fit_established':False,
        'hardware':backend.torch.cuda.get_device_name(0)}
