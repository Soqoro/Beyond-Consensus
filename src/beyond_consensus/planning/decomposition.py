"""Finite public-data plans. Local engineering opt-in, not calibrated research.

Selected plans are installed into EpisodeEngine, not run by another executor.
Structural validity never certifies semantic equivalence of generated instructions.
"""
from copy import deepcopy
from dataclasses import replace
import itertools
import math

from ..schemas import DelegationPlan, RecoveryUnit, WORKERS
from ..util import BCError, canonical, digest, strict_keys
from ..runtime.sqlite_executor import identifier

SCHEMA = 'bc-finite-decomposition-v1'
MAX_CANDIDATES = 4
MAX_UNITS = 6


def validate(candidate, task):
    strict_keys(candidate, {'id','units','schedule','terminal_requirements'}, {'id','units','schedule','terminal_requirements'})
    identifier(candidate['id'])
    if candidate['terminal_requirements'] != list(task.required_outputs):
        raise BCError('Original terminal requirements must be preserved exactly')
    units = candidate['units']
    if not isinstance(units, list) or not 1 <= len(units) <= MAX_UNITS or len(canonical(candidate)) > 24000:
        raise BCError('Plan size limit')
    seen, terminals = {}, set()
    for unit in units:
        strict_keys(unit, {'id','owner','inputs','contract','terminal','read_sources','message_recipients'},
                         {'id','owner','inputs','contract','terminal','read_sources','message_recipients'})
        identifier(unit['id'])
        if unit['id'] in seen or unit['owner'] not in WORKERS or type(unit['terminal']) is not bool:
            raise BCError('Invalid unit identity')
        if (unit['read_sources'] != list(task.sources) or unit['message_recipients'] != list(WORKERS)):
            raise BCError('Initial catalog holds original-source/message access fixed across plans')
        if not isinstance(unit['inputs'], list) or len(set(unit['inputs'])) != len(unit['inputs']):
            raise BCError('Invalid prerequisites')
        contract = unit['contract']
        if unit['terminal']:
            if unit['id'] not in task.required_outputs or contract != task.sources[unit['id']]:
                raise BCError('Terminal public contract changed')
            terminals.add(unit['id'])
        else:
            strict_keys(contract, {'kind','name','requirement','output_columns'}, {'kind','name','requirement','output_columns'})
            if unit['id'] in task.sources or contract['kind'] != 'view':
                raise BCError('Intermediate must be a fresh view')
            identifier(contract['name'])
            # Compare public schema only, never evaluator data.
            tables = {name for source in task.sources.values() for name in source.get('schema', {})}
            if contract['name'].lower() in {n.lower() for n in tables}:
                raise BCError('Intermediate shadows original data')
            if not isinstance(contract['requirement'], str) or not 1 <= len(contract['requirement']) <= 4096:
                raise BCError('Bounded intermediate instruction required')
            if not isinstance(contract['output_columns'], list) or not 1 <= len(contract['output_columns']) <= 32:
                raise BCError('Bounded intermediate columns required')
            for col in contract['output_columns']:
                identifier(col)
        seen[unit['id']] = unit
    if terminals != set(task.required_outputs):
        raise BCError('Missing original terminal output')
    schedule = candidate['schedule']
    if not isinstance(schedule, list) or len(schedule) != len(seen) or set(schedule) != set(seen):
        raise BCError('Schedule must execute every unit once')
    available = set()
    for name in schedule:
        if not set(seen[name]['inputs']) <= available:
            raise BCError('Cyclic, missing or unscheduled dependency')
        available.add(name)
    needed = set(terminals)
    while True:
        expanded = needed | {parent for key in needed for parent in seen[key]['inputs']}
        if expanded == needed:
            break
        needed = expanded
    if needed != set(seen):
        raise BCError('Unused intermediates do not constitute work decomposition')
    view_names = [u['contract'].get('name') for u in units if u['contract'].get('kind') == 'view']
    if len(view_names) != len(set(view_names)):
        raise BCError('Duplicate view boundary names')
    # Ignore owner and candidate ID when measuring graph variation. Canonicalize
    # intermediate names by all permutations (at most four intermediates).
    intermediate = [k for k in seen if k not in terminals]
    encodings = []
    for ordering in itertools.permutations(intermediate):
        names = {key:f'intermediate_{i}' for i,key in enumerate(ordering)}
        mapped = lambda key: names.get(key,key)
        encodings.append(sorted((mapped(k), tuple(sorted(mapped(i) for i in u['inputs'])), u['terminal']) for k,u in seen.items()))
    fingerprint = digest(min(encodings, key=canonical))
    return {'status':'structurally_valid', 'semantic_equivalence':'unverified',
            'effective_graph_hash':fingerprint, 'original_obligations':list(task.required_outputs)}


