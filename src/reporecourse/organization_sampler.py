"""Bounded public organization construction; separately gated private CPU certification.

No model calls, evaluator-ranked selection, topology solver, or training promotion.
The two authored shared interfaces come from public requirements. Reference bodies
are loaded only by qualification and never copied into the public catalog.
"""
from copy import deepcopy
import time
from . import v2
from .common import Rejected, digest, load
from .tasks import ROOT, catalog, load_task, private_task

TASKS=('jaffle-payment-release','github-multioperation-integration')
SCHEMA='rr-organization-catalog-v1'
RECIPES='rr-public-organization-recipes-v1'
MAX_CANDIDATES=12


def configuration(pool=7):
    from .interface import PROFILE
    return v2.configuration(pool,planning_lane='authored_diagnostic',
        execution_contract='plan_scoped_v1',planner_output_cap=6144,interface_profile=PROFILE)


def canonical_key(plan):
    """Known unit-ID/owner relabel equivalence, at most 24 uniquely named products.

    Artifact names and public interfaces are deliberately retained. This does not
    solve arbitrary DAG/semantic equivalence. Ownership equality is preserved.
    """
    units=plan.get('units',[])
    if not 1<=len(units)<=24:raise Rejected('canonicalization_bound')
    ordered=sorted(units,key=lambda u:tuple(sorted(u['produces'])))
    products=[tuple(sorted(u['produces'])) for u in ordered]
    if len(products)!=len(set(products)):raise Rejected('ambiguous_canonical_products')
    ids={u['id']:i for i,u in enumerate(ordered)};owners={};rows=[]
    for u in ordered:
        owner=owners.setdefault(u['worker'],len(owners))
        rows.append(dict(owner=owner,outputs=sorted(u['outputs']),produces=u['produces'],
            depends=sorted(ids[d] for d in u['depends']),
            consumes={a:{**b,'unit':ids[b['unit']]} for a,b in u['consumes'].items()},
            sources=sorted(u['sources']),interfaces=u.get('interfaces',{}),
            terminal_bindings=u.get('terminal_bindings',{o:o for o in u['outputs']})))
    return digest(rows)


def descriptors(plan):
    result=v2.descriptors(plan);depth={};width={}
    for unit in plan['units']:
        level=1+max((depth[d] for d in unit['depends']),default=0)
        depth[unit['id']]=level;width[level]=width.get(level,0)+1
    result.update(maximum_level_width=max(width.values()),
        produced_interfaces=sum(len(u['produces']) for u in plan['units']),
        grouped_outputs=any(len(u['outputs'])>1 for u in plan['units']),
        helper_units=sum(not u['outputs'] for u in plan['units']),
        descriptor_use='structural coverage only; not robustness or cost rewards')
    return result


def merge_independent(plan,public,c):
    """Several obligations become ONE unit/context, not same-owner isolated units."""
    if any(u['depends'] or u['consumes'] or not u['outputs'] for u in plan['units']):
        raise Rejected('merge_requires_independent_terminals')
    outputs=[r['id'] for r in public['required_outputs']]
    formats={r['id']:r['format'] for r in public['required_outputs']}
    unit=dict(id='grouped_outputs',worker=c['workers'][0],outputs=outputs,depends=[],
        description='Implement all named outputs together in this assignment, satisfying each public contract and their bundle consistency requirements.',
        produces=formats,consumes={},sources=sorted(public['sources']),
        interfaces={r['id']:f"Required public output {r['id']}; follow its complete public contract." for r in public['required_outputs']},
        terminal_bindings={o:o for o in outputs})
    return v2.validate_work_plan(dict(schema='rr-work-plan-v2',id='grouped',units=[unit]),public,c)


