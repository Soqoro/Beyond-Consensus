"""Fresh-price common derivation interface, preserving the historical wave baseline."""
from contextvars import ContextVar
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
from . import composite_scaling as spec, composite_scaling_runtime as runtime
from . import composite_scaling_launch as previous, composite_scaling_replacement as placement
from . import composite_derivation_interface as interface, composite_derivation_launch as diagnostic
from . import composite_math as worker
from .joint_schema import require
from .model import digest

base=previous.base
KEY='composite-common-derivation-wave1-v1'
_scope=ContextVar(KEY)
Engine=interface.Engine
coverage=interface.coverage
descriptor=interface.descriptor
check_profile=interface.check_profile

def key(c,t,mode):return digest(descriptor(c,t,mode))

def domain(components,n,prices=None):
    # Only translate the price lookup keys. The accepted optimiser/domain is unchanged.
    translated=None if prices is None else {e['historical_key']:prices[e['key']] for e in coverage(components)}
    return spec.domain(components,n,translated)

def identity():
    root=Path(__file__).resolve().parents[2]
    names=set(previous.identity())|{'src/bc_phase2/composite_common_derivation_launch.py',
        'src/bc_phase2/composite_derivation_interface.py','src/bc_phase2/composite_derivation_diagnostic.py',
        'src/bc_phase2/composite_derivation_launch.py','src/bc_phase2/composite_scaling_replacement.py',
        'scripts/composite_common_derivation_pilot.py','scripts/check_composite_common_derivation.py',
        'scripts/check_composite_derivation_order.py','experiments/run_composite_common_derivation.sbatch'}
    return {p:base.previous.local.file_hash(root/p) for p in sorted(names)}

def prior(parent):
    require(parent['release_digest']==digest({k:v for k,v in parent.items() if k!='release_digest'}),'parent release integrity')
    m=parent['manifest'];require(m['scope_digest']==diagnostic.PARENT_SCOPE==digest(m['scope']),'exact historical wave required')
    return m['scope']

def make_wave(parent_wave):
    require(parent_wave['wave_id']==digest({k:v for k,v in parent_wave.items() if k!='wave_id'}),'historical wave integrity')
    w=deepcopy(parent_wave);w.pop('wave_id');frozen=interface.freeze(w['bank'])
    require(w['components']==sorted(spec.reviewed(w['bank']),key=lambda c:c['source_id']),'same eight components')
    require([(b['n'],b['slot']) for b in w['bundles']]==[(2,1),(4,1),(6,1),(8,1)],'same four conditions')
    ids={}
    for b in w['bundles']:
        old=b['preprice_id'];b['parent_preprice_id']=old
        b['preprice_specification']={'historical':b['preprice_specification'],'interface_digest':frozen['interface_digest']}
        b['preprice_id']=digest(b['preprice_specification']);ids[old]=b['preprice_id']
    for row in w['matrix']:
        if 'preprice_id' in row:row['preprice_id']=ids[row['preprice_id']]
    w['profile_coverage']=coverage(w['components']);w['reused_profiles']={}
    w['profile_schedule']=runtime.schedule_profiles(w['components'],{})
    w['profile_consumers']={e['key']:[b['preprice_id'] for b in w['bundles'] if e['source_id'] in b['sources']] for e in w['profile_coverage']}
    count=sum(s['calls'] for s in w['profile_schedule'])+sum(b['call_bounds']['evaluation_calls'] for b in w['bundles'])
    require(sum(s['calls'] for s in w['profile_schedule'])==16 and count==192,'reviewed call ceiling')
    w['limits'].update(maximum_calls=count,token_cap=count*16384)
    w.update(parent_wave_id=parent_wave['wave_id'],worker_interface=frozen,
        profile_reuse='none; 16 fresh development calls, own prerequisites; no evaluation or diagnostic prices',
        condition=KEY,execution_allowed=False)
    w['wave_id']=digest(w);return w

