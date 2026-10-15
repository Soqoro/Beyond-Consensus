"""One approved matched pair, two fresh child processes, four synthetic calls max."""
from copy import deepcopy
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from ..util import BCError, digest, read_json, atomic_json
from ..models.competence import require_qualification
from ..models.action_schema import decoder_schema
from .manifest import source_revision
from . import rr_unique_preflight as unique

SCHEMA='rr-decoder-diagnostic-v1'
PROTOCOL='rr-native-unique-launch-blocking-pair-v1'
PARENT='a3aadd6913fb1f2968de6c735183c65f48dfd2cf36c0c9c7c2ed724c6d959a32'
NATIVE='reporecourse-json-reliable-v1-pool-7'
ARMS=('native','guarded')
require=unique.require


def selected_cases():return unique.cases()[:2]
def model(arm):return replace(unique.model(),action_constraint=NATIVE if arm=='native' else unique.MODE)


def approval_template(proposal):
    return dict(schema='rr-decoder-diagnostic-approval-v1',proposal_id=proposal['experiment_id'],
        scope_hash=digest({k:v for k,v in proposal.items() if k not in ('experiment_id','approval')}),
        decision='pending',reviewer=None,reviewed_at=None,maximum_calls=4,
        limitations_accepted=['synthetic_only','launch_blocking_debug_not_production_qualification',
            'fresh_process_per_arm','no_retry','trajectory_divergence_not_token_causal_proof'])


def build(root,guarded,native,controls,parent_manifest,parent_report):
    unique.check_controls(root,controls)
    require('test_rr_decoder_diagnostic.py' in controls.get('patterns',[]),'Matched diagnostic controls missing')
    require(parent_manifest.get('experiment_id')==PARENT and
        parent_manifest['experiment_id']==digest({k:v for k,v in parent_manifest.items() if k!='experiment_id'}) and
        parent_report.get('experiment_id')==PARENT and parent_report.get('manifest_hash')==digest(parent_manifest),
        'Original failed attempt provenance differs')
    require(parent_report.get('command_failed') is True,'Expected immutable failed parent')
    require(parent_manifest.get('model')==asdict(unique.model()),'Original model/settings changed')
    original_packages=(parent_report.get('runtime') or {}).get('dependencies',{})
    current_packages=guarded.get('decoder_qualification',{}).get('packages',{})
    require(original_packages and all(current_packages.get(k)==v for k,v in original_packages.items()),
        'Pinned parent runtime differs; no dependency upgrade in this diagnostic')
    parent_cases=[dict(id=r['id'],input_tokens=r.get('input_tokens'),prompt_hash=r.get('prompt_hash'),
        rendered_input_ids_hash=(r.get('generation') or {}).get('diagnostics',{}).get('rendered_input_ids_hash'))
        for r in parent_report.get('calls',[]) if r.get('id') in ('nested_mapping','escaped_keys')]
    m=dict(schema=SCHEMA,protocol=PROTOCOL,source_revision=source_revision(root),model=asdict(unique.model()),
        model_lock_sha256=digest(guarded),native_lock=native,controls=controls,
        parent_runtime_packages=original_packages,parent_experiment=PARENT,parent_manifest_hash=digest(parent_manifest),parent_report_hash=digest(parent_report),
        parent_cases=parent_cases,cases=selected_cases(),arms=list(ARMS),maximum_calls=4,
        maximum_calls_per_arm=2,maximum_logical_tokens=65536,shards=1,episodes=[],planned_episodes=0,
        task_inputs_used=False,task_execution_allowed=False,sql_executed=False,debug_environment={'CUDA_LAUNCH_BLOCKING':'1'},
        reconstruction='Original synthetic messages reconstructed verbatim from fixed cases; original rendered token IDs unavailable. Hash/count comparison recorded before dispatch.',
        models={a:asdict(model(a)) for a in ARMS},approval=None)
    m['experiment_id']=digest(m);check(m,root,guarded);return m


