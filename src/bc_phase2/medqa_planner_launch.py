"""Frozen MedQA planner-only bridge; no worker stage or implicit approval."""
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
from . import medqa_development as medqa
from .planner_qwen import verify_local_inventory
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot, environment_inventory
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.util import atomic_json, directory_lock, read_json, plain

COHORT='1f471cbd92f4f957678bc26af84985ffb44699422122367c297f83983e6159a0'
PUBLIC_HASH='c38c5fd2b9b4d5661810fe4eac0f267490244ccdbe6ac6d1a360fa8ce16edb4b'
SOURCES=tuple('dev/row/'+str(n) for n in (339,80,970,87,479,358,164,645,25,82,714,241))
CAP=196608
APPROVAL_SCHEMA='medqa-planner-v1-approval'


def identity():
    root=Path(__file__).resolve().parents[2]
    # Scope-bind the planner call path; the full committed tree is independently
    # covered by the immutable snapshot inventory/environment checks.
    names=['src/bc_phase2/medqa_planner_launch.py','src/bc_phase2/medqa_development.py',
           'src/bc_phase2/d1_natural_launch.py','src/bc_phase2/joint_d1_local.py',
           'scripts/launch_medqa_planner.py','experiments/run_medqa_planner.sbatch',
           'src/beyond_consensus/experiments/cluster.py',
           'src/beyond_consensus/experiments/snapshot.py',
           'src/beyond_consensus/experiments/manifest.py','src/beyond_consensus/util.py']
    return {**screen.implementation(),**{p:local.file_hash(root/p) for p in names}}


def source_records(scope):
    package=scope['source_package'];path=Path(package['path'])
    require(path.is_absolute(),'absolute public cohort path')
    raw=path.read_bytes()
    require(len(raw)<=2*1024*1024 and hashlib.sha256(raw).hexdigest()==PUBLIC_HASH
            and package['sha256']==PUBLIC_HASH,'exact frozen public file')
    from .joint_schema import decode
    cohort=decode(raw.decode('utf8'))
    require(cohort['cohort_digest']==COHORT==digest({k:v for k,v in cohort.items() if k!='cohort_digest'}),'cohort integrity')
    records=cohort['records']
    require([r['id'] for r in records]==list(SOURCES),'twelve frozen sources in order')
    for r in records:medqa.assert_public(r)
    return records


def source_blockers(review):
    # This is a review record, not a license inference from a mirror's code license.
    expected={'cohort_digest','dataset_sha256','authors_archive_equivalence',
              'rights_review','evidence_reference','reviewer','reviewed_at'}
    require(type(review)is dict and set(review)==expected,'source review fields')
    require(review['cohort_digest']==COHORT and review['dataset_sha256']==
        '774bbd90103af43badbe8d5294e336443573fc37b918763920b8fc3b3df581d9','review source binding')
    blockers=[]
    if review['authors_archive_equivalence']!='verified':blockers.append('authors_archive_equivalence_unresolved')
    if review['rights_review']!='permitted_for_scoped_development':blockers.append('source_usage_review_unresolved')
    if not all(type(review[k])is str and review[k].strip() for k in ('evidence_reference','reviewer','reviewed_at')):
        blockers.append('documented_source_review_missing')
    return blockers


