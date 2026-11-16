"""Second frozen MATH block, using existing transport, journal and Slurm registry."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,os,re,signal,sys,threading,time
from .model import digest
from .joint_schema import require
from . import prospective_pipeline as pipeline, prospective_sources as sources
from . import composite_math_launch as base, composite_math as worker
from . import d1_natural_launch as pilot, d1_natural_screen as screen, joint_d1_local as local
from . import medqa_planner_launch as previous
from beyond_consensus.util import atomic_json

KEY='prospective-math-block2-planner-v1'
TRANSPORT_EVIDENCE='real_prospective_planner'
ROOT=Path(__file__).resolve().parents[2]
CONFIG='configs/phase2/prospective_math_block2_source_review_v1.json'
LIMITS=dict(pipeline.LIMITS,maximum_calls=8,calls_per_source=1,token_cap=131072,wall_seconds=3600)
PUBLIC_HASH='b7ebe540f9c4b91d5bcf07b4e797f1de405982e748be3162721aaf3dfe82e5dd'

def cohort():
    bundle=json.loads((ROOT/CONFIG).read_text())
    require(bundle['review_bundle_digest']==digest({k:v for k,v in bundle.items() if k!='review_bundle_digest'}),'review bundle')
    c=bundle['cohort']
    require(c['cohort_digest']==digest({k:v for k,v in c.items() if k!='cohort_digest'}),'cohort digest')
    require(c['cohort_digest']=='439a352f650efcf04e09fcf20fcaf4e467beeefefa2e6b5020fe4238ac43e378','reviewed block')
    require(c['procedure_digest']==pipeline.procedure('math500')['procedure_digest'],'frozen scientific procedure')
    return c

def identity():
    names=set(base.identity())|{CONFIG,'src/bc_phase2/prospective_block2_launch.py',
        'src/bc_phase2/prospective_pipeline.py','src/bc_phase2/prospective_sources.py','src/bc_phase2/prospective_adapters.py',
        'scripts/launch_prospective_math_block2.py','experiments/run_prospective_math_block2.sbatch',
        'src/bc_phase2/medqa_planner_launch.py','src/bc_phase2/medqa_worker_launch.py',
        'src/bc_phase2/composite_scaling_runtime.py','src/bc_phase2/composite_scaling.py'}
    return {p:local.file_hash(ROOT/p) for p in sorted(names)}

def source_records(scope):
    package=scope['source_package'];path=Path(package['path'])
    require(path.is_absolute(),'absolute public package path')
    raw=path.read_bytes();require(len(raw)<=4*1024*1024 and hashlib.sha256(raw).hexdigest()==PUBLIC_HASH==package['sha256'],'public package changed')
    rows=json.loads(raw);require(len(rows)==500,'public package count')
    require(all(set(r)=={'id','problem'} for r in rows),'public fields only')
    by={r['id']:r for r in rows};require(len(by)==500,'unique sources')
    result={}
    for r in cohort()['blocks'][1]['records']:
        require(r['status']=='eligible','source review pending')
        pub=by[r['source_id']]
        require(sources.faithful_identity(pub)==(r['exact_hash'],r['normalized_hash']),'source identity')
        result[r['source_id']]=pub
    require(len(result)==8,'exact block');return result

def prepare(public,inventory,config,partition):
    require(inventory.get('schema')=='joint-d1-local-verification-v1' and inventory.get('checkpoint')==screen.CHECKPOINT
            and inventory.get('revision')==screen.REVISION,'pinned inventory receipt')
    old=inventory;model=dict(checkpoint=screen.CHECKPOINT,revision=screen.REVISION,local_path=old['local_path'],
        current_inventory=deepcopy(old['inventory']),generation_tokens=deepcopy(old['generation_tokens']),
        thinking=False,do_sample=False,dtype='bfloat16',attention='sdpa')
    for name,h in local.METADATA.items():require(local.file_hash(Path(model['local_path'])/name)==h,'local metadata')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(model['local_path'],local_files_only=True,trust_remote_code=False)
    model['non_thinking_verification']=screen.verify_non_thinking(tokenizer)
    package=dict(path=str(Path(public).resolve()),sha256=PUBLIC_HASH)
    records=source_records({'source_package':package})
    packet=pipeline.planning_packet(cohort(),2,records);measurements=[]
    for req in packet['requests']:
        rendered=screen.render_request(tokenizer,req,model['non_thinking_verification']['template_hash'])
        measurements.append(dict(source_id=req['payload']['source']['id'],**{k:rendered[k] for k in ('payload_digest','rendered_ids_digest','input_tokens')},reserved_tokens=rendered['input_tokens']+3072))
    dep=base.deployment()
    scope=dict(condition=KEY,cohort_digest=cohort()['cohort_digest'],source_ids=list(records),
        source_package=package,model=model,cluster=config,partition_record=partition,
        verified_requests=measurements,limits=LIMITS,runtime_identity=identity(),deployment=dep,
        scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},
        worker_execution_allowed=False,source_review_digest=json.loads((ROOT/CONFIG).read_text())['review_bundle_digest'])
    m=dict(schema=KEY+'-manifest',scope=scope,scope_digest=digest(scope),blockers=[],execution_allowed=False)
    m['blockers']=[] if dep['packages']==base.EXPECTED_PACKAGES and dep['solver_importable'] else ['execution_environment_mismatch']
    validate_manifest(m);return m

def validate_manifest(m):
    require(m['schema']==KEY+'-manifest' and m['scope_digest']==digest(m['scope']) and m['execution_allowed'] is False,'disabled manifest integrity')
    s=m['scope'];c=cohort()
    require(s['condition']==KEY and s['cohort_digest']==c['cohort_digest'] and s['limits']==LIMITS
            and s['runtime_identity']==identity() and s['worker_execution_allowed'] is False,'frozen scope/runtime')
    require(s['source_review_digest']==json.loads((ROOT/CONFIG).read_text())['review_bundle_digest'],'source review')
    model=s['model'];require(model['checkpoint']==screen.CHECKPOINT and model['revision']==screen.REVISION,'model identity')
    require(Path(model['local_path']).is_absolute() and Path(model['local_path']).name==screen.REVISION,'snapshot path')
    require(model['thinking'] is False and model['do_sample'] is False and model['dtype']=='bfloat16' and model['attention']=='sdpa','generation policy')
    inv=model['current_inventory'];require(len(set(inv['weight_shards']))==11 and all(k in inv['files'] for k in inv['weight_shards']),'weight inventory')
    require(all(inv['files'].get(k)==v for k,v in local.METADATA.items()),'inventory metadata')
    require(model['generation_tokens']=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop tokens')
    template=model['non_thinking_verification']
    require(template['enable_thinking'] is False and template['template_hash']==local.TEMPLATE_HASH and template['on_off_switch']['reasoning_support_verified'] is True,'non-thinking binding')
    config=base.cluster.ClusterConfig(**s['cluster'])
    require(config.partition=='HPCAIq' and config.time=='01:00:00' and config.memory_gb==128 and config.activation_script is None,'allocation caps')
    require(str(Path(config.python).resolve())==s['deployment']['python'],'interpreter')
    fields=dict(re.findall(r'(\w+)=([^\s]+)',s['partition_record']))
    require(fields.get('PartitionName')=='HPCAIq' and fields.get('State')=='UP','partition evidence')
    require(s['scheduler_policy']=={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},'overlap policy')
    records=source_records(s);require(s['source_ids']==list(records),'source order')
    require([r['source_id'] for r in s['verified_requests']]==list(records),'measured order')
    for row,pub in zip(s['verified_requests'],records.values()):
        require(row['payload_digest']==screen.request(pub)['payload_digest'],'exact planner request')
        require(type(row['input_tokens']) is int and 0<row['input_tokens']<=13312 and row['reserved_tokens']==row['input_tokens']+3072 and re.fullmatch('[0-9a-f]{64}',row['rendered_ids_digest']),'request fit')
    require(sum(r['reserved_tokens'] for r in s['verified_requests'])<=LIMITS['token_cap'],'aggregate reservation')
    return s

def approve(m,a):
    s=validate_manifest(m)
    require(not m['blockers'] and s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'environment blockers')
    require(set(a)=={'schema','decision','scope_digest','reviewer','reviewed_at','statement_transmission_authorized','GPU_spending_authorized'},'approval fields')
    require(a['schema']==KEY+'-approval' and a['decision']=='approved' and a['scope_digest']==m['scope_digest']
            and a['statement_transmission_authorized'] is True and a['GPU_spending_authorized'] is True,'exact planner-only approval')
    require(all(type(a[k]) is str and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema=KEY+'-release',manifest=deepcopy(m),approval=deepcopy(a));v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return v['manifest']['scope']

def make_transport(tokenizer,model,torch,s):
    t=pilot.CheckedTransport(tokenizer,model,torch);t.scope=s;return t

def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def arguments(c,snapshot,output):
    a=base.arguments(c,snapshot,output);a[-4]=str(snapshot/'experiments/run_prospective_math_block2.sbatch');return a

def check_scoped_allocation(record,s):previous.check_allocation(record)
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])

def dispatch(v,directory):
    s=validate_release(v);out=Path(directory);out.mkdir(exist_ok=False)
    cpu=time.process_time();wall=time.monotonic()
    atomic_json(out/'startup.json',dict(scope_digest=digest(s),state='started_no_retry'))
    timer=threading.Timer(3600,lambda:os.kill(os.getpid(),signal.SIGKILL));timer.daemon=True;timer.start()
    journal=None
    try:
        records=source_records(s);transport=open_transport(v)
        journal=worker.Journal(out/'journal',transport,digest(s),lambda:source_records(s),condition=KEY,limits=LIMITS)
        rows=pipeline.plan_block(journal,cohort(),2,records,out/'planning')
        result=dict(status='completed_planner_block_review_required',evidence=TRANSPORT_EVIDENCE,rows=rows,ledger=journal.snapshot(),
            totals=journal.snapshot()['totals'],model_executed=bool(journal.snapshot()['totals']['calls']),worker_execution_allowed=False,
            stage_resources=dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall))
        atomic_json(out/'result.json',result);return result
    except BaseException as exc:
        atomic_json(out/'failure.json',dict(error_type=type(exc).__name__,retry_allowed=False,
            totals=journal.snapshot()['totals'] if journal else None,
            cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall))
        raise
    finally:timer.cancel()