def check_cpu(q,w):
    from .composite_math_decoder import schema
    require(q['status']=='passed_cpu_checks' and q['interface_digest']==w['worker_interface']['interface_digest'],'CPU interface binding')
    require(q['model_executed'] is False and q['execution_allowed'] is False and q['xgrammar_version']=='0.1.32','CPU qualification only')
    require(q['metadata']==base.previous.local.METADATA and q['versions']==base.previous.local.VERSIONS,'metadata and packages')
    root=Path(__file__).resolve().parents[2]
    expected=('scripts/check_composite_common_derivation.py','scripts/check_composite_derivation_order.py','src/bc_phase2/composite_derivation_interface.py','src/bc_phase2/composite_math_decoder.py')
    require(q['implementation_hashes']=={p:base.previous.local.file_hash(root/p) for p in expected},'qualified schema implementation changed')
    require(q['bank_file_sha256']==base.previous.local.file_hash(root/'configs/phase2/composite_scaling_bank_v2.json'),'bank bytes')
    schemas={digest(schema(t)):schema(t) for t in interface.transport_tasks(w['components'])}
    require(len(q['rows'])==len(schemas)==9 and q['task_count']==14 and q['profile_entries']==16,'complete schema coverage')
    require({r['schema_hash'] for r in q['rows']}==set(schemas),'schema set')
    for r in q['rows']:
        require(r['schema']==schemas[r['schema_hash']] and r['passed'] is True,'schema content')
        require([o['eos'] for o in r['observations']]==[248046,248044],'EOS coverage')
        for o in r['observations']:
            checks=o['checks']
            require(all(checks['derivation_first'][k] is True for k in ('string_plus_eos','tokens_plus_eos','roundtrip_exact')),'positive controls')
            for name in ('derivation_last','extra_key','missing_field','malformed'):
                require(all(checks[name][k] is False for k in ('string_plus_eos','tokens_plus_eos')),'negative controls')

def source_records(s):return previous.source_records(s)
def transport_tasks(s):return interface.transport_tasks(s['wave']['components'])

def prepare(parent,config,q):
    old=prior(parent);w=make_wave(old['wave']);dep=base.deployment()
    s=dict(condition=KEY,parent_release=parent,wave=w,model=deepcopy(old['model']),source_package=deepcopy(old['source_package']),
        cluster=config,deployment=dep,runtime_identity=identity(),cpu_qualification=q,limits=w['limits'],cuda_check=placement.probe.PROBE,
        D2_D6_campaign_enabled=False,monetary_cost='unverified local allocation',
        limitations=['Four-hour deadline may leave conditions unrun; no automatic continuation.',
          'Structural completion is not mathematical correctness; blinded review remains required.',
          'Existing gecko completeness and producer/consumer overlap concerns remain unresolved.',
          'Fresh profiles are per-instance development proxies, not independent calibration.',
          'Full requests with generated parents are checked before each dispatch, not worst-case qualified.'])
    blockers=[] if dep['packages']==base.EXPECTED_PACKAGES and dep['solver_importable'] else ['deployment_mismatch']
    m=dict(schema=KEY+'-manifest',scope=s,scope_digest=digest(s),blockers=blockers,execution_allowed=False)
    validate_manifest(m);source_records(s);return m

def validate_manifest(m):
    require(m['schema']==KEY+'-manifest' and m['scope_digest']==digest(m['scope']) and m['execution_allowed'] is False,'disabled scope integrity')
    s=m['scope'];old=prior(s['parent_release'])
    require(s['condition']==KEY and s['runtime_identity']==identity(),'implementation binding')
    require(s['wave']==make_wave(old['wave']) and s['limits']==s['wave']['limits'],'fresh profile recipe')
    require(s['model']==old['model'] and s['source_package']==old['source_package'],'model and source preservation')
    require(s['cuda_check']==placement.probe.PROBE and s['D2_D6_campaign_enabled'] is False,'bounded runtime')
    c=base.cluster.ClusterConfig(**s['cluster'])
    require(c.partition=='HPCAIq' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'one reviewed placement')
    require(str(Path(c.python).resolve())==s['deployment']['python'],'interpreter binding')
    check_cpu(s['cpu_qualification'],s['wave'])
    require(s['cpu_qualification']['template']==s['model']['non_thinking_verification'],'nonthinking template')
    return s

def approve(m,a):
    s=validate_manifest(m);require(not m['blockers'],'unresolved deployment')
    require(s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'qualified deployment')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']==KEY+'-approval' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact new scope approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'explicit permissions')
    require(all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema=KEY+'-release',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])

class Journal(worker.Journal):
    def __init__(self,path,transport,scope,check_source):
        super().__init__(path,transport,scope,check_source,condition=KEY,limits=_scope.get()['limits'])

def run_recipe(journal,sources,out):
    return runtime.run_wave(journal,sources,out,_scope.get()['wave'],interface=sys.modules[__name__])
recipe=SimpleNamespace(Journal=Journal,run_recipe=run_recipe,blueprint=lambda:dict(schedule=['wave1']))
def check_cuda(torch):
    require(torch.cuda.get_device_properties(0).name=='NVIDIA A100 80GB PCIe','HPCAIq hardware binding')
    return placement.probe.check_cuda(torch)
def check_scoped_allocation(record,s):placement.check_allocation(record,s['cluster']['partition'])
def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def dispatch(v,directory):
    s=validate_release(v);token=_scope.set(s);pt=placement.probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_scope.reset(token);placement.probe._probe_output.reset(pt)
def arguments(c,snapshot,output):
    argv=base.arguments(c,snapshot,output);argv[-4]=str(snapshot/'experiments/run_composite_common_derivation.sbatch');return argv
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
