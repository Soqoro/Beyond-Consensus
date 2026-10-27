"""Small offline vertical slice. No external model or scheduler adapters."""
import json
import hashlib
import time
from pathlib import Path
from .model import Allocation, Invalid, digest, fixture, plain
from .allocation import allocate,llm_reply,llm_request
from .runtime import Executor,Budget,Journal,invariance,execute,repair,ownership_view,trace_from_record
from .planning import compile_slots,validate_disabled
from .analysis import matrix


def repair_identity(request,baseline,allocation,group,executor,repeat):
    """Bind reuse to the frozen code/limits, exact clean artifacts and incident policy."""
    return digest([request,baseline.key,allocation.partition,allocation.owner(tuple(group)),
                   executor.key,repeat,'repair-v1','independent-original-clean','no-mutation'])


def demo(path,config,cap=50000,repeats=2):
    cpu_started=time.process_time()
    validate_disabled(config)
    if type(cap) is not int or not 0<=cap<=100000 or repeats not in (1,2):raise Invalid('bounded offline demonstration')
    w=fixture(6);n=4;executor=Executor('seeded_mock')
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}
    core=Path(__file__).resolve().parents[1]/'bc_phase1/core.py'
    code['bc_phase1/core.py']=hashlib.sha256(core.read_bytes()).hexdigest()
    request=digest([w.key,executor.key,config,cap,repeats,code])
    prior=Path(path)/'spec.json'
    if prior.exists():
        spec=json.loads(prior.read_text())
        if spec.get('request')!=request:raise Invalid('resume request/code drift')
        report_path=Path(path)/'report.json'
        if report_path.exists():
            report=json.loads(report_path.read_text())
            if report['spec']!=digest(spec):raise Invalid('report specification mismatch')
            return report
        registry=spec['registry'];allocation_details=spec['allocation_details'];estimator=registry['estimator']
        conditions=[]
        for c in registry['conditions']:
            record=c['allocation']
            aa=Allocation(**{**record,'groups':tuple(tuple(g) for g in record['groups'])}) if record else None
            conditions.append({'method':c['method'],'allocation':aa})
    else:
        costs={t.id:str(t.synthetic_cost) for t in w.tasks}
        estimator=digest(['supplied synthetic',costs]);conditions=[];allocation_details={}
        for method in ('random_valid','direct_workload_balance','greedy_mean','greedy_worst','matching_mean','matching_worst'):
            a,details=allocate(w,n,costs,method,17,estimator);conditions.append({'method':method,'allocation':a});allocation_details[method]=details
        replies={'llm_mean':{'groups':[['t00','t05'],['t01','t04'],['t02'],['t03']]},
                 'llm_worst':{'groups':[['t00']]}}
        for method,reply in replies.items():
            validated=llm_reply(w,n,[reply]);llm_input=llm_request(w,n,costs,'worst' if method.endswith('worst') else 'mean')
            a=Allocation(w.key,n,validated['groups'],estimator,method,17,prompt_binding=digest(llm_input)) if validated['status']=='valid' else None
            conditions.append({'method':method,'allocation':a});allocation_details[method]={'reply':validated,'synthetic_recorded_reply':True,'request_digest':digest(llm_input)}
        qualification=invariance(w,[c['allocation'] for c in conditions if c['allocation']],executor)
        registry=compile_slots(w,n,conditions,repeats,executor.key,estimator,seed=41)
        spec={'request':request,'version':'phase2-mock-demo-v3','registry':registry,'config':digest(config),'cap':cap,
              'qualification':qualification,'allocation_details':allocation_details,'allocation_and_freeze_cpu_seconds':time.process_time()-cpu_started}
    journal=Journal(path,spec);report_path=Path(path)/'report.json';history=journal.events()
    if not history:journal.append({'type':'allocations_frozen','details':allocation_details,'registry':registry})
    starts={(e['slot'],e['attempt']) for e in history if e['type']=='start'}
    ends={(e['slot'],e['attempt']) for e in history if e['type']=='finish'}
    if starts!=ends:raise Invalid('unclosed physical attempt retained; uncertain usage requires review')
    budget=Budget(cap);clean={};physical={};rows=[];stopped=False;research_events=[]
    resumed_physical_ids={e['slot'] for e in history if e['type']=='finish'}
    previous={e['row']['slot']:e['row'] for e in history if e['type']=='logical_outcome'}
    for event in history:
        if event['type']!='finish':continue
        trace=trace_from_record(event['outcome']['trace']);research_events.append(trace)
        if trace.usage!='complete':raise Invalid('missing usage blocks further dispatch')
        budget.spent+=trace.observed_spend
        if trace.phase=='clean':clean[trace.repeat]=trace
        else:physical[event['slot']]=trace
    for slot in registry['slots']:
        if slot['id'] in previous:
            row=previous[slot['id']];rows.append(row)
            stopped=stopped or row['execution']!='completed' or row.get('usage')!='complete';continue
        condition=next(c for c in conditions if c['method']==slot['method']);a=condition['allocation'];rep=slot['repeat']
        base={'slot':slot['id'],'method':slot['method'],'repeat':rep,'unit':executor.unit,'executor':executor.key,
              'estimator':estimator,'partition':a.partition if a else None,'condition':a.key if a else None,
              'owner':a.owner(tuple(slot['owner_group'])) if a else None,'full_cost':None,'semantic':'unknown',
              'usage':'missing','observed_spend':None,'schema':'unknown'}
        if stopped:rows.append({**base,'execution':'not_run_due_campaign_stop'});continue
        if a is None:rows.append({**base,'execution':'invalid_allocation'});continue
        if rep not in clean:
            cid=digest([w.key,executor.key,rep,'clean']);journal.begin(cid)
            t=execute(w,executor,rep,budget,event_sink=journal.append);clean[rep]=t;research_events.append(t)
            journal.finish(cid,0,{'execution':t.execution,'trace':t})
        baseline=clean[rep]
        if baseline.execution!='completed':
            rows.append({**base,'execution':'no_clean_snapshot'});stopped=baseline.execution=='resource_stopped';continue
        g=tuple(slot['owner_group']);cache=repair_identity(request,baseline,a,g,executor,rep)
        if cache not in physical:
            journal.begin(cache)
            result=repair(w,executor,rep,budget,baseline,a,g,event_sink=journal.append)
            trace=result['trace'];physical[cache]=trace;research_events.append(trace)
            journal.finish(cache,0,{'execution':trace.execution,'trace':trace})
            reused=False
        else:
            trace=physical[cache]
            if trace.execution!='completed' or trace.usage!='complete' or trace.full_cost is None:
                raise Invalid('incomplete physical checkpoint cannot be reused; review required')
            reused=True
        row={**base,'execution':trace.execution,'schema':trace.schema,'semantic':trace.semantic,'usage':trace.usage,
             'full_cost':trace.full_cost,'observed_spend':trace.observed_spend,'physical_id':cache,
             'physical_reuse':reused,'baseline_semantic':baseline.semantic,'ownership_view':ownership_view(baseline,a),
             'deployment_cost':baseline.full_cost+trace.full_cost if baseline.full_cost is not None and trace.full_cost is not None else None,
             'clean_deployment_charge':baseline.full_cost,'restoration_from_valid_clean':baseline.semantic=='valid'}
        rows.append(row);journal.append({'type':'logical_outcome','row':row})
        if trace.execution!='completed' or trace.usage!='complete':stopped=True
    summaries={}
    for c in conditions:
        a=c['allocation']
        summaries[c['method']]=matrix([r for r in rows if r['method']==c['method']],a,repeats,executor.key,executor.unit) if a else {'status':'invalid_allocation'}
    process_cpu=time.process_time()-cpu_started
    worker_cpu=sum(e.get('worker_cpu_seconds',0) for t in research_events for e in t.events)
    new_worker_cpu=sum(e.get('worker_cpu_seconds',0) for key,t in physical.items() if key not in resumed_physical_ids for e in t.events)
    new_worker_cpu+=sum(e.get('worker_cpu_seconds',0) for rep,t in clean.items() if digest([w.key,executor.key,rep,'clean']) not in resumed_physical_ids for e in t.events)
    allocation_cpu=0 if history else spec['allocation_and_freeze_cpu_seconds']
    report={'schema':'phase2-mock-report-v3','spec':digest(spec),'synthetic':True,'model_executed':False,
            'allocation_details':allocation_details,'registry':registry,'outcomes':rows,'summaries':summaries,
            'accounting':{'unit':executor.unit,'physical_clean_sessions':len(clean),'physical_repair_sessions':len(physical),
              'known_research_spend':sum(t.observed_spend for t in research_events),'uncertain_reservations':budget.reserved,
              'deployment_view':'each logical outcome includes a full clean charge and ONE alternative incident',
              'reconstruction_view':'outcomes.full_cost, null when incomplete','CPU_separate_units':{'allocation_and_freeze_cpu_seconds':spec['allocation_and_freeze_cpu_seconds'],
                'physical_mock_worker_cpu_seconds':worker_cpu,'current_process_cpu_seconds':process_cpu,
                'protected_current_process_cpu_seconds':max(0,process_cpu-allocation_cpu-new_worker_cpu),
                'scope':'CPU seconds separate from synthetic spend; protected overhead covers current invocation only, excludes final report serialization'},
              'partition_reuse':'explicit physical_id links; reused observations are not independent replicates'},
            'limitations':['synthetic usage only','invalid synthetic LLM reply retained','no live backends','resume uses completed physical checkpoints; unclosed/unknown attempts require review, no automatic retry']}
    # Keep every planned row, including unstarted stop slots, in durable journal.
    journal.append({'type':'all_planned_outcomes','rows':rows})
    with report_path.open('x') as f:json.dump(plain(report),f,indent=2)
    return report
