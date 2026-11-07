"""Bounded metadata construction and disjoint-component execution-domain integration."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import itertools
import random
from .model import digest
from .joint_d1_local import METADATA
from .joint_schema import require, canonical_domain
from .joint_core import explicit_selection, compile_organisation, evaluate
from .joint_fixtures import artifact, ref, mode, event, route, variant, graph_fixture
from . import composite_math as base, composite_joint as ab

CONDITION='composite-scaling-n2-n8-v2'
ROOT_SEED='bc-composite-scaling-v1'
METHODS=('NEUTRAL','JOINT')


def reviewed(bank):
    require(bank['bank_id']==digest({k:v for k,v in bank.items() if k!='bank_id'}),'bank integrity')
    entries=[deepcopy(c) for c in bank['components'] if c['status']=='reviewed_development']
    require(len({c['source_id'] for c in entries})==len(entries),'unique sources')
    for c in entries:validate_component(c)
    return entries


def validate_component(c):
    require(c['contract_id']==digest({k:c[k] for k in ['source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode']}),'contract hash')
    require(c['namespace']=='c'+c['contract_id'][:10] and c['C']=='direct_parent_artifacts','supported isolated namespace/protocol')
    require(c['A_modes'] in (['base'],['original','algebraic']) and c['reference_mode']==c['A_modes'][0],'unsupported mode contract')
    seen=set()
    for t in c['tasks']:
        require(t['id'] not in seen and set(t['parents'])<=seen,'missing/late parent or duplicate task')
        require(t['responsibility'].strip() and t['fields'] and len(set(t['fields']))==len(t['fields']),'typed string-field obligation')
        seen.add(t['id'])
    require(c['outputs'] and set(c['outputs'])<=seen,'required answers')
    ancestors=set(c['outputs'])
    for t in reversed(c['tasks']):
        if t['id'] in ancestors:ancestors.update(t['parents'])
    require(ancestors==seen,'unrequired padding task')
    require(len(c['statement_sha256'])==64 and c['raw_plan_sha256'],'source/plan bindings')


def task(c,t,proof='base'):
    value=deepcopy(t)
    if proof=='algebraic' and t['id']==c['tasks'][0]['id']:value['responsibility']+=ab.ALGEBRAIC
    return value


def descriptor(c,t,proof):
    return dict(contract_id=c['contract_id'],statement_sha256=c['statement_sha256'],source_id=c['source_id'],
        task=task(c,t,proof),ancestor_mode=proof,prompt=base.PROMPT,worker=ab.WORKER_POLICY,tokenizer_metadata=METADATA,
        input_policy='own statement + complete immediate parent artifacts; fresh context; no bundle/n/owner/method',C=c['C'])


def key(c,t,proof):return digest(descriptor(c,t,proof))


def coverage(components):
    return [dict(key=key(c,t,a),component=c['namespace'],source_id=c['source_id'],task=t['id'],mode=a,descriptor=descriptor(c,t,a))
            for c in components for a in c['A_modes'] for t in c['tasks']]


def domain(components,n,prices=None):
    require(type(n)is int and 2<=n<=8,'n=2..8')
    for c in components:validate_component(c)
    require(len({c['source_id'] for c in components})==len(components),'source duplicate')
    m=sum(len(c['tasks']) for c in components);require(n<=m<=2*n,'K2 task count')
    d=graph_fixture(n,m,2)
    for name in ('tasks','sources','choices','events','routes','obligations'):d[name]=[]
    d['source']=dict(id=digest([c['contract_id'] for c in components]),kind='bound_external',provenance='reviewed component union; no cross-source processing')
    d['unit']='profile_input_plus_generated_tokens' if prices is not None else 'structural_placeholders_not_prices'
    order=[]
    for c in components:
        ns=c['namespace'];choice=ns+'_proof';multiple=len(c['A_modes'])>1
        if multiple:d['choices'].append(dict(id=choice,axis='A',options=c['A_modes']))
        for t in c['tasks']:
            tid=ns+'_'+t['id'];eid=ns+'_e'+t['id'][1:];sid=ns+'_s'+t['id'][1:];a=artifact(ns+'_a'+t['id'][1:],type='math-json')
            own=artifact(sid,type='math-json');d['sources'].append(dict(id=sid,artifact=own,origin='immutable_external',value=None))
            d['routes'].append(route(sid+'_read',ref(source=sid)))
            reads={'own':sid+'_read'};inputs={'own':own}
            for p in t['parents']:
                reads[p]=ns+'_e'+p[1:]+'_read';inputs[p]=artifact(ns+'_a'+p[1:],type='math-json')
            modes=[];variants=[]
            for am in c['A_modes']:
                when={choice:am} if multiple else {};price=prices[key(c,t,am)] if prices is not None else 1
                require(type(price)is int and price>0,'complete positive mode prices')
                modes.append(mode(am,reads,operator='opaque',when=when,initial=str(price),replay=str(price)))
                variants.append(variant(am,[eid],eid,when))
            d['tasks'].append(dict(id=tid,instruction=t['responsibility'],deliverables={'result':a},eligible_owners=[f'o{i}' for i in range(n)],variants=variants))
            d['events'].append(event(eid,tid,inputs,a,modes,sources=[ns+'_s'+x['id'][1:] for x in c['tasks']]));order.append(eid)
            d['routes'].append(route(eid+'_read',ref(event=eid)))
            if t['id'] in c['outputs']:d['obligations'].append(dict(id=ns+'_'+t['id']+'_answer',artifact=a,producers=[dict(when={},ref=ref(event=eid))]))
    d['schedule']['order']=order
    return canonical_domain(d)


def structural(d):
    v=deepcopy(d);v['unit']='price_free_structure'
    for e in v['events']:
        for mode in e['modes']:mode['initial']=mode['replay']=None
    return v


def neutral(components,n):
    d=domain(components,n)
    work=dict(components=[{k:c[k] for k in ('source_id','contract_id','tasks','outputs','A_modes','C','reference_mode')} for c in components],order=[c['namespace'] for c in components])
    work_id=digest(work);structure=structural(d)
    pre=dict(work_id=work_id,structure=structure,n=n,K=2,worker=dict(ab.WORKER_POLICY,tokenizer_metadata=METADATA),objective='mean_first',neutral_rule='one seeded permutation; first 2(m-n) tasks paired; canonical unlabelled groups')
    pre_id=digest(pre);seed=int(digest([ROOT_SEED,pre_id]),16)
    tasks=sorted(t['id'] for t in d['tasks']);random.Random(seed).shuffle(tasks)
    pairs=d['m']-n;groups=[sorted(tasks[2*i:2*i+2]) for i in range(pairs)]+[[t] for t in tasks[2*pairs:]];groups.sort()
    own={t:f'o{i}' for i,g in enumerate(groups) for t in g}
    A={c['namespace']+'_proof':c['reference_mode'] for c in components if len(c['A_modes'])>1}
    selection=explicit_selection(d,A,{},own);compile_organisation(d,selection)
    # Check every admitted mode's input/host/obligation feasibility, without scores.
    for options in itertools.product(*(c['A_modes'] for c in components)):
        a={c['namespace']+'_proof':x for c,x in zip(components,options) if len(c['A_modes'])>1}
        compile_organisation(d,explicit_selection(d,a,{},own))
    return dict(work_id=work_id,domain_structure_id=digest(structure),preprice_specification=pre,preprice_id=pre_id,neutral_seed=str(seed),neutral=dict(A=A,C={},ownership=own),n=n,K=2,m=d['m'],q=len(components))


def isolation(d):
    routes={r['id']:r for r in d['routes']};events={e['id']:e for e in d['events']}
    for e in d['events']:
        ns=e['host'].split('_')[0]
        if e['kind']!='compute' or any(s.split('_')[0]!=ns for s in e['allowed_sources']):return False
        for m in e['modes']:
            for rid in m['reads'].values():
                r=routes[rid];p=r['producer'];name=p['event'] or p['source']
                if name.split('_')[0]!=ns or r['transform']!='identity':return False
    return True


def call_bounds(components,n):
    d=domain(components,n);L=len(d['events']);generic=2*(n+1)*L;isolated=isolation(d)
    component=2*sum(len(c['tasks'])*(1+min(n,len(c['tasks']))) for c in components)
    return dict(Lmax=L,generic=generic,component=component if isolated else None,isolation_verified=isolated,evaluation_calls=component if isolated else generic)


def construct(entries,n,slot,previous=(),max_states=50000):
    """Bounded complete DFS, no unsound (index,sum) memoisation or score feedback."""
    ordered=sorted(entries,key=lambda c:digest([ROOT_SEED,n,slot,c['source_id']]))
    excluded={tuple(sorted(x)) for x in previous};used=set().union(*(set(x) for x in previous)) if previous else set()
    visited=0;rejected=[]
    class Exhausted(Exception):pass
    def search(index,remaining,chosen,disjoint):
        nonlocal visited
        visited+=1
        if visited>max_states:raise Exhausted()
        if remaining==0:
            ids=tuple(sorted(c['source_id'] for c in chosen))
            if len(ids)<2 or ids in excluded:return None
            selected=sorted(chosen,key=lambda c:c['source_id'])
            try:binding=neutral(selected,n)
            except (ValueError,KeyError,TypeError) as exc:
                rejected.append(dict(sources=list(ids),reason=str(exc)));return None
            return selected,binding
        if remaining<0 or index==len(ordered):return None
        if sum(len(c['tasks']) for c in ordered[index:])<remaining:return None
        c=ordered[index]
        if not disjoint or c['source_id'] not in used:
            found=search(index+1,remaining-len(c['tasks']),chosen+[c],disjoint)
            if found:return found
        return search(index+1,remaining,chosen,disjoint)
    try:
        for total in sorted(range(n+1,2*n+1),key=lambda x:(abs(x-(3*n+1)//2),x)):
            for disjoint in (True,False):
                found=search(0,total,[],disjoint)
                if found:
                    cs,b=found
                    return dict(status='supported_frozen',sources=[c['source_id'] for c in cs],components=cs,**b,call_bounds=call_bounds(cs,n),visited_states=visited,construction_rejections=rejected,slot=slot,source_disjoint_preferred=disjoint)
    except (Exhausted,TimeoutError):return dict(status='CONSTRUCTION_UNRESOLVED',n=n,slot=slot,visited_states=visited,construction_rejections=rejected)
    return dict(status='NO_SUPPORTED_BUNDLE_IN_REVIEWED_BANK',n=n,slot=slot,visited_states=visited,construction_rejections=rejected)


def packet(bank):
    entries=reviewed(bank);matrix=[];bundles=[]
    for n in range(2,9):
        for slot in range(1,4):
            row=dict(n=n,slot=slot,methods=list(METHODS),status='PENDING_REVIEW_NOT_FROZEN',execution='unrun',reason='later prospective wave; not frozen or authorised')
            if slot==1 and n in (2,4,6,8):
                b=construct(entries,n,slot);row['status']=b['status']
                if b['status']=='supported_frozen':row['preprice_id']=b['preprice_id'];bundles.append(b)
            matrix.append(row)
    used={c['source_id']:c for b in bundles for c in b['components']};components=sorted(used.values(),key=lambda c:c['source_id'])
    profiles=coverage(components)
    consumers={r['key']:[b['preprice_id'] for b in bundles if r['source_id'] in b['sources']] for r in profiles}
    return dict(schema='composite-scaling-wave-v2',bank_id=bank['bank_id'],bank=bank,matrix=matrix,bundles=bundles,profile_coverage=profiles,profile_consumers=consumers,
        later_waves_enabled=False,limits=dict(**ab.LIMITS,maximum_calls_override=None),methods=list(METHODS),execution_allowed=False)