def inspect(candidates, task):
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= MAX_CANDIDATES:
        raise BCError('Supply two to four finite candidates')
    reports, unique = [], set()
    for i, candidate in enumerate(candidates):
        try:
            report = validate(candidate, task)
            unique.add(report['effective_graph_hash'])
        except (BCError, TypeError, KeyError, ValueError):
            report = {'status':'invalid', 'reason':'structural_scope_or_graph_rejection'}
        reports.append({'index':i, **report})
    return {'schema':SCHEMA, 'candidates':reports, 'effective_unique_plans':len(unique),
            'status':'structural_variation' if len(unique)>=2 else 'insufficient_decomposition_variation',
            'native_competence_gate':False, 'calibrated_cost_gate':False,
            'policy_campaign_enabled':False}


def affected(candidate, identity, observed_edges=()):
    """All work by the identity, plus declared AND observed downstream closure."""
    hit = {u['id'] for u in candidate['units'] if u['owner']==identity}
    edges = {(p,u['id']) for u in candidate['units'] for p in u['inputs']} | set(observed_edges)
    while True:
        expanded = hit | {b for a,b in edges if a in hit}
        if expanded == hit:
            return hit
        hit = expanded


def rank_costed(evaluations, mode):
    """Shared finite objective/tie-break; eligibility is the caller's gate."""
    return min(evaluations,key=lambda e:(e['objective'] if mode=='recovery' else e['clean'], e['id']))


def select(candidates, task, costs, mode, cap, reserve, provenance, *, engineering=False):
    """Exhaustive tiny catalog, same cost rows/scenarios/reserve for all selectors.

    Costs include all phases explicitly. None/missing is never interpreted as 0.
    Repair rows are per-unit, recomputed at most once in an identity closure.
    """
    report = inspect(candidates, task)
    if report['status'] != 'structural_variation':
        raise BCError(report['status'])
    if mode not in ('fixed','nominal','recovery'):
        raise BCError('Unknown selector')
    if not engineering:
        raise BCError('Policy campaign blocked: observed native competence and matched calibration required')
    if provenance.get('status') != 'constructed_engineering_only':
        raise BCError('No compatible measured calibration has been qualified for this executor')
    evaluations = []
    for candidate, validity in zip(candidates, report['candidates']):
        if validity['status'] != 'structurally_valid':
            continue
        row = costs.get(candidate['id'], {})
        numbers = [row.get(k) for k in ('generation','selection','checking','integration')]
        ids = [u['id'] for u in candidate['units']]
        numbers += [row.get('primary',{}).get(u) for u in ids]
        numbers += [row.get('repair',{}).get(u) for u in ids]
        if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in numbers) or row.get('quality_eligible') is not True:
            evaluations.append({'id':candidate['id'],'status':'unknown_cost_or_quality'})
            continue
        clean = sum(row[k] for k in ('generation','selection','checking','integration'))+sum(row['primary'][u] for u in ids)
        scenarios = {w:sum(row['repair'][u] for u in affected(candidate,w)) for w in WORKERS}
        worst = max(scenarios.values())
        evaluations.append({'id':candidate['id'],'status':'eligible' if clean<=cap-reserve and clean+worst<=cap else 'over_budget',
                            'clean':clean,'worst_repair':worst,'objective':clean+worst,'scenarios':scenarios})
    eligible = [e for e in evaluations if e['status']=='eligible']
    if mode=='fixed':
        eligible = [e for e in eligible if e['id']==candidates[0]['id']]
    if not eligible:
        raise BCError('No costed feasible candidate')
    chosen = rank_costed(eligible, mode)
    return {'selected':chosen['id'],'evaluations':evaluations,'reserve':reserve,
            'status':'constructed_engineering_only','preparation':False,'repair_backend':'shared_existing_JIT',
            'cost_provenance':provenance,'search_states':len(candidates)*len(WORKERS)}


