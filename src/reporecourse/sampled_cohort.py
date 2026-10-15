"""Prepared-only organization characterization using the existing branch engine.

CPU catalogs are feasibility evidence. This module has no model loader or Slurm
route; a proposal is not a task-execution authorization.
"""
from copy import deepcopy
import time
from . import cohort, v2
from .common import Rejected, digest
from .resources import Resources
from .interface import PROFILE
from .qualification import implementation_hashes, runtime_versions

TASKS=('jaffle-payment-release','github-multioperation-integration')
SCHEMA='rr-sampled-cohort-proposal-v1'
MODE='reporecourse-json-unique-v1-pool-7'
LIMITATIONS=['development_only_not_held_out','sampled_authored_organizations_not_open_planner',
    'source_and_provider_rights_review_pending_not_clearance','independent_task_review_pending',
    'uncalibrated_engineering_caps_not_B0','observed_qualification_not_worst_case_fit',
    'persistent_availability_F_not_adaptive_adversary','no_retry_no_training',
    'offline_construction_and_qualification_not_free_planning']


def configuration(task,plan,*,seed=1):
    """An explicit sampled plan, never a disguised LLM or requirement planner."""
    c=v2.configuration(7,seed=seed,planner='sampled_organization',
        planning_lane='authored_diagnostic',execution_contract='plan_scoped_v1',planner_output_cap=6144,interface_profile=PROFILE)
    row=dict(schema='rr-sampled-configuration-v1',task=task,planner='sampled_organization',
        plan=deepcopy(plan),plan_id=digest(plan),config=c,seed_index=seed,target_rule='uniform',
        planning_sequences=0,task_weight=1,maximum_branches=2,stop_policy=deepcopy(cohort.STOP_POLICY),
        branch_identity_rule='sha256-frozen-request-plan-track-target-v1')
    return {**row,'configuration_id':digest(row)}


def check_configuration(row):
    if row!=configuration(row['task'],row['plan'],seed=row['seed_index']):
        raise Rejected('sampled_configuration_changed')


def schedule(row,public,model_binding=None):
    """Freeze plan and meaningful seeded owner before any clean evaluation."""
    check_configuration(row)
    if public['id']!=row['task']:raise Rejected('sampled_task_binding')
    started=time.process_time();r=Resources(100000,1200)
    request=v2.request(public,row['config'],model_binding)
    r.reconcile_cpu('sampled_plan_receipt',0,time.process_time()-started)
    frozen=v2.freeze(request,public,row['plan'],r,[],'authored_catalog',catalog_info={
        'source':'public_task_recipes','selector':'prespecified_structural_coverage',
        'offline_costs':'reported_separately_not_deployable_planner_cost'})
    if frozen['status']!='valid':raise Rejected('sampled_plan_invalid')
    record=cohort.schedule(row,frozen)
    # Existing scheduler counts a frozen receipt sequence, not generation calls.
    if frozen['physical_generation_count']!=0:raise Rejected('sampled_planner_generation')
    return record


def run_reference_schedule(row,s,public,private,worker,save):
    """CPU-only actual assignments, monitor/JIT, evaluator and branch ledgers."""
    if getattr(worker,'mode','')=='model':raise Rejected('sampled_gpu_execution_adapter_pending')
    return cohort.run_scheduled(row,s,
        lambda manifest,branch:v2.run_branch(manifest,branch['branch_id'],public,private,worker),save)


def model_settings():
    return dict(checkpoint='Qwen/Qwen3.5-27B',revision='fc05daec18b0a78c049392ed2e771dde82bdf654',
        tokenizer_revision='fc05daec18b0a78c049392ed2e771dde82bdf654',backend='transformers',dtype='bfloat16',
        context_limit=16384,max_new_tokens=2048,thinking=True,do_sample=False,temperature=0.7,top_p=0.8,top_k=20,action_constraint=MODE)


