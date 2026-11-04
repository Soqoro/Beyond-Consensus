"""Scoped deployment wrapper for the one composite recipe; no implicit approval."""
import importlib.metadata
import os
from pathlib import Path
import re
import sys
import threading
import signal
import time
from copy import deepcopy
from . import composite_math as recipe, math500_screen_launch as previous, d1_natural_launch as pilot
from . import d1_natural_screen as screen
from .model import digest
from .joint_schema import require
from .planner_qwen import verify_local_inventory
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.snapshot import create_snapshot,verify_snapshot,environment_inventory
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.util import read_json,atomic_json,directory_lock,plain

KEY=recipe.CONDITION
EXPECTED_PACKAGES={'torch':'2.10.0+cu126','transformers':'5.3.0','tokenizers':'0.22.2','safetensors':'0.7.0','ortools':'9.14.6206'}

def identity():
    root=Path(__file__).resolve().parents[2]
    files=set(previous.identity())|{str(p.relative_to(root)) for p in (root/'src/bc_phase2').glob('joint_*.py')}|{
        'src/bc_phase2/composite_math.py','src/bc_phase2/composite_math_launch.py','scripts/composite_math_pilot.py','experiments/run_composite_math.sbatch'}
    return {p:previous.local.file_hash(root/p) for p in sorted(files)}

def deployment():
    packages={}
    for name in ('torch','transformers','tokenizers','safetensors','ortools'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    try:
        from ortools.sat.python import cp_model
        ready=hasattr(cp_model,'CpSolver')
    except ImportError:ready=False
    return dict(python=str(Path(sys.executable).resolve()),packages=packages,solver_importable=ready,
                gpu_execution_verified=False,model_executed=False)

def prepare(screen_release,source_path,config_data,screen_result_path):
    # Completed screening configuration supplies provenance, never worker approval.
    old=previous.validate_release(screen_release)
    require(previous.local.file_hash(screen_result_path)=='ee6d947dee83acad37809ad458f03f0169f7d6ceface4d54386f25d56c9f00af','completed screening result hash')
    require(screen_release['manifest']['scope_digest']=='52d5fa47e44090fc5a958bb3e37d4653ddedbe4e336dd717c304410d699b4279','completed screening binding')
    require(Path(source_path).resolve()==Path(old['source_package']['path']).resolve()
            and previous.local.file_hash(source_path)==old['source_package']['statements_file_sha256'],'authorised statement-only package')
    recipe.statements(source_path)
    config=cluster.ClusterConfig(**config_data)
    require(config.partition=='NA100q' and config.time=='04:00:00' and config.memory_gb==128 and config.activation_script is None,'proposed allocation')
    dep=deployment();require(str(Path(config.python).resolve())==dep['python'],'inspect execution Python itself')
    scope=dict(screen_result_sha256=previous.local.file_hash(screen_result_path),condition=KEY,blueprint=recipe.blueprint(),model=deepcopy(old['model']),cluster=config_data,
        source_package=dict(path=str(Path(source_path).resolve()),sha256=previous.local.file_hash(source_path)),
        runtime_identity=identity(),deployment=dep,limits=recipe.LIMITS,
        grade='blinded human review; all validity unknown until reviewed; no model judge',
        continuation='same approved process profile -> frozen prices -> selection -> fresh evaluations',
        monetary_cost='unverified local allocation; no cloud service',D2_D6_campaign_enabled=False)
    blockers=[] if dep['solver_importable'] else ['execution_python_ortools_unavailable']
    blockers += ['execution_package_mismatch:'+k for k,v in EXPECTED_PACKAGES.items() if dep['packages'].get(k)!=v]
    return dict(schema='composite-r0-manifest-v1',scope=scope,scope_digest=digest(scope),blockers=blockers,execution_allowed=False)

def validate_manifest(m):
    require(m['schema']=='composite-r0-manifest-v1' and m['scope_digest']==digest(m['scope']),'manifest digest')
    s=m['scope'];require(s['condition']==KEY and s['blueprint']==recipe.blueprint() and s['limits']==recipe.LIMITS,'frozen recipe')
    require(s['runtime_identity']==identity(),'source changed')
    require(s['model']['checkpoint']==screen.CHECKPOINT and s['model']['revision']==screen.REVISION
            and s['model']['thinking'] is False and s['model']['do_sample'] is False,'model settings')
    require(s['model']['dtype']=='bfloat16' and s['model']['attention']=='sdpa','precision/backend')
    c=cluster.ClusterConfig(**s['cluster'])
    require(c.time=='04:00:00' and c.partition=='NA100q' and c.memory_gb==128 and c.activation_script is None,'resources')
    return s

def approve(m,a):
    validate_manifest(m);require(not m['blockers'],'deployment blocker')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'external nonrecursive approval')
    require(a['schema']=='composite-r0-approval-v1' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact worker recipe approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'all actual decisions required')
    require(all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema='composite-r0-release-v1',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity')
    return validate_manifest(v['manifest'])

def source_records(s):
    p=s['source_package'];require(previous.local.file_hash(p['path'])==p['sha256'],'statement file changed')
    return recipe.statements(p['path'])

def arguments(c,snapshot,output):
    argv=cluster.sbatch_arguments(c,snapshot,output,[0],1,mode='preflight')
    argv[-6:]=[str(snapshot/'experiments/run_composite_math.sbatch'),str(snapshot),str(output),c.python]
    return argv

def open_transport(v):
    s=validate_release(v)
    require(deployment()==s['deployment'] and s['deployment']['solver_importable'],'execution host deployment mismatch')
    require(s['deployment']['packages']==EXPECTED_PACKAGES,'qualified package versions')
    from beyond_consensus.models.transformers_backend import require_allocation
    require_allocation();root=verify_local_inventory(pilot.lock_for(s))
    import torch
    from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration
    require(torch.cuda.device_count()==1 and torch.cuda.get_device_properties(0).total_memory>=80000000000,'one >=80GB GPU')
    tokenizer=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==s['model']['non_thinking_verification'],'template verification')
    model=Qwen3_5ForConditionalGeneration.from_pretrained(str(root),local_files_only=True,trust_remote_code=False,
        use_safetensors=True,dtype=torch.bfloat16,attn_implementation='sdpa')
    model.to(torch.device('cuda:0'));model.requires_grad_(False);model.eval()
    transport=screen.NaturalTransport(tokenizer,model,torch)
    require(transport.tokens==s['model']['generation_tokens'],'EOS/pad binding')
    transport.binding.update(evidence='real_composite_worker_development',inventory_digest=digest(pilot.lock_for(s)))
    return transport

