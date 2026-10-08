"""Prospective configuration coverage and branch scheduling, independent of Slurm.

No evaluator or reference can influence planning or target selection. All durable
records are content addressed; an interrupted sequence is never regenerated.
"""
from copy import deepcopy
import math
import time
from . import v2
from .common import digest, Rejected
from .resources import Resources

SCHEMA='rr-prospective-cohort-v1'
PLANNERS=('requirement_level','prompted_open')
STOP_POLICY={'completed_semantic_failure':'continue','resource_exhausted':'continue',
             'invalid_plan':'retain_configuration_no_worker_branches',
             'infrastructure_failure':'pause_retain_unrun','interrupted':'pause_retain_unrun',
             'integrity_failure':'pause_retain_unrun','unsafe_execution':'pause_retain_unrun',
             'accounting_failure':'pause_retain_unrun','pause_scope':'remaining_branches_and_configurations','retry':'none'}


def configuration(task,planner,*,seed=1,target_rule='uniform'):
    if planner not in PLANNERS:raise Rejected('cohort_planner')
    c=v2.configuration(7,seed=seed,target_rule=target_rule,planner=planner,
        planning_lane='open_generated',execution_contract='plan_scoped_v1',planner_output_cap=6144)
    row=dict(task=task,planner=planner,config=c,seed_index=seed,
        target_rule=target_rule,planning_sequences=1,task_weight=1,
        branch_identity_rule='sha256-frozen-request-plan-track-target-v1',stop_policy=STOP_POLICY,
        maximum_branches=8 if target_rule=='all' else 2)
    return {**row,'configuration_id':digest(row)}


def check_configuration(row):
    expected=configuration(row['task'],row['planner'],seed=row['seed_index'],target_rule=row['target_rule'])
    if row!=expected:raise Rejected('cohort_configuration_changed')


def plan(row,public,model_binding,backend=None,save=None,mode='real_model'):
    check_configuration(row)
    req=v2.request(public,row['config'],model_binding)
    if row['planner']=='prompted_open':
        if backend is None:raise Rejected('planner_backend_required')
        return v2.PromptedPlanner(backend,6144,evidence_mode=mode).run(req,public,save)
    start=time.process_time()
    r=Resources(100000,1200)
    p=v2.requirement_plan(public,row['config'])
    r.reconcile_cpu('requirement_level_allocation',0,time.process_time()-start)
    # This is a deterministic public requirement allocation, not a reference solver.
    return v2.freeze(req,public,p,r,[],'deterministic_public')


def schedule(row,frozen):
    check_configuration(row);v2.verify_record(frozen,'frozen_id')
    v2.verify_record(frozen['request'],'request_id')
    if frozen['request']['config']!=row['config'] or frozen['request']['planner_input']['task_id']!=row['task']:
        raise Rejected('cohort_frozen_binding')
    resources=Resources(**deepcopy(frozen['planning_resources']))
    for event in resources.events:
        if event['kind']=='model_usage' and any(type(event.get(k)) is not int or event[k]<0 for k in ('input_tokens','output_tokens')):
            raise Rejected('planning_ledger_invalid_usage')
        if event['kind']=='cpu' and (type(event.get('cap_debit')) not in (int,float) or not math.isfinite(event['cap_debit']) or event['cap_debit']<0):
            raise Rejected('planning_ledger_invalid_usage')
    if any(type(x) not in (int,float) or not math.isfinite(x) or x<0 for x in
           (resources.actual_tokens,resources.uncertain_tokens,resources.cpu_seconds,resources.uncertain_cpu,resources.cpu_reserved)):
        raise Rejected('planning_ledger_invalid_usage')
    tokens=sum(e.get('input_tokens',0)+e.get('output_tokens',0) for e in resources.events if e['kind']=='model_usage')
    cpu=sum(e.get('cap_debit',0) for e in resources.events if e['kind']=='cpu')
    if tokens!=resources.actual_tokens or not math.isfinite(cpu) or not math.isclose(cpu,resources.cpu_seconds,abs_tol=1e-8):
        raise Rejected('planning_ledger_does_not_reconcile')
    if resources.token_cap!=100000 or resources.cpu_cap!=1200:raise Rejected('planning_budget_changed')
    if frozen['status']=='valid' and (resources.reservations or resources.cpu_pending or resources.uncertain_tokens or resources.uncertain_cpu or resources.remaining<0 or resources.cpu_seconds>1200):
        raise Rejected('planning_usage_unsettled')
    if frozen['status']=='valid':
        branches=v2.resolve_branches(frozen)
        if len(branches['rows'])>row['maximum_branches']:raise Rejected('cohort_branch_cap')
        target_status='frozen_before_execution'
    else:
        branches=None;target_status='not_applicable_invalid_planning' if frozen['status']=='invalid_plan' else 'unresolved_planning_failure'
    record=dict(schema='rr-cohort-schedule-v1',configuration_id=row['configuration_id'],
                frozen=frozen,branches=branches,target_status=target_status,
                planning_status=frozen['status'],planning_physical_sequences=1,
                planning_logical_multiplicity=len(branches['rows']) if branches else 0,
                unresolved_configuration_charge=frozen['planning_resources'] if branches is None else None)
    return {**record,'schedule_id':digest(record)}


