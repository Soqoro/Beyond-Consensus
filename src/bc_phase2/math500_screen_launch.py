"""Exact opt-in 20-source screening; historical pilot adapter remains unchanged."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import signal
import threading
import time

from . import d1_natural_screen as screen, d1_natural_launch as pilot, joint_d1_local as local
from .model import digest
from .joint_schema import require
from .planner_first import ORIGINAL_IDS, DIAGRAM_IDS
from .planner_qwen import verify_local_inventory
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot, environment_inventory
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.util import atomic_json, directory_lock, read_json, plain

PARENT='b4234287cdf6e2de07b748a66f5749c2f7a534a6bb1f62cf433e4115090adbcf'
COHORT='069667602f25dbb547e4bb09651831c62763826cf0f25bb3b2689948a2dafe15'
ADDITIONS=('test/counting_and_probability/190.json','test/algebra/634.json',
 'test/intermediate_algebra/1166.json','test/number_theory/533.json','test/prealgebra/105.json',
 'test/geometry/965.json','test/precalculus/190.json','test/algebra/524.json',
 'test/intermediate_algebra/1300.json','test/precalculus/1303.json',
 'test/counting_and_probability/1003.json','test/number_theory/572.json')
BLOCKED=sorted(set(DIAGRAM_IDS)|{'test/precalculus/1303.json'})
SOURCES=tuple(s for s in (*ORIGINAL_IDS,*ADDITIONS) if s not in screen.SMOKE and s not in BLOCKED)
CAP=85690
APPROVAL_SCHEMA='D1-math500-screen-v1-approval'


def identity():
    root=Path(__file__).resolve().parents[2]
    names=['src/bc_phase2/math500_screen_launch.py','scripts/launch_math500_screen.py',
           'experiments/run_math500_screen.sbatch','src/bc_phase2/d1_natural_launch.py',
           'src/bc_phase2/joint_d1_local.py','src/bc_phase2/planner_first.py',
           'src/bc_phase2/joint_d1_readiness.py','src/beyond_consensus/experiments/cluster.py',
           'src/beyond_consensus/experiments/snapshot.py','src/beyond_consensus/experiments/manifest.py',
           'src/beyond_consensus/util.py']
    return {**screen.implementation(),**{p:local.file_hash(root/p) for p in names}}


def bind(proposal,inventory_report,config_data,partition_record):
    require(proposal.get('schema')=='math500-screening-scope-proposal-v1'
            and proposal.get('scope_digest')==PARENT and digest(proposal.get('scope'))==PARENT,'exact reviewed parent proposal')
    require(proposal.get('approval') is None and proposal.get('execution_allowed') is False,'disabled parent required')
    p=proposal['scope'];model=p['model_binding'];rows=p['verified_requests']
    require(p['cohort_digest']==COHORT and p['source_ids']==list(SOURCES)
            and p['blocked_retained']==BLOCKED and p['completed_no_rerun']==list(screen.SMOKE),'frozen source membership/order')
    require(model['checkpoint']==screen.CHECKPOINT and model['revision']==screen.REVISION
            and model['interface_implementation']==screen.implementation(),'same model and natural interface')
    require(p['prompt_hash']==digest(screen.PROMPT) and p['schema_hash']==digest(screen.response_schema())
            and p['thinking'] is False and p['do_sample'] is False,'prompt/settings unchanged')
    require([r['source_id'] for r in rows]==list(SOURCES),'request order')
    for r in rows:
        require(type(r['input_tokens']) is int and 0<r['input_tokens']<=13312
                and r['output_cap']==3072 and r['reserved_tokens']==r['input_tokens']+3072,'request caps')
    require(sum(r['reserved_tokens'] for r in rows)==CAP,'aggregate reservation')
    limits={'maximum_calls':20,'calls_per_source':1,'output_cap':3072,'context_limit':16384,
            'aggregate_token_cap':CAP,'campaign_wall_seconds':3600,'physical_gpus':1,'concurrency':1,
            'cpus':4,'host_memory_gb':128,'minimum_vram_bytes':80000000000,'partition':'NA100q','scheduler_config_bound':False}
    require(p['resources_proposed']==limits,'reviewed resource ceilings')
    old=inventory_report
    require(old.get('schema')=='joint-d1-local-verification-v1' and old.get('checkpoint')==screen.CHECKPOINT
            and old.get('revision')==screen.REVISION and old.get('local_path')==p['snapshot_path'],'historical inventory identity')
    inventory=old['inventory'];files=inventory['files'];shards=inventory['weight_shards']
    require(all(files.get(k)==v for k,v in local.METADATA.items()),'inventory metadata')
    require(len(shards)==len(set(shards))==11 and all(s in files and s.endswith('.safetensors') for s in shards),'weight shards')
    require(all(Path(k).name==k and type(v) is str and re.fullmatch('[0-9a-f]{64}',v) for k,v in files.items()),'file inventory')
    require(old['generation_tokens']=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop tokens')
    config=cluster.ClusterConfig(**config_data)
    require(config.partition=='NA100q' and config.time=='01:00:00' and config.memory_gb==128
            and config.activation_script is None,'one-hour NA100q config')
    fields=dict(re.findall(r'(\w+)=([^\s]+)',partition_record))
    require(fields.get('PartitionName')=='NA100q' and fields.get('State')=='UP' and fields.get('Nodes')=='node01','current partition evidence')
    scope={'condition':'d1-math500-complementary-screen-v1','parent_scope_digest':PARENT,'cohort_digest':COHORT,
           'source_ids':list(SOURCES),'blocked_retained':BLOCKED,'completed_no_rerun':list(screen.SMOKE),
           'source_package':{'path':p['statement_file'],'statements_file_sha256':p['statement_file_sha256'],
                             'statement_hashes':{r['source_id']:r['statement_sha256'] for r in rows}},
           'verified_requests':deepcopy(rows),'model':{'checkpoint':screen.CHECKPOINT,'revision':screen.REVISION,
             'local_path':p['snapshot_path'],'current_inventory':deepcopy(inventory),
             'generation_tokens':deepcopy(old['generation_tokens']),'non_thinking_verification':deepcopy(model['template_check']),
             'thinking':False,'do_sample':False,'dtype':'bfloat16','attention':'sdpa'},
           'resources':{**limits,'scheduler_config_bound':True},'cluster':deepcopy(config_data),
           'partition_record':partition_record,'prompt_hash':p['prompt_hash'],'schema_hash':p['schema_hash'],
           'retry_policy':p['retry_policy'],'stop_policy':p['stop_policy'],'D2_D6_enabled':False,
           'one_hour_may_leave_unrun_sources':True,'runtime_identity':identity(),
           'parent_inventory_digest':digest(old),'attachment_review_digest':p['attachment_review_digest']}
    return {'schema':'math500-screening-bound-disabled-v1','scope':scope,'scope_digest':digest(scope),
            'binding_inputs':{'proposal':deepcopy(proposal),'inventory_report':deepcopy(old),
                             'config_data':deepcopy(config_data),'partition_record':partition_record},
            'approval':None,'execution_allowed':False}


def validate_manifest(manifest):
    require(manifest==bind(**manifest['binding_inputs']),'changed manifest/evidence/runtime')
    return manifest['scope']


def review(manifest):
    scope=validate_manifest(manifest)
    return {'status':'bound_pending_explicit_20_call_approval','scope_digest':manifest['scope_digest'],
            'parent_scope_digest':PARENT,'source_ids':scope['source_ids'],'resources':scope['resources'],
            'blocked_retained':BLOCKED,'completed_no_rerun':list(screen.SMOKE),
            'approval_template':{'schema':APPROVAL_SCHEMA,'decision':'pending','scope_digest':manifest['scope_digest'],
               'reviewer':None,'reviewed_at':None,'statement_transmission_authorized':False,'GPU_spending_authorized':False},
            'execution_allowed':False,'model_executed':False,'D2_D6_enabled':False,
            'limitations':['observed_fit_not_worst_case_memory_qualification','one_hour_can_leave_unrun_sources',
                           'development_screen_only_no_workflow_admission','local_monetary_charges_unverified']}


def approve(manifest,approval):
    validate_manifest(manifest)
    keys={'schema','decision','scope_digest','reviewer','reviewed_at','statement_transmission_authorized','GPU_spending_authorized'}
    require(type(approval) is dict and set(approval)==keys,'explicit expanded approval fields')
    require(approval['schema']==APPROVAL_SCHEMA and approval['decision']=='approved'
            and approval['scope_digest']==manifest['scope_digest']
            and approval['statement_transmission_authorized'] is True and approval['GPU_spending_authorized'] is True,'exact expanded approval; old pilot receipt forbidden')
    require(all(type(approval[k]) is str and approval[k].strip() for k in ('reviewer','reviewed_at')),'reviewer/time')
    value={'schema':'math500-screen-scoped-release-v1','manifest':deepcopy(manifest),'approval':deepcopy(approval)}
    value['release_digest']=digest(value)
    return value


def validate_release(value):
    require(value==approve(value['manifest'],value['approval']),'release integrity')
    return value['manifest']['scope']


def source_records(scope):
    p=scope['source_package']
    return local.statement_records(Path(p['path']),scope['source_ids'],p['statements_file_sha256'],p['statement_hashes'])


def arguments(config,snapshot,output):
    argv=pilot.arguments(config,snapshot,output)
    argv[-4]=str(snapshot/'experiments/run_math500_screen.sbatch')
    return argv


def submit(root,value,*,dry_run=True):
    require(not os.environ.get('SLURM_JOB_ID'),'no batch self-submission')
    scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster']);source_records(scope)
    output=Path(config.output_root)/('math500-screen-'+key)
    registry=cluster.registry_root();state_path=registry/'registry.json'
    def action():
        state=read_json(state_path) if state_path.exists() else {'jobs':[]}
        cluster.guard(state)
        # A second bind/output directory must not allow repeating this cohort's attempt.
        require(COHORT not in state.get('math500_screen_attempts',{}),'cohort already submitted/uncertain; no retry')
        require(not output.exists(),'preserve existing output')
        cluster.validate_site(config)
        snapshot=Path(config.snapshot_root)/'SNAPSHOT_CREATED_AT_SUBMISSION'
        if dry_run:return {'submitted':False,'dry_run':True,'scope_digest':key,'argv':arguments(config,snapshot,output)}
        manifest={'schema':'math500-screen-slurm-v1','source_revision':source_revision(root),'release':value}
        snapshot=create_snapshot(root,Path(config.snapshot_root),manifest,plain(config),pilot.lock_for(scope))
        for name,h in scope['runtime_identity'].items():require(local.file_hash(snapshot/name)==h,'committed source binding')
        (output/'logs').mkdir(parents=True,exist_ok=False);atomic_json(output/'manifest.json',manifest)
        argv=arguments(config,snapshot,output);cluster.command([argv[0],'--test-only',*argv[1:]])
        reservation={'scope_digest':key,'release_digest':value['release_digest'],'snapshot':str(snapshot),
                     'output':str(output),'state':'submission_uncertain'}
        state.setdefault('math500_screen_attempts',{})[COHORT]=reservation
        state['uncertain_submission']=dict(reservation);atomic_json(state_path,state)
        response=cluster.command(argv);job=response.split(';',1)[0]
        require(re.fullmatch('[0-9]+',job) is not None,'uncertain submission retained')
        reservation.update(job_id=job,state='submitted_no_retry');state['uncertain_submission']=None
        state['completed_jobs']=(state.get('completed_jobs',[])+state.get('jobs',[]))[-100:]
        state['jobs']=[{'job_id':job,'manifest_hash':digest(manifest),'snapshot':str(snapshot),'output':str(output),
                       'concurrency':1,'physical_gpus_per_job':1,'reserved_physical_gpus':1,'mode':'D1-math500-screen'}]
        atomic_json(state_path,state)
        return {'job_id':job,'snapshot':str(snapshot),'output':str(output),'scope_digest':key,'submitted':True}
    if dry_run:return action()
    with directory_lock(registry/'.submission.lock'):return action()


class Session(screen.NaturalMockSession):
    """Twenty frozen one-shot calls; same durable accounting and response semantics."""
    def __init__(self,directory,scope,records,transport,started_at):
        require(type(transport) is pilot.CheckedTransport and transport.scope==scope,'bound natural transport')
        require(scope['source_ids']==list(SOURCES) and [r['id'] for r in records]==list(SOURCES),'twenty frozen sources')
        require(scope['resources']['maximum_calls']==20 and scope['resources']['aggregate_token_cap']==CAP,'fixed caps')
        require(all(set(r)=={'id','problem'} and hashlib.sha256(r['problem'].encode()).hexdigest()==scope['source_package']['statement_hashes'][r['id']] for r in records),'source views/hashes')
        self.transport=transport
        self.binding={'version':screen.VERSION,'requests':[screen.request(r) for r in records],
                      'transport':deepcopy(transport.binding),'scope_digest':digest(scope),'runtime_identity':identity()}
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=False)
        with self._locked():self._save({'binding':self.binding,'binding_digest':digest(self.binding),'attempts':[],
                     'started_at':started_at,'model_executed':transport.binding['evidence']=='local_runtime_unqualified'})

    def _totals(self,state):
        result=pilot.Session._totals(state)
        result['evidence']=self.transport.binding['evidence']
        if result['evidence']!='local_runtime_unqualified':result['model_calls_observed']=0
        return result

    def advance(self,source_id):
        require(self.transport.binding==self.binding['transport'],'transport changed')
        source_records(self.transport.scope)
        with self._locked():
            state=self._read();attempts=state['attempts']
            require(all(screen.reliable_terminal(a) for a in attempts),'unreliable dispatch/usage or resource breach; no replay')
            require(len(attempts)<20 and self.binding['requests'][len(attempts)]['payload']['source']['id']==source_id,'one call in frozen order')
            require(0<=time.time()-state['started_at']<3600,'wall ceiling')
            req=self.binding['requests'][len(attempts)];rendered=self.transport.render(req)
            count=rendered['input_tokens'];require(type(count) is int and 0<count<=13312,'input cap')
            reservation=count+3072
            require(sum(a['actual_tokens'] or 0 for a in attempts)+reservation<=CAP,'aggregate token ceiling')
            attempt={'source_id':source_id,'state':'reserved','input_tokens':count,'reservation_tokens':reservation,
                     'actual_tokens':None,'outbound_payload':req['payload'],'payload_digest':req['payload_digest'],
                     'rendered':rendered,'reserved_at':datetime.now(timezone.utc).isoformat()}
            attempts.append(attempt);self._save(state)
            start=time.monotonic();cpu=time.process_time()
            observed=self.transport.generate(rendered) # crash leaves full reservation, never replay
            attempt.update(observation=deepcopy(observed),cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start)
            usage=observed.get('output_tokens')
            if type(usage) is not int or usage<0 or type(observed.get('input_tokens')) is not int or observed['input_tokens']!=count:
                attempt['state']='uncertain'
            else:
                attempt['actual_tokens']=count+usage
                attempt['state']='completed' if usage<=3072 else 'usage_violation'
            attempt['raw_response']=observed.get('final_text')
            if observed.get('finish_reason')!='eos' or observed.get('boundary_error'):
                if attempt['state']=='completed':attempt['state']='response_boundary_error'
            attempt['review']=screen.review_response(attempt['raw_response'],source_id)
            if attempt['review']['status']=='invalid' and attempt['state']=='completed':attempt['state']='invalid_response'
            if time.time()-state['started_at']>=3600:attempt['state']='wall_limit_exceeded'
            self._save(state)
            return deepcopy(attempt)


def open_transport(value):
    scope=validate_release(value)
    from beyond_consensus.models.transformers_backend import require_allocation
    require_allocation()
    root=verify_local_inventory(pilot.lock_for(scope))
    import torch
    from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration
    require(torch.cuda.device_count()==1,'one visible GPU')
    require(torch.cuda.get_device_properties(0).total_memory>=80_000_000_000,'80GB-class GPU before loading')
    tokenizer=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==scope['model']['non_thinking_verification'],'non-thinking template binding')
    # Existing RepoRecourse loading/placement contract; no new inference backend.
    model=Qwen3_5ForConditionalGeneration.from_pretrained(str(root),local_files_only=True,trust_remote_code=False,
            use_safetensors=True,dtype=torch.bfloat16,attn_implementation='sdpa')
    model.to(torch.device('cuda:0'));model.requires_grad_(False);model.eval()
    transport=pilot.CheckedTransport(tokenizer,model,torch)
    require(transport.tokens==scope['model']['generation_tokens'],'stop tokens')
    transport.scope=scope
    transport.binding.update(evidence='local_runtime_unqualified',inventory_digest=digest(pilot.lock_for(scope)))
    return transport


def dispatch(value,directory):
    scope=validate_release(value);directory=Path(directory);directory.mkdir(parents=True,exist_ok=False)
    start=time.time();cpu=time.process_time();wall=time.monotonic()
    atomic_json(directory/'startup.json',{'scope_digest':digest(scope),'state':'started_no_retry','started_at':start,
        'source_ids':scope['source_ids'],'blocked_retained':BLOCKED,'completed_no_rerun':list(screen.SMOKE)})
    watchdog=threading.Timer(3600,lambda:os.kill(os.getpid(),signal.SIGKILL));watchdog.daemon=True;watchdog.start()
    session=None
    try:
        records=source_records(scope);transport=open_transport(value)
        session=Session(directory/'requests',scope,records,transport,start)
        result=pilot.drive(session,scope['source_ids']);result['model_executed']=bool(result['ledger']['attempts'])
        result.update(cohort_digest=COHORT,blocked_retained=BLOCKED,completed_no_rerun=list(screen.SMOKE))
        result['stage_resources']={'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,
                                  'includes_inventory_loading_and_validation':True}
        atomic_json(directory/'result.json',result)
        return result
    except BaseException as exc:
        atomic_json(directory/'failure.json',{'error_type':type(exc).__name__,'dispatch_uncertain':session is not None,
                    'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,'retry_allowed':False})
        raise
    finally:watchdog.cancel()


def run_allocated(root,output):
    require(os.environ.get('SLURM_JOB_ID'),'allocation required')
    root=Path(root);output=Path(output);marker=verify_snapshot(root)
    manifest=read_json(root/'resolved/manifest.json')
    require(manifest.get('schema')=='math500-screen-slurm-v1','expanded snapshot required')
    value=manifest['release'];scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster'])
    require(read_json(root/'resolved/cluster.json')==plain(config),'cluster binding')
    require(output.resolve()==(Path(config.output_root)/('math500-screen-'+key)).resolve(),'output binding')
    require(read_json(output/'manifest.json')==manifest and marker['manifest_hash']==digest(manifest),'snapshot manifest binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','single array task')
    with directory_lock(cluster.registry_root()/'.submission.lock'):
        state=read_json(cluster.registry_root()/'registry.json')
    record=state.get('math500_screen_attempts',{}).get(COHORT,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry'
            and record.get('release_digest')==value['release_digest'] and record.get('scope_digest')==key
            and Path(record.get('snapshot','')).resolve()==root.resolve()
            and Path(record.get('output','')).resolve()==output.resolve(),'registered expanded job')
    pilot.check_allocation_record(cluster.command(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o']))
    active=cluster.active_gpu_jobs()
    require(active and all(j.split('_')[0]==job and count==1 for j,count in active.items()),'exclusive one-GPU campaign')
    require(environment_inventory(config.python)==read_json(root/'resolved/environment.json'),'environment changed')
    return dispatch(value,output/'execution')
