"""Opt-in two-method scope using the existing composite registry/Slurm launcher."""
from copy import deepcopy
from pathlib import Path
import sys
from . import composite_joint as recipe, composite_math as v4, composite_math_launch as base
from .model import digest
from .joint_schema import require
from beyond_consensus.experiments import cluster

KEY=recipe.CONDITION
PARENT_SCOPE='4cddbe4903c48ceb150ddaa9d36777a9d1d53966d5fe2dd8eb536a989c028f34'

def identity():
    root=Path(__file__).resolve().parents[2];files=set(base.identity())|{
        'src/bc_phase2/composite_joint.py','src/bc_phase2/composite_joint_launch.py',
        'scripts/composite_joint_pilot.py','experiments/run_composite_joint.sbatch',
        'src/bc_phase2/composite_joint_replacement.py','scripts/reconcile_composite_joint_failure.py'}
    return {p:base.previous.local.file_hash(root/p) for p in sorted(files)}

def qualify(snapshot):
    from .composite_math_decoder import qualify as check
    value=check(snapshot)
    value.update(condition=KEY,runtime_identity=identity())
    return value

def check_qualification(q):
    from .composite_math_decoder import schema
    require(q['schema']=='composite-json-cpu-v1' and q['condition']==KEY and q['status']=='passed','joint qualification')
    require(q['runtime_identity']==identity() and q['xgrammar_version']=='0.1.32','qualification source binding')
    require(q['metadata']==base.previous.local.METADATA and q['model_executed'] is False,'pinned metadata')
    require([r['task'] for r in q['rows']]==[t['id'] for t in v4.TASKS],'all task schemas')
    for t,r in zip(v4.TASKS,q['rows']):
        require(r['schema_hash']==digest(schema(t)) and all(r[k] is True for k in ['escaped_text_accepted','extra_key_rejected','malformed_rejected']),'grammar controls')

def verify_parent(parent):
    require(parent['release_digest']==digest({k:v for k,v in parent.items() if k!='release_digest'}),'parent release integrity')
    m=parent['manifest'];s=m['scope']
    require(m['scope_digest']==digest(s)==PARENT_SCOPE,'exact v4 provenance')
    require(s['blueprint']==v4.blueprint(),'v4 common task/prompt contract changed')
    return s

def prepare(parent,config,qualification):
    old=verify_parent(parent);source_records(old);check_qualification(qualification)
    require(qualification['template']==old['model']['non_thinking_verification'],'same template')
    cfg=cluster.ClusterConfig(**config)
    require(cfg.partition=='NA100q' and cfg.time=='04:00:00' and cfg.memory_gb==128 and cfg.activation_script is None,'allocation limits')
    dep=base.deployment();require(str(Path(cfg.python).resolve())==dep['python'],'actual execution interpreter')
    scope=dict(condition=KEY,parent_scope=PARENT_SCOPE,blueprint=recipe.blueprint(),
        domain=recipe.domain(),source_package=deepcopy(old['source_package']),model=deepcopy(old['model']),
        limits=recipe.LIMITS,cluster=config,deployment=dep,runtime_identity=identity(),decoder_qualification=qualification,
        mode_coverage=recipe.coverage(),objective='mean_first',methods=list(recipe.METHODS),
        quality='blinded human; declared final fields; unknown until reviewed; no model judge',
        profile_reuse='none; fresh seven calls; no fallback; no evaluation data to selector',
        source_permission='prior source locations/provenance only; new transmission requires exact approval',
        monetary_cost='unverified local allocation; no cloud API',D2_D6_campaign_enabled=False)
    blockers=[] if dep['solver_importable'] else ['execution_python_ortools_unavailable']
    blockers.extend('execution_package_mismatch:'+k for k,v in base.EXPECTED_PACKAGES.items() if dep['packages'].get(k)!=v)
    return dict(schema='composite-joint-manifest-v1',scope=scope,scope_digest=digest(scope),blockers=blockers,execution_allowed=False)

def validate_manifest(m):
    require(m['schema']=='composite-joint-manifest-v1' and digest(m['scope'])==m['scope_digest'],'scope integrity')
    s=m['scope'];require(s['condition']==KEY and s['parent_scope']==PARENT_SCOPE,'condition binding')
    require(s['blueprint']==recipe.blueprint() and s['domain']==recipe.domain() and s['limits']==recipe.LIMITS and s['mode_coverage']==recipe.coverage(),'frozen common domain')
    require(s['methods']==list(recipe.METHODS) and s['runtime_identity']==identity(),'methods/source binding')
    require(s['model']['checkpoint']==recipe.WORKER_POLICY['checkpoint'] and s['model']['revision']==recipe.WORKER_POLICY['revision'],'pinned checkpoint')
    for key in ('thinking','do_sample','dtype','attention'):require(s['model'][key]==recipe.WORKER_POLICY[key],'generation policy')
    c=cluster.ClusterConfig(**s['cluster']);require(c.partition=='NA100q' and c.time=='04:00:00' and c.memory_gb==128 and c.activation_script is None,'resources')
    check_qualification(s['decoder_qualification'])
    require(s['decoder_qualification']['template']==s['model']['non_thinking_verification'],'template binding')
    return s

def approve(m,a):
    validate_manifest(m);require(not m['blockers'],'deployment blockers')
    require(set(a)=={'schema','decision','scope_digest','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'external exact approval fields')
    require(a['schema']=='composite-joint-approval-v1' and a['decision']=='approved' and a['scope_digest']==m['scope_digest'],'new exact two-method approval required')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'scope consent')
    require(all(type(a[k]) is str and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema='composite-joint-release-v1',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity')
    return validate_manifest(v['manifest'])

def source_records(scope):return base.source_records(scope)
def arguments(c,snapshot,output):
    argv=base.arguments(c,snapshot,output);argv[-4]=str(snapshot/'experiments/run_composite_joint.sbatch');return argv

def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def dispatch(v,directory):return base.dispatch(v,directory,protocol=sys.modules[__name__])
def submit(root,value,*,dry_run=True):return base.submit(root,value,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