def public_seed(public,c,organization):
    if public['id'] not in TASKS:raise Rejected('unsupported_sampler_task')
    p=v2.authored_plan(public,c,organization)
    for u in p['units']:
        u['terminal_bindings']={o:o for o in u['outputs']}
        if u['outputs']:
            u['interfaces']={o:f"Required public output {o}; follow its complete public contract." for o in u['outputs']}
            u['description']='Implement '+', '.join(u['outputs'])+' under the public request. Declared imports are available, not mandatory; all original sources remain accessible.'
        elif public['id']=='jaffle-payment-release':
            u['description']='Provide reusable per-order recorded-payment totals and counts, retaining every order including unpaid orders. Amounts remain integer cents.'
            u['interfaces']={'shared_base':'One row per original order: order_id integer, customer_id integer, amount_cents integer (zero without payments), payment_count integer. Preserve distinct equal-valued payments; include unpaid orders. No customer or payment-method aggregation.'}
        else:
            u['description']='Provide the reusable topics-list schema shared by request, response, and client mapping contracts.'
            u['interfaces']={'topic_names':'JSON Schema for an array of strings; empty and duplicate names permitted, order and case preserved, no cardinality limit or normalization.'}
    return v2.validate_work_plan(p,public,c)


def sample(task,public,pool=7,candidate_limit=MAX_CANDIDATES):
    if task not in TASKS or public['id']!=task:raise Rejected('unsupported_sampler_task')
    if type(candidate_limit) is not int or not 3<=candidate_limit<=MAX_CANDIDATES:raise Rejected('candidate_limit_3_through_12')
    start=time.process_time();c=configuration(pool)
    independent=public_seed(public,c,'independent');shared=public_seed(public,c,'shared')
    grouped=merge_independent(independent,public,c)
    concentrated=deepcopy(independent);concentrated['id']='concentrated'
    for u in concentrated['units']:u['worker']='w0'
    renamed=deepcopy(independent);renamed['id']='renamed_copy'
    for i,u in enumerate(renamed['units']):u['id']='renamed_'+str(i);u['worker']=c['workers'][(i+1)%pool]
    attempts=[('separate_obligations',independent,[],['distinct public terminal contracts']),
        ('merge_compatible_assignments',grouped,['separate_obligations'],['independent terminals','same public source access','one assignment context']),
        ('share_public_semantic_interface',shared,[],['task-authored reusable public interface','existing supported artifact type']),
        ('concentrate_ownership',concentrated,['separate_obligations'],['preserve units/scopes; change identity fault scope']),
        ('rename_units_and_owners',renamed,['separate_obligations'],['bijective identity relabel only']),
        ('merge_dependent_assignments',None,['share_public_semantic_interface'],['independent terminals required'])]
    rows=[];seen=set();selected=[]
    for recipe,plan,parents,preconditions in attempts[:candidate_limit]:
        row=dict(recipe=recipe,parents=parents,parent_reference_kind="recipe_id",preconditions=preconditions,
            structure_origin='task_authored_public_seed' if recipe in ('separate_obligations','share_public_semantic_interface') else 'algorithmic_public_transformation',
            selected=False,qualification=dict(status='not_requested'))
        if plan is None:row.update(validity='inapplicable',reason='merge_requires_independent_terminals',plan=None)
        else:
            plan=v2.validate_work_plan(plan,public,c);key=canonical_key(plan)
            row.update(plan=plan,canonical_key=key,plan_id=digest(plan),descriptors=descriptors(plan),
                validity='duplicate' if key in seen else 'valid',reason='known_id_owner_relabel_equivalent' if key in seen else None)
            seen.add(key)
            if recipe in ('separate_obligations','merge_compatible_assignments','share_public_semantic_interface') and row['validity']=='valid':row['selected']=True
        row['candidate_id']=digest({k:v for k,v in row.items() if k!='qualification'})
        if row['selected']:selected.append(row['candidate_id'])
        rows.append(row)
    return dict(task=task,config=c,candidates=rows,selected=selected,
        status='constructed' if len(selected)==3 else 'insufficient_organization_variation',
        selection_rule='first prespecified valid representative: separate obligations, one grouped assignment, reusable public helper; never outcome ranked',
        canonicalization_scope='bounded exact product identities with unit-ID and owner relabeling; ownership partition retained; not semantic equivalence',
        candidate_limit=candidate_limit,candidates_examined=len(rows),construction_cpu_seconds=time.process_time()-start)


def reference_witness(candidate,private):
    """Private binding only; bodies remain the original task author references."""
    organization='shared' if candidate['recipe']=='share_public_semantic_interface' else 'independent'
    return deepcopy(next(w for w in private['witnesses'] if w['organization']==organization))


def _child_cpu():
    try:
        import resource
        usage=resource.getrusage(resource.RUSAGE_CHILDREN)
        return usage.ru_utime+usage.ru_stime
    except (ImportError,AttributeError):return None