def bind(cohort_path,verification,inventory_report,config_data,partition_record,source_review):
    package={'path':str(cohort_path),'sha256':PUBLIC_HASH}
    records=source_records({'source_package':package})
    v=verification
    require(v.get('status')=='initial_requests_fit_observed_no_model' and v.get('cohort_digest')==COHORT
            and v.get('checkpoint')==screen.CHECKPOINT and v.get('revision')==screen.REVISION
            and v.get('model_executed') is False and v.get('execution_allowed') is False
            and v.get('private_evaluator_read') is False,'token-fit receipt')
    require(v['limits']==medqa.PLAN_LIMITS,'same caps')
    root=Path(__file__).resolve().parents[2]
    for name in ('src/bc_phase2/medqa_development.py','src/bc_phase2/d1_natural_screen.py',
                 'scripts/prepare_d1_natural_screen.py'):
        require(v['implementation_hashes'].get(name)==local.file_hash(root/name),'measured interface changed')
    template=v['template_check']
    require(template['template_hash']==local.TEMPLATE_HASH and template['enable_thinking'] is False
            and template['on_off_switch']['reasoning_support_verified'] is True
            and template['on_off_switch']['probe_on_hash']!=template['on_off_switch']['probe_off_hash'],'non-thinking verified')
    for name in ('config.json','tokenizer.json','tokenizer_config.json','chat_template.jinja'):
        require(v['metadata'][name]['sha256']==local.METADATA[name],'measured metadata')
    rows=v['requests'];require([r['source_id'] for r in rows]==list(SOURCES),'measured order')
    for record,row in zip(records,rows):
        require(row['payload_digest']==medqa.planner_request(record)['payload_digest'],'frozen prompt/source/schema')
        require(type(row['input_tokens'])is int and 0<row['input_tokens']<=13312
                and row['output_cap']==3072 and row['reserved_tokens']==row['input_tokens']+3072
                and re.fullmatch('[0-9a-f]{64}',row['rendered_ids_digest']),'request fit')
    require(sum(r['reserved_tokens'] for r in rows)==v['total_reservation_tokens']<=CAP,'reservation sum')
    old=inventory_report
    require(old.get('schema')=='joint-d1-local-verification-v1' and old.get('checkpoint')==screen.CHECKPOINT
            and old.get('revision')==screen.REVISION,'historical model inventory identity')
    require(Path(old['local_path']).is_absolute() and Path(old['local_path']).name==screen.REVISION,'pinned local snapshot')
    inventory=old['inventory'];files=inventory['files'];shards=inventory['weight_shards']
    require(all(files.get(k)==h for k,h in local.METADATA.items()),'inventory metadata')
    require(len(shards)==len(set(shards))==11 and all(s in files and s.endswith('.safetensors') for s in shards),'weight shards')
    require(all(Path(k).name==k and type(h)is str and re.fullmatch('[0-9a-f]{64}',h) for k,h in files.items()),'file inventory')
    require(old['generation_tokens']=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop tokens')
    config=cluster.ClusterConfig(**config_data)
    require(config.partition=='HPCAIq' and config.time=='01:00:00' and config.memory_gb==128
            and config.activation_script is None,'one-hour HPCAIq resources')
    fields=dict(re.findall(r'(\w+)=([^\s]+)',partition_record))
    require(fields.get('PartitionName')=='HPCAIq' and fields.get('State')=='UP' and fields.get('Nodes')=='node14','partition evidence')
    blockers=source_blockers(source_review)
    scope={'condition':'medqa-planner-only-v1','cohort_digest':COHORT,'source_ids':list(SOURCES),
        'source_package':package,'source_review':deepcopy(source_review),'verified_requests':deepcopy(rows),
        'model':{'checkpoint':screen.CHECKPOINT,'revision':screen.REVISION,'local_path':old['local_path'],
                 'current_inventory':deepcopy(inventory),'generation_tokens':deepcopy(old['generation_tokens']),
                 'non_thinking_verification':deepcopy(template),'thinking':False,'do_sample':False,
                 'dtype':'bfloat16','attention':'sdpa'},
        'resources':deepcopy(medqa.PLAN_LIMITS),'cluster':deepcopy(config_data),
        'partition_record':partition_record,'runtime_identity':identity(),
        'retry_policy':'one_per_source_no_retry_no_correction',
        'stop_policy':screen.disabled_manifest()['scope']['stop_policy'],
        'D2_D6_enabled':False,'worker_execution_allowed':False}
    inputs=dict(cohort_path=str(cohort_path),verification=deepcopy(v),inventory_report=deepcopy(old),
                config_data=deepcopy(config_data),partition_record=partition_record,source_review=deepcopy(source_review))
    return dict(schema='medqa-planner-bound-disabled-v1',scope=scope,scope_digest=digest(scope),
                binding_inputs=inputs,blockers=blockers,approval=None,execution_allowed=False)


def validate_manifest(manifest):
    require(manifest==bind(**manifest['binding_inputs']),'changed manifest/evidence/runtime')
    return manifest['scope']


def review(manifest):
    scope=validate_manifest(manifest)
    return dict(status='blocked_source_review' if manifest['blockers'] else 'bound_pending_planner_approval',
        scope_digest=manifest['scope_digest'],cohort_digest=COHORT,source_ids=scope['source_ids'],
        limits=scope['resources'],blockers=manifest['blockers'],
        measured_reservation=sum(r['reserved_tokens'] for r in scope['verified_requests']),
        approval_template=dict(schema=APPROVAL_SCHEMA,decision='pending',scope_digest=manifest['scope_digest'],
            reviewer=None,reviewed_at=None,statement_transmission_authorized=False,GPU_spending_authorized=False),
        model_executed=False,execution_allowed=False,worker_execution_allowed=False,
        limitations=['observed_request_fit_not_GPU_memory_qualification','one_hour_may_leave_unrun_sources',
                     'local_fees_unverified','plans_require_human_review_not_automatic_admission'])


def approve(manifest,approval):
    validate_manifest(manifest)
    require(not manifest["blockers"],"source review unresolved; approval cannot bypass it")
    keys={'schema','decision','scope_digest','reviewer','reviewed_at','statement_transmission_authorized','GPU_spending_authorized'}
    require(type(approval) is dict and set(approval)==keys,'explicit expanded approval fields')
    require(approval['schema']==APPROVAL_SCHEMA and approval['decision']=='approved'
            and approval['scope_digest']==manifest['scope_digest']
            and approval['statement_transmission_authorized'] is True and approval['GPU_spending_authorized'] is True,'exact expanded approval; old pilot receipt forbidden')
    require(all(type(approval[k]) is str and approval[k].strip() for k in ('reviewer','reviewed_at')),'reviewer/time')
    value={'schema':'medqa-planner-scoped-release-v1','manifest':deepcopy(manifest),'approval':deepcopy(approval)}
    value['release_digest']=digest(value)
    return value


def validate_release(value):
    require(value==approve(value['manifest'],value['approval']),'release integrity')
    return value['manifest']['scope']


def arguments(config,snapshot,output):
    argv=cluster.sbatch_arguments(config,snapshot,output,[0],1,mode='preflight')
    argv[-6:]=[str(snapshot/'experiments/run_medqa_planner.sbatch'),str(snapshot),str(output),config.python]
    argv[-4]=str(snapshot/'experiments/run_medqa_planner.sbatch')
    return argv


def submit(root,value,*,dry_run=True):
    require(not os.environ.get('SLURM_JOB_ID'),'no batch self-submission')
    scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster']);source_records(scope)
    output=Path(config.output_root)/('medqa-planner-'+key)
    registry=cluster.registry_root();state_path=registry/'registry.json'
    def action():
        state=read_json(state_path) if state_path.exists() else {'jobs':[]}
        cluster.guard(state)
        # A second bind/output directory must not allow repeating this cohort's attempt.
        require(COHORT not in state.get('medqa_planner_attempts',{}),'cohort already submitted/uncertain; no retry')
        require(not output.exists(),'preserve existing output')
        cluster.validate_site(config)
        snapshot=Path(config.snapshot_root)/'SNAPSHOT_CREATED_AT_SUBMISSION'
        if dry_run:return {'submitted':False,'dry_run':True,'scope_digest':key,'argv':arguments(config,snapshot,output)}
        manifest={'schema':'medqa-planner-slurm-v1','source_revision':source_revision(root),'release':value}
        snapshot=create_snapshot(root,Path(config.snapshot_root),manifest,plain(config),pilot.lock_for(scope))
        for name,h in scope['runtime_identity'].items():require(local.file_hash(snapshot/name)==h,'committed source binding')
        (output/'logs').mkdir(parents=True,exist_ok=False);atomic_json(output/'manifest.json',manifest)
        argv=arguments(config,snapshot,output);cluster.command([argv[0],'--test-only',*argv[1:]])
        reservation={'scope_digest':key,'release_digest':value['release_digest'],'snapshot':str(snapshot),
                     'output':str(output),'state':'submission_uncertain'}
        state.setdefault('medqa_planner_attempts',{})[COHORT]=reservation
        state['uncertain_submission']=dict(reservation);atomic_json(state_path,state)
        response=cluster.command(argv);job=response.split(';',1)[0]
        require(re.fullmatch('[0-9]+',job) is not None,'uncertain submission retained')
        reservation.update(job_id=job,state='submitted_no_retry');state['uncertain_submission']=None
        state['completed_jobs']=(state.get('completed_jobs',[])+state.get('jobs',[]))[-100:]
        state['jobs']=[{'job_id':job,'manifest_hash':digest(manifest),'snapshot':str(snapshot),'output':str(output),
                       'concurrency':1,'physical_gpus_per_job':1,'reserved_physical_gpus':1,'mode':'D1-medqa-planner'}]
        atomic_json(state_path,state)
        return {'job_id':job,'snapshot':str(snapshot),'output':str(output),'scope_digest':key,'submitted':True}
    if dry_run:return action()
    with directory_lock(registry/'.submission.lock'):return action()


class Session(screen.NaturalMockSession):
    """Twelve frozen one-shot calls; same durable accounting and response semantics."""
    def __init__(self,directory,scope,records,transport,started_at):
        require(type(transport) is pilot.CheckedTransport and transport.scope==scope,'bound natural transport')
        require(scope['source_ids']==list(SOURCES) and [r['id'] for r in records]==list(SOURCES),'twelve frozen sources')
        require(scope['resources']==medqa.PLAN_LIMITS,'fixed caps')
        for record in records:medqa.assert_public(record)
        self.transport=transport
        self.binding={'version':screen.VERSION,'requests':[medqa.planner_request(r) for r in records],
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
            require(len(attempts)<12 and self.binding['requests'][len(attempts)]['payload']['source']['id']==source_id,'one call in frozen order')
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
        'source_ids':scope['source_ids']})
    watchdog=threading.Timer(3600,lambda:os.kill(os.getpid(),signal.SIGKILL));watchdog.daemon=True;watchdog.start()
    session=None
    try:
        records=source_records(scope);transport=open_transport(value)
        session=Session(directory/'requests',scope,records,transport,start)
        result=pilot.drive(session,scope['source_ids'])
        result['model_executed']=bool(result['ledger']['totals']['model_calls_observed'])
        result.update(cohort_digest=COHORT,worker_execution_allowed=False)
        attempts={a['source_id']:a for a in result['ledger']['attempts']}
        result['rows']=[dict(source_id=r['source_id'],raw_response=attempts.get(r['source_id'],{}).get('raw_response'),
                            review=attempts.get(r['source_id'],{}).get('review'),state=r['status']) for r in result['sources']]
        result['stage_resources']={'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,
                                  'includes_inventory_loading_and_validation':True}
        atomic_json(directory/'result.json',result)
        return result
    except BaseException as exc:
        atomic_json(directory/'failure.json',{'error_type':type(exc).__name__,'dispatch_uncertain':session is not None,
                    'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.monotonic()-wall,'retry_allowed':False})
        raise
    finally:watchdog.cancel()


def check_allocation(record):
    fields=dict(re.findall(r'(\w+)=([^\s]+)',record))
    require(fields.get('Partition')=='HPCAIq' and fields.get('NumNodes')=='1'
            and fields.get('NumCPUs')=='4' and fields.get('TimeLimit')=='01:00:00','allocated resources')
    tres=dict(item.split('=',1) for item in fields.get('ReqTRES','').split(',') if '=' in item)
    require(tres.get('cpu')=='4' and tres.get('gres/gpu')=='1'
            and tres.get('mem') in ('128G','131072M'),'allocated TRES')


def run_allocated(root,output):
    require(os.environ.get('SLURM_JOB_ID'),'allocation required')
    root=Path(root);output=Path(output);marker=verify_snapshot(root)
    manifest=read_json(root/'resolved/manifest.json')
    require(manifest.get('schema')=='medqa-planner-slurm-v1','expanded snapshot required')
    value=manifest['release'];scope=validate_release(value);key=value['manifest']['scope_digest']
    config=cluster.ClusterConfig(**scope['cluster'])
    require(read_json(root/'resolved/cluster.json')==plain(config),'cluster binding')
    require(output.resolve()==(Path(config.output_root)/('medqa-planner-'+key)).resolve(),'output binding')
    require(read_json(output/'manifest.json')==manifest and marker['manifest_hash']==digest(manifest),'snapshot manifest binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','single array task')
    with directory_lock(cluster.registry_root()/'.submission.lock'):
        state=read_json(cluster.registry_root()/'registry.json')
    record=state.get('medqa_planner_attempts',{}).get(COHORT,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry'
            and record.get('release_digest')==value['release_digest'] and record.get('scope_digest')==key
            and Path(record.get('snapshot','')).resolve()==root.resolve()
            and Path(record.get('output','')).resolve()==output.resolve(),'registered expanded job')
    allocation=cluster.command(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'])
    check_allocation(allocation)
    active=cluster.active_gpu_jobs()
    require(active and all(j.split('_')[0]==job and count==1 for j,count in active.items()),'exclusive one-GPU campaign')
    require(environment_inventory(config.python)==read_json(root/'resolved/environment.json'),'environment changed')
    return dispatch(value,output/'execution')