def qualified_candidate(candidate,task,public,entry,catalog):
    """Validate evidence bindings; positive status alone is insufficient."""
    from .organization_sampler import canonical_key, reference_witness, configuration as catalog_config, sample
    from .tasks import private_task, catalog as task_catalog, ROOT
    from .track_f_controls import PINS
    plan=candidate.get('plan');q=candidate.get('qualification',{})
    try:
        validated=v2.validate_work_plan(plan,public,catalog_config())
        rebuilt=sample(task,public,candidate_limit=entry.get('candidate_limit',12))
        original=next(x for x in rebuilt['candidates'] if x['candidate_id']==candidate.get('candidate_id'))
        card=next(x for x in task_catalog(ROOT/'rich')['tasks'] if x['id']==task)
        if (entry.get('source_available') is not True or entry.get('config')!=catalog_config() or
            entry.get('public_hash')!=digest(public) or entry.get('card_hash')!=digest(card) or
            entry.get('source_group')!=card['source_group'] or entry.get('selected')!=rebuilt['selected'] or
            {k:v for k,v in candidate.items() if k!='qualification'}!={k:v for k,v in original.items() if k!='qualification'}):
            return False
        expected=digest(reference_witness(candidate,private_task(task)))
        required={r['id'] for r in public['required_outputs']}
        negatives=q.get('negative_controls',[])
        return (validated==plan and candidate.get('plan_id')==digest(plan) and
            candidate.get('canonical_key')==canonical_key(plan) and
            catalog.get('implementation_hashes')==implementation_hashes() and
            q.get('reference_implementation_hashes')==implementation_hashes() and
            q.get('private_task_hash')==digest(private_task(task)) and
            q.get('plan_id')==digest(plan) and q.get('private_binding_hash')==expected and
            q.get('status')=='cpu_qualified_reference' and q.get('evidence')=='scripted_reference_only' and
            q.get('model_executed') is False and q.get('task_execution_allowed') is False and
            q.get('execution_status')=='completed' and q.get('contract_conformant') is True and
            q.get('source_integrity') is True and q.get('reset_repeat_identical') is True and
            q.get('runtime_versions')==runtime_versions() and
            all(q['runtime_versions'].get(k)==value for k,value in PINS.items()) and
            q.get('evaluation',{}).get('status')=='available' and q.get('evaluation',{}).get('success') is True and
            set(q.get('evaluation',{}).get('obligations',{}))==required and
            all(v is True for v in q['evaluation']['obligations'].values()) and
            all(x.get('detected') is True for x in negatives) and
            {(x.get('obligation'),x.get('mutation')) for x in negatives} >=
                {(o,kind) for o in required for kind in ('missing','wrong_semantics')})
    except (Rejected,KeyError,TypeError,ValueError,StopIteration):return False


def proposal(catalog,publics,*,worker_lock=None,normal_qualification=None):
    """Retain all six organization slots and twelve planned conditions if blocked.

    Supplied GPU evidence is retained for review, not trusted by status alone.
    An exact compatible normal-qualification validator and model execution route
    must be reviewed before a later implementation can open this gate.
    """
    if catalog.get('schema')!='rr-organization-catalog-v1':raise Rejected('sampled_catalog_schema')
    v2.verify_record(catalog,'catalog_id')
    rows=catalog.get('tasks',[])
    if len({r['task'] for r in rows})!=len(rows) or set(r['task'] for r in rows)-set(TASKS):
        raise Rejected('sampled_catalog_tasks')
    configurations=[];slots=[];missing=[];blockers=[]
    bytask={r['task']:r for r in rows}
    for task in TASKS:
        entry=bytask.get(task,{})
        selected=entry.get('selected',[])
        if len(selected)>3 or len(set(selected))!=len(selected):raise Rejected('sampled_selection_bound')
        candidates={r['candidate_id']:r for r in entry.get('candidates',[])}
        if len(candidates)!=len(entry.get('candidates',[])):raise Rejected('sampled_candidate_duplicate')
        public=publics.get(task)
        public_ok=public is not None and digest(public)==entry.get('public_hash')
        structural=set()
        for index in range(3):
            candidate=candidates.get(selected[index]) if index<len(selected) else None
            slot=dict(task=task,organization_slot=index,tracks=['clean','F'],candidate_id=selected[index] if index<len(selected) else None)
            reason=None
            if not candidate:reason='selected_plan_missing'
            elif not public_ok:reason='public_contract_unavailable_or_changed'
            elif not qualified_candidate(candidate,task,public,entry,catalog):reason='reference_qualification_missing_or_changed'
            elif candidate.get('canonical_key') in structural:reason='equivalent_organization'
            if reason:
                slot.update(status='blocked',reason=reason);missing.append(deepcopy(slot))
            else:
                structural.add(candidate['canonical_key'])
                c=configuration(task,candidate['plan'])
                s=schedule(c,public,worker_lock)
                configurations.append(dict(configuration=c,schedule=s,recipe=candidate.get('recipe'),
                    candidate_id=candidate['candidate_id'],source_group=entry.get('source_group')))
                slot.update(status='prepared',configuration_id=c['configuration_id'])
            slots.append(slot)
    if missing:blockers.append('six_cpu_qualified_materially_distinct_plans_required')
    if worker_lock is None:blockers.append('compatible_unique_worker_cpu_lock_required')
    elif worker_lock.get('decoder_qualification',{}).get('contract',{}).get('mode')!=MODE:
        blockers.append('worker_lock_is_not_unique_guard_mode')
    else:blockers.append('worker_cpu_lock_exact_compatibility_review_pending')
    if normal_qualification is None:blockers.append('guarded_normal_gpu_qualification_missing')
    else:blockers.append('guarded_normal_gpu_evidence_requires_exact_compatibility_review')
    blockers+=['catalog_scope_review_pending','changed_plan_decoder_exact_approval_pending',
               'source_rights_and_development_scope_verification_pending','sampled_gpu_execution_adapter_pending']
    base=dict(schema=SCHEMA,lane='rich_development_unreviewed',study='controlled_organization_characterization',
        catalog_id=catalog['catalog_id'],catalog=deepcopy(catalog),configurations=configurations,slots=slots,
        implementation_hashes=implementation_hashes(),model=model_settings(),interface_profile=PROFILE,
        missing_slots=missing,planned_conditions=12,planned_configurations=6,worker_mode=MODE,pool=7,
        role_output_caps={'worker':2048,'planner':6144},context_limit=16384,
        worker_lock_hash=digest(worker_lock) if worker_lock else None,
        normal_qualification_evidence=deepcopy(normal_qualification),
        maximum_logical_tokens=1200000,maximum_charged_cpu_seconds=14400,
        branch_caps={'token_cap':100000,'cpu_cap':1200},reserve_rule='none',target_rule='seed1_uniform_meaningful_owner_before_outcomes',
        physical_planner_calls=0,offline_costs=deepcopy(catalog.get('offline_costs')),
        offline_cost_scope='Construction/reference expense separate; branch receipts and workers charged in each branch.',
        split='development',limitations=LIMITATIONS,blockers=blockers,status='blocked',
        task_execution_allowed=False,submitted=False,model_executed=False)
    return {**base,'proposal_id':digest(base)}