def qualify_plan(public,private,candidate,c):
    """Retain a failing selected reference; never replace it with another candidate."""
    from .qualification import implementation_hashes
    start=time.process_time();child_start=_child_cpu()
    try:report=_qualify_plan(public,private,candidate,c)
    except Exception as exc:
        report=dict(status='failed',model_executed=False,task_execution_allowed=False,
            error_type=type(exc).__name__,error_category=str(exc) if isinstance(exc,Rejected) else 'reference_execution_error',
            resource_coverage='partial execution ledgers unavailable; process/child totals retained',
            analysis_cpu_seconds=time.process_time()-start)
    child_end=_child_cpu()
    report.update(private_task_hash=digest(private),reference_implementation_hashes=implementation_hashes(),
        child_cpu_seconds=None if child_start is None or child_end is None else child_end-child_start,
        offline_process_cpu_seconds=time.process_time()-start)
    return report


def _qualify_plan(public,private,candidate,c):
    from .engine import Engine,ScriptedWorker
    from .evaluator import evaluate
    from .resources import Resources
    from .rich_tasks import replace_bound_control
    from .qualification import runtime_versions
    from .track_f_controls import PINS
    versions=runtime_versions();start=time.process_time()
    if any(versions.get(k)!=v for k,v in PINS.items()):
        return dict(status='blocked_prerequisite',required=PINS,actual=versions,model_executed=False)
    witness=reference_witness(candidate,private);plan=v2.validate_work_plan(candidate['plan'],public,c)
    before=digest(public);engine=Engine(public,ScriptedWorker(witness),plan=plan,v2=c,resources=Resources(100000,1200))
    try:
        run=engine.run();grade=evaluate(public,private,run['state']);basis=deepcopy(run['state'])
    finally:engine.env.close()
    controls=[];basis_hash=digest(basis)
    for req in public['required_outputs']:
        key=req['id'];state=deepcopy(basis);state['bound'].pop(key,None)
        missing_grade=evaluate(public,private,state)
        controls.append(dict(obligation=key,mutation='missing',detected=missing_grade.get('success') is False,
            evaluator_resources=missing_grade.get('evaluator_resources')))
        if key not in basis['bound']:
            controls.append(dict(obligation=key,mutation='wrong_semantics',detected=False,reason='no_bound_reference_output'));continue
        a=basis['artifacts'][basis['bound'][key]];fmt=a['format']
        if fmt=='select':
            value='SELECT '+','.join(("'incorrect'" if typ=='string' else '999')+' AS '+col for col,typ in zip(req['columns'],req['types']));fmt='sql'
        elif fmt=='schema':value=True
        else:value=deepcopy(a['content']);value['fields']={}
        state,mutation_cost=replace_bound_control(public,basis,plan,key,value,fmt)
        mutant_grade=evaluate(public,private,state)
        controls.append(dict(obligation=key,mutation='wrong_semantics',detected=mutant_grade.get('success') is False,
            mutation_resources=mutation_cost,evaluator_resources=mutant_grade.get('evaluator_resources')))
        if fmt=='schema':
            state,mutation_cost=replace_bound_control(public,basis,plan,key,False)
            mutant_grade=evaluate(public,private,state)
            controls.append(dict(obligation=key,mutation='reject_all',detected=mutant_grade.get('success') is False,
                mutation_resources=mutation_cost,evaluator_resources=mutant_grade.get('evaluator_resources')))
    repeat=evaluate(public,private,basis)
    evaluator_same=all(repeat.get(k)==grade.get(k) for k in ('status','success','obligations','checks','bound_bundle_hash'))
    reset=Engine(public,ScriptedWorker(witness),plan=plan,v2=c,resources=Resources(100000,1200))
    try:
        reset_run=reset.run();reset_grade=evaluate(public,private,reset_run['state'])
    finally:reset.env.close()
    # Wall/CPU ledgers legitimately vary; compare actual fresh execution outcomes.
    same=reset_run['status']==run['status'] and all(reset_grade.get(k)==grade.get(k) for k in ('status','success','obligations','checks','bound_bundle_hash'))
    integrity=digest(public)==before and digest(basis)==basis_hash
    ok=run['status']=='completed' and grade.get('success') is True and run['conformance']['contract_conformant'] and same and evaluator_same and integrity and all(x['detected'] for x in controls)
    return dict(status='cpu_qualified_reference' if ok else 'failed',evidence='scripted_reference_only',
        model_executed=False,task_execution_allowed=False,plan_id=digest(plan),private_binding_hash=digest(witness),
        runtime_versions=versions,execution_status=run['status'],contract_conformant=run['conformance']['contract_conformant'],
        evaluation={k:grade.get(k) for k in ('status','success','obligations','bound_bundle_hash')},
        evaluator_check_count=len(grade.get('checks',[])),negative_controls=controls,
        reset_repeat_identical=same,evaluator_repeat_identical=evaluator_same,source_integrity=integrity,
        reset_execution_resources=reset_run['resource_profile'],reset_evaluator_resources=reset_grade.get('evaluator_resources'),
        resources=run['resource_profile'],evaluator_resources=grade.get('evaluator_resources'),
        repeat_evaluator_resources=repeat.get('evaluator_resources'),
        executable_binding_edges=sum(len(a['bindings']) for a in basis['artifacts'].values()),
        declared_edges=sum(len(u['consumes']) for u in plan['units']),
        observed_artifact_reads=sum(e['type']=='artifact_read' for e in run['events']),
        analysis_cpu_seconds=time.process_time()-start)


