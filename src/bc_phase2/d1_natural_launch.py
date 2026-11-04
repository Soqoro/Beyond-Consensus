"""Exact-scope natural screening release. No approval is inferred from preparation."""
from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import signal
import threading
import time

from . import d1_natural_screen as screen, d1_natural_binding as binding, joint_d1_local as local
from .model import digest
from .joint_schema import require
from .planner_qwen import verify_local_inventory
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot, environment_inventory
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.util import atomic_json, directory_lock, read_json, plain


def validate_manifest(manifest):
    inputs=manifest.get('binding_inputs',{})
    require(set(inputs)=={'verification','inventory_report','cluster_config','partition_record'},'complete binding receipts')
    expected=binding.bind(**inputs)
    require(manifest==expected,'scope differs from validated receipts/current implementation')
    return manifest['scope']


def approve(manifest, approval):
    """Consumes a separately supplied explicit receipt, never creates approval."""
    validate_manifest(manifest)
    keys={'schema','decision','scope_digest','reviewer','reviewed_at','statement_transmission_authorized','GPU_spending_authorized'}
    require(type(approval) is dict and set(approval)==keys,'exact approval fields')
    require(approval['schema']=='D1-natural-screen-v1-approval' and approval['decision']=='approved'
            and approval['scope_digest']==manifest['scope_digest']
            and approval['statement_transmission_authorized'] is True
            and approval['GPU_spending_authorized'] is True,'explicit exact approval required')
    require(all(type(approval[k]) is str and approval[k].strip() for k in ('reviewer','reviewed_at')),'reviewer/time required')
    value={'schema':'d1-natural-scoped-release-v1','manifest':deepcopy(manifest),'approval':deepcopy(approval)}
    value['release_digest']=digest(value)
    return value


def validate_release(value):
    require(type(value) is dict and set(value)=={'schema','manifest','approval','release_digest'},'release fields')
    require(value==approve(value['manifest'],value['approval']),'release changed')
    return value['manifest']['scope']


def arguments(config,snapshot,output):
    require(config.partition=='NA100q' and cluster.seconds(config.time)==3600 and config.memory_gb==128,'fixed resources')
    argv=cluster.sbatch_arguments(config,snapshot,output,[0],1,mode='preflight')
    argv[-6:]=[str(snapshot/'experiments/run_d1_natural.sbatch'),str(snapshot),str(output),config.python]
    return argv


def lock_for(scope):
    model=scope['model']
    return {'checkpoint':screen.CHECKPOINT,'revision':screen.REVISION,'local_path':model['local_path'],
            'files':model['current_inventory']['files']}


