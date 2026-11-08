"""One evidence-bound replacement of pre-model CUDA failure 1117531. No retries."""
from copy import deepcopy
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from . import composite_scaling_launch as original
from . import composite_joint_replacement as probe
from .model import digest
from .joint_schema import require
from beyond_consensus.util import read_json
from beyond_consensus.experiments.snapshot import verify_snapshot

base=original.base
recipe=original.recipe
JOB='1117531'
SCOPE='ed9f30f303eb4dc5f23d707182262cf1cc4fe58dfc78216e9f90b3ce776e5960'
KEY=original.KEY+'-replacement-'+JOB+'-once'

def failed_accounting(text):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    top = [r for r in rows if r[0] == JOB + '_0']
    require(len(top) == 1 and top[0][1:3] == ['FAILED', '1:0'],
            'exact terminal array-task failure missing')
    require(all(r[0] == JOB + '_0' or r[0].startswith(JOB + '_0.') for r in rows),
            'unexpected accounting job')


def inspect(output, registry, accounting):
    files = {}

    def read(path, as_json=True):
        require(not path.is_symlink(), 'symlink evidence forbidden')
        raw = path.read_bytes()
        files[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw) if as_json else raw.decode('utf8')

    state = read(registry)
    require(not state.get('uncertain_submission'), 'uncertain submission')
    record = state.get('composite_math_attempts', {}).get(original.KEY, {})
    require(record.get('job_id') == JOB and record.get('scope_digest') == SCOPE
            and record.get('state') == 'submitted_no_retry', 'original attempt binding')
    require(Path(record['output']).resolve() == output.resolve(), 'output binding')
    snapshot = Path(record['snapshot'])
    marker = verify_snapshot(snapshot)
    manifest = read(output / 'manifest.json')
    require(manifest == read(snapshot / 'resolved/manifest.json')
            and marker['manifest_hash'] == digest(manifest), 'snapshot manifest binding')
    release = manifest['release']
    require(release['release_digest'] == record['release_digest']
            == digest({k: v for k, v in release.items() if k != 'release_digest'}),
            'release integrity')
    require(release['manifest']['scope_digest'] == SCOPE
            == digest(release['manifest']['scope']), 'scope integrity')
    execution = output / 'execution'
    require(not execution.is_symlink() and
            {p.name for p in execution.iterdir()} ==
            {'startup.json', 'failure.json', 'recipe-state.json', 'cuda-access.json'},
            'unexpected execution evidence; inference cannot be excluded')
    startup = read(execution / 'startup.json')
    require(startup == dict(scope_digest=SCOPE, state='started_no_retry'), 'startup binding')
    failure = read(execution / 'failure.json')
    require(failure['error_type'] == 'AcceleratorError' and
            'CUDA-capable device(s) is/are busy or unavailable' in failure['error'] and
            failure['totals'] is None and failure['retry_allowed'] is False, 'failure mismatch')
    slots = read(execution / 'recipe-state.json')
    schedule = ['wave1']
    require(slots['status'] == 'halted' and set(slots['slots']) == set(schedule)
            and all(v == 'unrun' for v in slots['slots'].values()), 'attempted or missing slots')
    stderr = read(output / 'logs' / (JOB + '_0.err'), False)
    require("torch.empty(1,dtype=torch.uint8,device='cuda:0')" in stderr and
            'CUDA-capable device(s) is/are busy or unavailable' in stderr,
            'expected placement traceback absent')
    code = read(snapshot / 'src/bc_phase2/composite_math_launch.py', False)
    require('sources=p.source_records(s);transport=p.open_transport(v)' in code and
            code.index('sources=p.source_records(s);transport=p.open_transport(v)') <
            code.index('journal=implementation.Journal('), 'journal order changed')
    probe_record = read(execution/'cuda-access.json')
    require(probe_record['contract']==probe.PROBE and probe_record['state']=='failed'
            and probe_record['model_executed'] is False and probe_record['job_id']==JOB
            and probe_record['error_type']=='AcceleratorError'
            and 'CUDA-capable device(s) is/are busy or unavailable' in probe_record['error'], 'CUDA probe evidence')
    require(code.index('p.check_cuda(torch)') < code.index('tokenizer=AutoTokenizer.from_pretrained')
            < code.index('model=Qwen3_5ForConditionalGeneration.from_pretrained'), 'probe must precede loading')
    blockers = []
    try:
        require(accounting['returncode'] == 0, 'accounting unavailable')
        failed_accounting(accounting['stdout'])
    except Exception as exc:
        blockers.append(str(exc))
    require(hashlib.sha256(registry.read_bytes()).hexdigest() == files[str(registry)],
            'registry changed during inspection')
    return dict(schema='composite-scaling-cuda-reconciliation-v1',
                status='blocked' if blockers else 'verified_for_replacement_review',
                scope_digest=SCOPE, failed_attempt=record, input_hashes=files,
                snapshot_inventory_verified=True, no_request_journal=True,
                inference_dispatch_observed=False, startup_resources={k: failure[k] for k in
                ('cpu_seconds', 'wall_seconds')}, scheduler=accounting, blockers=blockers,
                registry_changed=False, replacement_authorized=False,
                replacement_submitted=False, execution_allowed=False)


