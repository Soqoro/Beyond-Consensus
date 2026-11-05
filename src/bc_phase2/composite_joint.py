"""One AB development comparison: NEUTRAL versus joint A/B selection, direct C.

No live permission is implicit. Historical composite-v4 recipe remains separate.
"""
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import csv
import json
from . import composite_math as base
from .model import digest
from .joint_schema import require
from .joint_core import compile_organisation, explicit_selection, evaluate
from .joint_pipeline_runtime import recover
from beyond_consensus.util import atomic_json

CONDITION='composite-neutral-joint-v3-ab'
METHODS=('NEUTRAL','JOINT')
A_OPTIONS=('original','algebraic')
ALGEBRAIC=' Use an algebraic inequality proof, without differentiation or numerical minimisation. Derive the required inequalities and their equality conditions; do not substitute numerical trials for a global proof.'
LIMITS={**base.LIMITS,'maximum_calls':57,'token_cap':57*16384}
WORKER_POLICY=dict(checkpoint='Qwen/Qwen3.5-27B',revision='fc05daec18b0a78c049392ed2e771dde82bdf654',
    dtype='bfloat16',attention='sdpa',thinking=False,do_sample=False,context=16384,output=3072,
    decoder='task-fields-xgrammar-v1',xgrammar='0.1.32',fresh_context=True,retry=False)

def task_for(op):
    task=deepcopy(base.TASKS[int(op.host[1:])])
    if op.id=='e0' and op.mode=='algebraic':task['responsibility']+=ALGEBRAIC
    return task

def coverage():
    """Ownership invariant contexts; upstream implementation is part of e1's key."""
    from .joint_d1_local import METADATA
    rows=[]
    for i,t in enumerate(base.TASKS):
        for mode in (A_OPTIONS if i<2 else ('base',)):
            instruction=t['responsibility']+(ALGEBRAIC if i==0 and mode=='algebraic' else '')
            descriptor=dict(operation='e'+str(i),host=t['id'],implementation=mode if i==0 else 'base',
                instruction=instruction,prompt=base.PROMPT,fields=t['fields'],
                source_sha256=base.HASHES[t['source']],parent_tasks=t['parents'],
                parent_implementation=mode if i==1 else None,
                C='direct_parent_artifacts',context='own original statement + complete declared parent fields; fresh',
                ownership_dependence='none; no identity, method, or history in request',
                model=WORKER_POLICY,metadata=METADATA)
            rows.append(dict(id=f'e{i}.{mode}',key=digest(descriptor),descriptor=descriptor))
    return rows

def domain(prices=None):
    keys={r['id'] for r in coverage()}
    if prices is not None:
        require(set(prices)==keys and all(type(v) is int and v>0 for v in prices.values()),'complete positive mode coverage')
    d=base.domain();d['source']['id']=CONDITION;d['unit']='mode_profile_input_plus_generated_tokens' if prices else 'unit_structural_placeholders_not_calibration'
    d['choices']=[dict(id='proof',axis='A',options=list(A_OPTIONS))]
    for i,e in enumerate(d['events']):
        original=deepcopy(e['modes'][0]);e['modes']=[]
        for mode in (A_OPTIONS if i<2 else ('base',)):
            row=deepcopy(original);row.update(id=mode,when={'proof':mode} if i<2 else {})
            value=str(prices[f'e{i}.{mode}']) if prices else '1'
            row.update(initial=value,replay=value);e['modes'].append(row)
    for i in (0,1):
        v=d['tasks'][i]['variants'][0]
        d['tasks'][i]['variants']=[dict(deepcopy(v),id=mode,when={'proof':mode}) for mode in A_OPTIONS]
    return d

def selection(d,proof='original',ownership=None):
    return explicit_selection(d,{'proof':proof},{},ownership or base.blueprint()['ownership'])

