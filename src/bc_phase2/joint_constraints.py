"""Symbolic joint constraints; CP-SAT translation is lazy and never enumerates designs.

The deterministic interpreter is a test aid for supplied candidates, not a solver.
"""
from fractions import Fraction
from math import lcm
from .joint_schema import canonical_domain, price, MAX_INT
from .model import Invalid


class Circuit:
    def __init__(self):
        self.nodes=[];self.inputs={};self.constraints=[]
    def node(self,op,args=(),data=None):
        i=len(self.nodes);self.nodes.append((op,tuple(args),data));return i
    def bit(self,key):
        i=self.node('input',data=key);self.inputs[key]=i;return i
    def AND(self,*args):return self.node('and',args)
    def OR(self,*args):return self.node('or',args)
    def SUM(self,terms):return self.node('sum',[i for c,i in terms],[c for c,i in terms])
    def MAX(self,*args):return self.node('max',args)
    def equal(self,a,b):self.constraints.append(('eq',a,b))
    def limit(self,a,lo,hi):self.constraints.append(('range',a,(lo,hi)))
    def implies(self,a,b):self.constraints.append(('implies',a,b))
    def evaluate(self,assignment):
        if set(assignment)!=set(self.inputs):raise Invalid('exact circuit inputs required')
        values=[]
        for op,args,data in self.nodes:
            x=[values[i] for i in args]
            if op=='input':
                v=assignment[data]
                if type(v) not in (bool,int) or v not in (0,1):raise Invalid('Boolean input')
            elif op=='and':v=int(all(x))
            elif op=='or':v=int(any(x))
            elif op=='sum':v=sum(c*y for c,y in zip(data,x))
            elif op=='max':v=max(x)
            values.append(v)
        feasible=True
        for kind,a,b in self.constraints:
            if kind=='eq':ok=values[a]==values[b]
            elif kind=='range':ok=b[0]<=values[a]<=b[1]
            else:ok=not values[a] or bool(values[b])
            feasible &= ok
        return feasible,values
    def cpsat(self):
        try:from ortools.sat.python import cp_model
        except ImportError as exc:raise Invalid('SOLVER_DEPENDENCY_BLOCKED: ortools==9.14.6206 required; not installed by this command') from exc
        model=cp_model.CpModel();variables=[];upper=[]
        for j,(op,args,data) in enumerate(self.nodes):
            x=[variables[i] for i in args]
            if op in ('input','and','or'):
                v=model.NewBoolVar('b'+str(j));bound=1
                if op=='and':
                    model.AddBoolAnd(x).OnlyEnforceIf(v)
                    model.AddBoolOr([a.Not() for a in x]).OnlyEnforceIf(v.Not())
                elif op=='or':
                    model.AddBoolOr(x).OnlyEnforceIf(v)
                    model.AddBoolAnd([a.Not() for a in x]).OnlyEnforceIf(v.Not())
            else:
                bound=sum(c*upper[i] for c,i in zip(data,args)) if op=='sum' else max(upper[i] for i in args)
                if bound>MAX_INT:raise Invalid('circuit integer range overflow')
                v=model.NewIntVar(0,bound,'v'+str(j))
                if op=='sum':model.Add(v==sum(c*y for c,y in zip(data,x)))
                else:model.AddMaxEquality(v,x)
            variables.append(v);upper.append(bound)
        for kind,a,b in self.constraints:
            if kind=='eq':model.Add(variables[a]==variables[b])
            elif kind=='range':
                model.Add(variables[a]>=b[0]);model.Add(variables[a]<=b[1])
            else:model.AddImplication(variables[a],variables[b])
        return cp_model,model,variables


