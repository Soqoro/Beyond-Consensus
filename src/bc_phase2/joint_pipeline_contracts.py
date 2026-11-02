"""Offline joint pipeline contracts. No provider or dataset loading on import."""
from copy import deepcopy
import json
import re
from .joint_schema import decode, canonical_domain, require
from .joint_core import explicit_selection, compile_organisation
from .model import Invalid, digest

PROMPT = ('joint-neutral-blueprint-v1: Specify meaningful responsibilities, artifacts, '
          'dependencies and finite implementation/delivery alternatives before ownership. '
          'Sequential reasoning is allowed. Do not pad tasks, solve the problem into trusted '
          'inputs, optimise recovery, or supply cost estimates. Return unsupported when needed. '
          'Ownership is assigned separately after this blueprint is frozen.')


def public_problem(record):
    require(type(record) is dict and type(record.get('id')) is str and
            type(record.get('problem')) is str, 'public source fields')
    return {k: record[k] for k in ('id', 'problem')}


def planner_payload(record, n, K):
    require(type(n) is int and type(K) is int and n > 0 and K > 0, 'capacity')
    return dict(schema='joint-neutral-request-v1', prompt=PROMPT,
                source=public_problem(record), n=n, K=K, task_range=[n,n*K])


def blueprint_wire(domain):
    """Synthetic authoring helper. Predicted costs are NOT planner-controlled."""
    d=deepcopy(domain)
    for e in d['events']:
        for mode in e['modes']:
            del mode['initial']; del mode['replay']
    return d


def bind_blueprint(wire, prices):
    d=deepcopy(wire)
    keys={(e['id'],m['id']) for e in d['events'] for m in e['modes']}
    require(set(prices)==keys, 'complete externally supplied price support')
    for e in d['events']:
        for m in e['modes']:
            require('initial' not in m and 'replay' not in m, 'planner supplied prices')
            initial,replay=prices[e['id'],m['id']]
            m.update(initial=initial,replay=replay)
    return canonical_domain(d)


def generate_neutral(record, n, K, responses, prices=None, *, synthetic=False):
    """At most one structural correction; raw responses and reasons preserved.

    Prices are caller-owned development estimates or explicitly synthetic fixtures.
    This function never selects owners or grants qualitative admission.
    """
    payload=planner_payload(record,n,K); history=[]; domain=None; status='invalid'
    for raw in responses[:2]:
        reason=None
        try:
            row=decode(raw)
            require(type(row) is dict and row.get('schema')=='joint-blueprint-v1','blueprint schema')
            if row.get('status')=='unsupported':
                require(set(row)=={'schema','status','reason'} and type(row['reason']) is str,'unsupported fields')
                status='unsupported'
            else:
                require(set(row)=={'schema','status','blueprint'} and row['status']=='plan','blueprint fields')
                structural_prices={(e['id'],m['id']):('1','1') for e in row['blueprint']['events'] for m in e['modes']} if prices is None else prices
                domain=bind_blueprint(row['blueprint'],structural_prices)
                require(domain['n']==n and domain['K']==K and domain['source']['id']==record['id'],'source/capacity binding')
                # External protected values must be supplied by the source adapter, not a generator.
                require(all(s['value'] is None for s in domain['sources']) or
                        (synthetic and domain['source']['kind']=='synthetic_fixture'),'generated trusted input value')
                status='structurally_valid'
        except (Invalid,ValueError,TypeError,KeyError) as exc:
            reason=str(exc);domain=None
        history.append(dict(raw=raw,structural_error=reason))
        if reason is None:break
    texts=[] if domain is None else [t['instruction'] for t in domain['tasks']]
    return dict(schema='joint-neutral-record-v1',payload=payload,history=history,
                correction_requests=max(0,len(history)-1),status=status,domain=domain,
                blueprint_hash=None if domain is None else digest(blueprint_wire(domain)),
                answer_like_review_flag=any(re.search(r'final answer\s*(?:is|=)|\\boxed',s,re.I) for s in texts),
                price_status='structural_placeholders_not_estimates' if prices is None else 'caller_supplied_prices',
                qualitative_status='not_reviewed',execution_qualified=False,model_executed=False)


