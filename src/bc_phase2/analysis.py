"""Exact descriptive summaries, never success-only filtering or invented CIs."""
from fractions import Fraction
from .model import Invalid, rational


def budget_status(full,observed,threshold):
    if threshold is None:return 'not_applicable'
    b=rational(threshold,False)
    if observed is not None and rational(observed,False)>b:return 'exceeded'
    if full is None:return 'unknown'
    return 'within' if rational(full,False)<=b else 'exceeded'


def restoration(row,threshold):
    execution=row['execution'];b=budget_status(row.get('full_cost'),row.get('observed_spend'),threshold)
    if execution=='invalid_allocation':return 'fail'  # intention-to-plan, not a zero bill
    if execution in ('not_run_due_campaign_stop','no_clean_snapshot','pending'):return 'unknown'
    if b=='exceeded':return 'fail'
    if execution in ('task_error','resource_stopped','protocol_violation'):return 'fail'
    if row.get('schema')=='invalid' or row.get('semantic')=='invalid':return 'fail'
    if execution=='completed' and row.get('semantic')=='valid' and row.get('usage')=='complete' and row.get('schema')=='valid' and b=='within':return 'pass'
    return 'unknown'


def matrix(rows,allocation,repeats,executor,unit):
    expected={(allocation.owner(g),r) for g in allocation.groups for r in range(repeats)};seen={};missing=[]
    for row in rows:
        if any(row.get(k)!=v for k,v in [('partition',allocation.partition),('condition',allocation.key),('estimator',allocation.estimator),('executor',executor),('unit',unit)]):raise Invalid('mixed allocation/estimator/executor/unit matrix')
        key=(row['owner'],row['repeat'])
        if key in seen or key not in expected:raise Invalid('duplicate or unplanned logical slot')
        seen[key]=row
    for key in expected:
        row=seen.get(key)
        if row is None or row.get('full_cost') is None or row.get('execution')!='completed' or row.get('usage')!='complete':missing.append(key)
    if missing:return {'status':'incomplete','missing':sorted(missing),'mean':None,'worst_owner_mean':None,'observed_max':None}
    means={owner:sum((rational(seen[owner,r]['full_cost'],False) for r in range(repeats)),Fraction())/repeats for owner,_ in expected}
    return {'status':'complete','mean':sum(means.values())/allocation.n,'worst_owner_mean':max(means.values()),
            'observed_max':max(rational(v['full_cost'],False) for v in seen.values()),'owner_means':means,
            'semantic_invalid_retained':sum(v.get('semantic')=='invalid' for v in seen.values())}


def common_complete(left,right,weights,metric='mean'):
    if metric not in ('mean','worst_owner_mean'):raise Invalid('objective-matched metric')
    if set(left)!=set(right) or set(left)!=set(weights):raise Invalid('planned source conditions must match')
    if any(rational(v)<=0 for v in weights.values()):raise Invalid('source weights')
    keep=[k for k in sorted(weights) if left[k]['status']==right[k]['status']=='complete']
    total=sum((rational(weights[k]) for k in keep),Fraction())
    return {'cohort':keep,'excluded':[k for k in sorted(weights) if k not in keep],
            'left':sum((rational(weights[k])*left[k][metric] for k in keep),Fraction())/total if total else None,
            'right':sum((rational(weights[k])*right[k][metric] for k in keep),Fraction())/total if total else None,
            'claim':'conditional common-complete only; outcome-dependent missingness can bias coverage'}


def endpoints(source_rows,weights,threshold):
    if set(source_rows)!=set(weights):raise Invalid('frozen source denominator')
    details={};lower=upper=Fraction();total=sum(rational(v) for v in weights.values())
    for source,rows in source_rows.items():
        if not rows:raise Invalid('planned incidents required')
        labels=[restoration(r,threshold) for r in rows];p=labels.count('pass');u=labels.count('unknown')
        details[source]={'pass':p,'fail':labels.count('fail'),'unknown':u,'planned':len(rows)}
        lower+=rational(weights[source])*Fraction(p,len(rows))/total;upper+=rational(weights[source])*Fraction(p+u,len(rows))/total
    return {'by_source':details,'bounds':[lower,upper],'kind':'missingness identification bounds, not confidence intervals'}


def accounting(clean,repairs,allocation_cost=0,protected_cost=0):
    # One deployment has one selected owner incident, never a sum over alternatives.
    def cost(t):return t.full_cost
    research_known=clean.observed_spend+sum(t.observed_spend for t in repairs)+allocation_cost+protected_cost
    complete=clean.usage=='complete' and all(t.usage=='complete' for t in repairs)
    return {'unit':'synthetic_work','synthetic':True,'research':{'known_observed':research_known,'usage_complete':complete,
             'clean_physical_count':1,'repair_physical_count':len(repairs),'allocation':allocation_cost,'protected':protected_cost},
            'one_deployment_per_incident':[{'clean':cost(clean),'repair':cost(t),
              'total':cost(clean)+cost(t)+allocation_cost+protected_cost if cost(clean) is not None and cost(t) is not None else None} for t in repairs],
            'reconstruction':[cost(t) for t in repairs], 'alternative_incidents_not_one_cumulative_deployment':True}