def approval_template(p):
    v2.verify_record(p,'proposal_id')
    return dict(schema='rr-sampled-cohort-approval-v1',proposal_id=p['proposal_id'],
        scope_hash=digest({k:p[k] for k in ('slots','configurations','worker_mode','branch_caps','target_rule','reserve_rule')}),
        decision='pending',reviewer=None,reviewed_at=None,maximum_execution_branches=12,
        maximum_model_planner_calls=0,limitations_accepted=deepcopy(LIMITATIONS),
        task_execution_allowed=False,blockers=deepcopy(p['blockers']))


def analyze(p,records):
    """Read-only task-balanced labels. Unrun conditions remain unknown."""
    v2.verify_record(p,'proposal_id')
    expected={r['configuration']['configuration_id'] for r in p['configurations']}
    if set(records)-expected:raise Rejected('sampled_unknown_result_configuration')
    bytask={t:[] for t in TASKS};out=[]
    for item in p['configurations']:
        c=item['configuration'];s=item['schedule'];cohort.check_schedule(c,s)
        record=records.get(c['configuration_id']);results={}
        if record:
            if record.get('configuration_id')!=c['configuration_id'] or record.get('schedule_id')!=s['schedule_id']:
                raise Rejected('sampled_result_binding')
            expected_branches={b['branch_id']:b for b in s['branches']['rows']}
            for result in record.get('branches',[]):
                bid=result.get('branch_id');expected_branch=expected_branches.get(bid)
                if not expected_branch or bid in results or any(result.get(k)!=expected_branch[k] for k in ('track','target')):
                    raise Rejected('sampled_result_branch')
                results[bid]=result
        branches=[]
        for scheduled in s['branches']['rows']:
            result=results.get(scheduled['branch_id'])
            labels=cohort.branch_metrics(result) if result else dict(status='unrun',complete_in_budget=None)
            labels.update(track=scheduled['track'],target=scheduled['target'],eligible=scheduled['eligible'],
                fault_fraction=scheduled['fault_fraction'],branch_id=scheduled['branch_id'],
                evaluation=deepcopy(result.get('evaluation')) if result else None,
                evidence_mode=result.get('mode','unknown') if result else 'unrun')
            branches.append(labels);bytask[c['task']].append(labels)
        out.append(dict(task=c['task'],plan=deepcopy(c['plan']),plan_id=c['plan_id'],
            configuration_id=c['configuration_id'],source_group=item['source_group'],recipe=item['recipe'],
            declared_imports=[dict(unit=u['id'],imports=u.get('consumes',{})) for u in c['plan']['units']],
            branch_metrics=branches,physical_planner_calls=0))
    summary={}
    for task,branches in bytask.items():
        summary[task]={}
        for track in ('clean','F'):
            observed=[b for b in branches if b['track']==track]
            scores=[b.get('complete_in_budget') for b in observed]
            summary[task][track]=dict(planned=3,represented=len(observed),
                known=sum(type(x) is bool for x in scores),successes=sum(x is True for x in scores),
                complete_rate=sum(x is True for x in scores)/3 if len(scores)==3 and all(type(x) is bool for x in scores) else None)
    return dict(schema='rr-sampled-cohort-analysis-v1',proposal_id=p['proposal_id'],configurations=out,
        by_task=summary,missing_slots=p['missing_slots'],planned_conditions=12,
        historical_scores_changed=False,model_executed=False,sql_executed=False,
        interpretation='Repeated organizations and fault conditions within two development tasks; no independent-task or planner-superiority claim.',
        accounting='Logical branch resources; offline catalog expense separate; post-alarm expense is a subset of total.')