def build(domain,partial=None,use_bounds=True):
    """Polynomial-size symbolic encoding. No complete candidate enumeration."""
    from .joint_bounds import mandatory_bound, checked_partial
    d=canonical_domain(domain);partial=checked_partial(d,partial)
    g=Circuit();zero=g.OR();one=g.AND()
    choices={c['id']:c for c in d['choices']};tasks={t['id']:t for t in d['tasks']}
    owners=[o['id'] for o in d['owners']];events={e['id']:e for e in d['events']}
    routes={r['id']:r for r in d['routes']};sources={s['id']:s for s in d['sources']}
    options={}
    for c in choices.values():
        bits=[]
        for v in c['options']:
            bit=g.bit(('choice',c['id'],v));options[c['id'],v]=bit;bits.append(bit)
        g.limit(g.SUM([(1,b) for b in bits]),1,1)
    x={(t,o):g.bit(('owner',t,o)) for t in tasks for o in owners}
    for t in tasks:
        g.limit(g.SUM([(1,x[t,o]) for o in owners]),1,1)
        for o in owners:
            if o not in tasks[t]['eligible_owners']:g.equal(x[t,o],zero)
    K=min(d['K'],d['m']-d['n']+1)
    for o in owners:g.limit(g.SUM([(1,x[t,o]) for t in tasks]),1,K)
    for axis in ('A','C'):
        for c,v in partial[axis].items():g.equal(options[c,v],one)
    for t,o in partial['P'].items():g.equal(x[t,o],one)
    def cond(c):return g.AND(*(options[k,v] for k,v in c.items()))
    active={v:cond(e['when']) for v,e in events.items()}
    modes={};edges={};reads={};q={v:[] for v in events}
    costs=[price(m[k]) for e in events.values() for m in e['modes'] for k in ('initial','replay')]
    scale=lcm(*(p.denominator for p in costs))
    cap=sum(int(c*scale) for c in costs);modecost={}
    if 4*cap*d['n']>MAX_INT:raise Invalid('unsupported solver integer range: linear-domain safety margin')
    for v,e in events.items():
        bs=[]
        for m in e['modes']:
            b=g.AND(active[v],cond(m['when']));modes[v,m['id']]=b;bs.append(b)
            modecost[v,m['id']]=(int(price(m['initial'])*scale),int(price(m['replay'])*scale))
        g.equal(g.SUM([(1,b) for b in bs]),active[v])
    for t in tasks.values():
        bs=[]
        for variant in t['variants']:
            b=cond(variant['when']);bs.append(b)
            for v in variant['required_events']:g.implies(b,active[v])
            for ref in variant['deliverables'].values():g.implies(b,active[ref['event']])
        g.limit(g.SUM([(1,b) for b in bs]),1,1)
    for group in d['exclusive']:g.limit(g.SUM([(1,active[v]) for v in group]),0,1)
    for c in d['forbidden']:g.equal(cond(c),zero)
    position={v:i for i,v in enumerate(d['schedule']['order'])}
    for v,e in events.items():
        for m in e['modes']:
            b=modes[v,m['id']]
            for port,rid in m['reads'].items():
                route=routes[rid];ref=route['producer'];u=ref['event'];s=ref['source']
                g.implies(b,cond(route['when']))
                contract=events[u]['output'] if u is not None else sources[s]['artifact']
                if contract!=e['inputs'][port] or (u is not None and position[u]>=position[v]):
                    g.equal(b,zero);continue
                if u is not None:
                    g.implies(b,active[u]);edges.setdefault((u,v),[]).append(b)
                else:reads.setdefault((s,v),[]).append(b)
                if route['owner_pairs'] is not None:
                    allowed=[]
                    for sender,receiver in route['owner_pairs']:
                        if u is None:
                            if sender=='protected':allowed.append(x[e['host'],receiver])
                        elif sender in owners:allowed.append(g.AND(x[events[u]['host'],sender],x[e['host'],receiver]))
                    g.implies(b,g.OR(*allowed))
    edge={pair:g.OR(*bs) for pair,bs in edges.items()}
    provenance={};r={}
    order=d['schedule']['order']
    for v in order:
        parents=[(u,b) for (u,w),b in edge.items() if w==v]
        for s in sources:
            p=g.OR(*reads.get((s,v),[]),*(g.AND(b,provenance[s,u]) for u,b in parents))
            provenance[s,v]=p
            if s not in events[v]['allowed_sources']:g.equal(p,zero)
        for o in owners:r[o,v]=g.OR(g.AND(active[v],x[events[v]['host'],o]),*(g.AND(b,r[o,u]) for u,b in parents))
    for obligation in d['obligations']:
        bs=[]
        for producer in obligation['producers']:
            b=cond(producer['when']);v=producer['ref']['event'];bs.append(b);q[v].append(b);g.implies(b,active[v])
        g.limit(g.SUM([(1,b) for b in bs]),1,1)
    h={}
    for v in reversed(order):h[v]=g.OR(*q[v],*(g.AND(b,h[w]) for (u,w),b in edge.items() if u==v))
    R={}
    for o in owners:
        terms=[]
        for (v,k),b in modes.items():terms.append((modecost[v,k][1],g.AND(r[o,v],h[v],b)))
        R[o]=g.SUM(terms)
    S=g.SUM([(1,R[o]) for o in owners]);W=g.MAX(*(R[o] for o in owners))
    initial=g.SUM([(modecost[v,k][0],b) for (v,k),b in modes.items()])
    for owner in d['owners']:
        o=owner['id']
        if owner['max_operations'] is not None:g.limit(g.SUM([(1,g.AND(active[v],x[e['host'],o])) for v,e in events.items()]),0,min(len(events),owner['max_operations']))
        if owner['max_initial'] is not None:g.limit(g.SUM([(modecost[v,k][0],g.AND(b,x[events[v]['host'],o])) for (v,k),b in modes.items()]),0,min(cap,int(price(owner['max_initial'],zero=True)*scale)))
    for key,node in (('initial',initial),('incident',W)):
        if d['budgets'][key] is not None:g.limit(node,0,min(cap,int(price(d['budgets'][key],zero=True)*scale)))
    bound=mandatory_bound(d,partial)
    if use_bounds:
        from math import ceil
        g.limit(S,ceil(bound['sum']*scale),cap*d['n']);g.limit(W,ceil(bound['worst']*scale),cap)
    return {'domain':d,'circuit':g,'scale':scale,'R':R,'S':S,'W':W,'initial':initial,'partial':partial,'bound':bound,'use_bounds':use_bounds}