def dispatch(v,directory):
    s=validate_release(v);out=Path(directory);out.mkdir(exist_ok=False)
    wall=time.monotonic();cpu=time.process_time()
    atomic_json(out/'startup.json',dict(scope_digest=digest(s),state='started_no_retry'))
    timer=threading.Timer(14400,lambda:os.kill(os.getpid(),signal.SIGKILL));timer.daemon=True;timer.start()
    journal=None
    try:
        sources=source_records(s);transport=open_transport(v)
        journal=recipe.Journal(out/'journal',transport,digest(s),lambda:source_records(s))
        result=recipe.run_recipe(journal,sources,out)
        result['stage_resources']=dict(wall_seconds=time.monotonic()-wall,cpu_seconds=time.process_time()-cpu)
        atomic_json(out/'result.json',result)
        return result
    except BaseException as e:
        state=read_json(out/'recipe-state.json') if (out/'recipe-state.json').exists() else {'slots':{k:'unrun' for k in recipe.blueprint()['schedule']}}
        attempts=journal.snapshot()['attempts'] if journal else []
        for slot in state['slots']:
            saved=out/(slot.replace('/','_')+'.json')
            state['slots'][slot]=read_json(saved)['status'] if saved.exists() else 'interrupted' if any(a['slot']==slot for a in attempts) else 'unrun'
        state['status']='halted';atomic_json(out/'recipe-state.json',state)
        atomic_json(out/'failure.json',dict(error_type=type(e).__name__,error=str(e),retry_allowed=False,
            totals=journal.snapshot()['totals'] if journal else None,unstarted_slots='derive from frozen schedule and saved slots',
            wall_seconds=time.monotonic()-wall,cpu_seconds=time.process_time()-cpu))
        raise
    finally:timer.cancel()


