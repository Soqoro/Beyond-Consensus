"""Deterministic joint compiler and exact required-output recovery evaluator."""
from dataclasses import dataclass
from fractions import Fraction
from math import prod
import json
from .model import closure, digest, Invalid
from .joint_schema import (validate_domain, canonical_domain, parse_selection,
    matches, require, price, DOMAIN_VERSION, SELECTION_VERSION)


@dataclass(frozen=True)
class Read:
    port: str
    source: str | None
    event: str | None
    artifact: tuple


@dataclass(frozen=True)
class Operation:
    id: str
    host: str
    owner: str
    kind: str
    mode: str
    reads: tuple
    output: tuple
    initial: Fraction
    replay: Fraction
    operator: str


@dataclass(frozen=True)
class Execution:
    domain_id: str
    organisation_id: str
    objective: str
    unit: str
    n: int
    m: int
    K: int
    K_eff: int
    groups: tuple  # (label, sorted task group); ordered by group, not label.
    sources: tuple
    operations: tuple  # Executable serial schedule, not owner turns.
    edges: tuple
    outputs: tuple
    task_deliverables: tuple


def contract(row):return tuple(row[k] for k in ('artifact','version','type'))


def one(rows, selected):
    found=[r for r in rows if matches(r['when'],selected)]
    require(len(found)==1,'one compatible variant/mode/producer required')
    return found[0]


def explicit_selection(d, A, C, ownership):
    """Offline construction helper, not a selector: derive only forced fields.

    Caller supplies every A/C and P choice. Ambiguous or absent derived fields
    fail; compilation never fills missing selected fields implicitly.
    """
    selected={**A,**C}
    return {'schema':SELECTION_VERSION,'domain':digest(canonical_domain(d)),
        'A':dict(A),'C':dict(C),'ownership':dict(ownership),
        'variants':{t['id']:one(t['variants'],selected)['id'] for t in d['tasks']},
        'modes':{e['id']:one(e['modes'],selected)['id'] for e in d['events'] if matches(e['when'],selected)},
        'outputs':{q['id']:one(q['producers'],selected)['ref'] for q in d['obligations']}}


def compile_organisation(domain, selection):
    d=canonical_domain(domain)
    s=parse_selection(json.dumps(selection,allow_nan=False))
    require(s['domain']==digest(d),'domain mismatch')
    choices={c['id']:c for c in d['choices']}
    for axis in ('A','C'):
        require(set(s[axis])=={k for k,v in choices.items() if v['axis']==axis},'all and only relevant choices')
        require(all(v in choices[k]['options'] for k,v in s[axis].items()),'unknown alternative')
    selected={**s['A'],**s['C']}
    require(not any(matches(c,selected) for c in d['forbidden']),'forbidden joint combination')
    tasks={t['id']:t for t in d['tasks']}; owners={o['id']:o for o in d['owners']}
    require(set(s['ownership'])==set(tasks),'exact ownership coverage')
    require(all(o in tasks[t]['eligible_owners'] for t,o in s['ownership'].items()),'owner eligibility')
    grouped={o:tuple(sorted(t for t in tasks if s['ownership'][t]==o)) for o in owners}
    eff=min(d['K'],d['m']-d['n']+1)
    require(all(1<=len(g)<=eff for g in grouped.values()),'nonempty owners/capacity')
    events={e['id']:e for e in d['events'] if matches(e['when'],selected)}
    for group in d['exclusive']:require(len(set(group)&set(events))<=1,'mutually exclusive events')
    require(set(s['modes'])==set(events) and set(s['variants'])==set(tasks),'active modes/implementations coverage')
    modes={}
    for k,e in events.items():
        mode=one(e['modes'],selected)
        require(s['modes'][k]==mode['id'],'price mode must follow selected inputs/context')
        modes[k]=mode
    deliverables=[]
    for k,t in tasks.items():
        variant=one(t['variants'],selected)
        require(s['variants'][k]==variant['id'],'wrong selected implementation')
        require(set(variant['required_events'])<=set(events),'inactive implementation')
        for name,ref in sorted(variant['deliverables'].items()):
            require(ref['event'] in events and events[ref['event']]['host']==k,'deliverable host/activity')
            deliverables.append((k,name,ref['event']))
    sources={x['id']:x for x in d['sources']};routes={r['id']:r for r in d['routes']}
    order=[e for e in d['schedule']['order'] if e in events];position={e:i for i,e in enumerate(order)}
    operations=[];edges=set();origins={}
    for key in order:
        e=events[key];mode=modes[key];reads=[];inherited=set()
        for port,route_id in sorted(mode['reads'].items()):
            route=routes[route_id];require(matches(route['when'],selected),'route unavailable for choices')
            ref=route['producer'];source=ref['source'];parent=ref['event']
            if parent is not None:
                require(parent in events and position[parent]<position[key],'event cycle or late artifact production')
                producer=events[parent]['output'];seed=s['ownership'][events[parent]['host']]
                edges.add((parent,key));inherited.update(origins[parent])
            else:
                producer=sources[source]['artifact'];seed='protected';inherited.add(source)
            require(producer==e['inputs'][port],'artifact identity/version/type mismatch')
            receiver=s['ownership'][e['host']]
            if route['owner_pairs'] is not None:
                require([seed,receiver] in route['owner_pairs'],'owner/network-position incompatibility')
            reads.append(Read(port,source,parent,contract(producer)))
        require(inherited<=set(e['allowed_sources']),'undeclared protected-source provenance')
        origins[key]=inherited
        operations.append(Operation(key,e['host'],s['ownership'][e['host']],e['kind'],mode['id'],
            tuple(reads),contract(e['output']),price(mode['initial']),price(mode['replay']),mode['operator']))
    outputs=[]
    require(set(s['outputs'])=={q['id'] for q in d['obligations']},'required obligations cannot change')
    for q in d['obligations']:
        ref=one(q['producers'],selected)['ref']
        require(s['outputs'][q['id']]==ref and ref['event'] in events,'selected required producer')
        outputs.append((q['id'],ref['event']))
    for owner,limits in owners.items():
        ops=[v for v in operations if v.owner==owner]
        if limits['max_operations'] is not None:require(len(ops)<=limits['max_operations'],'owner operation limit')
        if limits['max_initial'] is not None:require(sum(v.initial for v in ops)<=price(limits['max_initial'],zero=True),'owner initial resource limit')
    execution=Execution(digest(d),digest(s),d['objective'],d['unit'],d['n'],d['m'],d['K'],eff,
        tuple(sorted(grouped.items(),key=lambda item:item[1])),
        tuple((k,contract(v['artifact']),Fraction(v['value']) if v['value'] is not None else None) for k,v in sorted(sources.items())),
        tuple(operations),tuple(sorted(edges)),tuple(outputs),tuple(deliverables))
    result=evaluate(execution)
    for k,metric in (('initial','initial_expenditure'),('incident','max')):
        if d['budgets'][k] is not None:require(result[metric]<=price(d['budgets'][k],zero=True),'predicted '+k+' budget')
    return execution