def assign_seed(neutral, A, C, ownership):
    require(neutral['status']=='structurally_valid','no usable blueprint')
    d=neutral['domain'];s=explicit_selection(d,A,C,ownership);compile_organisation(d,s)
    return s


BASE_FIELDS=('cohort','source_eligibility','model_settings','prompt_versions','caps',
             'metering','cache_retry_policy','approval')
STAGE_FIELDS={
 'D1':('planner_binding',),
 'D2':('worker_binding','evaluator_qualification','collection_manifest'),
 'D3':('worker_binding','evaluator_qualification','frozen_estimator','admission','analysis'),
 'D4':('worker_binding','evaluator_qualification','frozen_estimator','admission','analysis'),
 'D5':('worker_binding','evaluator_qualification','frozen_estimator','admission','analysis',
       'heldout_cohort','source_family_decisions','sample_repetition_freeze','inference_spec'),
 'D6':('worker_binding','evaluator_qualification','frozen_estimator','admission','analysis','selected_strata')}


def stage_template(stage):
    require(stage in STAGE_FIELDS,'stage')
    return dict(schema='joint-stage-v1',stage=stage,enabled=False,
                bindings={k:None for k in BASE_FIELDS+STAGE_FIELDS[stage]},
                design={'n':4,'K':2,'max_workflows':3,'repetitions':1,
                        'methods':['cost_informed_llm','joint'],'all_owners':True} if stage=='D3' else None)


def preflight(manifest):
    require(type(manifest) is dict and set(manifest)=={'schema','stage','enabled','bindings','design'},'stage fields')
    stage=manifest['stage'];require(stage in STAGE_FIELDS and manifest['schema']=='joint-stage-v1','stage schema')
    require(type(manifest['enabled']) is bool,'enabled type')
    require(set(manifest['bindings'])==set(BASE_FIELDS+STAGE_FIELDS[stage]),'stage binding fields')
    if stage=='D3':require(manifest['design']==stage_template(stage)['design'],'D3 bounded design')
    missing=[k for k,v in manifest['bindings'].items() if v is None]
    # Non-null user data is not qualification or approval. No live binding is registered here.
    blockers=['missing:'+k for k in missing]
    blockers+=['live_adapter_not_registered','exact_binding_and_approval_verification_not_implemented']
    if not manifest['enabled']:blockers.append('disabled_manifest')
    return dict(stage=stage,status='blocked',blockers=blockers,execution_allowed=False,
                model_executed=False,next_stage_authorized=False)


def stratum(n,m,K,kind='capacity',same_work=True):
    require(all(type(x) is int and x>0 for x in (n,m,K)) and n<=m<=n*K,'fixed-work feasibility')
    require(kind in {'capacity','team_size','worst_first','fixed_A','fixed_P','fixed_C','bound_off','R1'},'selected stratum')
    return dict(n=n,m=m,K=K,K_eff=min(K,m-n+1),same_work=same_work,
                three_task_group_possible=m>=n+2 and K>=3,kind=kind,automatic_grid=False)


def same_work_capacity(base,variant):
    """K ceiling study only; forbid new responsibilities, modes or cost edits."""
    a=canonical_domain(base);b=canonical_domain(variant)
    require(a['n']==b['n'],'capacity stratum keeps n fixed')
    old_K=a.pop('K');new_K=b.pop('K')
    require(a==b,'capacity study changed workload or feasible alternatives')
    return dict(schema='joint-same-work-capacity-v1',base_K=old_K,K=new_K,
                same_work_hash=digest(a),task_count=a['m'],same_work_validated=True,
                three_task_group_possible=new_K>=3 and a['m']>=a['n']+2)
