"""Conservative forced-fact exposure bounds; no completion enumeration."""
from fractions import Fraction
from math import ceil
from .joint_schema import canonical_domain,price,require
from .model import digest


def checked_partial(d,partial=None):
    p={'A':{},'C':{},'P':{}} if partial is None else partial
    require(type(p) is dict and set(p)=={'A','C','P'},'partial fields')
    choices={c['id']:c for c in d['choices']};owners={o['id'] for o in d['owners']};tasks={t['id'] for t in d['tasks']}
    for axis in p:
        require(type(p[axis]) is dict,'partial map')
        for k,v in p[axis].items():
            if axis=='P':require(k in tasks and type(v) is str and v in owners,'partial owner')
            else:require(k in choices and choices[k]['axis']==axis and type(v) is str and v in choices[k]['options'],'partial choice')
    return {k:dict(v) for k,v in p.items()}


def mandatory_bound(domain,partial=None):
    d=canonical_domain(domain);p=checked_partial(d,partial);known={**p['A'],**p['C']}
    def forced(c):return all(known.get(k)==v for k,v in c.items())
    def possible(c):return all(k not in known or known[k]==v for k,v in c.items())
    events={e['id']:e for e in d['events']};routes={r['id']:r for r in d['routes']}
    active={v for v,e in events.items() if forced(e['when'])};edges=set();prices={}
    for v in active:
        modes=[m for m in events[v]['modes'] if possible(m['when'])]
        if modes:prices[v]=min(price(m['replay']) for m in modes)
        if len(modes)==1:
            for rid in modes[0]['reads'].values():
                u=routes[rid]['producer']['event']
                if u in active:edges.add((u,v))
    outputs=set()
    for q in d['obligations']:
        producers=[s for s in q['producers'] if possible(s['when'])]
        if len(producers)==1 and producers[0]['ref']['event'] in active:outputs.add(producers[0]['ref']['event'])
    # Only paths of individually forced edges. No union of merely possible paths.
    relevant=set(outputs)
    for v in reversed(d['schedule']['order']):
        if any(u==v and w in relevant for u,w in edges):relevant.add(v)
    upstream={};rows=[];K=min(d['K'],d['m']-d['n']+1)
    for v in d['schedule']['order']:
        if v not in active:continue
        ts={events[v]['host']}
        for u,w in edges:
            if w==v:ts.update(upstream.get(u,set()))
        upstream[v]=ts
        if v not in relevant or v not in prices:continue
        a=len(ts);fixed={p['P'][t] for t in ts if t in p['P']}
        ell=max(ceil(a/K),d['n']-(d['m']-a),len(fixed))
        rows.append({'event':v,'tasks':tuple(sorted(ts)),'owners':tuple(sorted(fixed)),'ell':ell,'price':prices[v]})
    total=sum((r['price']*r['ell'] for r in rows),Fraction())
    task=max((sum((r['price'] for r in rows if t['id'] in r['tasks']),Fraction()) for t in d['tasks']),default=Fraction())
    return {'domain':digest(d),'partial':p,'scope':'partial completion domain; not an infeasibility claim',
            'rows':rows,'sum':total,'mean':total/d['n'],'task':task,'worst':max(total/d['n'],task)}
