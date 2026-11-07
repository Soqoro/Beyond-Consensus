"""Exact wave-one approval, shared registry and accepted single-GPU launcher."""
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from . import composite_scaling as spec, composite_scaling_runtime as runtime
from . import composite_math as old, composite_joint_launch as joint, composite_joint_replacement as probe
from .joint_schema import require
from .model import digest
from beyond_consensus.util import read_json, atomic_json

base=joint.base
KEY=spec.CONDITION+'-wave1'
_scope=ContextVar('scaling_scope')


def identity():
    root=Path(__file__).resolve().parents[2]
    files=set(joint.identity())|{'src/bc_phase2/composite_scaling.py','src/bc_phase2/composite_scaling_runtime.py','src/bc_phase2/composite_scaling_launch.py','scripts/composite_scaling_pilot.py','experiments/run_composite_scaling.sbatch','configs/phase2/composite_scaling_bank_v2.json'}
    return {p:base.previous.local.file_hash(root/p) for p in sorted(files)}


def make_wave(bank,reused):
    p=spec.packet(bank)
    components=sorted({c['source_id']:c for b in p['bundles'] for c in b['components']}.values(),key=lambda c:c['source_id'])
    allowed={r['key'] for r in p['profile_coverage']}
    require(set(reused)<=allowed,'unrecognised reuse keys')
    runtime.validate_receipts(reused,p['profile_coverage'])
    schedule=runtime.schedule_profiles(components,reused)
    calls=sum(b['call_bounds']['evaluation_calls'] for b in p['bundles'])+sum(s['calls'] for s in schedule)
    limits={**old.LIMITS,'maximum_calls':calls,'token_cap':calls*16384,'solver_seconds':30}
    p.update(components=components,reused_profiles=reused,profile_schedule=schedule,limits=limits,
             wall_policy='4-hour total allocation including startup; unrun cells retained; no automatic extension',
             method_order=['NEUTRAL','JOINT'],owner_order='o0..o(n-1), interleaved methods',solver=dict(seconds=30,threads=1,random_seed=0),
             profile_reuse='earliest compatible v4 profiles first, completed AB algebraic profiles next; no evaluation bills; new contract keys once')
    p['wave_id']=digest(p)
    return p


def transport_tasks(s):return runtime.catalog(s['wave']['components'])


def qualify(snapshot,bank,reused):
    from .composite_math_decoder import qualify as cpu
    wave=make_wave(bank,reused);value=cpu(snapshot,tasks=runtime.catalog(wave['components']))
    value.update(condition=KEY,runtime_identity=identity(),wave_id=wave['wave_id'])
    return value


def check_qualification(q,wave,model):
    from .composite_math_decoder import schema,TaskTransport
    require(q['status']=='passed' and q['condition']==KEY and q['runtime_identity']==identity() and q['wave_id']==wave['wave_id'],'exact wave CPU qualification')
    require(q['metadata']==base.previous.local.METADATA and q['xgrammar_version']=='0.1.32' and q['model_executed'] is False,'pinned grammar metadata')
    require(q['template']==model['non_thinking_verification'],'same non-thinking template')
    tasks=runtime.catalog(wave['components']);require(len(q['rows'])==len(tasks),'all grammar contracts')
    for t,r in zip(tasks,q['rows']):
        require(r['task']==TaskTransport.task_key(t) and r['schema_hash']==digest(schema(t)) and all(r[k] is True for k in ('escaped_text_accepted','extra_key_rejected','malformed_rejected')),'grammar row')


def source_records(s):
    p=s['source_package'];raw=Path(p['path']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==p['sha256'],'statement package integrity')
    rows=json.loads(raw)
    if isinstance(rows,dict):rows=rows.get('statements',rows.get('cards',[]))
    needed={c['source_id']:c for c in s['wave']['components']};values={}
    for row in rows:
        sid=row.get('id',row.get('source_id'))
        if sid not in needed:continue
        require(sid not in values,'duplicate statement');text=row['problem']
        require(hashlib.sha256(text.encode()).hexdigest()==needed[sid]['statement_sha256'],'statement binding')
        values[sid]=text
    require(set(values)==set(needed),'missing authorised source statements')
    return values