def accounting():
    try:
        c=subprocess.run(['sacct','--noheader','--parsable2','-j',JOB,
            '--format=JobID,State,ExitCode,Elapsed,NodeList,ReqTRES,AllocTRES'],capture_output=True,text=True,timeout=30)
        return dict(returncode=c.returncode,stdout=c.stdout,stderr=c.stderr)
    except (OSError,subprocess.TimeoutExpired) as exc:
        return dict(returncode=None,stdout='',stderr=str(exc))


def recheck(report,state):
    require(report['status']=='verified_for_replacement_review' and not report['blockers'],'verified pre-model failure required')
    require(report['scope_digest']==SCOPE and report['replacement_authorized'] is False
            and report['execution_allowed'] is False,'reconciliation is not approval')
    require(KEY not in state.get('composite_math_attempts',{}),'replacement already consumed')
    require(state.get('composite_math_attempts',{}).get(original.KEY)==report['failed_attempt'],'original attempt changed')
    require(not state.get('uncertain_submission'),'uncertain submission')
    fresh=inspect(Path(report['failed_attempt']['output']),base.cluster.registry_root()/'registry.json',accounting())
    require(fresh['status']=='verified_for_replacement_review' and probe.stable_report(fresh)==probe.stable_report(report),'failure evidence changed')


def identity():
    root=Path(__file__).resolve().parents[2]
    files={'src/bc_phase2/composite_scaling_replacement.py','scripts/composite_scaling_replacement.py','experiments/run_composite_scaling_replacement.sbatch'}
    return {**original.identity(),**{p:base.previous.local.file_hash(root/p) for p in sorted(files)}}


def prior_scope(v):
    require(v['manifest']['scope_digest']==SCOPE,'only original failed wave')
    return original.validate_release(v)


def prepare(previous,report,output_root,*,partition=None):
    old=prior_scope(previous)
    recheck(report,read_json(base.cluster.registry_root()/'registry.json'))
    require(report['failed_attempt']['release_digest']==previous['release_digest'],'failed release binding')
    require(base.deployment()==old['deployment'],'execution environment changed')
    original.source_records(old)
    s=deepcopy(old);s['cluster']['output_root']=str(Path(output_root).resolve());s['runtime_identity']=identity()
    s['replacement']=dict(maximum_replacements=1,previous_release=previous,reconciliation=report)
    if partition not in (None,old['cluster']['partition']):
        require(partition=='HPCAIq','only the reviewed HPCAIq alternative')
        s['cluster']['partition']=partition
        s['replacement']['placement']=capture_placement()
    m=dict(schema='composite-scaling-replacement-manifest-v1',scope=s,scope_digest=digest(s),blockers=[],execution_allowed=False)
    validate_manifest(m);return m


def validate_manifest(m):
    require(m['schema']=='composite-scaling-replacement-manifest-v1' and m['scope_digest']==digest(m['scope']),'replacement scope integrity')
    require(not m['blockers'] and m['execution_allowed'] is False,'disabled manifest')
    s=m['scope'];r=s['replacement']
    require(set(r) in ({'maximum_replacements','previous_release','reconciliation'},{'maximum_replacements','previous_release','reconciliation','placement'}) and type(r['maximum_replacements']) is int and r['maximum_replacements']==1,'single replacement')
    old=prior_scope(r['previous_release'])
    exclude={'cluster','runtime_identity','replacement'}
    require({k:v for k,v in old.items() if k not in exclude}=={k:v for k,v in s.items() if k not in exclude},'wave, qualification or resources changed')
    require(s['runtime_identity']==identity(),'replacement implementation changed')
    allowed={'output_root'}
    if 'placement' in r:
        validate_placement(r['placement'])
        require(old['cluster']['partition']=='NA100q' and s['cluster']['partition']=='HPCAIq','exact partition amendment')
        allowed.add('partition')
    require({k:v for k,v in old['cluster'].items() if k not in allowed}=={k:v for k,v in s['cluster'].items() if k not in allowed},'cluster changed')
    require(Path(s['cluster']['output_root']).resolve()!=Path(old['cluster']['output_root']).resolve(),'fresh output root required')
    report=r['reconciliation']
    require(report['status']=='verified_for_replacement_review' and not report['blockers']
            and report['scope_digest']==SCOPE and report['failed_attempt']['job_id']==JOB
            and report['failed_attempt']['release_digest']==r['previous_release']['release_digest'],'reconciled prior attempt')
    return s


