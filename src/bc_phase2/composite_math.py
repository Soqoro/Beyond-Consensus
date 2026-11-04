"""One fixed-A/C development recipe. No changes to the accepted joint core."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import time
from .model import digest, Invalid
from .joint_schema import require, decode
from .joint_core import compile_organisation, explicit_selection, evaluate
from .joint_fixtures import graph_fixture
from .joint_pipeline_runtime import Engine, Artifact, recover, snapshot_digest
from .d1_natural_screen import NaturalMockSession, NaturalTransport, reliable_terminal
from beyond_consensus.util import atomic_json, plain

CONDITION='composite-math-r0-b-dev-v3-json'
IDS=('test/intermediate_algebra/1166.json','test/counting_and_probability/1003.json')
HASHES=('199e104d517ec67e4f167c49f035776c7bdaf933e41971c80716e26979d3a9a8','d4e914d360a34942f21e2a635cd2c97d3b6cec1a1f2ced16de22d6fd1b5712d0')
RAW_PLAN_HASHES=['9a1a0f405abc9a011c35f67f0b8ef11db2ddb55c8e8fc55bed09f57fc6304a5d', '4eaae1878a8dc422b893ee3fb13d185df4b5170e3e252977621c49f1fe2069be']
PROMPT='''Execute only the declared mathematical task. Use the original statement and supplied parent artifacts. Return one JSON object with exactly the named string fields. Give the mathematical derivation and all conditions needed by consumers, not a plan for future work. Do not solve another task, call tools, or invent missing parent results. No markdown fences. An unsupported derivation must be stated honestly in its field; no retry will occur.'''
# Source content and answers are never embedded in these contracts.
TASKS=[
 dict(id='t0',source=0,parents=[],responsibility='Reformulate the expression as needed and prove a global lower bound for all positive a,b,c. State every inequality and its equality conditions. Do not claim attainability without a witness.',fields=['bound','derivation','equality_conditions']),
 dict(id='t1',source=0,parents=['t0'],responsibility='Using the supplied bound and equality conditions, determine whether the bound is attainable. Produce positive values or a positive family satisfying all conditions and check the original expression. State the minimum with a complete justification, or explicitly report that the claimed bound is not attained/proven.',fields=['witness','attainment_check','final_answer','justification']),
 dict(id='t2',source=1,parents=[],responsibility='Parameterise the six face probabilities using the heavy face probability and its opposite. Record normalization, opposite-face pairing, and every admissibility constraint. Use a symbolic heavy-face label if its number is unspecified.',fields=['probabilities','pairing','constraints','derivation']),
 dict(id='t3',source=1,parents=['t2'],responsibility='Use the supplied probabilities to derive the two-roll sum-of-seven probability, including ordered outcomes. Form the equation using the probability in the original statement. Preserve the probability constraints; do not solve the equation yet.',fields=['event_probability','equation','constraints','derivation']),
 dict(id='t4',source=1,parents=['t3'],responsibility='Solve the supplied equation under its constraints and the original statement. Reject inadmissible roots with reasons. Express the required probability in lowest terms and compute the requested numerator-plus-denominator answer.',fields=['roots','admissibility','reduced_fraction','final_answer','justification'])]
LIMITS=dict(maximum_calls=55,context=16384,input_cap=13312,output_cap=3072,token_cap=901120,
            wall_seconds=14400,physical_gpus=1,cpus=4,host_memory_gb=128,minimum_vram_bytes=80000000000,
            solver_seconds=10,solver_threads=1,solver_seed=0)

def blueprint():
    order=[t['id'] for t in TASKS];permutation=order[:];random.Random(0).shuffle(permutation)
    groups=[sorted(permutation[:2])]+[[x] for x in permutation[2:]];groups.sort()
    return dict(condition=CONDITION,n=4,K=2,tasks=deepcopy(TASKS),source_ids=list(IDS),statement_hashes=list(HASHES),
                raw_plan_sha256=RAW_PLAN_HASHES,required_outputs={'q0':'e1','q1':'e4'},display_mapping={'q0':IDS[0],'q1':IDS[1]},
                neutral_seed=0,permutation=permutation,groups=groups,
                ownership={t:'o'+str(i) for i,g in enumerate(groups) for t in g},
                objective='mean_first',A='fixed',C='direct_parent_artifacts',
                admission='reviewer_authored_development_contract_pending_user_acceptance',
                profile_rule='one same-instance neutral profile; input+generated token prices; no content/grades to selector',
                schedule=['profile','neutral/clean','selected/clean']+[f'{m}/owner/o{i}' for i in range(4) for m in ('neutral','selected')],
                identical_design='one evaluation clean and four repairs, explicitly shared method observations',
                prompt=PROMPT,limits=LIMITS,decoder='task-fields-xgrammar-v1',decoder_cpu_seconds_per_call=30)

def statements(path):
    rows=json.loads(Path(path).read_text())
    if isinstance(rows,dict):rows=rows.get('statements',rows.get('cards',[]))
    out={}
    for row in rows:
        sid=row.get('id',row.get('source_id'))
        if sid in IDS:
            require(sid not in out,'duplicate source')
            out[sid]=row['problem']
    require(set(out)==set(IDS),'two original statements required')
    for s,h in zip(IDS,HASHES):require(hashlib.sha256(out[s].encode()).hexdigest()==h,'source integrity')
    return out

def domain(prices=None):
    parents={i:[int(x[1:]) for x in t['parents']] for i,t in enumerate(TASKS)}
    d=graph_fixture(4,5,2,parents,prices)
    d['source']=dict(id=CONDITION,kind='bound_external',provenance='Reviewer-authored composite; raw-plan lineage retained; fixed A/C development only')
    d['unit']='profile_input_plus_generated_tokens' if prices else 'unit_structural_placeholders_not_calibration'
    for i,(t,e,s) in enumerate(zip(d['tasks'],d['events'],d['sources'])):
        t['instruction']=TASKS[i]['responsibility'];s.update(origin='immutable_external',value=None)
        e['allowed_sources']=[f's{j}' for j in range(5) if TASKS[j]['source']==TASKS[i]['source']]
        e['modes'][0].update(operator='opaque',initial=str(prices[i]) if prices else '1')
    for i,obligation in enumerate(d['obligations']):obligation['id']=f'q{i}'
    # Compiler contracts describe serialized math artifacts, not rational fixture values.
    for source in d['sources']:source['artifact']['type']='math-json'
    for task in d['tasks']:
        for artifact in task['deliverables'].values():artifact['type']='math-json'
    for event in d['events']:
        event['output']['type']='math-json'
        for artifact in event['inputs'].values():artifact['type']='math-json'
    for obligation in d['obligations']:obligation['artifact']['type']='math-json'
    return d

def selection(d,ownership):return explicit_selection(d,{}, {},ownership)

def request(task,sources,store):
    # Method/owner/phase/cost identifiers are deliberately absent.
    payload=dict(instruction=PROMPT,task_id=task['id'],responsibility=task['responsibility'],
        source={'id':IDS[task['source']],'problem':sources[IDS[task['source']]]},
        parent_artifacts={p:json.loads(store['e'+p[1:]].value) for p in task['parents']},
        required_string_fields=task['fields'])
    return dict(payload=payload,payload_digest=digest(payload))

def parse_artifact(text,task):
    obj=decode(text)
    require(type(obj) is dict and set(obj)==set(task['fields']),'artifact schema')
    require(all(type(v) is str and v.strip() for v in obj.values()),'nonempty mathematical fields')
    return json.dumps(obj,ensure_ascii=False,sort_keys=True)

class Halt(Invalid):pass

class Journal(NaturalMockSession):
    """Reuse fsync, locking, bounded integrity envelope; one reservation per task call."""
    def __init__(self,path,transport,scope,check_source):
        self.transport=transport;self.check_source=check_source
        self.binding=dict(condition=CONDITION,scope=scope,transport=deepcopy(transport.binding))
        self.root=Path(path);self.root.mkdir(exist_ok=False)
        with self._locked():self._save(dict(binding=self.binding,binding_digest=digest(self.binding),attempts=[],started_at=time.time()))
    def invoke(self,req,slot,event):
        self.check_source()
        require(self.transport.binding==self.binding['transport'],'transport changed')
        with self._locked():
            s=self._read();a=s['attempts']
            if any(not reliable_terminal(x) for x in a):raise Halt('unresolved dispatch/usage; no replay')
            if len(a)>=55 or time.time()-s['started_at']>=14400:raise Halt('resource ceiling')
            require(not any(x['slot']==slot and x['event']==event for x in a),'no retries')
            try:r=self.transport.render(req)
            except Invalid as exc:
                if str(exc)=='input overflow; never truncate':return None
                raise Halt('render integrity failure') from exc
            n=r['input_tokens'];require(type(n) is int and 0<n<=13312,'input cap')
            if sum(x['actual_tokens'] for x in a)+n+3072>901120:raise Halt('aggregate token cap')
            x=dict(slot=slot,event=event,id=f'call-{len(a)}',state='reserved',input_tokens=n,
                   actual_tokens=None,reservation_tokens=n+3072,request=req,rendered=r)
            a.append(x);self._save(s)
            try:obs=self.transport.generate(r)
            except BaseException:raise Halt('dispatch interrupted: reservation retained')
            x['observation']=obs;v=obs.get('output_tokens')
            if type(v) is int and v>=0 and obs.get('input_tokens')==n and type(obs.get('input_tokens')) is int:
                x.update(actual_tokens=n+v,state='completed' if v<=3072 else 'usage_violation')
            else:x['state']='uncertain'
            self._save(s)
            if not reliable_terminal(x):raise Halt('unreliable usage/termination')
            return deepcopy(x)
    def _totals(self,s):
        a=s['attempts']
        return dict(actual_tokens=sum(x['actual_tokens'] or 0 for x in a),reserved_tokens=sum(x['reservation_tokens'] for x in a if x['actual_tokens'] is None),calls=len(a))

class MathEngine(Engine):
    """String artifacts with the accepted recover()/snapshot-role/closure machinery."""
    def __init__(self,journal,sources,out):
        super().__init__();self.journal=journal;self.sources=sources;self.out=Path(out)
    def run(self,execution,slot,worker=None,*,store=None,required=None,phase='clean',**unused):
        require(slot not in self.slots,'no slot replay')
        needed=set(o.id for o in execution.operations) if required is None else set(required)
        wall=time.monotonic();cpu=time.process_time()
        artifacts=dict(store or {});trace=[];calls=[];cost=0;status='complete'
        require(needed<=set(o.id for o in execution.operations),'frozen operations only')
        for op in execution.operations:
            if op.id not in needed:continue
            task=TASKS[int(op.host[1:])];reads=[]
            for r in op.reads:
                if r.event:
                    require(r.event in artifacts,'missing parent')
                    item=artifacts[r.event]
                    require(item.organisation==execution.organisation_id and item.contract==r.artifact,'foreign artifact')
                    if r.event in needed:require(item.invocation in calls,'affected parent must be current fork')
                    reads.append(dict(event=r.event,invocation=item.invocation))
            req=request(task,self.sources,artifacts)
            row=self.journal.invoke(req,slot,op.id)
            if row is None:status='input_overflow';break
            calls.append(row['id']);cost+=row['actual_tokens'];obs=row['observation']
            trace.append(dict(event=op.id,invocation=row['id'],payload_digest=req['payload_digest'],reads=reads,usage=row['actual_tokens'],committed=False))
            try:
                require(obs['finish_reason']=='eos' and not obs.get('boundary_error'),'unusable response')
                value=parse_artifact(obs.get('final_text'),task)
            except (Invalid,TypeError) as exc:
                trace[-1]['artifact_error']={'type':type(exc).__name__,'message':str(exc),'cause':str(exc.__cause__) if exc.__cause__ else None}
                status='unusable_artifact';break
            artifacts[op.id]=Artifact(op.output,value,row['id'],execution.organisation_id);trace[-1]['committed']=True
        complete=status=='complete' and needed<=set(artifacts)
        row=dict(slot=slot,organisation=execution.organisation_id,status=status,complete=complete,
                 snapshot_role='initial' if phase=='clean' else 'profile' if phase=='profile' else 'repair',
                 store=artifacts,trace=trace,invocations=calls,known_attempted_spend=cost,
                 full_cost=cost if complete else None,accounting_complete=True,semantic_validity='unknown',
                 intermediate_validity='unreviewed',attempted=bool(calls),wall_seconds=time.monotonic()-wall,cpu_seconds=time.process_time()-cpu)
        row['snapshot_digest']=snapshot_digest(row);self.slots[slot]=row
        atomic_json(self.out/(slot.replace('/','_')+'.json'),serial(row))
        return row

def serial(value):
    if isinstance(value,Artifact):return dict(contract=list(value.contract),value=value.value,invocation=value.invocation,organisation=value.organisation)
    if isinstance(value,dict):return {k:serial(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [serial(v) for v in value]
    if isinstance(value,Fraction):return str(value)
    return value

def independent_reconstruction(ownership,owner):
    affected={t for t,o in ownership.items() if o==owner}
    changed=True
    while changed:
        expanded=affected|{t['id'] for t in TASKS if affected.intersection(t['parents'])}
        changed=expanded!=affected;affected=expanded
    needed={'t1','t4'}
    changed=True
    while changed:
        expanded=needed|{p for t in TASKS if t['id'] in needed for p in t['parents']}
        changed=expanded!=needed;needed=expanded
    return {'e'+t[1:] for t in affected&needed}


def run_recipe(journal,sources,out,solver=None):
    from .joint_solver import solve
    solver=solver or solve;out=Path(out);out.mkdir(exist_ok=True)
    b=blueprint();atomic_json(out/'recipe-state.json',dict(status='profile_pending',slots={k:'unrun' for k in b['schedule']}));d=domain();neutral=selection(d,b['ownership']);ex=compile_organisation(d,neutral)
    engine=MathEngine(journal,sources,out)
    profile=engine.run(ex,'profile',phase='profile')
    if not profile['complete']:
        slots={k:'unrun' for k in b['schedule']};slots['profile']=profile['status']
        atomic_json(out/'recipe-state.json',dict(status='profile_failed',slots=slots))
        evidence=journal.binding['transport'].get('evidence')
        return dict(status='profile_failed',evidence=evidence,model_executed=evidence=='real_composite_worker_development' and bool(profile['invocations']),
                    profile=serial(profile),comparisons='unrun',totals=journal.snapshot()['totals'])
    prices=[next(t['usage'] for t in profile['trace'] if t['event']==f'e{i}') for i in range(5)]
    # No profile content or correctness crosses the solver interface.
    frozen=dict(rule=b['profile_rule'],prices=prices,invocations=profile['invocations'],blueprint_digest=digest(b))
    frozen['digest']=digest(frozen);atomic_json(out/'prices.frozen.json',frozen)
    d=domain(prices);neutral=selection(d,b['ownership'])
    certificate=solver(d,seed=neutral,seconds=10,threads=1,random_seed=0)
    require(certificate['status']!='SOLVER_DEPENDENCY_BLOCKED','solver dependency not qualified')
    chosen=certificate.get('candidate') or neutral
    en=compile_organisation(d,neutral);es=compile_organisation(d,chosen)
    require(evaluate(es)['objective_pair']<=evaluate(en)['objective_pair'],'selector cannot worsen retained feasible fallback')
    identical=sorted(g for _,g in en.groups)==sorted(g for _,g in es.groups)
    executions={'neutral':en,'selected':es};methods=['neutral'] if identical else ['neutral','selected']
    schedule=[m+'/clean' for m in methods]+[f'{m}/owner/o{i}' for i in range(4) for m in methods]
    atomic_json(out/'selection.frozen.json',serial(dict(neutral=neutral,selected=chosen,certificate=certificate,
                identical=identical,price_digest=frozen['digest'],schedule=schedule)))
    atomic_json(out/'recipe-state.json',dict(status='evaluation_pending',slots={'profile':'complete',**{k:'unrun' for k in schedule}}))
    clean={m:engine.run(executions[m],m+'/clean') for m in methods};repairs={m:[] for m in methods}
    for i in range(4):
        for m in methods:
            repair=recover(engine,executions[m],clean[m],'o'+str(i),f'{m}/owner/o{i}',None)
            if repair['status']!='no_clean_snapshot':
                mapping={t:o for o,g in executions[m].groups for t in g}
                require(set(repair['reconstruction'])==independent_reconstruction(mapping,'o'+str(i)),'independent reconstruction mismatch')
            repairs[m].append(repair)
    result=dict(status='completed_recipe',evidence=journal.binding['transport'].get('evidence'),
                model_executed=journal.binding['transport'].get('evidence')=='real_composite_worker_development',identical_design=identical,shared_observations=identical,
                profile=serial(profile),prices=frozen,selection=serial(certificate),methods={},totals=journal.snapshot()['totals'])
    for m in methods:
        costs=[r['full_cost'] for r in repairs[m]];covered=all(c is not None for c in costs)
        result['methods'][m]=dict(predicted=serial(evaluate(executions[m])),clean=serial(clean[m]),repairs=serial(repairs[m]),
            replay_mean=str(Fraction(sum(costs),4)) if covered else None,replay_max=max(costs) if covered else None,
            full_cost_coverage=covered,all_required_answers_valid='unknown',quality_preserving_saving=None)
    if identical:result['methods']['selected']={'shared_with':'neutral','independent_replication':False,'organisational_advantage':False}
    result['planned_calls_after_selection']=5+sum(5+sum(len(v) for v in evaluate(executions[m])['recovery_sets']) for m in methods)
    for m in methods:
        for repair in result['methods'][m]['repairs']:
            events=repair.get('reconstruction',[])
            proxy=sum(prices[int(e[1:])] for e in events) if repair.get('status')!='no_clean_snapshot' else None
            repair['profile_proxy_tokens']=proxy
            repair['observed_minus_proxy']=repair['full_cost']-proxy if repair['full_cost'] is not None and proxy is not None else None
    import csv
    with (out/'RECOVERY_RESULTS.csv').open('x',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['method','owner','status','profile_proxy_tokens','observed_tokens','attempted_tokens','quality'])
        writer.writeheader()
        for m in methods:
            for i,row in enumerate(result['methods'][m]['repairs']):
                writer.writerow(dict(method=m,owner=f'o{i}',status=row['status'],profile_proxy_tokens=row['profile_proxy_tokens'],observed_tokens=row['full_cost'],attempted_tokens=row['known_attempted_spend'],quality='unknown'))
    # Opaque review IDs; no method, owner, cost or selection information in this file.
    packet=[];private_map={}
    for slot in sorted(engine.slots,key=lambda s:digest(['blind-v1',s])):
        if slot=='profile':continue
        row=engine.slots[slot]
        for q,event in en.outputs:
            if event not in row['store']:continue
            opaque='review-'+digest([CONDITION,slot,q])[:20];private_map[opaque]={'slot':slot,'output':q}
            packet.append(dict(id=opaque,statement=sources[IDS[int(q[1:])]],
                          intermediate_artifacts={k:json.loads(v.value) for k,v in row['store'].items() if TASKS[int(k[1:])]['source']==int(q[1:])},
                          required_artifact=TASKS[int(event[1:])]['fields'],
                          output=json.loads(row['store'][event].value),validity='unknown'))
    atomic_json(out/'QUALITY_REVIEW.blinded.json',packet);atomic_json(out/'QUALITY_REVIEW.mapping.private.json',private_map)
    text=['# First composite reconstruction result','', 'Development fixed-A/C ownership pilot; one same-instance profile and one repetition.', '',f"Identical design: {identical}; shared observations: {identical}.",'', 'All mathematical quality is UNKNOWN pending blinded human review. No quality-preserving saving is established.','', '| Method | Clean tokens | Four replay costs | Observed mean | Observed maximum |', '|---|---:|---|---:|---:|']
    for m in methods:
        row=result['methods'][m]
        text.append(f"| {m} | {row['clean']['full_cost']} | {[x['full_cost'] for x in row['repairs']]} | {row['replay_mean']} | {row['replay_max']} |")
    text += ['', 'Prices are profile proxies, not expected replay costs. Selection/certificate details are in selection.frozen.json. Profile spend and CPU/wall overhead are separate from evaluation in result.json. Incomplete incidents retain attempted spend and null full cost.']
    (out/'FIRST_REAL_RECOVERY_REPORT.md').write_text('\n'.join(text)+'\n')
    (out/'QUALITY_REVIEW.md').write_text('# Blinded review pending\n\nUse QUALITY_REVIEW.blinded.json without the private mapping or cost files. For each source: verify original obligations, domain/admissibility, mathematical derivation, and final answer. Grade each final answer valid/invalid/unknown and intermediate claims separately. Both answers must be valid for bundle success. Record judgments before unblinding. No gold was accessed through the worker lane; no feedback or regeneration is allowed. Replay correction of an initially wrong answer is not retention.\n')
    atomic_json(out/'recipe-state.json',dict(status='recipe_finished',slots={k:v['status'] for k,v in engine.slots.items()}))
    return result
