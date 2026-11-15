"""One reviewed five-task MedQA composite; reuse metering, solver and R0 runtime."""
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json,sys
from . import medqa_development as adapter, medqa_planner_launch as planner
from . import composite_math_launch as base, composite_scaling as spec
from . import composite_scaling_runtime as runtime, composite_math as worker
from . import composite_scaling_replacement as placement
from .joint_schema import require,decode
from .model import digest
KEY='medqa-first-worker-composite-v1'
ROOT=Path(__file__).resolve().parents[2]
CONFIG='configs/phase2/medqa_worker_first_v1.json'
_scope=ContextVar(KEY)

def frozen():return json.loads((ROOT/CONFIG).read_text())
def identity():
    names=set(base.identity())|{'src/bc_phase2/medqa_development.py','src/bc_phase2/medqa_planner_launch.py','src/bc_phase2/medqa_worker_launch.py',
        'src/bc_phase2/composite_scaling.py','src/bc_phase2/composite_scaling_runtime.py','src/bc_phase2/composite_derivation_interface.py',
        'src/bc_phase2/composite_scaling_replacement.py','src/bc_phase2/composite_joint_replacement.py','src/bc_phase2/composite_joint.py',
        'scripts/medqa_worker.py','experiments/run_medqa_worker.sbatch',CONFIG}
    return {p:base.previous.local.file_hash(ROOT/p) for p in sorted(names)}

def wave():
    cfg=frozen();cs=cfg['components'];b=spec.neutral(cs,4)
    b.update(slot=1,status='supported_frozen',components=cs,sources=[c['source_id'] for c in cs],call_bounds=spec.call_bounds(cs,4))
    coverage=adapter.coverage(cs);schedule=runtime.schedule_profiles(cs,{})
    require(sum(s['calls'] for s in schedule)==5 and b['call_bounds']['evaluation_calls']==28,'exact single-composite ceiling')
    w=dict(condition=KEY,components=cs,bundles=[b],matrix=[dict(n=4,slot=1,status='supported_frozen')],
        profile_coverage=coverage,profile_schedule=schedule,profile_consumers={e['key']:[b['preprice_id']] for e in coverage},
        reused_profiles={},limits=cfg['limits'],execution_allowed=False)
    w['wave_id']=digest(w);return w

def tasks():return [dict(t,source_id=c['source_id']) for c in frozen()['components'] for t in c['tasks']]
def transport_tasks(s):return tasks()
def source_records(s):
    all_rows=planner.source_records(s);rows={r['id']:r for r in all_rows}
    selected={c['source_id']:rows[c['source_id']] for c in frozen()['components']}
    for c in frozen()['components']:require(digest(selected[c['source_id']])==c['statement_sha256'],'worker source changed')
    return selected

def qualify(snapshot):
    from .composite_math_decoder import qualify as check
    q=check(snapshot,tasks=tasks());q.update(condition=KEY,runtime_identity=identity());return q

def check_cpu(q):
    from .composite_math_decoder import schema,TaskTransport
    require(q['status']=='passed' and q['condition']==KEY and q['runtime_identity']==identity(),'CPU qualification binding')
    require(q['model_executed'] is False and q['metadata']==base.previous.local.METADATA and q['xgrammar_version']=='0.1.32','CPU-only pinned qualification')
    require(len(q['rows'])==len(tasks()),'complete grammar coverage')
    for t,r in zip(tasks(),q['rows']):
        require(r['task']==TaskTransport.task_key(t) and r['schema_hash']==digest(schema(t)) and all(r[k] is True for k in ('escaped_text_accepted','extra_key_rejected','malformed_rejected')),'schema controls')

def prepare(parent,config,q):
    # Historical release is evidence, not permission for workers. Do not require
    # historical implementation hashes to equal this prospective release.
    require(parent['release_digest']==digest({k:v for k,v in parent.items() if k!='release_digest'}),'parent release hash')
    pm=parent['manifest'];old=pm['scope'];require(pm['scope_digest']==digest(old),'parent scope hash')
    require(old['cohort_digest']==planner.COHORT and old['condition']=='medqa-planner-only-v1','same cohort')
    require(parent['approval']['decision']=='approved' and parent['approval']['scope_digest']==pm['scope_digest'],'parent approval identity')
    check_cpu(q);dep=base.deployment()
    s=dict(condition=KEY,wave=wave(),limits=frozen()['limits'],model=deepcopy(old['model']),source_package=deepcopy(old['source_package']),
        source_provenance=deepcopy(old['source_review']),parent_scope=pm['scope_digest'],cluster=config,deployment=dep,cpu_qualification=q,
        runtime_identity=identity(),scheduler_policy={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},
        D2_D6_campaign_enabled=False,private_evaluator_loaded=False)
    blockers=[] if dep['packages']==base.EXPECTED_PACKAGES and dep['solver_importable'] else ['deployment_mismatch']
    m=dict(schema=KEY+'-manifest',scope=s,scope_digest=digest(s),blockers=blockers,execution_allowed=False)
    validate_manifest(m);records=source_records(s)
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(s['model']['local_path'],local_files_only=True,trust_remote_code=False)
    from .d1_natural_screen import render_request
    measured=[]
    for c in s['wave']['components']:
        for t in c['tasks']:
            if t['parents']:continue # Generated parent contents do not exist yet.
            req=adapter.worker_request(c,t,records,{})
            row=render_request(tokenizer,req,s['model']['non_thinking_verification']['template_hash'])
            measured.append(dict(source_id=c['source_id'],task=t['id'],input_tokens=row['input_tokens'],rendered_ids_digest=row['rendered_ids_digest'],payload_digest=req['payload_digest']))
    s['initial_request_fit']=measured;s['dependent_fit']='checked_at_each_dispatch_not_worst_case_qualified'
    m['scope_digest']=digest(s);return m