def blueprint():
    b=base.blueprint()
    b.update(condition=CONDITION,methods=list(METHODS),domain_axes='AB; fixed direct C',
        A_options=list(A_OPTIONS),C_protocols=['direct_parent_artifacts'],
        alternative_instruction=ALGEBRAIC,mode_coverage=coverage(),limits=LIMITS,
        neutral_A={'proof':'original'},neutral_C={},
        profile_schedule=[dict(slot='profile/original',proof='original',events=['e0','e1','e2','e3','e4']),
                          dict(slot='profile/algebraic',proof='algebraic',events=['e0','e1'])],
        profiling_call_cap=7,Lmax=5,evaluation_call_bound=50,
        profile_rule='fresh ordered observations; exactly one per mode key; no fallback or historical price reuse',
        schedule=['profile/original','profile/algebraic']+[m+'/clean' for m in METHODS]+[f'{m}/owner/o{i}' for i in range(4) for m in METHODS],
        identical_design='share only identical full compiled organisation identity; otherwise separate clean and repairs')
    return b

class Journal(base.Journal):
    def __init__(self,path,transport,scope,check_source):
        super().__init__(path,transport,scope,check_source,condition=CONDITION,limits=LIMITS)

class ModeEngine(base.MathEngine):
    def task_for_operation(self,op):return task_for(op)

def same_design(a,b):
    return a==b  # Full compiled identity, including modes, owners, inputs and order.

def checked_candidate(d,certificate,neutral):
    require(certificate.get('status')!='SOLVER_DEPENDENCY_BLOCKED','solver unavailable')
    chosen=certificate.get('candidate') or neutral
    score=evaluate(compile_organisation(d,chosen));ns=evaluate(compile_organisation(d,neutral))
    require(score['objective_pair']<=ns['objective_pair'],'retained neutral incumbent worsened')
    if certificate.get('score') is not None:
        require(base.serial(certificate['score'])==base.serial(score),'certificate score mismatch')
    lower=certificate.get('lower')
    if lower is not None:require(Fraction(lower)<=score['objective_pair'][0],'certificate lower exceeds incumbent')
    if certificate.get('primary_certified'):
        require(lower is not None and Fraction(lower)==score['objective_pair'][0],'primary certificate mismatch')
    if certificate.get('lexicographic_certified'):
        require(certificate.get('primary_certified') is True,'secondary without primary proof')
    return chosen

def pending_result():
    return dict(status='unrun',methods={m:dict(status='unrun',question_quality='unknown',composite_quality='unknown',
                clean=None,repairs=[],full_cost_coverage=False,replay_sum=None,replay_mean=None,replay_max=None,
                quality_preserving_saving=None,shared_with=None) for m in METHODS})