def install(task, candidate, config):
    """Local mock gate only. Actual native policy manifests remain blocked."""
    if (task.kind != 'sqlite_fixture' or not task.metadata.get('synthetic') or
            config.model.backend != 'mock' or config.protocol != 'A' or config.policies != ('jit',)):
        raise BCError('Finite graph execution is local synthetic/JIT only; scientific gates remain blocked')
    validate(candidate, task)
    sources = deepcopy(task.sources)
    sources.update({u['id']:deepcopy(u['contract']) for u in candidate['units']})
    metadata = deepcopy(task.metadata)
    metadata['dependencies'] = {u['id']:list(u['inputs']) for u in candidate['units']}
    metadata['finite_graph_installed'] = digest(candidate)
    return replace(task, sources=sources, metadata=metadata)


def delegation(candidate, reserve):
    by_id = {u['id']:u for u in candidate['units']}
    return DelegationPlan(candidate['id'], tuple(RecoveryUnit(k, by_id[k]['contract']['requirement'],
        by_id[k]['owner'],tuple(by_id[k]['inputs']),(k,),'finite_replaceable_view_v1') for k in candidate['schedule']),
        reserve=reserve, allocation_status='uncalibrated_engineering_graph')


def generation_prompt(task):
    """Allowlisted public inputs only. This function never calls a model."""
    public = {'specification':task.specification, 'sources':task.sources,
              'terminal_requirements':list(task.required_outputs), 'workers':list(WORKERS)}
    return ('Propose 2 to 4 finite work graphs. Preserve every terminal contract exactly. '
            'Intermediate units may define a view using public instructions. No solution SQL. '
            'Return a JSON list of {id,terminal_requirements,units,schedule}. '
            'Each unit has {id,owner,inputs,contract,terminal,read_sources,message_recipients}. '
            'Terminal contract may be {source_contract: the unit ID}, which is expanded to that exact public contract. Intermediate contract has '
            '{kind:"view",name,requirement,output_columns}. All read_sources are the original source IDs; '
            'all message_recipients are the fixed four workers. Schedule is topological. '
            'Structural validity does not establish correctness.\n'+canonical(public))


