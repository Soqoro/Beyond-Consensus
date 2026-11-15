"""One reviewed prospective MATH pair; reuse the accepted worker/registry runtime."""
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import importlib.util,json,re,sys
from . import prospective_planner_launch as planner, prospective_pipeline as pipeline
from . import composite_math_launch as base, composite_math as worker, composite_scaling as spec
from . import composite_common_derivation_launch as common
from . import joint_d1_local as local, d1_natural_screen as screen
from .composite_math_decoder import schema
from .joint_schema import require
from .model import digest

ROOT=Path(__file__).resolve().parents[2]
KEY='prospective-math-block1-worker-v1'
CONFIG='configs/phase2/prospective_math_block1_worker_v1.json'
_scope=ContextVar(KEY)

def packet():
    v=json.loads((ROOT/CONFIG).read_text())
    require(v['packet_digest']==digest({k:x for k,x in v.items() if k!='packet_digest'}),'contract packet integrity')
    require(v['cohort_digest']==planner.cohort()['cohort_digest'] and v['execution_allowed'] is False,'reviewed cohort')
    require(v['wave']==pipeline.wave(planner.cohort(),1,v['dispositions']),'frozen neutral and ranking')
    require(v['wave']['limits']['maximum_calls']==38,'bounded one-pair recipe')
    return v

def identity():
    names=set(planner.identity())|set(common.identity())|{CONFIG,'src/bc_phase2/prospective_worker_launch.py',
        'scripts/launch_prospective_worker.py','experiments/run_prospective_worker.sbatch',
        'scripts/check_composite_common_derivation.py','scripts/check_composite_derivation_order.py'}
    return {p:local.file_hash(ROOT/p) for p in sorted(names)}

def read(path):
    path=Path(path);raw=path.read_bytes();require(len(raw)<=64*1024*1024,'bounded evidence')
    return json.loads(raw)

def parent_evidence(run):
    run=Path(run).resolve();v=packet();release=read(run/'manifest.json')['release']
    old=planner.validate_release(release)
    require(release['manifest']['scope_digest']==v['planner_scope'],'exact planner parent')
    path=run/'execution/result.json';require(local.file_hash(path)==v['planner_result_sha256'],'original planner result bytes')
    r=read(path);require(r['totals']=={'actual_tokens':11491,'calls':8,'reserved_tokens':0},'planner overhead')
    records=planner.source_records(old);rows=r['rows'];attempts=r['ledger']['attempts']
    require([x['source_id'] for x in rows]==list(records) and len(attempts)==8,'complete planning block')
    require(r['ledger']['binding_digest']==digest(r['ledger']['binding']) and r['ledger']['binding']['scope']==v['planner_scope'],'planner ledger binding')
    for row,a in zip(rows,attempts):
        sid=row['source_id'];require(row['raw_response']==a['observation']['final_text'] and row['invocation']==a['id'],'raw response link')
        require(a['request']==pipeline.adapters.planner_request('math500',records[sid]) and worker.reliable_terminal(a),'planner request and usage')
        require(pipeline.admit('math500',planner.cohort(),records[sid],row['raw_response'],v['reviews'][sid])==v['dispositions'][sid],'exact reviewed contract')
    return dict(run=str(run),release=release,result_sha256=v['planner_result_sha256'],planning_tokens=11491,planning_calls=8)

def source_records(s):
    records=planner.source_records(s)
    return {c['source_id']:records[c['source_id']] for c in s['wave']['components']}

def transport_tasks(s):
    return [dict(spec.task(c,t,mode),source_id=c['source_id']) for c in s['wave']['components'] for mode in c['A_modes'] for t in c['tasks']]

