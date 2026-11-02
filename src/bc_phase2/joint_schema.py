"""Strict finite joint A/P/C wire contracts, independent of legacy B-only JSON."""
from fractions import Fraction
from math import lcm
import json
import re
from .model import Invalid, digest

DOMAIN_VERSION = 'joint-domain-v1'
SELECTION_VERSION = 'joint-selection-v1'
MAX_BYTES = 1048576
MAX_INT = 2**63-1


def require(ok, reason):
    if not ok: raise Invalid(reason)


def keys(value, names):
    require(type(value) is dict and set(value) == set(names.split()), 'unexpected/missing fields: '+names)


def name(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_.:-]{0,79}', value), 'identifier')


def text(value):
    require(type(value) is str and 0 < len(value.strip()) <= 8000, 'bounded nonempty text')


def array(value, limit=128):
    require(type(value) is list and len(value) <= limit, 'bounded JSON array')


def unique(value, limit=128):
    array(value, limit)
    for v in value: name(v)
    require(len(set(value)) == len(value), 'duplicate IDs')


def records(value, limit=128):
    array(value, limit); result={}
    for row in value:
        require(type(row) is dict and 'id' in row, 'record ID'); name(row['id'])
        require(row['id'] not in result, 'duplicate record'); result[row['id']]=row
    return result


def price(value, *, zero=False):
    require(type(value) in (str, int), 'exact integer/rational wire price required')
    if type(value) is str:
        require(len(value) <= 40 and re.fullmatch(r'\d+(?:/[1-9]\d*)?', value), 'rational syntax')
    try: q=Fraction(value)
    except (ValueError, ZeroDivisionError): raise Invalid('rational value')
    require(q >= 0 if zero else q > 0, 'positive price/nonnegative bound')
    require(abs(q.numerator) <= MAX_INT and q.denominator <= MAX_INT, 'rational overflow')
    return q


