"""Read-only plan/trace comparison. Missing observations remain unknown."""
from copy import deepcopy
from .common import digest


def report(row):
    plan=row.get('plan') or {}
    state=row.get('state',row)
    artifacts=state.get('artifacts',{})
    events=state.get('events',row.get('events',row.get('event_timeline',[])))
    units={u['id']:u for u in plan.get('units',[])}
    declared={(x['unit'],u['id']) for u in units.values() for x in u.get('consumes',{}).values()}
    # Older authored plans have depends but no typed consumes.
    declared|={(d,u['id']) for u in units.values() for d in u.get('depends',[])}
    producers={};stages={};active={};ambiguous=[]
    for e in events:
        if e.get('type')=='assignment_start':active[e['worker']]=(e['unit'],e.get('stage','unknown'))
        if e.get('type')=='publish':
            unit=e.get('unit',e.get('producer_unit'));stage=e.get('stage')
            if unit is None and e.get('worker') in active:unit,stage=active[e['worker']]
            if unit is not None:producers[e['version']]=unit;stages[e['version']]=stage or 'unknown'
        if e.get('type')=='unit_end':
            for v in e.get('new_versions',[]):
                if v in producers and producers[v]!=e['unit']:ambiguous.append(v)
                else:producers[v]=e['unit'];stages[v]=e.get('stage','unknown')
    for v,a in artifacts.items():
        if a.get('producer_unit') is not None:producers[v]=a['producer_unit'];stages[v]=a.get('stage','unknown')
    direct=[];unknown=[];transitive=[]
    def ancestors(v,seen):
        out=set();pending=[v];seen=set(seen)
        while pending:
            current=pending.pop()
            if current in seen or current not in artifacts:continue
            seen.add(current);parents=set(artifacts[current].get('bindings',{}).values())
            out|=parents;pending.extend(parents-seen)
        return out
    for v,a in artifacts.items():
        dst=producers.get(v)
        for alias,p in a.get('bindings',{}).items():
            src=producers.get(p)
            r=dict(producer=src,consumer=dst,alias=alias,version=p,consumer_version=v,stage=stages.get(v,'unknown'))
            if src is None or dst is None or v in ambiguous or p in ambiguous:unknown.append(r)
            else:direct.append({**r,'declared':src==dst or (src,dst) in declared})
        transitive.append({'version':v,'ancestor_versions':sorted(ancestors(v,set())),
                           'recorded_exposure':deepcopy(a.get('exposure',[]))})
    # Explicit body reads/reexecution are direct imports even without a later
    # publication. Metadata and inherited provenance remain separate surfaces.
    for e in events:
        if e.get('type')!='scope_delivery' or e.get('surface') not in ('read_artifact','execute_artifact','rebind_artifact','bind_output'):continue
        for v in e.get('direct_versions',[]):
            src=producers.get(v);dst=e.get('unit')
            r=dict(producer=src,consumer=dst,version=v,consumer_version=None,
                   surface=e['surface'],stage=e.get('stage','unknown'))
            if src is None or dst is None:unknown.append(r)
            else:direct.append({**r,'declared':src==dst or (src,dst) in declared})
    primary={(r['producer'],r['consumer']) for r in direct if r['producer']!=r['consumer'] and r['stage']=='primary'}
    observed={(r['producer'],r['consumer']) for r in direct if r['producer']!=r['consumer']}
    scopes=state.get('scope_state')
    contract=state.get('execution_contract',row.get('execution_contract','adaptive_legacy'))
    exposure=[deepcopy(e) for e in events if e.get('type') in ('scope_observation','scope_delivery','context_reset','message','artifact_read')]
    denied=[deepcopy(e) for e in events if e.get('type')=='scope_denied']
    violations=[deepcopy(e) for e in events if e.get('type')=='protocol_violation']
    complete=bool(scopes and scopes.get('coverage')=='mediated-v1' and events) and all(a.get('scope_id') for a in artifacts.values())
    if complete:
        from .scope import influence
        published={e.get('version') for e in events if e.get('type')=='publish'}
        complete=set(artifacts)<=published and all(any(e.get('type')=='context_reset' and e.get('scope_id')==sid for e in events) for sid in scopes['records'])
        for e in exposure:
            if e.get('type') not in ('scope_observation','scope_delivery'):continue
            permission=scopes['records'].get(e.get('scope_id'))
            if permission is None:
                complete=False;continue
            allowed=set(permission['imports'].values())|set(permission['recovery_versions'])|{v for v,a in artifacts.items() if a.get('scope_id')==permission['id']}
            direct_versions=set(e.get('direct_versions',e.get('visible_versions',[])))
            if not direct_versions<=allowed:violations.append({'type':'protocol_violation','surface':e.get('surface','observation'),'scope_id':permission['id']})
            ancestry=set()
            try:
                for v in allowed:ancestry |= influence(artifacts,v)
            except Exception:complete=False
            if not set(e.get('transitive_versions',[]))<=ancestry:violations.append({'type':'protocol_violation','surface':'transitive_exposure','scope_id':permission['id']})
    if complete:
        for r in direct:
            if r['stage']=='primary' and not r['declared']:violations.append({'type':'protocol_violation','surface':'binding',**r})
        from .scope import validate_bundle
        try:validate_bundle(state)
        except Exception:violations.append({'type':'protocol_violation','surface':'publication_integrity'})
    conformant=(None if contract=='adaptive_legacy' else False if violations else
                None if not complete or unknown else True)
    resource=row.get('resource_profile',row.get('resources',{}))
    in_budget=None
    if all(k in resource for k in ('actual_tokens','uncertain_tokens','token_cap','cpu_cap_debit','cpu_cap')):
        in_budget=(resource['actual_tokens']+resource['uncertain_tokens']<=resource['token_cap'] and resource['cpu_cap_debit']<=resource['cpu_cap'] and not resource.get('reserved_tokens') and not resource.get('cpu_reserved'))
    return dict(schema='rr-plan-conformance-v1',execution_contract=contract,plan_hash=digest(plan),
        declared_permissions=[{'producer':a,'consumer':b} for a,b in sorted(declared)],
        planned_active_workers=len({u.get('worker') for u in units.values()}-{None}),
        observed_active_workers=len({e.get('worker') for e in events if e.get('type') in ('assignment_start','unit_end')}-{None}),
        version_resolution='latest permitted producer publication at assignment admission; immutable for that assignment',
        direct_imports=direct,unknown_imports=unknown,realized_edges=[list(e) for e in sorted(observed)],
        extra_primary_edges=[list(e) for e in sorted(primary-declared)],
        allowed_not_observed=[list(e) for e in sorted(declared-observed)],
        unused_interpretation='not observed in supplied evidence; no forced reads',
        transitive_provenance=transitive,observed_exposures=exposure,denied_requests=denied,
        recovery_overlays=deepcopy(scopes.get('overlays',[])) if scopes else [],
        evidence_complete=complete,unknown_surfaces=[] if complete else ['prompt/metadata/message/context coverage','publication scope receipts'],
        contract_conformant=conformant,protocol_violations=violations,
        task_correct=row.get('evaluation',{}).get('success',row.get('success',row.get('outcome',{}).get('success'))),
        in_budget=in_budget,execution_status=row.get('status',row.get('outcome',{}).get('status')),
        historical_scores_changed=False,model_executed=False,sql_executed=False,
        interpretation='adaptive deviations are descriptive; allowed edges are permissions, not required consumption; mediated surfaces do not prove semantic independence')