def submit(root,value,*,dry_run=True):
    require(not os.environ.get('SLURM_JOB_ID'),'no batch self-submission')
    scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster'])
    statements=Path(scope['source_package']['path'])
    local.statement_records(statements,screen.SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
    output=Path(config.output_root)/('natural-'+key)
    registry=cluster.registry_root();state_path=registry/'registry.json'
    def action():
        state=read_json(state_path) if state_path.exists() else {'jobs':[]}
        cluster.guard(state)
        require(key not in state.get('d1_natural_scopes',{}),'already submitted/uncertain; no retry')
        require(not output.exists(),'output exists; preserve evidence')
        cluster.validate_site(config)
        snapshot=Path(config.snapshot_root)/'SNAPSHOT_CREATED_AT_SUBMISSION'
        if dry_run:return {'submitted':False,'dry_run':True,'scope_digest':key,'argv':arguments(config,snapshot,output)}
        manifest={'schema':'d1-natural-slurm-v1','source_revision':source_revision(root),'release':value}
        snapshot=create_snapshot(root,Path(config.snapshot_root),manifest,plain(config),lock_for(scope))
        # Snapshot hashes must equal the reviewed runtime before any submission.
        for name,h in {**scope['implementation'],**scope['binding_implementation']}.items():
            require(local.file_hash(snapshot/name)==h,'committed source differs from approved runtime')
        (output/'logs').mkdir(parents=True,exist_ok=False)
        atomic_json(output/'manifest.json',manifest)
        argv=arguments(config,snapshot,output)
        cluster.command([argv[0],'--test-only',*argv[1:]])
        reservation={'scope_digest':key,'release_digest':value['release_digest'],'snapshot':str(snapshot),
                     'output':str(output),'state':'submission_uncertain'}
        state.setdefault('d1_natural_scopes',{})[key]=reservation
        state['uncertain_submission']=dict(reservation)
        atomic_json(state_path,state)
        response=cluster.command(argv);job=response.split(';',1)[0]
        require(re.fullmatch('[0-9]+',job) is not None,'uncertain submission retained')
        reservation.update(job_id=job,state='submitted_no_retry');state['uncertain_submission']=None
        state['completed_jobs']=(state.get('completed_jobs',[])+state.get('jobs',[]))[-100:]
        state['jobs']=[{'job_id':job,'manifest_hash':digest(manifest),'snapshot':str(snapshot),'output':str(output),
                       'concurrency':1,'physical_gpus_per_job':1,'reserved_physical_gpus':1,'mode':'D1-natural'}]
        atomic_json(state_path,state)
        return {'job_id':job,'snapshot':str(snapshot),'output':str(output),'scope_digest':key,'submitted':True}
    if dry_run:return action()
    with directory_lock(registry/'.submission.lock'):return action()


class CheckedTransport(screen.NaturalTransport):
    def render(self,request):
        result=super().render(request)
        row=next(r for r in self.scope['verified_requests'] if r['source_id']==request['payload']['source']['id'])
        require(all(result[k]==row[k] for k in ('payload_digest','rendered_ids_digest','input_tokens')), 'rendered request changed')
        return result


class Session(screen.NaturalMockSession):
    """Reuse the exact tested one-shot advance and atomic durable ledger."""
    def __init__(self,directory,scope,records,transport,started_at):
        require(type(transport) is CheckedTransport and transport.scope==scope,'bound transport required')
        require([r['id'] for r in records]==scope['source_ids'],'frozen source order')
        require(all(set(r)=={'id','problem'} for r in records),'source views')
        import hashlib
        require(all(hashlib.sha256(r['problem'].encode()).hexdigest()==local.STATEMENT_HASHES[r['id']] for r in records),'source hashes')
        self.transport=transport
        self.binding={'version':screen.VERSION,'requests':[screen.request(r) for r in records],
                      'transport':deepcopy(transport.binding),'scope_digest':digest(scope),
                      'implementation':screen.implementation(),'model_executed':True}
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=False)
        with self._locked():
            self._save({'binding':self.binding,'binding_digest':digest(self.binding),'attempts':[],
                        'started_at':started_at,'model_executed':True,'execution_allowed':True})

    @staticmethod
    def _totals(state):
        attempts=state['attempts']
        return {'actual_tokens':sum(a['actual_tokens'] or 0 for a in attempts),
                'reserved_tokens':sum(a['reservation_tokens'] for a in attempts if a['actual_tokens'] is None),
                'attempts':len(attempts), 'model_calls_observed':sum('observation' in a for a in attempts),
                'evidence':'local_runtime_unqualified'}

    def advance(self,source_id):
        # Detect source changes before each call; never dispatch on integrity failure.
        scope=self.transport.scope
        local.statement_records(Path(scope['source_package']['path']),screen.SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
        return super().advance(source_id)


def drive(session,source_ids):
    rows=[];halted=False
    for source in source_ids:
        if halted:
            rows.append({'source_id':source,'status':'unrun'});continue
        try:
            attempt=session.advance(source)
            rows.append({'source_id':source,'status':attempt['state'],'review':attempt.get('review'),
                         'actual_tokens':attempt.get('actual_tokens')})
            halted=not screen.reliable_terminal(attempt)
        except Exception as exc:
            rows.append({'source_id':source,'status':'stopped','error_type':type(exc).__name__})
            halted=True
    return {'sources':rows,'halted':halted,'ledger':session.snapshot(),'D2_D6_enabled':False}


def open_transport(value):
    scope=validate_release(value) # before optional imports or model reads
    from beyond_consensus.models.transformers_backend import require_allocation
    require_allocation()
    root=verify_local_inventory(lock_for(scope))
    import torch
    from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration
    require(torch.cuda.device_count()==1,'one visible GPU only')
    require(torch.cuda.get_device_properties(0).total_memory>=80_000_000_000,'80GB-class GPU before loading')
    # Same RepoRecourse/Qwen loader and single-device placement; no new backend/offload.
    tokenizer=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==scope['model']['non_thinking_verification'],'template binding')
    model=Qwen3_5ForConditionalGeneration.from_pretrained(str(root),local_files_only=True,trust_remote_code=False,
            use_safetensors=True,dtype=torch.bfloat16,attn_implementation='sdpa')
    model.to(torch.device('cuda:0'));model.requires_grad_(False);model.eval()
    transport=CheckedTransport(tokenizer,model,torch)
    require(transport.tokens==scope['model']['generation_tokens'],'stop tokens changed')
    transport.scope=scope
    transport.binding.update(evidence='local_runtime_unqualified',inventory_digest=digest(lock_for(scope)))
    return transport