def write_csv(out,result):
    fields=['method','status','shared_with','clean_tokens','replay_sum','replay_mean','largest_observed','replay_calls','full_cost_coverage','question_quality','composite_quality']
    with (out/'NEUTRAL_VS_JOINT_RESULTS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for m in METHODS:
            row=result['methods'][m];w.writerow(dict(method=m,status=row['status'],shared_with=row.get('shared_with'),
                clean_tokens=(row.get('clean') or {}).get('full_cost'),replay_sum=row.get('replay_sum'),replay_mean=row.get('replay_mean'),
                largest_observed=row.get('replay_max'),replay_calls=sum(len(x['invocations']) for x in row.get('repairs',[])),
                full_cost_coverage=row['full_cost_coverage'],question_quality='unknown',composite_quality='unknown'))

def write_report(out,result):
    lines=['# NEUTRAL versus JOINT: AB development pilot','',
        'A implementation and B ownership are variable; C is fixed direct delivery. This does not test independent C benefit.',
        'One repetition; same-instance profile proxies; final mathematical fields require blinded human review.',
        'Incorrect outputs remain charged observations. No quality-preserving saving is established.','',
        'Status: '+result['status'], 'Physical totals: '+json.dumps(result.get('totals')),
        'Shared full-identity observations: '+str(result.get('shared_observations',False)),
        'Profile attempted tokens: '+str(sum(x['known_attempted_spend'] for x in result.get('profile',[]))),
        '', '| Method | Status | Clean tokens | Four-repair sum | Mean | Largest observed |',
        '|---|---|---:|---:|---:|---:|']
    for m in METHODS:
        r=result['methods'][m]
        lines.append(f"| {m} | {r['status']} | {(r.get('clean') or {}).get('full_cost')} | {r.get('replay_sum')} | {r.get('replay_mean')} | {r.get('replay_max')} |")
    lines+=['','All four owner incidents are alternative counterfactuals, not a cumulative deployment trajectory.',
        'Frozen designs contain the encoded bounds/certificate, mode choices and initial expenditure. Raw ledgers preserve uncertain usage and unrun outcomes.',
        'Full mathematical success remains unknown until review; equal failure does not establish quality preservation.']
    (out/'FIRST_JOINT_RESULT.md').write_text('\n'.join(lines)+'\n')

def run_recipe(journal,sources,out,solver=None):
    from .joint_solver import solve
    out=Path(out);out.mkdir(exist_ok=True);b=blueprint();result=pending_result();result.update(profile=[],condition=CONDITION,
        evidence=journal.binding['transport'].get('evidence'),model_executed=False,shared_observations=False)
    state=dict(status='profile_pending',slots={k:'unrun' for k in b['schedule']})
    atomic_json(out/'recipe-state.json',state);write_csv(out,result)
    atomic_json(out/'FROZEN_DOMAIN_AND_SCOPE.json',dict(scope_digest=journal.binding['scope'],blueprint=b,domain=domain(),status='unpriced_structural_domain'))
    atomic_json(out/'FROZEN_TWO_ARM_DESIGNS.json',dict(methods={m:None for m in METHODS},status='pending_profile',prices=None))
    engine=ModeEngine(journal,sources,out)
    def save():
        state['slots'].update({k:v['status'] for k,v in engine.slots.items()})
        result['totals']=journal.snapshot()['totals'];result['model_executed']=result['evidence']=='real_composite_worker_development' and result['totals']['calls']>0
        atomic_json(out/'recipe-state.json',state);atomic_json(out/'result.json',base.serial(result));write_csv(out,result);write_report(out,result)
    try:
        observations={};d=domain()
        for spec in b['profile_schedule']:
            ex=compile_organisation(d,selection(d,spec['proof']))
            row=engine.run(ex,spec['slot'],required=set(spec['events']),phase='profile');result['profile'].append(base.serial(row));save()
            if not row['complete']:
                result['status']=state['status']='profile_coverage_failed';save();return result
            for tr in row['trace']:
                op=next(op for op in ex.operations if op.id==tr['event']);key=op.id+'.'+op.mode
                require(key not in observations,'duplicate mode observation; no adaptive profiling')
                observations[key]=dict(tokens=tr['usage'],invocation=tr['invocation'],slot=spec['slot'])
        require(set(observations)=={r['id'] for r in coverage()},'unpriced required mode')
        prices={k:v['tokens'] for k,v in observations.items()}
        frozen=dict(prices=prices,observations=observations,coverage=coverage(),transport_binding=journal.binding['transport'],
                    blueprint_digest=digest(b),rule=b['profile_rule']);frozen['digest']=digest(frozen)
        atomic_json(out/'prices.frozen.json',frozen);result['prices']=frozen
        d=domain(prices);neutral=selection(d)
        atomic_json(out/'FROZEN_DOMAIN_AND_SCOPE.json',dict(scope_digest=journal.binding['scope'],blueprint=b,domain=d,prices_digest=frozen['digest'],status='priced_before_selection'))
        certificate=(solver or solve)(d,seed=neutral,seconds=10,threads=1,random_seed=0)
        chosen=checked_candidate(d,certificate,neutral)
        executions={m:compile_organisation(d,s) for m,s in zip(METHODS,(neutral,chosen))}
        identical=same_design(*executions.values());methods=METHODS[:1] if identical else METHODS
        design=dict(methods=dict(NEUTRAL=neutral,JOINT=chosen),domain=d,prices_digest=frozen['digest'],
                    certificate=base.serial(certificate),predicted={m:base.serial(evaluate(ex)) for m,ex in executions.items()},
                    available_axes='AB; direct C fixed',search_axes=['A','B'],
                    changed=dict(A=neutral['A']!=chosen['A'],B=sorted(g for _,g in executions['NEUTRAL'].groups)!=sorted(g for _,g in executions['JOINT'].groups),C=False),
                    exact_shared_identity=identical,status='frozen_before_evaluation')
        atomic_json(out/'FROZEN_TWO_ARM_DESIGNS.json',design);result['designs']=design;result['shared_observations']=identical
        state['status']='evaluation_pending';save()
        clean={};repairs={m:[] for m in methods}
        for m in methods:
            clean[m]=engine.run(executions[m],m+'/clean')
            result['methods'][m].update(status='evaluation_pending',clean=base.serial(clean[m]));save()
        for i in range(4):
            for m in methods:
                row=recover(engine,executions[m],clean[m],'o'+str(i),f'{m}/owner/o{i}',None)
                if row['status']!='no_clean_snapshot':
                    ownership={t:o for o,g in executions[m].groups for t in g}
                    require(set(row['reconstruction'])==base.independent_reconstruction(ownership,'o'+str(i)),'recovery closure mismatch')
                engine.slots[row['slot']]=row
                atomic_json(out/(row['slot'].replace('/','_')+'.json'),base.serial(row));repairs[m].append(row)
                result['methods'][m]['repairs']=base.serial(repairs[m]);save()
        for m in methods:
            costs=[x['full_cost'] for x in repairs[m]];covered=len(costs)==4 and all(c is not None for c in costs)
            ops={o.id:o for o in executions[m].operations}
            for row in repairs[m]:
                proxy=sum(ops[e].replay for e in row['reconstruction']) if 'reconstruction' in row else None
                row['profile_proxy_tokens']=str(proxy) if proxy is not None else None
                row['observed_minus_proxy']=str(row['full_cost']-proxy) if proxy is not None and row['full_cost'] is not None else None
            result['methods'][m].update(status='complete' if covered and clean[m]['complete'] else 'incomplete',
                clean=base.serial(clean[m]),repairs=base.serial(repairs[m]),predicted=base.serial(evaluate(executions[m])),
                full_cost_coverage=covered,replay_sum=sum(costs) if covered else None,
                replay_mean=str(Fraction(sum(costs),4)) if covered else None,replay_max=max(costs) if covered else None)
        if identical:
            result['methods']['JOINT']=deepcopy(result['methods']['NEUTRAL']);result['methods']['JOINT']['shared_with']='NEUTRAL'
            for k in state['slots']:
                if k.startswith('JOINT/'):state['slots'][k]='shared_with_NEUTRAL'
        complete=all(r['full_cost_coverage'] for r in result['methods'].values());den=result['methods']['NEUTRAL']['replay_sum']
        result['recovery_token_reduction']=str(1-Fraction(result['methods']['JOINT']['replay_sum'],den)) if complete and den and not identical else '0' if complete and identical else None
        packet=[];mapping={}
        for slot,row in sorted(engine.slots.items(),key=lambda kv:digest(kv[0])):
            if slot.startswith('profile/'):continue
            for q,event in executions['NEUTRAL'].outputs:
                if event not in row.get('store',{}):continue
                opaque='review-'+digest([CONDITION,slot,q])[:20];mapping[opaque]=dict(slot=slot,output=q)
                packet.append(dict(id=opaque,statement=sources[base.IDS[int(q[1:])]],
                    intermediate_artifacts={e:json.loads(v.value) for e,v in row['store'].items() if base.TASKS[int(e[1:])]['source']==int(q[1:])},
                    output=json.loads(row['store'][event].value),validity='unknown'))
        atomic_json(out/'QUALITY_REVIEW.blinded.json',packet);atomic_json(out/'QUALITY_REVIEW.mapping.private.json',mapping)
        result['status']=state['status']='completed_recipe';save();return result
    except BaseException:
        result['status']=state['status']='halted';save();raise
