"""Open planning preparation and an injected-backend vertical slice.

Uses existing PromptedPlanner/Engine/ModelWorker. No scheduler or gate bypass.
"""
from copy import deepcopy
from .common import Rejected,digest
from . import v2


def proposal(historical,lock,planner_output_cap=2048):
    """Build a blocked engineering proposal from actual resolved stock settings."""
    if historical.get('schema')!='rr-v2-stock-competence-v1' or historical.get('task')!='synthetic-stock':
        raise Rejected('resolved_stock_manifest_required')
    if historical.get('experiment_id')!=digest({k:v for k,v in historical.items() if k!='experiment_id'}):raise Rejected('manifest_integrity')
    if historical['model_lock_sha256']!=digest(lock):raise Rejected('historical_model_lock_mismatch')
    model=deepcopy(historical['model']);c=v2.check_config(historical['config'])
    if any(model.get(k)!=lock.get(k) for k in ('checkpoint','revision','tokenizer_revision')):raise Rejected('model_binding_mismatch')
    if model['checkpoint']!='Qwen/Qwen3.5-27B' or model['revision']!='fc05daec18b0a78c049392ed2e771dde82bdf654' or model['dtype']!='bfloat16' or c['pool_size']!=7:
        raise Rejected('frozen_stock_model_required')
    worker=deepcopy(model);worker['action_constraint']='reporecourse-json-scoped-v1-pool-7'
    planner=deepcopy(model);planner.update(action_constraint='reporecourse-plan-scoped-v1-pool-7',max_new_tokens=planner_output_cap)
    config=v2.configuration(7,planning_lane='open_generated',execution_contract='plan_scoped_v1',
        planner='prompted_open',token_cap=c['resource']['token_cap'],cpu_cap=c['resource']['cpu_cap'],
        seed=historical['seed'],max_units=c['max_units'],planner_output_cap=planner_output_cap)
    # Seed streams and worker limits are actual resolved settings, not a
    # reconstruction from a summary or a new default.
    config['seeds']=deepcopy(c['seeds'])
    for field in ('max_actions','scheduler','count_mode','primary_count','threat','target_rule','reserve_rule'):
        if config[field]!=c[field]:raise Rejected('historical_worker_settings_not_supported')
    from .qualification import implementation_hashes
    result=dict(schema='rr-open-engineering-proposal-v1',config=config,worker_config={'model':worker},planner_config={'model':planner},
        historical_manifest=historical['experiment_id'],historical_lock_hash=digest(lock),task='synthetic-stock',
        public_hash=historical['public_hash'],qualification_basis=historical['qualification'],
        implementation_hashes=implementation_hashes(),plan_generations=1,maximum_structural_revisions=2,
        maximum_planner_calls=config['planning_calls'],clean_branches=1,conditional_F_branches=1,
        maximum_execution_branches=2,executed=0,model_executed=False,submitted=False,
        planning_costs='actual planning ledger charged logically in each branch; physical generation once',
        engineering_caps_not_B0=True,qualified_plan_footprint=None,
        blockers=['changed_CPU_execution_contract_controls','renewed_worker_and_planner_grammar_locks',
                  'new_scope_observation_and_planner_output_footprint_qualification','explicit_open_clean_engineering_approval',
                  'F_requires_clean_conformant_success_review_and_separate_approval'],
        campaign_allowed=False,task_execution_allowed=False,
        target_selection='after single plan freeze, before clean evaluation; never retarget on nontrigger',
        scheduler='existing shared registry; one physical GPU; qualification concurrency one; campaign maximum four')
    result['proposal_id']=digest(result);return result


def run_with_backends(request,public,private,planner_backend,worker_backend,*,evidence_mode):
    """Exercise actual model interfaces with labelled CPU doubles until GPU approval.

    A future authorized runner can reuse these components, but must supply the
    shared-registry allocation/evidence gate; this function never supplies one.
    """
    if evidence_mode!='scripted_mock':raise Rejected('open_GPU_qualification_and_approval_pending')
    c=v2.check_config(request['config'])
    if c.get('planning_lane')!='open_generated':raise Rejected('open_generated_required')
    frozen=v2.PromptedPlanner(planner_backend,c['planner_output_cap'],evidence_mode).run(request,public)
    manifest=v2.resolve_branches(frozen)
    from .engine import ModelWorker
    # Explicit class label for CPU doubles; no real model may use this entry.
    class DoubleWorker(ModelWorker):mode='scripted_mock'
    worker=DoubleWorker(worker_backend,context_limit=getattr(worker_backend,'context_limit',16384),output_cap=2048)
    clean=manifest['rows'][0]
    row=v2.run_branch(manifest,clean['branch_id'],public,private,worker)
    return dict(frozen=frozen,manifest=manifest,results=[row],evidence='scripted_mock_model_interfaces',
                model_executed=False,F_executed=False,planned_F_retained=True)