def prepare(parent,bank,reused,config,qualification):
    prior=joint.verify_parent(parent);wave=make_wave(bank,reused)
    expected_old={x['key'] for x in wave['profile_coverage'] if x['source_id'] in old.IDS}
    require(expected_old<=reused.keys(),'existing v4/AB profile ledger binding required; do not recollect')
    require(wave['bundles'],'no supported wave')
    require(config['partition']=='NA100q' and config['time']=='04:00:00' and config['memory_gb']==128 and config.get('activation_script') is None,'allocation caps')
    deployment=base.deployment();require(str(Path(config['python']).resolve())==deployment['python'],'execution interpreter')
    s=dict(condition=KEY,parent_release=parent,wave=wave,model=deepcopy(prior['model']),cluster=config,
           source_package=deepcopy(prior['source_package']),runtime_identity=identity(),deployment=deployment,
           decoder_qualification=qualification,limits=wave['limits'],cuda_check=probe.PROBE,
           monetary_cost='unverified local allocation',D2_D6_campaign_enabled=False)
    source_records(s);check_qualification(qualification,wave,s['model'])
    blockers=['environment_mismatch'] if deployment['packages']!=base.EXPECTED_PACKAGES or not deployment['solver_importable'] else []
    return dict(schema='composite-scaling-manifest-v2',scope=s,scope_digest=digest(s),blockers=blockers,execution_allowed=False)


def validate_manifest(m):
    require(m['schema']=='composite-scaling-manifest-v2' and m['scope_digest']==digest(m['scope']),'scope digest')
    s=m['scope'];require(s['condition']==KEY and s['runtime_identity']==identity(),'wave/source binding')
    prior=joint.verify_parent(s['parent_release'])
    require(s['model']==prior['model'] and s['source_package']==prior['source_package'],'pinned model/source provenance')
    w=s['wave'];require(w==make_wave(w['bank'],w['reused_profiles']) and s['limits']==w['limits'],'frozen wave and limits')
    expected_old={x['key'] for x in w['profile_coverage'] if x['source_id'] in old.IDS}
    require(expected_old<=w['reused_profiles'].keys(),'existing v4/AB profile binding missing')
    require(all(w['reused_profiles'][k]['kind']=='historical_profile' for k in expected_old),'historical profile receipts required')
    require(s['cuda_check']==probe.PROBE and s['D2_D6_campaign_enabled'] is False,'bounded dispatch')
    c=base.cluster.ClusterConfig(**s['cluster']);require(c.partition=='NA100q' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'allocation')
    check_qualification(s['decoder_qualification'],w,s['model'])
    return s


def approve(m,a):
    s=validate_manifest(m);require(not m['blockers'],'unresolved deployment')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']=='composite-scaling-approval-v2' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact expanded scope approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'expanded source/contract/GPU permission')
    require(all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema='composite-scaling-release-v2',manifest=m,approval=a);v['release_digest']=digest(v);return v


def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])


class Journal(old.Journal):
    def __init__(self,path,transport,scope,check_source):
        super().__init__(path,transport,scope,check_source,condition=KEY,limits=_scope.get()['limits'])


def run_recipe(journal,sources,out):return runtime.run_wave(journal,sources,out,_scope.get()['wave'])
def blueprint():return dict(schedule=['wave1'])
recipe=SimpleNamespace(Journal=Journal,run_recipe=run_recipe,blueprint=blueprint)
def check_cuda(torch):return probe.check_cuda(torch)
def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def dispatch(v,directory):
    s=validate_release(v);token=_scope.set(s);pt=probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_scope.reset(token);probe._probe_output.reset(pt)
def arguments(c,snapshot,output):
    argv=base.arguments(c,snapshot,output);argv[-4]=str(snapshot/'experiments/run_composite_scaling.sbatch');return argv

def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