def dispatch(value,directory):
    scope=validate_release(value)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    start=time.time();cpu=time.process_time();wall=time.monotonic()
    atomic_json(directory/'startup.json',{'scope_digest':digest(scope),'state':'started_no_retry','started_at':start})
    watchdog=threading.Timer(3600,lambda:os.kill(os.getpid(),signal.SIGKILL));watchdog.daemon=True;watchdog.start()
    session=None
    try:
        records=local.statement_records(Path(scope['source_package']['path']),screen.SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
        transport=open_transport(value)
        session=Session(directory/'requests',scope,records,transport,start)
        result=drive(session,scope['source_ids']);result['model_executed']=bool(result['ledger']['attempts'])
        result['stage_resources']={'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,
                                  'includes_inventory_loading_and_validation':True}
        atomic_json(directory/'result.json',result)
        return result
    except BaseException as exc:
        atomic_json(directory/'failure.json',{'error_type':type(exc).__name__,'dispatch_uncertain':session is not None,
                    'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,'retry_allowed':False})
        raise
    finally:watchdog.cancel()


def check_allocation_record(record):
    fields=dict(re.findall(r'(\w+)=([^\s]+)',record))
    require(fields.get('Partition')=='NA100q' and fields.get('NumNodes')=='1'
            and fields.get('NumCPUs')=='4' and fields.get('TimeLimit')=='01:00:00', 'allocated scheduler resources changed')
    tres=dict(item.split('=',1) for item in fields.get('ReqTRES','').split(',') if '=' in item)
    require(tres.get('cpu')=='4' and tres.get('gres/gpu')=='1'
            and tres.get('mem') in ('128G','131072M'), 'requested allocation outside approved resources')


def run_allocated(root,output):
    require(os.environ.get('SLURM_JOB_ID'),'allocation required')
    root=Path(root);output=Path(output);marker=verify_snapshot(root)
    manifest=read_json(root/'resolved/manifest.json')
    require(manifest.get('schema')=='d1-natural-slurm-v1','natural snapshot required')
    value=manifest['release'];scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster'])
    require(read_json(root/'resolved/cluster.json')==plain(config),'cluster binding')
    require(output.resolve()==(Path(config.output_root)/('natural-'+key)).resolve(),'output binding')
    require(read_json(output/'manifest.json')==manifest and marker['manifest_hash']==digest(manifest),'snapshot/output binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','single array element')
    with directory_lock(cluster.registry_root()/'.submission.lock'):
        state=read_json(cluster.registry_root()/'registry.json')
    record=state.get('d1_natural_scopes',{}).get(key,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry'
            and record.get('release_digest')==value['release_digest']
            and Path(record.get('snapshot','')).resolve()==root.resolve()
            and Path(record.get('output','')).resolve()==output.resolve(),'registered exact job')
    check_allocation_record(cluster.command(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o']))
    active=cluster.active_gpu_jobs()
    require(active and all(j.split('_')[0]==job and count==1 for j,count in active.items()),'exclusive one-GPU campaign')
    require(environment_inventory(config.python)==read_json(root/'resolved/environment.json'),'environment changed')
    return dispatch(value,output/'execution')