def approve(proposal,approval):
    validate(proposal)
    expected=approval_template(proposal)
    require(proposal.get('approval') is None,'Proposal already approved')
    require({k:v for k,v in approval.items() if k not in ('decision','reviewer','reviewed_at')}==
            {k:v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')} and
            approval.get('decision')=='approved' and bool(approval.get('reviewer')) and bool(approval.get('reviewed_at')),
            'Exact diagnostic approval required')
    m=deepcopy(proposal);m['approval']=approval;m['experiment_id']=digest({k:v for k,v in m.items() if k!='experiment_id'})
    validate(m);return m


def validate(m):
    require(m.get('schema')==SCHEMA and m.get('experiment_id')==digest({k:v for k,v in m.items() if k!='experiment_id'}),'Diagnostic identity changed')
    fixed=dict(protocol=PROTOCOL,model=asdict(unique.model()),cases=selected_cases(),arms=list(ARMS),maximum_calls=4,
        maximum_calls_per_arm=2,maximum_logical_tokens=65536,shards=1,episodes=[],planned_episodes=0,
        task_inputs_used=False,task_execution_allowed=False,sql_executed=False,parent_experiment=PARENT,
        debug_environment={'CUDA_LAUNCH_BLOCKING':'1'},models={a:asdict(model(a)) for a in ARMS})
    for key,value in fixed.items():
        require(type(m.get(key)) is type(value) and m[key]==value,'Diagnostic scope changed: '+key)
    if m.get('approval'):
        proposal=deepcopy(m);proposal['approval']=None;proposal['experiment_id']=digest({k:v for k,v in proposal.items() if k!='experiment_id'})
        expected=approval_template(proposal);actual=m['approval']
        require(all(actual.get(k)==v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')) and
            actual.get('decision')=='approved' and bool(actual.get('reviewer')) and bool(actual.get('reviewed_at')),'Diagnostic approval changed')
    return SimpleNamespace(model=unique.model(),shards=1,task_kind='rr_decoder_diagnostic')


def check(m,root,guarded):
    validate(m);unique.check_controls(root,m['controls'])
    require(m['source_revision']==source_revision(root) and m['model_lock_sha256']==digest(guarded),'Diagnostic source/lock changed')
    native=m['native_lock']
    require(m.get('parent_runtime_packages') and all(guarded.get('decoder_qualification',{}).get('packages',{}).get(k)==v for k,v in m['parent_runtime_packages'].items()),'Original pinned runtime changed')
    for arm,lock in [('native',native),('guarded',guarded)]:
        require_qualification(lock,lock.get('decoder_qualification',{}).get('packages',{}),16384,model(arm).action_constraint,2048)
    require({k:v for k,v in guarded.items() if k!='decoder_qualification'}==
        {k:v for k,v in native.items() if k!='decoder_qualification'},'Arms require same staged model lock')
    for key in ('packages','effective_generation_tokens','thinking_template','vocab_size'):
        require(native['decoder_qualification'].get(key)==guarded['decoder_qualification'].get(key),'Arm runtime mismatch: '+key)
    require(decoder_schema(NATIVE)==decoder_schema(unique.MODE),'Arm native schemas differ')


def submission(m,root,lock,mode,concurrency,output):
    check(m,root,lock)
    require(mode=='preflight' and concurrency==1,'Matched diagnostic is preflight-only, concurrency one')
    require(m.get('approval') is not None,'Exact diagnostic approval pending')
    require(not (Path(output)/'decoder-diagnostic-started.json').exists(),'Diagnostic already started; no retry')


def arm_run(m,arm,lock_path,root,output):
    validate(m)
    require(m.get('approval') is not None,'Exact diagnostic approval pending')
    require(arm in ARMS and os.environ.get('CUDA_LAUNCH_BLOCKING')=='1','Launch blocking must be set before process startup')
    require(os.environ.get('SLURM_JOB_ID'),'Slurm GPU allocation required')
    output=Path(output);require(not output.exists(),'Arm already started; no retry')
    report=dict(arm=arm,status='started',command_failed=True,experiment_id=m['experiment_id'],
        protocol=PROTOCOL,model_executed=False,model_instances=0,calls=[],task_execution_allowed=False,
        launch_blocking='1',process_id=os.getpid(),flush_status='atomic_checkpoint',runtime=None)
    start=time.monotonic()
    def save(rows):
        report.update(calls=deepcopy(rows),model_executed=any(r.get('dispatched') for r in rows),
            actual_tokens=sum(r['resources']['actual_tokens'] for r in rows),
            uncertain_tokens=sum(r['resources']['uncertain_tokens'] for r in rows),wall_seconds=time.monotonic()-start)
        # Compare before dispatch; unknown original IDs remain explicitly unknown.
        originals={r['id']:r for r in m['parent_cases']}
        for row in report['calls']:
            old=originals.get(row['id'],{});new=row.get('pre_dispatch',{})
            row['parent_input_comparison']={k:(None if old.get(k) is None or new.get(k) is None else old[k]==new[k])
                for k in ('prompt_hash','rendered_input_ids_hash')}
            row['parent_input_comparison']['input_tokens']=None if old.get('input_tokens') is None or row.get('input_tokens') is None else old['input_tokens']==row['input_tokens']
        atomic_json(output,report)
    save([]);stage='model_load'
    try:
        from ..models.transformers_backend import TransformersBackend
        backend=TransformersBackend(model(arm),lock_path)
        require(backend.runtime.get('vram_total_bytes',0)>=79_000_000_000,'Full 80-GB-class allocated GPU required')
        report.update(runtime=backend.runtime,model_instances=1)
        def memory(reset):
            cuda=backend.torch.cuda;cuda.synchronize()
            if reset:cuda.reset_peak_memory_stats(0)
            free,total=cuda.mem_get_info(0)
            return dict(peak_allocated_bytes=cuda.max_memory_allocated(0),peak_reserved_bytes=cuda.max_memory_reserved(0),free_bytes=free,total_bytes=total)
        stage='sequence'
        rows=unique.sequence(backend,memory,save,selected_cases=selected_cases(),mode=model(arm).action_constraint,diagnostic=True)
        report.update(status='completed',command_failed=not all(r['passed'] for r in rows));save(rows)
    except BaseException as exc:
        report.update(status='error',**unique.error_details(exc,stage));save(report['calls'])
        print(json.dumps(dict(arm=arm,error_type=type(exc).__name__,stage=stage,report=str(output))),file=sys.stderr,flush=True)
        raise
    return report


def reconcile_interrupted_arm(report):
    """Reconcile only persisted host reservations; no guessed device usage."""
    report=deepcopy(report)
    if report.get('status')!='started':return report
    report.update(status='interrupted',command_failed=True)
    for call in report.get('calls',[]):
        usage=call.get('resources',{})
        if call.get('status')!='started':continue
        pending=usage.get('reserved_tokens',0);cpu=usage.get('cpu_reserved',0)
        if call.get('dispatched') and 'generation' not in call:
            usage['uncertain_tokens']=usage.get('uncertain_tokens',0)+pending
            usage.setdefault('events',[]).append(dict(kind='uncertain_child_exit',reserved=pending,actual_tokens=None))
        elif pending:
            usage.setdefault('events',[]).append(dict(kind='released_before_dispatch',reserved=pending))
        usage['reserved_tokens']=0
        if cpu:
            usage['uncertain_cpu']=usage.get('uncertain_cpu',0)+cpu
            usage['cpu_cap_debit']=usage.get('cpu_cap_debit',0)+cpu
            usage.setdefault('events',[]).append(dict(kind='uncertain_child_cpu_exit',allowance=cpu,actual_cpu_seconds=None))
            usage['cpu_reserved']=0
        call['status']='interrupted'
    for name in ('actual_tokens','uncertain_tokens','uncertain_cpu','cpu_cap_debit'):
        report[name]=sum(c.get('resources',{}).get(name,0) for c in report.get('calls',[]))
    return report


def run(m,lock_path,root,output):
    output=Path(output);submission(m,root,read_json(lock_path),'preflight',1,output.parent)
    require(not output.exists(),'Use new diagnostic output');output.parent.mkdir(parents=True,exist_ok=True)
    with (output.parent/'decoder-diagnostic-started.json').open('x') as f:json.dump({'experiment_id':m['experiment_id']},f)
    packet=output.parent/'diagnostic-input.json';atomic_json(packet,m)
    native_path=output.parent/'native-lock.json';atomic_json(native_path,m['native_lock'])
    report=dict(schema='rr-decoder-diagnostic-report-v1',protocol=PROTOCOL,experiment_id=m['experiment_id'],manifest_hash=digest(m),
        parent_experiment=PARENT,status='started',command_failed=True,maximum_calls=4,task_execution_allowed=False,
        sql_executed=False,worst_case_fit_established=False,arms=[dict(arm=a,status='not_attempted') for a in ARMS])
    atomic_json(output,report)
    env=dict(os.environ);env['CUDA_LAUNCH_BLOCKING']='1'
    for index,arm in enumerate(ARMS):
        target=output.parent/(arm+'-report.json')
        argv=[sys.executable,'-I',str(Path(root)/'scripts/run_rr_decoder_diagnostic.py'),'--manifest',str(packet),
            '--arm',arm,'--model-lock',str(native_path if arm=='native' else lock_path),'--output',str(target)]
        # No CUDA imports in this parent. Each arm loads exactly one fresh model.
        report['arms'][index]=dict(arm=arm,status='started');atomic_json(output,report)
        try:
            result=subprocess.run(argv,env=env,check=False)
        except BaseException as exc:
            # subprocess.run terminates/waits its child on interruption. Preserve
            # its host checkpoint; later arms remain explicitly not_attempted.
            arm_report=read_json(target) if target.is_file() else dict(arm=arm,status='missing_report')
            arm_report=reconcile_interrupted_arm(arm_report)
            report['arms'][index]={**arm_report,'parent_interruption':unique.error_details(exc,'child_process_wait')}
            report.update(status='interrupted',command_failed=True,**unique.error_details(exc,'child_process_wait'))
            for key in ('actual_tokens','uncertain_tokens','uncertain_cpu','cpu_cap_debit'):
                report[key]=sum(a.get(key,0) for a in report['arms'])
            atomic_json(output,report)
            raise
        arm_report=read_json(target) if target.is_file() else dict(arm=arm,status='missing_report',command_failed=True)
        arm_report=reconcile_interrupted_arm(arm_report)
        report['arms'][index]={**arm_report,'process_exit_code':result.returncode}
        atomic_json(output,report)
    report['model_instances']=sum(a.get('model_instances',0) for a in report['arms'])
    report['model_executed']=any(a.get('model_executed') for a in report['arms'])
    report['status']='completed';report['command_failed']=any(a.get('command_failed',True) for a in report['arms'])
    report['accounting_complete']=all(a.get('status')!='missing_report' for a in report['arms'])
    report['actual_tokens']=sum(a.get('actual_tokens',0) for a in report['arms'])
    report['uncertain_tokens']=sum(a.get('uncertain_tokens',0) for a in report['arms'])
    runtimes=[a.get('runtime') or {} for a in report['arms']]
    report['same_hardware_model']=runtimes[0].get('hardware')==runtimes[1].get('hardware') if all(runtimes) else None
    report['matched_inputs']=matched_inputs(report)
    report['interpretation']='Integration diagnostic only; trajectories may diverge; no production qualification or root-cause conclusion'
    atomic_json(output,report);return report


def aggregate(m,output):
    validate(m);report=read_json(Path(output)/'preflight.json')
    require(report.get('experiment_id')==m['experiment_id'] and report.get('manifest_hash')==digest(m),'Diagnostic report identity changed')
    return report


def matched_inputs(report):
    arms=report.get('arms',[])
    if [a.get('arm') for a in arms]!=list(ARMS):return False
    calls=[a.get('calls',[]) for a in arms]
    if any(len(c)!=2 for c in calls):return False
    return all(left.get('pre_dispatch',{}).get('rendered_input_ids_hash') is not None and
        all(left.get('pre_dispatch',{}).get(k)==right.get('pre_dispatch',{}).get(k)
            for k in ('prompt_hash','rendered_input_ids_hash','seed','output_cap','call_order','cache_policy','context_policy'))
        for left,right in zip(*calls))


def normal_eligible(report):
    arms=report.get('arms',[])
    if report.get('schema')!='rr-decoder-diagnostic-report-v1' or report.get('protocol')!=PROTOCOL or report.get('status')!='completed' or not matched_inputs(report):return False
    pids=[a.get('process_id') for a in arms]
    if any(type(p) is not int or p<=0 for p in pids) or len(set(pids))!=2:return False
    for arm in arms:
        calls=arm.get('calls',[]);name=arm.get('arm')
        if arm.get('status')!='completed' or arm.get('launch_blocking')!='1' or arm.get('process_exit_code') not in (0,1):return False
        if [c.get('id') for c in calls]!=[c['id'] for c in selected_cases()]:return False
        for c in calls:
            generation=c.get('generation',{});d=generation.get('diagnostics',{});r=c.get('resources',{});inputs=c.get('pre_dispatch',{})
            if not c.get('dispatched') or c.get('rendered_generation_input_matches') is not True or c.get('generation_completion')!='eos' or d.get('finish_reason')!='eos' or c.get('accelerator_status')!='no_exception_observed':return False
            if any(r.get(k)!=0 for k in ('uncertain_tokens','uncertain_cpu','reserved_tokens','cpu_reserved')):return False
            if inputs.get('settings')!=asdict(model(name)) or inputs.get('grammar_mode')!=model(name).action_constraint:return False
            if inputs.get('rendered_input_ids_hash')!=digest(inputs.get('rendered_input_ids')):return False
            if r.get('actual_tokens')!=c.get('input_tokens',0)+generation.get('output_tokens',0):return False
            if not (0<=r.get('cpu_cap_debit',-1)<=1200 and r.get('actual_tokens',-1)<=16384):return False
            if name=='guarded' and (c.get('passed') is not True or d.get('constraint_complete') is not True):return False
    return True


def review_template(m,report):
    validate(m)
    require(m.get('approval') is not None,'Matched diagnostic approval missing')
    require(report.get('experiment_id')==m['experiment_id'] and report.get('manifest_hash')==digest(m),'Diagnostic report provenance changed')
    return dict(schema='rr-decoder-diagnostic-review-v1',decision='pending',reviewer=None,reviewed_at=None,
        experiment_id=m['experiment_id'],report_hash=digest(report),manifest_hash=digest(m),
        observed_both_arms_completed=normal_eligible(report),
        native_parse_rejection_is_not_accelerator_failure=True,
        normal_qualification_allowed=False,task_execution_allowed=False)