def check_schedule(row,s):
    if s!=schedule(row,s['frozen']):raise Rejected('cohort_schedule_changed')


def run_scheduled(row,s,execute,save):
    """execute receives ONLY frozen planning and the current branch, never results.

    save must durably persist the complete schedule before the first execution.
    A completed wrong answer never changes the remaining schedule.
    """
    check_schedule(row,s);save('schedule',s)
    results=[];paused=s['planning_status'] if s['planning_status'] not in ('valid','invalid_plan') else None
    for branch in (s['branches']['rows'] if s['branches'] else []):
        if paused:
            result=dict(branch_id=branch['branch_id'],track=branch['track'],target=branch['target'],
                        status='unrun',success=None,pause_reason=paused)
        else:
            save('branch-start-'+branch['branch_id'],{'schedule_id':s['schedule_id']})
            try:result=execute(deepcopy(s['branches']),deepcopy(branch))
            except (Exception,KeyboardInterrupt) as exc:
                result=dict(status='interrupted' if isinstance(exc,(KeyboardInterrupt,InterruptedError)) else 'infrastructure_failed',
                            success=None,error_type=type(exc).__name__)
            result.update(branch_id=branch['branch_id'],track=branch['track'],target=branch['target'])
            if result['status'] not in ('completed','resource_exhausted','no_intervention') or result.get('cleanup_error_type'):
                paused=result['status'] if result['status']!='completed' else 'cleanup_failure'
            if result.get('contract_conformant') is False:
                paused='contract_violation'
        save('branch-'+branch['branch_id'],result);results.append(result)
    result=dict(configuration_id=row['configuration_id'],schedule_id=s['schedule_id'],
                status='paused' if paused else 'completed' if s['planning_status']=='valid' else s['planning_status'],target_status=s['target_status'],
                planning=s['frozen'],branches=results,pause_reason=paused)
    save('configuration-result',result)
    return result