def decode(raw):
    require(type(raw) is str, 'JSON text required')
    try:
        require(len(raw.encode('utf-8')) <= MAX_BYTES, 'joint JSON byte limit')
        def pairs(items):
            d={}
            for k,v in items:
                require(k not in d, 'duplicate JSON key'); d[k]=v
            return d
        def reject(x): raise Invalid('floats/nonfinite JSON forbidden; use rational strings')
        out=json.loads(raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
        json.dumps(out, ensure_ascii=False, allow_nan=False).encode('utf-8')
        return out
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise Invalid('invalid bounded JSON') from exc


def condition(value, choices):
    require(type(value) is dict, 'condition object')
    for k,v in value.items():
        require(k in choices and type(v) is str and v in choices[k]['options'], 'unknown condition')


def matches(when, selected): return all(selected.get(k)==v for k,v in when.items())


def artifact(value):
    keys(value, 'artifact version type')
    for v in value.values(): name(v)


def reference(value, sources, events):
    keys(value, 'source event port')
    require((value['source'] is None) != (value['event'] is None), 'one provenance producer')
    if value['source'] is not None:
        require(type(value['source']) is str and value['source'] in sources and value['port']=='out', 'source port')
        return sources[value['source']]['artifact']
    require(type(value['event']) is str and value['event'] in events and value['port']=='out', 'event port')
    return events[value['event']]['output']


def validate_domain(d):
    # Recheck size and strict scalars for callers supplying Python objects too.
    try: d=decode(json.dumps(d, allow_nan=False))
    except (TypeError, ValueError, RecursionError) as exc: raise Invalid('invalid JSON domain') from exc
    keys(d, 'schema source n m K objective unit tasks owners sources choices events routes schedule network exclusive forbidden obligations budgets')
    require(d['schema']==DOMAIN_VERSION, 'domain version')
    keys(d['source'], 'id kind provenance'); text(d['source']['id']); text(d['source']['provenance'])
    require(d['source']['kind'] in ('synthetic_fixture','bound_external'), 'source provenance kind')
    for k in ('n','m','K'): require(type(d[k]) is int and 1 <= d[k] <= 128, 'bounded positive count')
    require(d['n'] <= d['m'] <= d['n']*d['K'], 'n <= m <= nK')
    require(d['objective'] in ('mean_first','worst_first'), 'objective'); text(d['unit'])
    tasks=records(d['tasks']); owners=records(d['owners']); sources=records(d['sources'])
    choices=records(d['choices'],16); events=records(d['events']); routes=records(d['routes'],256)
    require(len(tasks)==d['m'] and len(owners)==d['n'], 'task/owner count')
    for owner in owners.values():
        keys(owner, 'id max_operations max_initial')
        if owner['max_operations'] is not None:
            require(type(owner['max_operations']) is int and owner['max_operations'] >= 1, 'owner operation limit')
        if owner['max_initial'] is not None: price(owner['max_initial'],zero=True)
    for c in choices.values():
        keys(c, 'id axis options'); require(c['axis'] in ('A','C'), 'choice axis')
        unique(c['options'],16); require(c['options'], 'nonempty choice')
    for s in sources.values():
        keys(s, 'id artifact origin value'); artifact(s['artifact'])
        require(s['origin'] in ('immutable_external','synthetic_fixture'), 'no planner solution as protected source')
        if s['value'] is not None:
            require(s['origin']=='synthetic_fixture', 'only synthetic fixtures embed values')
            price(s['value'],zero=True)
    keys(d['network'], 'nodes edges'); unique(d['network']['nodes']); array(d['network']['edges'],512)
    seen=set()
    for edge in d['network']['edges']:
        array(edge,2);require(len(edge)==2 and all(type(x) is str and x in d['network']['nodes'] for x in edge), 'network edge')
        require(tuple(edge) not in seen, 'duplicate physical edge');seen.add(tuple(edge))
    keys(d['schedule'], 'template order');require(d['schedule']['template']=='serial-event-order-v1','unsupported schedule template')
    unique(d['schedule']['order']);require(set(d['schedule']['order'])==set(events),'complete potential event order')
    costs=[]
    for e in events.values():
        keys(e, 'id host kind when inputs output allowed_sources modes')
        require(type(e['host']) is str and e['host'] in tasks, 'predefined host task')
        require(e['kind'] in ('compute','relay','state','synthesis','diagnostic'), 'event kind')
        condition(e['when'],choices);artifact(e['output']);unique(e['allowed_sources'])
        require(set(e['allowed_sources'])<=set(sources),'source permission')
        require(type(e['inputs']) is dict and len(e['inputs'])<=32,'typed input ports')
        for port,contract in e['inputs'].items(): name(port);artifact(contract)
        modes=records(e['modes'],32);require(modes,'nonempty modes')
        for mode in modes.values():
            keys(mode,'id when reads initial replay operator');condition(mode['when'],choices)
            require(type(mode['reads']) is dict and set(mode['reads'])==set(e['inputs']), 'exact input coverage')
            require(all(type(r) is str and r in routes for r in mode['reads'].values()),'known read route')
            costs += [price(mode['initial']),price(mode['replay'])]
            require(mode['operator'] in ('opaque','identity','sum','product','square','negate'), 'trusted synthetic operator')
            if mode['operator'] in ('identity','square','negate'): require(len(mode['reads'])==1,'unary operator arity')
            if mode['operator'] in ('sum','product'): require(mode['reads'],'nonempty arithmetic inputs')
    for r in routes.values():
        keys(r,'id producer transform path when owner_pairs cost_accounting')
        require(r['cost_accounting']=='included_in_consumer_mode','explicit transport accounting required')
        reference(r['producer'],sources,events);condition(r['when'],choices)
        require(r['transform']=='identity','transform requires an explicit hosted operation')
        array(r['path']);require(r['path'] and all(type(x) is str and x in d['network']['nodes'] for x in r['path']), 'route path')
        require(all((a,b) in seen for a,b in zip(r['path'],r['path'][1:])), 'route physical link')
        if r['owner_pairs'] is not None:
            array(r['owner_pairs'])
            for pair in r['owner_pairs']:
                array(pair,2);require(len(pair)==2 and pair[0] in [*owners,'protected'] and pair[1] in owners,'owner-position route constraint')
    for t in tasks.values():
        keys(t,'id instruction deliverables eligible_owners variants');text(t['instruction'])
        unique(t['eligible_owners']);require(t['eligible_owners'] and set(t['eligible_owners'])<=set(owners),'owner eligibility')
        require(type(t['deliverables']) is dict and t['deliverables'],'fixed task deliverables')
        for k,v in t['deliverables'].items():name(k);artifact(v)
        variants=records(t['variants'],32);require(variants,'task implementations')
        for v in variants.values():
            keys(v,'id when required_events deliverables');condition(v['when'],choices)
            unique(v['required_events']);require(v['required_events'] and set(v['required_events'])<=set(events), 'implementation events')
            require(all(events[x]['host']==t['id'] for x in v['required_events']), 'wrong implementation host')
            require(type(v['deliverables']) is dict and set(v['deliverables'])==set(t['deliverables']), 'deliverable coverage')
            for k,ref in v['deliverables'].items():
                require(reference(ref,sources,events)==t['deliverables'][k], 'task artifact/version contract')
                require(ref['event'] in v['required_events'], 'task deliverable must be owned implementation output')
    array(d['exclusive'])
    for group in d['exclusive']:
        unique(group); require(len(group)>=2 and set(group)<=set(events),'exclusive events')
    array(d['forbidden'])
    for c in d['forbidden']: condition(c,choices)
    obligations=records(d['obligations']);require(obligations,'fixed required outputs')
    for q in obligations.values():
        keys(q,'id artifact producers');artifact(q['artifact']);array(q['producers'],32);require(q['producers'],'output producers')
        for prod in q['producers']:
            keys(prod,'when ref');condition(prod['when'],choices)
            require(reference(prod['ref'],sources,events)==q['artifact'] and prod['ref']['event'] is not None,'forced output representation')
    keys(d['budgets'],'initial incident')
    for value in d['budgets'].values():
        if value is not None:price(value,zero=True)
    scale=lcm(*(c.denominator for c in costs)) if costs else 1
    require(scale<=MAX_INT and sum(int(c*scale) for c in costs)*d['n']<=MAX_INT, 'exact coefficient/aggregate scaling overflow')
    return d


def canonical_domain(d):
    d=validate_domain(d)
    for key in ('tasks','owners','sources','choices','events','routes','obligations'):
        d[key].sort(key=lambda x:x['id'])
    for t in d['tasks']:
        t['eligible_owners'].sort();t['variants'].sort(key=lambda x:x['id'])
        for v in t['variants']:v['required_events'].sort()
    for e in d['events']:
        e['allowed_sources'].sort();e['modes'].sort(key=lambda x:x['id'])
        for mode in e['modes']:
            for k in ('initial','replay'):mode[k]=str(price(mode[k]))
    for s in d['sources']:
        if s['value'] is not None:s['value']=str(price(s['value'],zero=True))
    for c in d['choices']:c['options'].sort()
    for r in d['routes']:
        if r['owner_pairs'] is not None:r['owner_pairs'].sort()
    for q in d['obligations']:q['producers'].sort(key=digest)
    for o in d['owners']:
        if o['max_initial'] is not None:o['max_initial']=str(price(o['max_initial'],zero=True))
    for k,v in d['budgets'].items():
        if v is not None:d['budgets'][k]=str(price(v,zero=True))
    d['network']['nodes'].sort();d['network']['edges'].sort()
    d['exclusive']=sorted(sorted(g) for g in d['exclusive']);d['forbidden'].sort(key=digest)
    return d


def domain_id(d):return digest(canonical_domain(d))


def parse_domain(text):return validate_domain(decode(text))


def parse_selection(text):
    s=decode(text);keys(s,'schema domain A C ownership variants modes outputs')
    require(s['schema']==SELECTION_VERSION,'selection version')
    require(type(s['domain']) is str and re.fullmatch('[0-9a-f]{64}',s['domain']), 'domain identity')
    for k in ('A','C','ownership','variants','modes','outputs'):require(type(s[k]) is dict,'complete choice object')
    for k in ('A','C','ownership','variants','modes'):
        for key,value in s[k].items():name(key);name(value)
    for key,ref in s['outputs'].items():name(key);keys(ref,'source event port')
    return s
