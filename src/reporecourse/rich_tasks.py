"""Three authored requests and one honestly blocked candidate; no online solver.

Expected values are independent Python reductions, never exposed by worker tools.
Reference artifacts continue through the existing restricted executor/interpreter.
"""
from copy import deepcopy
import math
import time
from .common import digest, load, Rejected
from .tasks import ROOT, catalog, load_task, private_task
from .resources import Resources
from . import v2

RICH = ROOT/'rich'


def energy_rows_match(actual,expected,types):
    if len(actual)!=len(expected):return False
    for a,b in zip(actual,expected):
        if len(a)!=len(b) or len(a)!=len(types):return False
        for x,y,t in zip(a,b,types):
            if t=='number':
                if type(x) not in (int,float) or not math.isfinite(x) or not math.isclose(x,y,abs_tol=1e-9,rel_tol=1e-12):return False
            elif x!=y:return False
    return True


def expected(kind,tables):
    def records(name):
        t=tables[name]
        return [dict(zip([c[0] for c in t['columns']],r)) for r in t['rows']]
    if kind=='rich_jaffle':
        cs,os,ps=records('customers'),records('orders'),records('payments')
        out={k:[] for k in ('order_payments','customer_summary','method_summary','reconciliation')}
        by_order={o['id']:[p for p in ps if p['order_id']==o['id']] for o in os}
        for o in sorted(os,key=lambda x:x['id']):
            payments=by_order[o['id']]
            out['order_payments'].append([o['id'],o['user_id'],sum(p['amount'] for p in payments),len(payments)])
        for c in sorted(cs,key=lambda x:x['id']):
            orders=[o for o in os if o['user_id']==c['id']]
            payments=[p for o in orders for p in by_order[o['id']]]
            total=sum(p['amount'] for p in payments)
            paid=sum(bool(by_order[o['id']]) for o in orders)
            out['customer_summary'].append([c['id'],total,len(payments),len(orders)])
            out['reconciliation'].append([c['id'],paid,len(orders)-paid,total])
        for method in sorted({p['payment_method'] for p in ps}):
            payments=[p for p in ps if p['payment_method']==method]
            out['method_summary'].append([method,sum(p['amount'] for p in payments),len(payments)])
        return out
    if kind=='rich_energy':
        rows=sorted(records('energy'),key=lambda x:(x['iso_code'],x['year']))
        selected=[r for r in rows if r['iso_code'] in ('DNK','FIN') and 2019<=r['year']<=2022]
        out={'generation_report':[[r['iso_code'],r['year'],r['electricity_generation']] for r in selected if r['electricity_generation'] is not None],
             'window_summary':[], 'coverage_report':[], 'exclusions':[],
             'field_contract':[['generation_twh','TWh','omitted','observed_years_sum']]}
        for iso in ('DNK','FIN'):
            country=[r for r in selected if r['iso_code']==iso]
            vals=[r['electricity_generation'] for r in country if r['electricity_generation'] is not None]
            out['window_summary'].append([iso,len(vals),sum(vals)])
            out['coverage_report'].append([iso,len(country),len(vals),len(country)-len(vals)])
        for r in rows:
            reason='country' if r['iso_code'] not in ('DNK','FIN') else 'year' if not 2019<=r['year']<=2022 else 'missing' if r['electricity_generation'] is None else None
            if reason:out['exclusions'].append([r['iso_code'],r['year'],reason])
        return out
    raise Rejected('rich_oracle')


def consistent(kind,b):
    """Cross-output outcome constraints; no required implementation edge."""
    try:
        if kind=='rich_jaffle':
            orders,customers,methods,recon=(b[k] for k in ('order_payments','customer_summary','method_summary','reconciliation'))
            if sum(r[2] for r in orders)!=sum(r[1] for r in methods):return False
            if sum(r[3] for r in orders)!=sum(r[2] for r in methods):return False
            rc={r[0]:r[1:] for r in recon}
            if set(rc)!={r[0] for r in customers}:return False
            for cid,amount,count,norders in customers:
                selected=[r for r in orders if r[1]==cid]
                if [amount,count,norders]!=[sum(r[2] for r in selected),sum(r[3] for r in selected),len(selected)]:return False
                if rc[cid]!=[sum(r[3]>0 for r in selected),sum(r[3]==0 for r in selected),amount]:return False
            return True
        if kind=='rich_energy':
            generation,window,coverage,excluded,contract=(b[k] for k in ('generation_report','window_summary','coverage_report','exclusions','field_contract'))
            for iso,n,total in window:
                rs=[r for r in generation if r[0]==iso]
                if n!=len(rs) or not math.isclose(total,sum(r[2] for r in rs),abs_tol=1e-9,rel_tol=1e-12):return False
            for iso,observed,measured,missing in coverage:
                if observed!=measured+missing or measured!=sum(r[0]==iso for r in generation):return False
                if missing!=sum(r[0]==iso and r[2]=='missing' for r in excluded):return False
            return contract==[['generation_twh','TWh','omitted','observed_years_sum']]
    except (KeyError,TypeError,ValueError,IndexError):return False
    return False