def validate_manifest(m):
    require(m['schema']==KEY+'-manifest' and m['scope_digest']==digest(m['scope']) and m['execution_allowed'] is False,'disabled scope integrity')
    s=m['scope'];require(s['condition']==KEY and s['wave']==wave() and s['limits']==frozen()['limits'] and s['runtime_identity']==identity(),'frozen recipe')
    require(s['scheduler_policy']=={'allow_accounted_external_jobs':True,'maximum_user_gpus':4},'scheduler policy')
    model=s['model'];require(model['checkpoint']==base.screen.CHECKPOINT and model['revision']==base.screen.REVISION,'model identity')
    require(model['thinking'] is False and model['do_sample'] is False and model['dtype']=='bfloat16' and model['attention']=='sdpa','generation settings')
    require(model['generation_tokens']=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop tokens')
    require(all(model['current_inventory']['files'].get(k)==v for k,v in base.previous.local.METADATA.items()),'metadata inventory')
    c=base.cluster.ClusterConfig(**s['cluster'])
    require(c.partition=='HPCAIq' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'allocation limits')
    require(str(Path(c.python).resolve())==s['deployment']['python'],'interpreter')
    check_cpu(s['cpu_qualification']);require(s['cpu_qualification']['template']==model['non_thinking_verification'],'template')
    return s

def approve(m,a):
    s=validate_manifest(m);require(not m['blockers'] and s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'deployment blockers')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']==KEY+'-approval' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact worker approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'worker permissions')
    require(all(type(a[k]) is str and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema=KEY+'-release',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])

class Engine(adapter.Engine):
    def parse_artifact(self,text,task):
        value=super().parse_artifact(text,task)
        if 'option_label' in task['fields']:require(decode(value)['option_label'] in adapter.LABELS,'exact terminal option label')
        return value
coverage=adapter.coverage
key=adapter.key
domain=adapter.domain
descriptor=adapter.descriptor
check_profile=adapter.check_profile
class Journal(worker.Journal):
    def __init__(self,path,transport,scope,check_source):super().__init__(path,transport,scope,check_source,condition=KEY,limits=_scope.get()['limits'])
def run_recipe(journal,sources,out):return runtime.run_wave(journal,sources,out,_scope.get()['wave'],interface=sys.modules[__name__])
recipe=SimpleNamespace(Journal=Journal,run_recipe=run_recipe,blueprint=lambda:dict(schedule=['medqa-first']))
check_cuda=placement.probe.check_cuda
def check_scoped_allocation(record,s):placement.check_allocation(record,s['cluster']['partition'])
def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def dispatch(v,directory):
    s=validate_release(v);token=_scope.set(s);pt=placement.probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_scope.reset(token);placement.probe._probe_output.reset(pt)
def arguments(c,snapshot,output):
    a=base.arguments(c,snapshot,output);a[-4]=str(snapshot/'experiments/run_medqa_worker.sbatch');return a
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])

def grade_results(result,sources,protected):
    """Offline post-run grading only. Never called from the GPU execution path."""
    w=wave();require(result['wave_id']==w['wave_id'],'graded wave identity')
    rows=[]
    for condition in result['conditions']:
        require(condition['preprice_id']==w['bundles'][0]['preprice_id'],'graded condition identity')
        for method,value in condition['methods'].items():
            require(method in ('NEUTRAL','JOINT'),'method')
            repairs=value.get('repairs',[])
            sessions=[('clean',value.get('clean'))]+[(f'owner/o{i}',repairs[i] if i<len(repairs) else None) for i in range(4)]
            for slot,session in sessions:
                for c in w['components']:
                    sid=c['source_id'];require(digest(sources[sid])==c['statement_sha256'],'grade public identity')
                    event=c['namespace']+'_e'+c['outputs'][0][1:]
                    item=(session or {}).get('store',{}).get(event)
                    grade=adapter.grade(item['value'],protected[sid],sources[sid]) if item else dict(status='missing_artifact',correct=None)
                    rows.append(dict(method=method,slot=slot,source_id=sid,session_complete=(session or {}).get('complete',False),invocation=item.get('invocation') if item else None,grade=grade))
    return dict(wave_id=w['wave_id'],result_digest=digest(result),rows=rows,model_executed=False,
                meaning='Exam-answer agreement; repeated retained artifacts are not independent answers.')