def qualify_catalog(sources,pool=7,candidate_limit=MAX_CANDIDATES,qualify=False):
    from .qualification import implementation_hashes
    begin=time.process_time();cards=catalog(ROOT/'rich')['tasks'];rows=[]
    for task in TASKS:
        card=next(x for x in cards if x['id']==task);blockers=[];available=True
        try:_,public=load_task(task,sources)
        except (Rejected,OSError) as exc:
            available=False;blockers.append(str(exc) if isinstance(exc,Rejected) else 'source_unavailable')
            public=load(ROOT/'rich'/'public'/(task+'.json'))
        row=sample(task,public,pool,candidate_limit)
        row.update(source_group=card['source_group'],split='development',card_hash=digest(card),public_hash=digest(public),
            source_available=available,public_plan_scope='loaded_public_contract' if available else 'unresolved_source_outline_only',
            independent_review=card['independent_review'],license_review=card['license_review'])
        for candidate in row['candidates']:
            if not candidate['selected']:continue
            if qualify and available:candidate['qualification']=qualify_plan(public,private_task(task),candidate,row['config'])
            elif not available:candidate['qualification']=dict(status='blocked_prerequisite',reason='source_missing_or_changed')
        qualified=sum(x['selected'] and x['qualification']['status']=='cpu_qualified_reference' for x in row['candidates'])
        row['qualified_plans']=qualified
        if qualified!=3:blockers.append('three_cpu_qualified_organizations_required')
        row['status']='cpu_qualified_review_pending' if qualified==3 else ('insufficient_organization_variation' if len(row['selected'])!=3 else 'blocked_prerequisite')
        row['blockers']=blockers;rows.append(row)
    result=dict(schema=SCHEMA,recipe_version=RECIPES,config=configuration(pool),tasks=rows,
        status='cpu_qualified_review_pending' if all(r['qualified_plans']==3 for r in rows) else 'blocked_prerequisite',
        implementation_hashes=implementation_hashes(),model_executed=False,task_execution_allowed=False,
        selection_before_qualification=True,future_model_observations=[],
        offline_costs=dict(accounting='Separate construction/reference qualification; never a free deployable planner or historical task debit',
            relationship='analysis_cpu_seconds includes construction and qualification parent CPU; child CPU is separate; subset fields must not be added twice',
            construction_cpu_seconds=sum(r['construction_cpu_seconds'] for r in rows),analysis_cpu_seconds=time.process_time()-begin,
            qualification_process_cpu_seconds=sum(x['qualification'].get('offline_process_cpu_seconds',0) for r in rows for x in r['candidates']),
            qualification_child_cpu_seconds=sum(x['qualification'].get('child_cpu_seconds') or 0 for r in rows for x in r['candidates']),
            qualification_child_cpu_unknown=any(x['qualification'].get('child_cpu_seconds') is None for r in rows for x in r['candidates'] if x['selected'] and qualify and r['source_available'])),
        limitations=['development_only','private_references_are_feasibility_not_model_competence','independent_review_pending','no_B0_calibration','no_training_promotion'])
    result['catalog_id']=digest(result);return result