def summarize(configurations,records):
    """A failed/invalid configuration stays in its task/planner denominator."""
    ids={c['configuration_id'] for c in configurations}
    if len(ids)!=len(configurations) or set(records)-ids:raise Rejected('cohort_result_coverage')
    rows=[];groups={}
    for c in configurations:
        check_configuration(c);r=records.get(c['configuration_id'])
        f=r.get('planning') if r else None
        status=r['status'] if r else 'unrun'
        plans=v2.descriptors(f['plan']) if f and f.get('plan') else None
        if plans:
            outputs={}
            for unit in f['plan']['units']:outputs[unit['worker']]=outputs.get(unit['worker'],0)+len(unit['outputs'])
            n=sum(outputs.values())
            plans['output_ownership_concentration']=sum((v/n)**2 for v in outputs.values())
            meaningful={u['id'] for u in f['plan']['units'] if u['outputs']}
            for u in reversed(f['plan']['units']):
                if u['id'] in meaningful:meaningful.update(u['depends'])
            plans['meaningful_active_owners']=sorted({u['worker'] for u in f['plan']['units'] if u['id'] in meaningful})
        branches=r.get('branches',[]) if r else []
        clean=next((b for b in branches if b['track']=='clean'),None)
        faults=[b for b in branches if b['track']=='F']
        invalid=f and f['status']=='invalid_plan'
        mean=lambda bs:sum(b['success'] is True for b in bs)/len(bs) if bs and all(b.get('success') is not None for b in bs) else None
        cr=False if invalid else clean.get('success') if clean else None
        fr=0.0 if invalid else mean(faults)
        row=dict(task=c['task'],planner=c['planner'],configuration_id=c['configuration_id'],status=status,
            planning_status=f.get('status') if f else None,descriptors=plans,pool=7,
            planning_resources=Resources(**f['planning_resources']).summary() if f else None,
            interrupted_planning_usage=r.get('planning_interrupted_usage') if r else None,
            physical_planner_calls=f.get('physical_generation_count',0) if f else None,
            planning_rejected_responses=sum('error' in e.get('feedback',{}) for e in f.get('planning_events',[])) if f else None,
            target_status=r.get('target_status') if r else 'unresolved',
            clean_success=cr,unconditional_configuration_fault_score=fr,
            branches=deepcopy(branches),invalid_planning_counts_as_configuration_failure=bool(invalid))
        row['branch_metrics']=[branch_metrics(b) for b in branches]
        rows.append(row);groups.setdefault(c['planner'],[]).append(row)
    balanced={}
    for planner,rs in groups.items():
        by_task={}
        for r in rs:by_task.setdefault(r['task'],[]).append(r)
        if any(len(x)!=1 for x in by_task.values()):raise Rejected('duplicate_task_planner')
        scores=[r['unconditional_configuration_fault_score'] for r in rs]
        balanced[planner]=dict(scheduled_tasks=len(rs),resolved_tasks=sum(s is not None for s in scores),
            fault_configuration_mean=sum(scores)/len(scores) if scores and all(s is not None for s in scores) else None)
    return dict(schema='rr-cohort-summary-v1',configurations=rows,task_balanced=balanced,
                missing_configurations=sum(c['configuration_id'] not in records for c in configurations),
                interpretation='Development characterization; no worst-case robustness, planner superiority or independent-branch inference.')


def branch_metrics(b):
    events=b.get('events',[]);resources=b.get('resource_profile',{});conf=b.get('conformance',{})
    return dict(track=b['track'],target=b['target'],status=b['status'],correct=b.get('task_correct'),
        complete_in_budget=b.get('success'),contract_conformant=b.get('contract_conformant'),
        loss_triggered=b.get('intervention_triggered'),fault_fraction=b.get('fault_fraction'),
        loss_event=next((e for e in events if e['type']=='unavailable'),None),
        allowed_unused_edges=conf.get('allowed_not_observed'),observed_imports=conf.get('direct_imports'),
        retained_versions=b.get('retained_versions'),artifact_executions=b.get('artifact_executions'),
        explicit_rebindings=b.get('explicit_rebindings'),reexecutions=sum(e['type']=='jit_reexecute' for e in events) if events else None,
        repair_assignments=[{k:e.get(k) for k in ('unit','worker','new_versions','actual_tokens','cpu_cap_debit')} for e in events if e['type']=='unit_end' and e['stage']=='repair'],
        primary_assignment_tokens=sum(e['actual_tokens'] for e in events if e['type']=='unit_end' and e['stage']=='primary') if events else None,
        primary_assignment_cpu=sum(e['cpu_cap_debit'] for e in events if e['type']=='unit_end' and e['stage']=='primary') if events else None,
        post_alarm_tokens=b.get('post_alarm_tokens'),post_alarm_cpu=b.get('post_alarm_cpu'),
        total_tokens=resources.get('actual_tokens'),total_cpu=resources.get('cpu_cap_debit'),
        uncertain_tokens=resources.get('uncertain_tokens'),uncertain_cpu=resources.get('uncertain_cpu'),
        component_note='Assignment totals exclude separate monitoring/orchestration; post-alarm is the recorded runtime cutoff, not a new additive ledger.')
