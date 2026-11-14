"""Reuse the accepted shared-registry launcher for one prospective dice/MATH wave."""
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json,sys
from . import composite_dice_next as recipe_impl,composite_common_derivation_launch as common
from . import composite_scaling_runtime as runtime,composite_math as worker
from .joint_schema import require
from .model import digest
from beyond_consensus.experiments.snapshot import verify_snapshot

base=common.base
KEY='composite-dice-boundary-next-math-v1'
_scope=ContextVar(KEY)

def identity():
    root=Path(__file__).resolve().parents[2]
    files=set(common.identity())|{'src/bc_phase2/composite_dice_next.py','src/bc_phase2/composite_dice_next_launch.py',
        'scripts/composite_dice_next.py','experiments/run_composite_dice_next.sbatch'}
    return {p:base.previous.local.file_hash(root/p) for p in sorted(files)}

def historical(run,snapshot):
    run=Path(run).resolve();snapshot=Path(snapshot).resolve();files={}
    def read(path):
        require(not path.is_symlink(),'symlink evidence');raw=path.read_bytes();require(len(raw)<=64*1024*1024,'bounded evidence')
        files[str(path)]=base.previous.local.file_hash(path);return json.loads(raw)
    m=read(run/'manifest.json');release=m['release'];old=release['manifest']
    require(old['scope_digest']==recipe_impl.PARENT_SCOPE==digest(old['scope']),'exact job 1120759 scope')
    require(release['release_digest']==digest({k:v for k,v in release.items() if k!='release_digest'}),'historical release integrity')
    a=release['approval'];require(a['scope_digest']==old['scope_digest'] and a['decision']=='approved' and all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'historical approval')
    marker=verify_snapshot(snapshot);require(marker['manifest_hash']==digest(m) and read(snapshot/'resolved/manifest.json')==m,'original snapshot manifest')
    for name,h in old['scope']['runtime_identity'].items():require(base.previous.local.file_hash(snapshot/name)==h,'historical implementation binding')
    # Freeze workload/neutral before opening any new price observations.
    frozen=recipe_impl.freeze(old['scope']['wave'])
    q=old['scope']['cpu_qualification'];common.check_cpu(q,old['scope']['wave'])
    require(q['template']==old['scope']['model']['non_thinking_verification'],'qualified template')
    # Syntax and field order are unchanged by the new instruction.
    from .composite_math_decoder import schema
    for c in frozen['components']:
        for t in c['tasks']:
            require(schema(recipe_impl.revised_task(c,t,c['reference_mode']))==schema(common.interface.task(t)),'schema compatibility')
    env=read(run/'execution/journal/ledger.json');prices=read(run/'execution/prices.frozen.json');profiles={}
    for c in old['scope']['wave']['components']:
        if c['source_id']==recipe_impl.DICE:continue
        for mode in c['A_modes']:
            slot='profile/'+c['namespace']+'/'+mode
            profiles[slot]=read(run/'execution'/(slot.replace('/','_')+'.json'))
    reused=recipe_impl.import_profiles(old['scope'],env,prices,profiles)
    wave=recipe_impl.attach_prices(frozen,reused)
    return dict(parent_release=release,wave=wave,files=files,snapshot_inventory_digest=digest(marker),run=str(run),snapshot=str(snapshot))

def verify_files(evidence):
    for path,h in evidence['files'].items():require(base.previous.local.file_hash(path)==h,'historical evidence changed')

def prepare(run,snapshot,config):
    h=historical(run,snapshot);old=h['parent_release']['manifest']['scope'];dep=base.deployment()
    s=dict(condition=KEY,history=h,wave=h['wave'],model=deepcopy(old['model']),source_package=deepcopy(old['source_package']),cluster=config,
        deployment=dep,runtime_identity=identity(),limits=h['wave']['limits'],cuda_check=common.placement.probe.PROBE,
        D2_D6_campaign_enabled=False,monetary_cost='unverified local allocation',
        price_compatibility='Exact unchanged public requests, schema/order, model settings and fresh prerequisite profile lineage; original release and receipt retained; dice chain excluded',
        outcome_policy='Known local profile failure blocks dependents; fixed order continues safely; no semantic rejection/resampling; uncertainty stops all')
    blockers=[] if dep['packages']==base.EXPECTED_PACKAGES and dep['solver_importable'] else ['deployment_mismatch']
    m=dict(schema=KEY+'-manifest',scope=s,scope_digest=digest(s),blockers=blockers,execution_allowed=False)
    validate_manifest(m);source_records(s);return m

def validate_manifest(m):
    require(m['schema']==KEY+'-manifest' and digest(m['scope'])==m['scope_digest'] and m['execution_allowed'] is False,'scope integrity')
    s=m['scope'];require(s['condition']==KEY and s['runtime_identity']==identity(),'runtime binding')
    fresh=historical(s['history']['run'],s['history']['snapshot'])
    require(fresh==s['history'] and s['wave']==fresh['wave'] and s['limits']==fresh['wave']['limits'],'bound history and recipe')
    old=fresh['parent_release']['manifest']['scope']
    require(s['model']==old['model'] and s['source_package']==old['source_package'],'model/source exact')
    require(s['cuda_check']==common.placement.probe.PROBE and s['D2_D6_campaign_enabled'] is False,'bounded runtime')
    c=base.cluster.ClusterConfig(**s['cluster'])
    require(c.partition=='HPCAIq' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'reviewed allocation caps')
    require(str(Path(c.python).resolve())==s['deployment']['python'],'interpreter')
    return s

def approve(m,a):
    s=validate_manifest(m);require(not m['blockers'] and s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'deployment')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']==KEY+'-approval' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','new scope approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'scope permissions')
    require(all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema=KEY+'-release',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])
def source_records(s):
    verify_files(s['history']);return common.source_records(s)
def transport_tasks(s):
    return [dict(recipe_impl.revised_task(c,t,c['reference_mode']),source_id=c['source_id']) for c in s['wave']['components'] for t in c['tasks']]
class Journal(worker.Journal):
    def __init__(self,path,transport,scope,check_source):super().__init__(path,transport,scope,check_source,condition=KEY,limits=_scope.get()['limits'])
def run_recipe(journal,sources,out):return runtime.run_wave(journal,sources,out,_scope.get()['wave'],interface=recipe_impl)
recipe=SimpleNamespace(Journal=Journal,run_recipe=run_recipe,blueprint=lambda:dict(schedule=['wave1']))
check_cuda=common.check_cuda
check_scoped_allocation=common.check_scoped_allocation

def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def arguments(c,snapshot,output):
    argv=base.arguments(c,snapshot,output);argv[-4]=str(snapshot/'experiments/run_composite_dice_next.sbatch');return argv
def dispatch(v,directory):
    s=validate_release(v);token=_scope.set(s);pt=common.placement.probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_scope.reset(token);common.placement.probe._probe_output.reset(pt)
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