def generate_candidates(backend, task, config, ledger, seed, *, user_authorized=False):
    """One bounded planner call through the same frozen backend/JSON envelope.

    The existing message action is a serialization carrier ONLY: no message is
    delivered and no worker tool is executed. The text must encode the public
    candidate schema. Invalid output consumes its charge and yields no catalog.
    """
    import json
    import math
    from ..models.action_schema import contract, DECODER_CPU_SECONDS
    if not user_authorized:
        raise BCError('Real candidate generation requires separate user authorization')
    if config.model.backend != 'mock' and config.model.checkpoint != 'Qwen/Qwen3.5-27B':
        raise BCError('This phase uses only the pinned frozen 27B backend')
    messages=[{'role':'system','content':
        'Return exactly one JSON action with tool message, recipient w0, and text containing a JSON-encoded candidate list. '
        'This is a planning envelope, not a delivered message. Maximum decoded text length 4096 characters. '
        'No tools are executed.\n'+generation_prompt(task)}]
    n=backend.count_input(messages)
    if n+config.model.max_new_tokens>config.model.context_limit:
        raise BCError('Planner context limit; no source truncation')
    constrained=config.model.action_constraint!='none'
    reserve_decoder=DECODER_CPU_SECONDS*config.budget.tool_charge if constrained else 0
    call=ledger.reserve_call('planning_generation',n,config.model.max_new_tokens,reserve_decoder,generation_seed=seed)
    decoder=ledger.reserve_work('planning_generation',reserve_decoder,'constrained_decoding') if constrained else None
    try:
        generation=backend.generate(messages,config.model.max_new_tokens,seed)
        ledger.reconcile(call,output_tokens=generation.output_tokens,reasoning_tokens=generation.reasoning_tokens,
                         device_seconds=generation.device_seconds)
        if constrained:
            details=generation.diagnostics
            seconds=details.get('constraint_cpu_seconds')
            if (details.get('action_constraint')!=contract(config.model.action_constraint) or
                    type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<=seconds<=DECODER_CPU_SECONDS):
                raise BCError('Planner decoder provenance/accounting missing')
            ledger.reconcile_work(decoder,math.ceil(seconds)*config.budget.tool_charge)
            if details.get('constraint_complete') is not True:
                raise BCError('Incomplete planner envelope')
    except Exception:
        if call in ledger.reservations:ledger.reconcile(call,output_tokens=None,failed=True)
        if decoder in ledger.reservations:ledger.reconcile_work(decoder,None)
        raise
    ledger.charge('planning_validation',config.budget.tool_charge,kind='finite_catalogue_validation',cpu_limit_seconds=1)
    try:
        envelope=json.loads(generation.text)
        strict_keys(envelope,{'tool','recipient','text'},{'tool','recipient','text'})
        if envelope['tool']!='message' or envelope['recipient']!='w0' or not isinstance(envelope['text'],str) or len(envelope['text'])>4096:
            raise BCError('Invalid planner carrier')
        candidates=json.loads(envelope['text'])
        if not isinstance(candidates,list) or not 2<=len(candidates)<=MAX_CANDIDATES:
            raise BCError('Candidate count')
        for candidate in candidates:
            for unit in candidate.get('units',[]):
                if unit.get('terminal') is True and unit.get('contract') == {'source_contract':unit.get('id')}:
                    unit['contract']=deepcopy(task.sources[unit['id']])
        report=inspect(candidates,task)
    except (BCError,ValueError,TypeError,KeyError,RecursionError):
        candidates=[]
        report={'status':'invalid_candidate_envelope','effective_unique_plans':0}
    return {'schema':SCHEMA,'candidates':candidates,'inspection':report,'model_calls':1,
        'prompt_hash':digest(messages),'response_hash':digest(generation.text),'seed':seed,
        'message_delivered':False,'reference_access':False,'backend':config.model.backend,
        'native_policy_gate':False,'generation_diagnostics':generation.diagnostics}


def resolve(task, config):
    """Resolve a frozen explicit candidate or local constructed-cost selector."""
    candidate=task.metadata.get('finite_decomposition')
    catalog=task.metadata.get('finite_catalogue')
    if candidate and catalog:
        raise BCError('Freeze either an explicit candidate or a finite selector catalog')
    report=None
    if catalog:
        if config.model.backend!='mock' or task.kind!='sqlite_fixture' or not task.metadata.get('synthetic'):
            raise BCError('Measured finite policy selection remains gated')
        report=select(catalog['candidates'],task,catalog['costs'],catalog['selector'],config.budget.total,
                      config.budget.total*config.budget.reserve_fraction,catalog['provenance'],engineering=True)
        candidate=next(p for p in catalog['candidates'] if p['id']==report['selected'])
    installed=install(task,candidate,config) if candidate else task
    return installed,candidate,report


def dependency_report(candidate, store):
    declared={(p,u['id']) for u in candidate['units'] for p in u['inputs']}
    units={u['id'] for u in candidate['units']}
    observed=set()
    contributors={u:set() for u in units}
    for artifact in store.artifacts.values():
        if artifact.unit not in units:
            continue
        contributors[artifact.unit].update(artifact.contributors)
        for parent in artifact.parents:
            if parent in store.artifacts:
                origin=store.artifacts[parent].unit
                if origin in units and origin != artifact.unit:
                    observed.add((origin,artifact.unit))
    return {'declared_edges':sorted(declared),'observed_edges':sorted(observed),
            'undeclared_observed_edges':sorted(observed-declared),
            'unit_contributors':{u:sorted(c) for u,c in contributors.items()},
            'message_events':sum(e['type']=='message' for e in store.events),
            'semantics':'Observed history includes invalidated versions; actual provenance governs repair.'}