def evaluate(execution):
    ops={v.id:v for v in execution.operations};outputs={event for _,event in execution.outputs}
    relevant=closure(outputs,execution.edges,reverse=True)
    recovery=[];vector=[];exposure={}
    for v in execution.operations:
        inherited={v.owner}
        for a,b in execution.edges:
            if b==v.id:inherited.update(exposure[a])
        exposure[v.id]=inherited
    for owner,tasks in execution.groups:
        seeds={v.id for v in execution.operations if v.owner==owner}
        affected=closure(seeds,execution.edges)&relevant
        recovery.append(tuple(sorted(affected)))
        vector.append(sum((ops[v].replay for v in affected),Fraction()))
    total=sum(vector,Fraction());maximum=max(vector)
    identity=sum((ops[v].replay*len(exposure[v]) for v in relevant),Fraction())
    require(total==identity,'owner exposure accounting identity')
    return {'groups':execution.groups,'relevant':tuple(sorted(relevant)),
        'recovery_sets':tuple(recovery),'vector':tuple(vector),'sum':total,'mean':total/execution.n,
        'max':maximum,'objective_pair':(total,maximum) if execution.objective=='mean_first' else (maximum,total),
        'initial_expenditure':sum((v.initial for v in execution.operations),Fraction()),
        'exposure':{v:tuple(sorted(exposure[v])) for v in sorted(ops)},'exposure_sum':identity,
        'responsibilities':execution.m,'charged_operations':len(ops),
        'accounting':'exact encoded prices; not measured spend','unit':execution.unit}


def execute_synthetic(execution):
    """Trusted arithmetic fixtures only. Opaque/natural-language operations cannot run."""
    values={};source_values={s:v for s,_,v in execution.sources};trace=[]
    for op in execution.operations:
        args=[];observed=[]
        for read in op.reads:
            value=source_values[read.source] if read.source is not None else values[read.event]
            require(value is not None,'missing synthetic source value')
            args.append(value);observed.append({'port':read.port,'source':read.source,'event':read.event,'artifact':list(read.artifact)})
        if op.operator=='identity':value=args[0]
        elif op.operator=='square':value=args[0]**2
        elif op.operator=='negate':value=-args[0]
        elif op.operator=='sum':value=sum(args,Fraction())
        elif op.operator=='product':value=prod(args)
        else:raise Invalid('opaque event not executable in synthetic interpreter')
        values[op.id]=value
        trace.append({'event':op.id,'host':op.host,'owner':op.owner,'reads':observed,'output':list(op.output)})
    validate_trace(execution,trace)
    return {'values':values,'outputs':{k:values[v] for k,v in execution.outputs},'trace':trace,
            'model_executed':False,'evidence':'synthetic arithmetic only'}


def validate_trace(execution, trace):
    require(type(trace) is list and len(trace)==len(execution.operations),'missing/extra runtime calls')
    for op,row in zip(execution.operations,trace):
        expected={'event':op.id,'host':op.host,'owner':op.owner,
            'reads':[{'port':r.port,'source':r.source,'event':r.event,'artifact':list(r.artifact)} for r in op.reads],
            'output':list(op.output)}
        require(row==expected,'frozen contract violation: undeclared read/state/host/output/order')
    return True
