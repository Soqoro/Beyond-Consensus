"""Exact rational general matching, independent bounded oracle and baselines."""
from fractions import Fraction
from itertools import combinations
from math import lcm
import random
import time
from .model import Allocation, Invalid, closure, digest, groups, rational

MATCHING_VERSION = '3.4.2'  # Separate Phase II pin; Phase I pins are untouched.


def prepare(w, n, costs):
    if type(n) is not int or not n <= len(w.ids) <= 2*n: raise Invalid('n <= m <= 2n')
    if set(costs) != set(w.ids): raise Invalid('cost/task coverage')
    c = {t: rational(costs[t]) for t in w.ids}
    ds = {t: closure([t], w.edges) for t in w.ids}
    weights = {g: sum((c[t] for t in set().union(*(ds[v] for v in g))), Fraction())
               for k in (1,2) for g in combinations(w.ids, k)}
    return c, ds, weights


def metrics(w, n, allocation, costs):
    gs = groups(w,n,allocation); c,ds,weights = prepare(w,n,costs)
    rs = [weights[g] for g in gs]
    return {'groups': gs, 'R': rs, 'closures': [sorted(set().union(*(ds[v] for v in g))) for g in gs],
            'sum': sum(rs), 'max': max(rs), 'mean': sum(rs)/n,
            'common_mean_max': [sum(rs)/n,max(rs)]}


def match_table(ids, n, table, objective, budget=None):
    """Polynomial general weighted matching. Never falls back to enumeration."""
    try: import networkx as nx
    except ImportError as exc: raise Invalid('optional NetworkX 3.4.2 unavailable; no fallback') from exc
    if nx.__version__ != MATCHING_VERSION: raise Invalid('Phase II matching version must be 3.4.2')
    if objective not in ('mean','worst'): raise Invalid('objective')
    limit = rational(budget,False) if budget is not None else None
    scale = lcm(*(x.denominator for x in table.values()), limit.denominator if limit is not None else 1)
    # Integer positions keep arbitrary real labels disjoint from virtual vertices.
    edges = {(i,j): table[tuple(sorted((ids[i],ids[j])))] for i,j in combinations(range(len(ids)),2)}
    for i,t in enumerate(ids):
        for j in range(len(ids),2*n): edges[i,j] = table[(t,)]
    weighted = {p:int(v*scale) for p,v in edges.items() if limit is None or v <= limit}
    thresholds = sorted(set(weighted.values())); calls=0
    def match(threshold):
        nonlocal calls
        calls += 1; graph=nx.Graph();graph.add_nodes_from(range(2*n))
        for (a,b),v in sorted(weighted.items()):
            if v <= threshold: graph.add_edge(a,b,weight=v)
        result=nx.min_weight_matching(graph,weight='weight')
        if len(result)!=n or not nx.is_perfect_matching(graph,result): return None
        ps=sorted(tuple(sorted(p)) for p in result)
        return sum(weighted[p] for p in ps),ps
    initial = match(thresholds[-1]) if thresholds else None
    meta={'dependency_version':nx.__version__,'solver':'networkx.min_weight_matching',
          'integer_scale':scale,'virtual_vertices':2*n-len(ids),'virtual_virtual_edges':0,
          'budget':limit,'budget_claim':'supplied-estimates-only' if limit is not None else 'not_applicable'}
    if initial is None: return {**meta,'status':'infeasible','matching_calls':calls}
    low, high = 0,len(thresholds)-1
    while low<high:
        mid=(low+high)//2;v=match(thresholds[mid])
        if v is not None and (objective=='worst' or v[0]==initial[0]): high=mid
        else: low=mid+1
    result=match(thresholds[low]);assert result is not None
    gs=tuple(sorted(tuple(ids[i] for i in p if i<len(ids)) for p in result[1]))
    assert all(1<=len(g)<=2 for g in gs)
    return {**meta,'status':'optimal','groups':gs,'matching_calls':calls}


def solve(w,n,costs,objective='mean',budget=None,cost_model='supplied-rational-v1',direct=False):
    start=time.process_time(); c,ds,weights=prepare(w,n,costs)
    if direct: weights={g:sum(c[t] for t in g) for g in weights}
    prep=time.process_time()-start; start=time.process_time()
    result=match_table(w.ids,n,weights,objective,budget)
    solve_time=time.process_time()-start
    if result['status']=='optimal':
        result.update(metrics(w,n,result['groups'],c))
        if direct: result['owned_costs']=[sum(c[t] for t in g) for g in result['groups']]
        values=result['owned_costs'] if direct else result['R']
        result['optimised_pair']=[sum(values),max(values)] if objective=='mean' else [max(values),sum(values)]
    return {**result,'objective':objective,'objective_basis':'owned-task-costs' if direct else 'recovery-union-costs','cost_model':cost_model,'preprocessing_cpu_seconds':prep,
            'solve_cpu_seconds':solve_time,'exactness':'represented rational estimates, not realised costs'}


def partitions(items,n):
    """Independent restricted partition recursion; bounded at eight tasks."""
    if len(items)>8: raise Invalid('reference limited to eight tasks')
    if not items:
        if n==0: yield ()
        return
    if not n<=len(items)<=2*n:return
    first,*tail=items
    for rest in partitions(tuple(tail),n-1):yield ((first,),)+rest
    for j,t in enumerate(tail):
        for rest in partitions(tuple(tail[:j]+tail[j+1:]),n-1):yield ((first,t),)+rest


