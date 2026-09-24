"""Terminal-only behavioral evaluator. No policy selection, repair, or feedback."""
from copy import deepcopy
import time
from .common import Rejected, digest
from .runtime import Environment
from .resources import Resources


def oracle(kind,tables):
    def records(name):
        t=tables[name];return [dict(zip([x[0] for x in t['columns']],r)) for r in t['rows']]
    if kind=='jaffle':
        customers,orders,payments=records('customers'),records('orders'),records('payments')
        owner={o['id']:o['user_id'] for o in orders}
        summary=[[c['id'],sum(p['amount'] for p in payments if owner[p['order_id']]==c['id'])/100.0,
                  sum(1 for p in payments if owner[p['order_id']]==c['id'])] for c in sorted(customers,key=lambda x:x['id'])]
        methods=sorted({p['payment_method'] for p in payments})
        return {'customer_summary':summary,'method_summary':[[m,sum(p['amount'] for p in payments if p['payment_method']==m)/100.0,
            sum(p['payment_method']==m for p in payments)] for m in methods]}
    if kind=='energy':
        rows=records('energy'); chosen=[r for r in rows if r['iso_code'] in ('DNK','FIN') and 2019<=r['year']<=2022]
        report=[[r['iso_code'],r['year'],r['electricity_generation']] for r in sorted(chosen,key=lambda x:(x['iso_code'],x['year'])) if r['electricity_generation'] is not None]
        coverage=[[c,sum(r['iso_code']==c for r in chosen),sum(r['iso_code']==c and r['electricity_generation'] is None for r in chosen)] for c in ('DNK','FIN')]
        return {'generation_report':report,'coverage_report':coverage}
    if kind=='inventory':
        rows=records('stock')
        return {'stock_report':[[r['sku'],r['qty']] for r in sorted(rows,key=lambda x:x['sku'])],
                'zero_report':[[r['sku']] for r in sorted(rows,key=lambda x:x['sku']) if r['qty']==0]}
    raise Rejected('evaluator_unavailable')


def evaluate(public, private, state):
    frozen=deepcopy(state['bound']);start=time.process_time();wall=time.monotonic()
    per={r['id']:True for r in public['required_outputs']}; reports=[]
    resources=Resources(token_cap=1,cpu_cap=240)
    for fixture in private['fixtures']:
        p=deepcopy(public)
        if 'tables' in fixture:p['tables']=fixture['tables']
        env=Environment(p,resources=resources)
        try:
            env.artifacts=deepcopy(state['artifacts']);env.bound=frozen
            if public['family']=='data_product':
                expected=oracle(private['oracle'],p['tables'])
                for req in public['required_outputs']:
                    key=req['id'];v=frozen.get(key)
                    if v is None:per[key]=False;continue
                    try:out=env.execute(v)
                    except Rejected as e:
                        if str(e)=='blocked_prerequisite':return {'status':'blocked_prerequisite','success':None}
                        out={'status':'rejected'}
                    ok=out['status']=='ok' and out['outputs'][0]['columns']==req['columns'] and out['outputs'][0]['rows']==expected[key]
                    if ok:
                        allowed={'integer':(int,),'number':(int,float),'string':(str,)}
                        ok=all(len(row)==len(req['types']) and all(type(v) in allowed[t] for v,t in zip(row,req['types'])) for row in out['outputs'][0]['rows'])
                    per[key]&=ok
                    reports.append({'obligation':key,'passed':ok})
            else:
                for case in fixture['cases']:
                    key=case['obligation'];v=frozen.get(key)
                    if v is None:per[key]=False;continue
                    try:out=env.execute(v,case['input'])
                    except Rejected as e:
                        if str(e)=='blocked_prerequisite':return {'status':'blocked_prerequisite','success':None}
                        out={'status':'rejected'}
                    ok=out.get('status')=='ok' and out.get('valid')==case['valid']
                    if case.get('valid') and 'output' in case:ok=ok and out.get('output')==case['output']
                    per[key]&=ok;reports.append({'obligation':key,'passed':ok})
                # Composition on every valid response, using the SAME bound bundle.
                for value in fixture.get('composition',[]):
                    if not all(k in frozen for k in ('response','consumer')):per['consumer']=False;continue
                    r=env.execute(frozen['response'],value);m=env.execute(frozen['consumer'],value)
                    per['consumer'] &= r.get('valid') is True and m.get('valid') is True
        finally:env.close()
    try:resources.parent_overhead('terminal_evaluator_parent',start,0)
    except Rejected:
        return {'status':'blocked_prerequisite','reason':'evaluator_cpu_cap','success':None,'evaluator_resources':resources.summary()}
    return {'status':'available','success':all(per.values()),'obligations':per,'checks':reports,
        'bound_bundle_hash':digest(frozen),'finite_tests_only':True,'worker_feedback':False,
        'evaluator_resources':resources.summary(),'analysis_cpu_seconds':time.process_time()-start,
        'wall_seconds':time.monotonic()-wall}