def input_bits(encoded,A,C,P):
    chosen={**A,**C}
    return {key:int(chosen[key[1]]==key[2] if key[0]=='choice' else P[key[1]]==key[2]) for key in encoded['circuit'].inputs}


def decode_solution(encoded,values):
    from .joint_core import explicit_selection,compile_organisation,evaluate
    A={};C={};P={};d=encoded['domain']
    for c in d['choices']:
        opts=[v for v in c['options'] if values[encoded['circuit'].inputs['choice',c['id'],v]]]
        if len(opts)!=1:raise Invalid('decoded choice not unique')
        (A if c['axis']=='A' else C)[c['id']]=opts[0]
    for t in d['tasks']:
        owners=[o['id'] for o in d['owners'] if values[encoded['circuit'].inputs['owner',t['id'],o['id']]]]
        if len(owners)!=1:raise Invalid('decoded owner not unique')
        P[t['id']]=owners[0]
    candidate=explicit_selection(d,A,C,P);execution=compile_organisation(d,candidate);score=evaluate(execution)
    expected={owner:v for (owner,_),v in zip(score['groups'],score['vector'])}
    for owner,node in encoded['R'].items():
        if Fraction(values[node],encoded['scale'])!=expected[owner]:raise Invalid('solver vector mismatch')
    for key,node in (('sum',encoded['S']),('max',encoded['W']),('initial_expenditure',encoded['initial'])):
        if Fraction(values[node],encoded['scale'])!=score[key]:raise Invalid('solver metric mismatch')
    return candidate,score
