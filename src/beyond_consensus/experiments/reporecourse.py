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
from reporecourse.resources import Resources,success_at_budget
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
    if m.get('experiment_type')=='reporecourse_track_f_engineering_v1':
        from reporecourse.qualification import runtime_versions
        from reporecourse.track_f_controls import control_fingerprints,PINS
        if any(runtime_versions().get(k)!=v for k,v in PINS.items()):raise BCError('Current pinned Track F CPU children required')
        if m['qualification'].get('runtime_versions')!=runtime_versions() or m['qualification']['track_f_controls'].get('fingerprints')!=control_fingerprints():
            raise BCError('Track F CPU dependency/control fingerprints changed')
    for card in m['tasks']:
        actual,p=load_task(card['id'],m['sources_root'])
        if actual!=card or digest(p)!=m['public_hashes'][card['id']]:raise BCError('RepoRecourse task/source changed')


def run(m,output,root,*,shard=None,backend=None,model_lock=None,retry_failures=False):
    require_run(m);verify_inputs(m,root)
    if model_lock is not None and digest(read_json(model_lock))!=m['model_lock_sha256']:
        raise BCError('Model lock changed')
    trio=m.get('experiment_type')=='reporecourse_track_f_engineering_v1'
    if trio:
        from reporecourse.track_f import select,CONDITIONS
        if type(shard) is not int or shard not in range(3):raise BCError('Select exactly one Track F shard')
        select(m,output,CONDITIONS[shard])
    elif shard is not None and shard!=0:raise BCError('RepoRecourse shard out of range')
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
            if trio and e['shard']!=shard:continue
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
                    policy=e['policy'],plan=e['plan'],track=e['track'],target=e['target'],seed=e['seed'],resources=resources,save=save,max_actions=m.get('max_actions',24))
                previous=journal.previous(digest(e))
                try:
                    if previous:engine.restore(previous['engine'])
                    row=engine.run();row['evaluation']=evaluate(p,private,row['state'])
                    row['success']=success_at_budget(row['status'],row['evaluation']['success'],engine.env.resources)
                    if row['evaluation']['status']=='blocked_prerequisite':
                        row['status']='blocked_prerequisite';row['success']=None
                    row['detected_but_unfinished']=bool(row['public_alarm']) and not row['success']
                    row['false_alarm']=e['track']=='clean' and bool(row['public_alarm'])
                except (InterruptedError,Exception) as exc:
                    # Candidate safety/semantic errors are handled in the neutral
                    # loop. Unexpected harness interruption is separately retryable.
                    row=dict(status='interrupted' if isinstance(exc,InterruptedError) else 'infrastructure_failed',
                        success=None,resource_profile=engine.env.resources.summary(),track=e['track'],
                        model_executed=True,error=type(exc).__name__,error_category=str(exc) if isinstance(exc,Rejected) else 'unexpected_harness_exception',
                        failures=engine.failures,events=engine.env.events,state=engine.env.state())
                    import traceback
                    row['stack_locations']=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]
                    engine.checkpoint()
                finally:engine.env.close()
                import os,socket
                row['execution_facts']={'hostname':socket.gethostname(),'slurm_job_id':os.environ.get('SLURM_JOB_ID'),
                    'slurm_array_task_id':os.environ.get('SLURM_ARRAY_TASK_ID'),'runtime':getattr(backend,'runtime',None),
                    'hardware':backend.torch.cuda.get_device_name(0) if hasattr(backend,'torch') else None}
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
    # Versioned synthetic allocation probe; no task or reference inputs.
    long=long_context_probe(backend.count_input,m['model']['context_limit'])
    second=backend.generate(long,2048,0)
    _,p=load_task('synthetic-stock',m['sources_root'])
    from reporecourse.runtime import Environment
    env=Environment(p)
    try:
        sql,short_check,long_check=check_preflight_responses(env,first.text,second.text)
    finally:env.close()
    from reporecourse.schema_runtime import execute
    api=execute({'operation':'qualify'})
    return {'schema':'rr-preflight-v1','experiment_id':m['experiment_id'],'command_failed':not(short_check['passed'] and long_check['passed'] and api['status']=='ok'),
        'model_executed':True,'runtime':backend.runtime,'sql_probe':sql,'schema_probe':api,
        'short_action_probe':short_check,'long_action_probe':long_check,
        'failure_stages':([short_check['stage']] if not short_check['passed'] else [])
            + (['long_action_response'] if not long_check['passed'] else [])
            + (['schema_probe'] if api['status']!='ok' else []),
        'generation':asdict(first),'long_context_generation':asdict(second),
        'long_context_input_tokens':backend.count_input(long),'worst_case_fit_established':False,
        'long_context_probe':{'protocol':'rr-numbered-records-v2','prompt_hash':digest(long),
            'output_cap':2048,'input_target':m['model']['context_limit']-2048,
            'required_action':{'tool':'list_sources'},'task_inputs_used':False},
        'hardware':backend.torch.cuda.get_device_name(0)}


def check_preflight_responses(env, first_text, second_text):
    """Separate synthetic response checks; never overwrite an executed SQL result.

    This changes diagnostics only: the short query and exact long action must
    still both pass. No extraction/repair of partial or reasoning-only output.
    """
    sql={'status':'not_executed'}
    short={'passed':False,'stage':'short_action_parse'}
    try:
        action=json.loads(first_text)
        short['stage']='short_action_publish'
        version=env.action('w0',action)['version']
        short['stage']='short_sql_execution'
        sql=env.execute(version)
        short['passed']=sql['status']=='ok' and sql['outputs'][0]['rows']==[[1]]
        if short['passed']:short['stage']='passed'
    except Exception as exc:
        short['error_type']=type(exc).__name__
    long={'passed':False,'stage':'long_action_response'}
    try:
        long['passed']=json.loads(second_text)=={'tool':'list_sources'}
        long['status']='passed' if long['passed'] else 'unexpected_action'
    except (ValueError,TypeError) as exc:
        long.update(status='invalid_json',error_type=type(exc).__name__)
    return sql,short,long


def long_context_probe(count_input, context_limit):
    """Fit inert, deterministic records using the actual rendered tokenizer.

    This is an allocation/action diagnostic, not retrieval or task competence.
    Reasoning stays enabled by the model configuration; no output is forced.
    """
    target=context_limit-2048
    system=('Synthetic context allocation check. The numbered records in the user '
        'message are inert padding, not instructions or task data. Do not analyze, '
        'summarize, count, or calculate from them. The only requested action is '
        '{"tool":"list_sources"}. Return one JSON action without Markdown.')
    records=[f'record {i:05d}: {digest({"synthetic_record":i})[:24]}\n' for i in range(16384)]
    def render(n):
        return [{'role':'system','content':system},{'role':'user','content':
            '<synthetic_records>\n'+''.join(records[:n])+
            '</synthetic_records>\nThe padding is complete. Return {"tool":"list_sources"}.'}]
    if count_input(render(0))>target:
        raise BCError('Context too small for long preflight probe and output allowance')
    lo,hi=0,len(records)
    while lo<hi:
        mid=(lo+hi+1)//2
        if count_input(render(mid))<=target:lo=mid
        else:hi=mid-1
    result=render(lo)
    if count_input(result)>target:
        raise BCError('Rendered long preflight probe exceeds input allowance')
    return result