def submit(root,value,*,dry_run=True):
    require(not os.environ.get('SLURM_JOB_ID'),'no batch self-submission')
    scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster']);source_records(scope)
    output=Path(config.output_root)/('composite-'+key)
    registry=cluster.registry_root();state_path=registry/'registry.json'
    def action():
        state=read_json(state_path) if state_path.exists() else {'jobs':[]}
        cluster.guard(state)
        # A second bind/output directory must not allow repeating this cohort's attempt.
        require(KEY not in state.get('composite_math_attempts',{}),'cohort already submitted/uncertain; no retry')
        require(not output.exists(),'preserve existing output')
        cluster.validate_site(config)
        snapshot=Path(config.snapshot_root)/'SNAPSHOT_CREATED_AT_SUBMISSION'
        if dry_run:return {'submitted':False,'dry_run':True,'scope_digest':key,'argv':arguments(config,snapshot,output)}
        manifest={'schema':'composite-r0-slurm-v1','source_revision':source_revision(root),'release':value}
        snapshot=create_snapshot(root,Path(config.snapshot_root),manifest,plain(config),pilot.lock_for(scope))
        for name,h in scope['runtime_identity'].items():require(previous.local.file_hash(snapshot/name)==h,'committed source binding')
        (output/'logs').mkdir(parents=True,exist_ok=False);atomic_json(output/'manifest.json',manifest)
        argv=arguments(config,snapshot,output);cluster.command([argv[0],'--test-only',*argv[1:]])
        reservation={'scope_digest':key,'release_digest':value['release_digest'],'snapshot':str(snapshot),
                     'output':str(output),'state':'submission_uncertain'}
        state.setdefault('composite_math_attempts',{})[KEY]=reservation
        state['uncertain_submission']=dict(reservation);atomic_json(state_path,state)
        response=cluster.command(argv);job=response.split(';',1)[0]
        require(re.fullmatch('[0-9]+',job) is not None,'uncertain submission retained')
        reservation.update(job_id=job,state='submitted_no_retry');state['uncertain_submission']=None
        state['completed_jobs']=(state.get('completed_jobs',[])+state.get('jobs',[]))[-100:]
        state['jobs']=[{'job_id':job,'manifest_hash':digest(manifest),'snapshot':str(snapshot),'output':str(output),
                       'concurrency':1,'physical_gpus_per_job':1,'reserved_physical_gpus':1,'mode':'composite-r0'}]
        atomic_json(state_path,state)
        return {'job_id':job,'snapshot':str(snapshot),'output':str(output),'scope_digest':key,'submitted':True}
    if dry_run:return action()
    with directory_lock(registry/'.submission.lock'):return action()


def check_allocation(record):
    fields=dict(re.findall(r'(\w+)=([^\s]+)',record))
    require(fields.get('TimeLimit')=='04:00:00','allocated wall limit')
    pilot.check_allocation_record(record.replace('TimeLimit=04:00:00','TimeLimit=01:00:00'))

def run_allocated(root,output):
    require(os.environ.get('SLURM_JOB_ID'),'allocation required')
    root=Path(root);output=Path(output);marker=verify_snapshot(root)
    manifest=read_json(root/'resolved/manifest.json')
    require(manifest.get('schema')=='composite-r0-slurm-v1','expanded snapshot required')
    value=manifest['release'];scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster'])
    require(read_json(root/'resolved/cluster.json')==plain(config),'cluster binding')
    require(output.resolve()==(Path(config.output_root)/('composite-'+key)).resolve(),'output binding')
    require(read_json(output/'manifest.json')==manifest and marker['manifest_hash']==digest(manifest),'snapshot manifest binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','single array task')
    with directory_lock(cluster.registry_root()/'.submission.lock'):
        state=read_json(cluster.registry_root()/'registry.json')
    record=state.get('composite_math_attempts',{}).get(KEY,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry'
            and record.get('release_digest')==value['release_digest'] and record.get('scope_digest')==key
            and Path(record.get('snapshot','')).resolve()==root.resolve()
            and Path(record.get('output','')).resolve()==output.resolve(),'registered expanded job')
    check_allocation(cluster.command(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o']))
    active=cluster.active_gpu_jobs()
    require(active and all(j.split('_')[0]==job and count==1 for j,count in active.items()),'exclusive one-GPU campaign')
    require(environment_inventory(config.python)==read_json(root/'resolved/environment.json'),'environment changed')
    return dispatch(value,output/'execution')
