"""Reference policies through public tools. No private evaluator imports."""
from copy import deepcopy
import math
from .common import Rejected, digest
from .runtime import WORKERS


def validate_plan(plan, public):
    if set(plan)!={'id','units'} or not 1<=len(plan['units'])<=8:raise Rejected('plan')
    required={r['id'] for r in public['required_outputs']};seen=set();outputs=[]
    for unit in plan['units']:
        if set(unit)!={'id','worker','outputs','depends','description'} or unit['id'] in seen or unit['worker'] not in WORKERS:
            raise Rejected('plan_unit')
        if not set(unit['depends'])<=seen or set(unit['outputs'])-required:raise Rejected('plan_dependency')
        if not isinstance(unit['description'],str) or len(unit['description'])>2048:raise Rejected('plan_description')
        seen.add(unit['id']);outputs.extend(unit['outputs'])
    if sorted(outputs)!=sorted(required):raise Rejected('plan_coverage')
    return plan


def organization_key(plan):
    # Owner renaming and descriptions are not structural alternatives. Actual
    # grouping/dependencies/output sets remain; count active workers separately.
    names={u['id']:str(i) for i,u in enumerate(plan['units'])}
    return digest([{'outputs':sorted(u['outputs']),'depends':sorted(names[d] for d in u['depends'])} for u in plan['units']])


def variation(plans,public):
    for p in plans:validate_plan(p,public)
    return {'organizations':len({organization_key(p) for p in plans}),
        'plans':[dict(id=p['id'],key=organization_key(p),active_workers=len({u['worker'] for u in p['units']})) for p in plans],
        'costs_measured':False,'ranking_reversal_required':False}


def choose_plan(public, policy, outline='independent'):
    if policy not in ('solo','delegation_jit','restart','replication'):raise Rejected('policy_requires_matched_calibration')
    name='grouped' if policy=='solo' else outline
    plan=deepcopy(next(p for p in public['outlines'] if p['id']==name))
    return validate_plan(plan,public)


def select_calibrated(plans,public,calibration,mode,compatibility,*,cap=None,reserve=0,ranker=None):
    # Optional finite policy selector; incomplete or unmeasured costs do not become 0.
    if mode not in ('nominal','recovery') or not calibration or calibration.get('compatibility')!=compatibility or calibration.get('measured') is not True:
        raise Rejected('matched_calibration_required')
    for p in plans:validate_plan(p,public)
    entries=calibration['plans']
    if set(entries)!={organization_key(p) for p in plans}:raise Rejected('calibration_catalog')
    evaluations=[]
    for row in entries.values():
        if row.get('eligible') is not True or any(type(row.get(k)) not in (int,float) or not math.isfinite(row[k]) or row[k]<0 for k in ('clean_tokens','worst_total_tokens')):
            raise Rejected('calibration_quality')
        if row['worst_total_tokens']<row['clean_tokens']:raise Rejected('calibration_quality')
    if cap is None:raise Rejected('calibration_cap_required')
    if not 0<=reserve<cap:raise Rejected('reserve')
    for p in plans:
        row=entries[organization_key(p)]
        if row['clean_tokens']<=cap-reserve and row['worst_total_tokens']<=cap:
            evaluations.append({'id':p['id'],'clean':row['clean_tokens'],'objective':row['worst_total_tokens']})
    if not evaluations:raise Rejected('no_costed_feasible_plan')
    chosen=(ranker(evaluations,mode) if ranker else min(evaluations,key=lambda e:(e['objective'] if mode=='recovery' else e['clean'],e['id'])))
    return deepcopy(next(p for p in plans if p['id']==chosen['id']))