def inventory(sources):
    from .qualification import runtime_versions
    from .track_f_controls import PINS
    rows=[]
    registry=load(ROOT/'source_registry.json')
    for card in catalog(RICH)['tasks']:
        public=load(RICH/'public'/(card['id']+'.json'))
        private=private_task(card['id'])
        blockers=['independent_review_pending','fresh_cpu_qualification_required','public_prompt_footprint_unmeasured','cohort_approval_required']
        loaded=None
        try:_,loaded=load_task(card['id'],sources)
        except (Rejected,OSError) as e:blockers.append(str(e))
        if card['pack']=='energy':blockers.append('underlying_provider_license_review_pending')
        c=v2.configuration(7,planning_lane='authored_diagnostic',execution_contract='plan_scoped_v1',planner_output_cap=6144)
        # Only public source names are needed for structural diagnostics.
        structures=[v2.descriptors(v2.authored_plan(public,c,w['organization'])) for w in private['witnesses']]
        pack=next(p for p in registry['packs'] if p['id']==card['pack'])
        rows.append(dict(card=card,required_outputs=public['required_outputs'],blockers=blockers,
            source_pin=pack,reference_structures=structures,fixture_variants=len(private['fixtures']),
            source_table_count=len(loaded['tables']) if loaded is not None else None,
            source_schema_breadth={k:len(t['columns']) for k,t in loaded['tables'].items()} if loaded is not None else None,
            structure_scope='private reference only, not preferred model plans'))
    rows.append(load(RICH/'blocked-api-integration.json'))
    versions=runtime_versions()
    return dict(schema='rr-rich-inventory-v1',candidates=rows,runtime_versions=versions,
                dependencies_available=all(versions.get(k)==v for k,v in PINS.items()),
                executable_cards=3,authoring_target=4,source_groups=3,model_executed=False,
                task_execution_allowed=False)


def qualify(task,sources):
    from .engine import Engine,ScriptedWorker
    from .evaluator import evaluate
    from .qualification import implementation_hashes,runtime_versions
    from .track_f_controls import PINS
    start=time.process_time()
    actual=runtime_versions()
    if any(actual.get(k)!=v for k,v in PINS.items()):return dict(status='blocked_prerequisite',required=PINS,actual=actual,task=task)
    card,public=load_task(task,sources)
    private=private_task(task)
    c=v2.configuration(7,planning_lane='authored_diagnostic',execution_contract='plan_scoped_v1',planner_output_cap=6144)
    positive=[];basis=None
    for witness in private['witnesses']:
        plan=v2.authored_plan(public,c,witness['organization'])
        engine=Engine(public,ScriptedWorker(witness),plan=plan,v2=c,resources=Resources(100000,1200))
        try:
            row=engine.run();grade=evaluate(public,private,row['state'])
            positive.append(dict(organization=witness['organization'],success=grade.get('success'),
                status=row['status'],conformant=row['conformance']['contract_conformant'],structure=v2.descriptors(plan),
                checks=len(grade.get('checks',[])),resources=row['resource_profile'],evaluator_resources=grade.get('evaluator_resources')))
            if basis is None:basis=deepcopy(row['state'])
        finally:engine.env.close()
    controls=[]
    for req in public['required_outputs']:
        key=req['id']
        for mutation in ('missing','wrong_semantics'):
            state=deepcopy(basis)
            if mutation=='missing':state['bound'].pop(key,None)
            else:
                bad=deepcopy(private['witnesses'][0])
                action=next(x['action'] for x in bad['actions'] if key in x['action']['obligations'])
                if action['format']=='sql':
                    action['content']='SELECT '+','.join(("'incorrect'" if typ=="string" else "999")+" AS "+col for col,typ in zip(req['columns'],req['types']))
                elif action['format']=='schema':action['content']=True
                else:action['content']['fields']={}
                eng=Engine(public,ScriptedWorker(bad),plan=v2.authored_plan(public,c,bad['organization']),v2=c,resources=Resources(100000,1200))
                try:state=eng.run()['state']
                finally:eng.env.close()
            controls.append(dict(obligation=key,mutation=mutation,detected=evaluate(public,private,state).get('success') is False))
        if req['format']=='schema':
            bad=deepcopy(private['witnesses'][0])
            next(x['action'] for x in bad['actions'] if key in x['action']['obligations'])['content']=False
            eng=Engine(public,ScriptedWorker(bad),plan=v2.authored_plan(public,c,bad['organization']),v2=c,resources=Resources(100000,1200))
            try:state=eng.run()['state']
            finally:eng.env.close()
            controls.append(dict(obligation=key,mutation='reject_all',detected=evaluate(public,private,state).get('success') is False))
    repeat=evaluate(public,private,basis)
    _,again=load_task(task,sources)
    integrity=digest(public)==digest(again)
    ok=all(r['success'] is True and r['conformant'] for r in positive) and all(r['detected'] for r in controls) and integrity and repeat.get('success') is True
    return dict(schema='rr-rich-qualification-v1',task=task,task_hash=digest(card),public_hash=digest(public),private_hash=digest(private),
        status='cpu_qualified_review_pending' if ok else 'failed',witnesses=positive,negative_controls=controls,
        source_integrity=integrity,reset_repeat_identical=repeat.get('success') is True,
        implementation_hashes=implementation_hashes(),runtime_versions=actual,
        model_executed=False,evidence='scripted_reference_only',task_execution_allowed=False,independent_review='pending',
        source_schema_breadth={k:len(v['columns']) for k,v in public['tables'].items()},
        retained_source_count=len(public['sources']),required_output_count=len(public['required_outputs']),
        analysis_cpu_seconds=time.process_time()-start)