def qualify(s):
    """Only local tokenizer and CPU grammar; synthetic parents are not fit proofs."""
    import importlib.metadata
    require(importlib.metadata.version('xgrammar')=='0.1.32','pinned grammar package')
    from transformers import AutoTokenizer
    import xgrammar as xgr
    root=Path(s['model']['local_path'])
    for name,h in local.METADATA.items():require(local.file_hash(root/name)==h,'metadata changed')
    tok=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
    template=screen.verify_non_thinking(tok);require(template==s['model']['non_thinking_verification'],'template')
    config=read(root/'config.json');size=config.get('text_config',config)['vocab_size']
    info=xgr.TokenizerInfo.from_huggingface(tok,vocab_size=size,stop_token_ids=[248046,248044])
    compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
    load=importlib.util.spec_from_file_location('prospective_cpu_controls',ROOT/'scripts/check_composite_common_derivation.py')
    controls=importlib.util.module_from_spec(load);load.loader.exec_module(controls)
    unique={digest(schema(t)):t for t in transport_tasks(s)};rows=[]
    for h,t in sorted(unique.items()):
        grammar=compiler.compile_json_schema(schema(t),any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
        obs=controls.controls(lambda:xgr.GrammarMatcher(grammar),tok,t['fields'],[248046,248044])
        rows.append(dict(schema_hash=h,schema=schema(t),observations=obs,passed=all(o['passed'] for o in obs)))
    records=source_records(s);requests=[]
    for c in s['wave']['components']:
        for mode in c['A_modes']:
            for t0 in c['tasks']:
                t=spec.task(c,t0,mode)
                parents={p:{f:'Synthetic parent artifact.' for f in next(x for x in c['tasks'] if x['id']==p)['fields']} for p in t['parents']}
                req=pipeline.worker_request(c,t,records,parents)
                rendered=screen.render_request(tok,req,template['template_hash'])
                requests.append(dict(source_id=c['source_id'],task=t['id'],mode=mode,synthetic_parents=bool(parents),**{k:rendered[k] for k in ('input_tokens','payload_digest','rendered_ids_digest')}))
    return dict(status='passed_cpu_checks' if all(r['passed'] for r in rows) else 'failed',rows=rows,requests=requests,
        template=template,xgrammar_version='0.1.32',model_executed=False,full_parent_fit_verified=False)

def check_cpu(s):
    q=s['cpu_qualification'];require(q['status']=='passed_cpu_checks' and q['model_executed'] is False and q['xgrammar_version']=='0.1.32','CPU qualification')
    require(q['template']==s['model']['non_thinking_verification'],'qualified template')
    schemas={digest(schema(t)):schema(t) for t in transport_tasks(s)}
    require(len(q['rows'])==len(schemas) and {r['schema_hash'] for r in q['rows']}==set(schemas),'complete schema coverage')
    for r in q['rows']:
        require(r['schema']==schemas[r['schema_hash']] and r['passed'] is True,'schema content')
        require([o['eos'] for o in r['observations']]==[248046,248044],'EOS coverage')
        for o in r['observations']:
            require(o['passed'] is True,'grammar observation')
            checks=o['checks'];require(all(checks['derivation_first'][k] is True for k in ('string_plus_eos','tokens_plus_eos','roundtrip_exact')),'positive grammar controls')
            for name in ('derivation_last','extra_key','missing_field','malformed'):
                require(all(checks[name][k] is False for k in ('string_plus_eos','tokens_plus_eos')),'negative grammar controls')
    expected=[(c['source_id'],t['id'],mode,bool(t['parents'])) for c in s['wave']['components'] for mode in c['A_modes'] for t in c['tasks']]
    require([(r['source_id'],r['task'],r['mode'],r['synthetic_parents']) for r in q['requests']]==expected,'request coverage')
    require(all(type(r['input_tokens']) is int and 0<r['input_tokens']<=13312 for r in q['requests']),'observed fit')
    records=source_records(s)
    for r,(sid,tid,mode,_) in zip(q['requests'],expected):
        c=next(c for c in s['wave']['components'] if c['source_id']==sid)
        t=spec.task(c,next(t for t in c['tasks'] if t['id']==tid),mode)
        parents={p:{f:'Synthetic parent artifact.' for f in next(x for x in c['tasks'] if x['id']==p)['fields']} for p in t['parents']}
        require(r['payload_digest']==pipeline.worker_request(c,t,records,parents)['payload_digest'],'qualified request binding')
        require(re.fullmatch('[0-9a-f]{64}',r['rendered_ids_digest']),'rendered request digest')


def prepare(run,config,partition):
    h=parent_evidence(run);old=h['release']['manifest']['scope'];p=packet();dep=base.deployment()
    s=dict(condition=KEY,parent=h,contract_packet_digest=p['packet_digest'],wave=p['wave'],model=deepcopy(old['model']),
        source_package=deepcopy(old['source_package']),cluster=config,partition_record=partition,deployment=dep,
        runtime_identity=identity(),limits=p['wave']['limits'],scheduler_policy=old['scheduler_policy'],
        cuda_check=common.placement.probe.PROBE,D2_D6_campaign_enabled=False,
        planning_overhead={'calls':8,'actual_tokens':11491,'charged_physically_once':True,'new_scope_calls':False},
        limitations=['AI-assisted reviewer merges, not autonomous decomposition.',
        'Fixed A/C; only ownership B is available for optimisation.',
        'Synthetic parent fit is not worst-case qualification; actual requests checked before each dispatch.',
        'MATH correctness remains blinded review; structural completion is not correctness.'])
    s['cpu_qualification']=qualify(s)
    blockers=[] if dep['packages']==base.EXPECTED_PACKAGES and dep['solver_importable'] else ['deployment_mismatch']
    m=dict(schema=KEY+'-manifest',scope=s,scope_digest=digest(s),blockers=blockers,execution_allowed=False)
    validate_manifest(m);return m

def validate_manifest(m):
    require(m['schema']==KEY+'-manifest' and m['scope_digest']==digest(m['scope']) and m['execution_allowed'] is False,'disabled integrity')
    s=m['scope'];p=packet();require(s['condition']==KEY and s['runtime_identity']==identity(),'implementation binding')
    h=parent_evidence(s['parent']['run']);old=h['release']['manifest']['scope']
    require(s['parent']==h and s['contract_packet_digest']==p['packet_digest'] and s['wave']==p['wave'] and s['limits']==p['wave']['limits'],'frozen recipe')
    require(s['model']==old['model'] and s['source_package']==old['source_package'],'pinned parent bindings')
    require(s['scheduler_policy']=={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},'overlap limit')
    require(s['cuda_check']==common.placement.probe.PROBE and s['D2_D6_campaign_enabled'] is False,'allocation probe')
    c=base.cluster.ClusterConfig(**s['cluster'])
    require(c.partition=='HPCAIq' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'resource caps')
    require(str(Path(c.python).resolve())==s['deployment']['python'],'Python binding')
    fields=dict(re.findall(r'(\w+)=([^\s]+)',s['partition_record']))
    require(fields.get('PartitionName')=='HPCAIq' and fields.get('State')=='UP','partition evidence')
    require(s['planning_overhead']=={'calls':8,'actual_tokens':11491,'charged_physically_once':True,'new_scope_calls':False},'prior overhead accounting')
    check_cpu(s);source_records(s);return s

def approve(m,a):
    s=validate_manifest(m);require(not m['blockers'] and s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'deployment')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']==KEY+'-approval' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact worker approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'scope permissions')
    require(all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema=KEY+'-release',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])
class Journal(worker.Journal):
    def __init__(self,path,transport,scope,check_source):super().__init__(path,transport,scope,check_source,condition=KEY,limits=_scope.get()['limits'])
def run_recipe(journal,sources,out):
    result=pipeline.run_wave(journal,sources,out,_scope.get()['wave'])
    result['planning_overhead']=deepcopy(_scope.get()['planning_overhead'])
    return result
recipe=SimpleNamespace(Journal=Journal,run_recipe=run_recipe,blueprint=lambda:dict(schedule=['block1']))
check_cuda=common.check_cuda
check_scoped_allocation=common.check_scoped_allocation

def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def arguments(c,snapshot,output):
    a=base.arguments(c,snapshot,output);a[-4]=str(snapshot/'experiments/run_prospective_worker.sbatch');return a
def dispatch(v,directory):
    s=validate_release(v);token=_scope.set(s);pt=common.placement.probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_scope.reset(token);common.placement.probe._probe_output.reset(pt)
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
