"""One evidence-bound replacement of job 1115702; original registry entry retained."""
from contextvars import ContextVar
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import time
from . import composite_joint_launch as joint
from .joint_schema import require
from .model import digest
from beyond_consensus.util import atomic_json, read_json

base = joint.base
recipe = joint.recipe
KEY = joint.KEY + '-replacement-1115702-once'
SCOPE = 'ec01b31b5b2f2beb379571cf4e641d57fd905c1cdf5cbac5dbc8693801d96364'
PROBE = dict(version='cuda-allocation-v1', device='cuda:0', elements=1,
             dtype='uint8', synchronize=True, model_executed=False,
             qualification=False, charged_to_stage_resources=True)
_probe_output = ContextVar('composite_probe_output')


def auditor():
    path = Path(__file__).resolve().parents[2] / 'scripts/reconcile_composite_joint_failure.py'
    spec = importlib.util.spec_from_file_location('_composite_failure_auditor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_previous(v):
    require(v['release_digest'] == digest({k:x for k,x in v.items() if k!='release_digest'}), 'prior release integrity')
    require(v['manifest']['scope_digest'] == SCOPE == digest(v['manifest']['scope']), 'only failed exact scope')
    return v['manifest']['scope']


def stable_report(r):
    value = deepcopy(r)
    # Other campaigns may update registry metadata; exact old attempt is still checked.
    value['input_hashes'] = {k:v for k,v in value['input_hashes'].items() if not k.endswith('/registry.json')}
    value.pop('scheduler', None)
    return value


def recheck(report, state):
    require(report['status']=='verified_for_replacement_review' and not report['blockers'], 'verified reconciliation required')
    require(report['scope_digest']==SCOPE and report['replacement_authorized'] is False
            and report['execution_allowed'] is False, 'reconciliation not approval')
    require(KEY not in state.get('composite_math_attempts',{}), 'replacement already consumed')
    require(state.get('composite_math_attempts',{}).get(joint.KEY)==report['failed_attempt'], 'original attempt changed')
    require(not state.get('uncertain_submission'), 'uncertain submission')
    c = subprocess.run(['sacct','--noheader','--parsable2','-j','1115702',
        '--format=JobID,State,ExitCode,Elapsed,NodeList,ReqTRES,AllocTRES'],
        capture_output=True,text=True,timeout=30)
    accounting = dict(returncode=c.returncode,stdout=c.stdout,stderr=c.stderr)
    fresh = auditor().inspect(Path(report['failed_attempt']['output']),
                             base.cluster.registry_root()/'registry.json',accounting)
    require(fresh['status']=='verified_for_replacement_review' and stable_report(fresh)==stable_report(report),
            'failed evidence or terminal state changed')


def prepare(previous, report, config, qualification):
    old = validate_previous(previous)
    registry = base.cluster.registry_root()/'registry.json'
    recheck(report, read_json(registry))
    require(report['failed_attempt']['release_digest']==previous['release_digest'], 'reconciled release mismatch')
    joint.check_qualification(qualification)
    joint.source_records(old)
    require({k:v for k,v in config.items() if k!='output_root'} ==
            {k:v for k,v in old['cluster'].items() if k!='output_root'}, 'only output directory may change')
    require(config['output_root']!=old['cluster']['output_root'], 'fresh output root required')
    s = deepcopy(old)
    s.update(cluster=config, runtime_identity=joint.identity(), decoder_qualification=qualification,
             deployment=base.deployment(), replacement=dict(maximum_replacements=1,
             previous_release=previous, reconciliation=report, cuda_check=PROBE))
    require(s['deployment']==old['deployment'], 'execution environment changed')
    value = dict(schema='composite-joint-manifest-v1',scope=s,scope_digest=digest(s),blockers=[],execution_allowed=False)
    validate_manifest(value)
    return value


def validate_manifest(m):
    s = joint.validate_manifest(m)
    r = s['replacement']
    require(set(r)=={'maximum_replacements','previous_release','reconciliation','cuda_check'} and
            type(r['maximum_replacements']) is int and r['maximum_replacements']==1 and r['cuda_check']==PROBE,
            'one fixed replacement and CUDA check')
    old = validate_previous(r['previous_release'])
    exclude={'runtime_identity','decoder_qualification','replacement','cluster'}
    require({k:v for k,v in s.items() if k not in exclude}=={k:v for k,v in old.items() if k not in exclude},
            'scientific or resource scope changed')
    require({k:v for k,v in s['cluster'].items() if k!='output_root'}==
            {k:v for k,v in old['cluster'].items() if k!='output_root'}, 'cluster changed')
    require(s['cluster']['output_root']!=old['cluster']['output_root'], 'fresh output root required')
    require(r['reconciliation']['failed_attempt']['release_digest']==r['previous_release']['release_digest'], 'prior receipt binding')
    return s


def approve(m,a):
    validate_manifest(m)
    return joint.approve(m,a)


def validate_release(v):
    require(v==approve(v['manifest'],v['approval']), 'replacement exact approval')
    return validate_manifest(v['manifest'])


def submission_check(v,state):
    s = validate_release(v)
    recheck(s['replacement']['reconciliation'],state)


def check_cuda(torch):
    """One byte allocated, synchronised and freed; no forward or model loading."""
    path = _probe_output.get()/'cuda-access.json'
    wall = time.monotonic(); cpu = time.process_time()
    record = dict(contract=PROBE, state='started', CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),
                  job_id=os.environ.get('SLURM_JOB_ID'), model_executed=False)
    atomic_json(path,record)
    try:
        buffer = torch.empty(1,dtype=torch.uint8,device='cuda:0')
        torch.cuda.synchronize()
        del buffer
        torch.cuda.empty_cache()
        record['state']='passed'
    except BaseException as exc:
        record.update(state='failed',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        record.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall)
        atomic_json(path,record)


def source_records(s):return joint.source_records(s)
def arguments(c,snapshot,output):return joint.arguments(c,snapshot,output)
def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def dispatch(v,directory):
    token = _probe_output.set(Path(directory))
    try:return base.dispatch(v,directory,protocol=sys.modules[__name__])
    finally:_probe_output.reset(token)
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,output):return base.run_allocated(root,output,protocol=sys.modules[__name__])
