"""Disabled template, future dependency checks and frozen mock slot registry."""
import json
import random
from pathlib import Path
from .model import Invalid, digest, groups, plain

MAIN=('random_valid','direct_workload_balance','greedy_mean','greedy_worst','llm_mean','llm_worst','matching_mean','matching_worst')
PILOT=('direct_workload_balance','greedy_mean','llm_mean','llm_worst','matching_mean','matching_worst')


def stage_readiness(config,stage):
    """Report missing future bindings; never grants a real executable backend."""
    if stage not in ('offline_validation','calibration','smoke','pilot','main','corruption','unit_cost_ablation'):raise Invalid('stage')
    blockers=[]
    if config.get('comparative_run',{}).get('predicted_incident_budget') is not None: blockers.append('comparative_B_must_be_null')
    requirements=config.get('stage_gate_requirements',{})
    keys=list(requirements.get('offline_validation',[])) if stage=='offline_validation' else list(requirements.get('all_model_execution',[]))
    if stage in ('smoke','pilot'):keys+=requirements.get('smoke_and_pilot',[])
    else:keys+=requirements.get(stage,[])
    supplied=config.get('verified_bindings',{})
    blockers += [key for key in keys if not supplied.get(key)]
    if stage=='main' and not config.get('sampling',{}).get('estimator_version'):blockers.append('final_estimator_missing')
    return {'stage':stage,'missing':sorted(set(blockers)),'dependencies_ready':not blockers,
            'execution_allowed':stage=='offline_validation' and not blockers,'real_backend_available':False}


def validate_disabled(config):
    if config.get('protocol')!='beyond_consensus_phase2' or str(config.get('version'))!='3.0':raise Invalid('versioned protocol')
    ex=config['execution']
    if ex.get('default_mode')!='mock_cpu':raise Invalid('only mock_cpu')
    for key in ('real_model_calls_enabled','api_calls_enabled','local_model_inference_enabled','downloads_enabled','cluster_submission_enabled','git_write_actions_enabled','real_backends_registered_in_this_handoff'):
        if ex.get(key) is not False:raise Invalid('real execution forbidden: '+key)
    if config['comparative_run']['predicted_incident_budget'] is not None or config['budgets']['predicted_incident_budget'] is not None:raise Invalid('comparative B must be null')
    if config['datasets']['arc100']['enabled'] is not False:raise Invalid('ARC identity unresolved')
    return True


def compile_slots(w,n,conditions,repeats,executor,estimator,seed=0,draw=0):
    if not 4<=n<=10 or not n<len(w.ids)<=2*n:raise Invalid('meaningful m>n and eligible n=4..10')
    if type(repeats) is not int or repeats<=0 or not conditions:raise Invalid('explicit conditions/repetitions')
    methods=[c['method'] for c in conditions]
    if len(set(methods))!=len(methods):raise Invalid('duplicate method')
    for c in conditions:
        a=c.get('allocation')
        if a is not None:
            if (a.workflow,a.n,a.estimator,a.method,a.draw)!=(w.key,n,estimator,c['method'],draw):raise Invalid('condition drift')
            groups(w,n,a.groups)
    # Independent scheduling stream; no prices, gains or evaluation outcomes.
    rng=random.Random(seed);base=sorted(methods);rng.shuffle(base);slots=[]
    for repeat in range(repeats):
        orders={}
        for c in conditions:
            a=c.get('allocation');owners=list(a.groups) if a else [None]*n
            random.Random(int(digest([seed,w.key,c['method'],repeat,'owners']),16)).shuffle(owners);orders[c['method']]=owners
        for k in range(n):
            rotated=base[(repeat+k)%len(base):]+base[:(repeat+k)%len(base)]
            for method in rotated:
                c=next(c for c in conditions if c['method']==method);a=c.get('allocation');g=orders[method][k]
                identity=[w.key,n,estimator,executor,method,draw,repeat,tuple(g) if g else ['invalid-owner-slot',k],a.key if a else None]
                slots.append({'id':digest(identity),'method':method,'repeat':repeat,'owner_group':g,
                              'allocation':a.key if a else None,'status':'pending','invalid_allocation':a is None})
    return {'workflow':w.key,'n':n,'repeats':repeats,'executor':executor,'estimator':estimator,'allocation_draw':draw,
            'conditions':plain(conditions),'slots':slots,'clean_sessions':repeats,'repair_sessions':len(slots),
            'shared_clean_requires_qualification':True,'schedule_seed':seed,'digest':digest(slots)}


def pilot_eligibility(workflows):
    counts={4:0,7:0,10:0};sources=set()
    for w,n in workflows:
        if n not in counts or not n<len(w.ids)<=2*n or w.source in sources:raise Invalid('pilot eligibility/source duplicates; no padding')
        counts[n]+=1;sources.add(w.source)
    if counts!={4:4,7:4,10:4}:raise Invalid('pilot size bands not covered')
    return {'clean':len(workflows)*2,'repairs':sum(n*6*2 for w,n in workflows),'total':len(workflows)*2+sum(n*6*2 for w,n in workflows)}


def scale_coverage(observed,requested):
    missing=sorted(set(requested)-set(observed))
    return {'status':'blocked' if missing else 'covered','unsupported_n':missing,'claim':'size bands only; context/closure coverage needs separate review'}