def reference(w,n,costs,objective,budget=None):
    # Independent graph walk and union evaluation, not production preprocessing.
    c={t:rational(v) for t,v in costs.items()}; cap=rational(budget,False) if budget is not None else None
    best=None; chosen=None;count=0
    for gs in partitions(w.ids,n):
        rs=[]
        for group in gs:
            seen=set(group);todo=list(group)
            while todo:
                t=todo.pop()
                for child in w.tasks:
                    if t in child.parents and child.id not in seen:seen.add(child.id);todo.append(child.id)
            rs.append(sum(c[t] for t in seen))
        count+=1
        if cap is not None and max(rs)>cap:continue
        pair=(sum(rs),max(rs)) if objective=='mean' else (max(rs),sum(rs))
        if best is None or pair<best:best,chosen=pair,gs
    return {'pair':best,'groups':chosen,'partitions':count,'status':'infeasible' if best is None else 'optimal'}


def random_valid(w,n,seed):
    prepare(w,n,dict.fromkeys(w.ids,1));ts=list(w.ids);random.Random(seed).shuffle(ts);p=len(ts)-n
    return groups(w,n,[tuple(ts[2*i:2*i+2]) for i in range(p)]+[(t,) for t in ts[2*p:]])


def greedy(w,n,costs,initial,objective):
    current=groups(w,n,initial);_,_,weights=prepare(w,n,costs);moves=[]
    def key(gs):
        r=[weights[g] for g in gs];return (sum(r),max(r)) if objective=='mean' else (max(r),sum(r))
    for _ in range(20):
        neighbors=set()
        for i,j in combinations(range(n),2):
            for a in current[i]:
                for b in current[j]:
                    z=[list(g) for g in current];z[i].remove(a);z[j].remove(b);z[i].append(b);z[j].append(a)
                    neighbors.add(groups(w,n,z))
            for aidx,bidx in ((i,j),(j,i)):
                if len(current[aidx])==2 and len(current[bidx])==1:
                    for a in current[aidx]:
                        z=[list(g) for g in current];z[aidx].remove(a);z[bidx].append(a);neighbors.add(groups(w,n,z))
        better=[g for g in neighbors if key(g)<key(current)]
        if not better:break
        current=min(better,key=lambda g:(key(g),g));moves.append({'groups':current,'pair':key(current)})
    return {'groups':current,'moves':moves,'fallback':False}


def allocate(w,n,costs,method,seed=0,estimator='supplied-rational-v1'):
    initial=random_valid(w,n,seed)
    objective='worst' if 'worst' in method or method=='direct_workload_balance' else 'mean'
    details={}
    if method=='random_valid':gs=initial
    elif method in ('greedy_mean','greedy_worst'):
        details=greedy(w,n,costs,initial,objective);gs=details['groups']
    elif method in ('matching_mean','matching_worst','matching_mean_unit','matching_worst_unit','direct_workload_balance'):
        cc=dict.fromkeys(w.ids,1) if method.endswith('_unit') else costs
        details=solve(w,n,cc,objective,direct=method=='direct_workload_balance');gs=details['groups']
    else:raise Invalid('unknown local method; LLM replies must be separately validated')
    a=Allocation(w.key,n,gs,estimator,method,seed)
    return a,{'optimisation':details,'evaluation_under_supplied_costs':metrics(w,n,gs,costs)}


def llm_request(w,n,costs,objective):
    c,ds,weights=prepare(w,n,costs)
    if objective not in ('mean','worst'):raise Invalid('objective')
    return {'workflow':w.key,'tasks':[{'id':t.id,'description':t.description,'parents':t.parents} for t in w.tasks],
            'costs':c,'group_scores':[{'group':g,'cost':v} for g,v in weights.items()],
            'n':n,'cap':2,'objective':objective,'outputs':w.outputs,'maximum_structural_corrections':1}


def llm_reply(w,n,replies):
    if not 1<=len(replies)<=2:raise Invalid('at most initial reply plus one structural correction')
    attempts=[]
    for reply in replies:
        try:
            if not isinstance(reply,dict) or set(reply)!={'groups'}:raise Invalid('response schema')
            # Decoded JSON boundary: internal ownership tuples remain supported by groups().
            value=reply['groups']
            if (type(value) is not list or len(value)!=n or
                    any(type(g) is not list or len(g) not in (1,2) for g in value) or
                    any(not isinstance(t,str) or not t or t not in w.ids for g in value for t in g)):
                raise Invalid('response groups require arrays of known task IDs')
            gs=groups(w,n,value);attempts.append('valid')
            if len(attempts)!=len(replies):
                return {'status':'invalid_allocation','groups':None,'attempts':attempts,
                        'error':'extra correction after valid response','fallback':False}
            return {'status':'valid','groups':gs,'attempts':attempts,'allocation_usage':'synthetic/unmeasured'}
        except (Invalid,TypeError,KeyError) as exc:attempts.append('invalid')
    return {'status':'invalid_allocation','groups':None,'attempts':attempts,'fallback':False}