def approve(m,a):
    validate_manifest(m)
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']=='composite-scaling-replacement-approval-v1' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact replacement approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'replacement consent')
    require(all(type(a[k]) is str and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema='composite-scaling-replacement-release-v1',manifest=m,approval=a);v['release_digest']=digest(v);return v


def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release integrity');return validate_manifest(v['manifest'])


def submission_check(v,state):
    s=validate_release(v);recheck(s['replacement']['reconciliation'],state)
    if 'placement' in s['replacement']:capture_placement()
def source_records(s):return original.source_records(s)
def transport_tasks(s):return original.transport_tasks(s)
def check_cuda(torch):
    if original._scope.get()['cluster']['partition']=='HPCAIq':
        require(torch.cuda.get_device_properties(0).name=='NVIDIA A100 80GB PCIe','approved HPCAIq GPU model changed')
    return probe.check_cuda(torch)
def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def arguments(c,snapshot,output):
    argv=base.arguments(c,snapshot,output);argv[-4]=str(snapshot/'experiments/run_composite_scaling_replacement.sbatch');return argv

def dispatch(v,directory):
    s=validate_release(v);token=original._scope.set(s);pt=probe._probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:original._scope.reset(token);probe._probe_output.reset(pt)
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])



def fields(record):return dict(re.findall(r'(\w+)=([^\s]+)',record))


def validate_placement(p):
    require(set(p)=={'partition','node','partition_record','node_record','hardware_required','binding_digest'},'placement fields')
    require(p['binding_digest']==digest({k:v for k,v in p.items() if k!='binding_digest'}),'placement digest')
    require(p['partition']=='HPCAIq' and p['node']=='node14' and p['hardware_required']=='NVIDIA A100 80GB PCIe','reviewed placement only')
    part=fields(p['partition_record']);node=fields(p['node_record'])
    require(part.get('PartitionName')=='HPCAIq' and part.get('Nodes')=='node14' and part.get('State')=='UP','partition record')
    require(node.get('NodeName')=='node14' and 'HPCAIq' in node.get('Partitions','').split(',') and 'gpu:8' in node.get('Gres',''),'node membership')
    require(node.get('State') in ('IDLE','MIXED','ALLOCATED'),'node down/draining/unavailable')
    require(int(node.get('RealMemory','0'))>=128*1024,'host memory capacity')
    # FreeMem/GPU counts are transient observations, not promises of allocation/access.


def capture_placement():
    p=dict(partition='HPCAIq',node='node14',hardware_required='NVIDIA A100 80GB PCIe',
        partition_record=base.cluster.command(['scontrol','show','partition','HPCAIq','-o']),
        node_record=base.cluster.command(['scontrol','show','node','node14','-o']))
    p['binding_digest']=digest(p);validate_placement(p);return p


def check_allocation(record,partition):
    f=fields(record)
    require(partition in ('NA100q','HPCAIq') and f.get('Partition')==partition,'allocated partition differs from approval')
    if partition=='HPCAIq':require(f.get('NodeList')=='node14','approved HPCAIq node changed')
    require(f.get('NumNodes')=='1' and f.get('NumCPUs')=='4' and f.get('TimeLimit')=='04:00:00','allocated scheduler resources changed')
    tres=dict(item.split('=',1) for item in f.get('ReqTRES','').split(',') if '=' in item)
    require(tres.get('cpu')=='4' and tres.get('gres/gpu')=='1' and tres.get('mem') in ('128G','131072M'),'requested resources changed')


def run_allocated(root,output):
    # Same snapshot/registry/environment guards as the accepted launcher, with
    # the exact approved partition checked instead of its historical NA100q literal.
    require(os.environ.get('SLURM_JOB_ID'),'allocation required')
    root=Path(root);output=Path(output);marker=verify_snapshot(root)
    manifest=read_json(root/'resolved/manifest.json')
    require(manifest.get('schema')=='composite-r0-slurm-v1','expanded snapshot required')
    value=manifest['release'];scope=validate_release(value);key=value['manifest']['scope_digest']
    config=base.cluster.ClusterConfig(**scope['cluster'])
    require(read_json(root/'resolved/cluster.json')==base.plain(config),'cluster binding')
    require(output.resolve()==(Path(config.output_root)/('composite-'+key)).resolve(),'output binding')
    require(read_json(output/'manifest.json')==manifest and marker['manifest_hash']==digest(manifest),'snapshot manifest binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','single array task')
    with base.directory_lock(base.cluster.registry_root()/'.submission.lock'):
        state=read_json(base.cluster.registry_root()/'registry.json')
    record=state.get('composite_math_attempts',{}).get(KEY,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry'
            and record.get('release_digest')==value['release_digest'] and record.get('scope_digest')==key
            and Path(record.get('snapshot','')).resolve()==root.resolve()
            and Path(record.get('output','')).resolve()==output.resolve(),'registered expanded job')
    check_allocation(base.cluster.command(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o']),config.partition)
    active=base.cluster.active_gpu_jobs()
    require(active and all(j.split('_')[0]==job and count==1 for j,count in active.items()),'exclusive one-GPU campaign')
    require(base.environment_inventory(config.python)==read_json(root/'resolved/environment.json'),'environment changed')
    return dispatch(value,output/'execution')
