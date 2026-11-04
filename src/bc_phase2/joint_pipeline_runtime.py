"""Instrumented serial mock execution and independent snapshot reconstruction.

Application-level data isolation, not an OS sandbox for untrusted Python plugins.
No live adapters are registered. Only the fixed trusted mock interpreter runs.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction
from math import prod
from copy import deepcopy
import json
import os
from pathlib import Path
from .joint_core import evaluate
from .joint_schema import require
from .model import Invalid, digest, closure


class Meter:
    """Conservative serial reservations; unknown bills retain their maximum."""
    def __init__(self, cap=100000):
        require(type(cap) is int and cap>=0,'campaign cap')
        self.cap=cap;self.spent=0;self.reserved={};self.attempts=[]

    def begin(self,slot,event,maximum,phase):
        require(type(maximum) is int and maximum>0,'call reservation')
        if self.spent+sum(self.reserved.values())+maximum>self.cap:return None
        identity=f'physical-{len(self.attempts)}'
        self.reserved[identity]=maximum
        self.attempts.append(dict(id=identity,slot=slot,event=event,phase=phase,
                                  actual=None,reservation=maximum,status='started'))
        return identity

    def finish(self,identity,usage,status):
        row=next(r for r in self.attempts if r['id']==identity)
        require(row['status']=='started','attempt already closed')
        row['status']=status
        if usage is None:
            row['status']='usage_unknown';return
        require(type(usage) is int and usage>=0,'integer actual usage')
        row['actual']=usage;maximum=self.reserved.pop(identity);self.spent+=usage
        require(usage<=maximum,'observed reservation overrun: charged, stop')

    def report(self):
        return dict(unit='synthetic_work',known_spend=self.spent,unresolved_reservations=dict(self.reserved),
                    accounting_complete=not self.reserved,physical_attempts=deepcopy(self.attempts),
                    actual_total=None if self.reserved else self.spent)


@dataclass(frozen=True)
class Artifact:
    contract: tuple
    value: Fraction
    invocation: str
    organisation: str


class Inputs:
    __slots__=('__values','observed')
    def __init__(self,values):
        self.__values=values;self.observed=[]
    def payload(self):
        return {k:dict(value=str(v),**p) for k,(v,p) in self.__values.items()}
    def read(self,port):
        require(port in self.__values,'undeclared read/state/cache')
        value,provenance=self.__values[port]
        self.observed.append(dict(port=port,**provenance))
        return value


@dataclass(frozen=True)
class Request:
    identity: str
    payload_id: str
    event: str
    operator: str
    ports: tuple
    seed: str


@dataclass(frozen=True)
class Response:
    request_id: str
    output: Fraction | None
    usage: int | None
    finish_reason: str
    error: str | None


class MockWorker:
    """Deterministic arithmetic; optional identity-seeded synthetic usage variability."""
    def __init__(self, stochastic=False, faults=None):
        self.stochastic=stochastic;self.faults=faults or {}
    def invoke(self,request,inputs):
        values=[inputs.read(p) for p in request.ports]
        fault=self.faults.get(request.event)
        if fault=='undeclared':inputs.read('hidden_cache')
        op=request.operator
        require(op in {'sum','product','square','identity','negate'},'opaque workflow unsupported by mock')
        value={'sum':lambda:sum(values,Fraction()),'product':lambda:prod(values),
               'square':lambda:values[0]**2,'identity':lambda:values[0],
               'negate':lambda:-values[0]}[op]()
        usage=1+(int(request.seed[:8],16)%3 if self.stochastic else 0)
        if fault=='wrong':value+=1
        return Response(request.identity,None if fault=='failure' else value,
                        None if fault=='unknown_usage' else usage,
                        'error' if fault=='failure' else 'stop','mock_failure' if fault=='failure' else None)


def read_inputs(execution,op,store):
    sources={s:(c,v) for s,c,v in execution.sources};values={}
    for r in op.reads:
        if r.source is not None:
            contract,value=sources[r.source];invocation='protected-source:'+r.source
        else:
            require(r.event in store,'late or missing artifact')
            item=store[r.event]
            require(item.organisation==execution.organisation_id,'foreign/stale organisation')
            contract,value,invocation=item.contract,item.value,item.invocation
        require(contract==r.artifact and value is not None,'stale version or unavailable source')
        values[r.port]=(value,dict(source=r.source,event=r.event,artifact=list(contract),producer_invocation=invocation))
    return Inputs(values)


class Engine:
    def __init__(self,meter=None):
        self.meter=meter or Meter();self.slots={};self.unclosed_slots=set()

    def run(self,execution,slot,worker,*,store=None,required=None,phase='clean',
            stream=None,stop_after=None,corrupt_owner=None,attack_budget=0,delta=0):
        """Idempotent logical slot; no automatic retry and no persistent worker context."""
        require(slot not in self.unclosed_slots,'unclosed physical attempt; reservation retained, automatic redispatch disabled')
        require(type(worker) is MockWorker,'only trusted mock adapter registered')
        required=set(v.id for v in execution.operations) if required is None else set(required)
        require(required<=set(v.id for v in execution.operations),'new calls outside frozen graph')
        binding=digest([execution.organisation_id,sorted(required),phase,stream,stop_after,
                        corrupt_owner,attack_budget,delta,worker.stochastic,worker.faults,
                        [(k,list(v.contract),str(v.value),v.invocation) for k,v in sorted((store or {}).items())]])
        if slot in self.slots:
            require(self.slots[slot]['binding']==binding,'changed resume binding')
            return self.slots[slot]
        artifacts=dict(store or {});trace=[];invocations=[];known=0;unknown=False;status='complete';attempted=0;attacks=[]
        for op in execution.operations:
            if op.id not in required:continue
            if stop_after is not None and attempted>=stop_after:status='interrupted';break
            phase_name=phase.get(op.id,'repair') if isinstance(phase,dict) else phase
            identity=self.meter.begin(slot,op.id,8,phase_name)
            if identity is None:status='budget_stopped';break
            attempted+=1;invocations.append(identity)
            try:
                inputs=read_inputs(execution,op,artifacts)
                seed=digest([execution.organisation_id,stream or slot,op.id])
                request=Request(identity,digest([op.id,inputs.payload()]),
                                op.id,op.operator,tuple(r.port for r in op.reads),seed)
                response=worker.invoke(request,inputs)
                require(response.request_id==identity,'late response')
                require([r['port'] for r in inputs.observed]==list(request.ports),'actual read trace mismatch')
                self.meter.finish(identity,response.usage,'error' if response.error else 'returned')
                if response.usage is None:unknown=True
                else:known+=response.usage
                trace.append(dict(event=op.id,host=op.host,owner=op.owner,request=asdict(request),
                                  reads=inputs.observed,usage=response.usage,finish_reason=response.finish_reason,
                                  error=response.error,committed=False))
                if response.error:status='worker_failed';break
                require(isinstance(response.output,Fraction),'output schema rational')
                value=response.output
                if op.owner==corrupt_owner:
                    allowed=len([a for a in attacks if a['allowed']])<attack_budget
                    # Fixed synthetic transform work, separate from provider usage;
                    # not an adaptive attacker/model call or a currency estimate.
                    attack_id=self.meter.begin(slot,op.id,1,'attack_sham')
                    if attack_id is None:
                        status='budget_stopped';break
                    self.meter.finish(attack_id,1,'returned')
                    attacks.append(dict(event=op.id,allowed=allowed,zero_effect=delta==0,physical_attempt=attack_id))
                    if allowed:value+=delta
                artifacts[op.id]=Artifact(op.output,value,identity,execution.organisation_id)
                trace[-1]['committed']=True
                if unknown:status='usage_unknown';break
            except (Invalid,ValueError,KeyError,TypeError) as exc:
                # Unknown exceptions after dispatch cannot be called zero usage.
                if self.meter.attempts[-1]['status']=='started':self.meter.finish(identity,None,'error');unknown=True
                status='structural_mismatch';trace.append(dict(event=op.id,error=str(exc),committed=False));break
        bills=[a for a in self.meter.attempts if a['id'] in invocations]
        known=sum(a['actual'] for a in bills if a['actual'] is not None)
        unknown=any(a['actual'] is None for a in bills)
        complete=status!='structural_mismatch' and required<=set(artifacts)
        row=dict(binding=binding,slot=slot,organisation=execution.organisation_id,status=status,
                 snapshot_role='initial' if phase=='clean' else 'repair',
                 complete=complete,accounting_complete=not unknown,known_attempted_spend=known,
                 full_cost=known if complete and not unknown else None,store=artifacts,trace=trace,
                 invocations=invocations,attacks=attacks,attempted=attempted>0,
                 schema_status='invalid' if status=='structural_mismatch' else 'valid',
                 budget_status='stopped' if status=='budget_stopped' else 'within',
                 semantic_validity='unknown',intermediate_validity='unreviewed')
        row['snapshot_digest']=snapshot_digest(row)
        self.slots[slot]=row;return row


def snapshot_digest(row):
    return digest([row['organisation'],row['complete'],row.get('snapshot_role'),[(k,list(v.contract),str(v.value),v.invocation,v.organisation) for k,v in sorted(row['store'].items())]])


def invalidated(execution,owner):
    require(owner in dict(execution.groups),'unknown owner')
    return closure({v.id for v in execution.operations if v.owner==owner},execution.edges)


def recover(engine,execution,snapshot,owner,slot,worker,*,interrupted=False,stop_after=None,stream=None):
    require(snapshot.get('snapshot_role')=='initial','recovery must fork an original execution, never a repaired incident')
    require(snapshot['organisation']==execution.organisation_id,'snapshot organisation')
    require(snapshot.get('snapshot_digest')==snapshot_digest(snapshot),'altered snapshot')
    if not interrupted and not snapshot['complete']:
        return dict(slot=slot,status='no_clean_snapshot',complete=False,full_cost=None,
                    known_attempted_spend=0,attempted=False,semantic_validity='unknown',accounting_complete=True,
                    organisation=execution.organisation_id,invocations=[])
    revoked=invalidated(execution,owner);relevant=set(evaluate(execution)['relevant']);D=revoked&relevant
    committed=set(snapshot['store']);missing=relevant-committed if interrupted else set()
    reconstruction=D&committed;required=D|missing
    preserved={k:v for k,v in snapshot['store'].items() if k not in revoked}
    phases={k:'missing_work' if k in missing else 'repair' for k in required}
    result=engine.run(execution,slot,worker,store=preserved,required=required,phase=phases,
                      stream=stream,stop_after=stop_after)
    result.update(owner=owner,owner_group=dict(execution.groups)[owner],revoked=sorted(revoked),
                  reconstruction=sorted(reconstruction),missing_work=sorted(missing),
                  cost_interpretation='interrupted_completion_not_Ri' if interrupted else 'completed_trace_R0')
    return result


def r1_pair(engine,execution,target,worker,*,prefix='r1',budget=1,delta=1,stop_after=None):
    require(type(budget) is int and budget>=0,'fixed owner attack budget')
    require(target in dict(execution.groups),'target')
    rows={}
    # Identical immutable initial prefix and streams, output corruption only before consumption.
    for arm,change in (('attack',delta),('sham',0)):
        original=engine.run(execution,prefix+'/'+arm,worker,corrupt_owner=target,
                            attack_budget=budget,delta=change,stream=prefix+'/paired',stop_after=stop_after)
        rows[arm]=dict(original=original,repair=recover(engine,execution,original,target,
                      prefix+'/'+arm+'/repair',worker,interrupted=True,stream=prefix+'/paired-repair'))
    return dict(boundary='completion_failure_or_resource',randomness_policy='paired_identity_seed',
                owner_budget=budget,target=target,arms=rows,live_attack_enabled=False)


def save_checkpoint(engine,path):
    """Exclusive offline checkpoint after calls; not a live crash journal."""
    slots=deepcopy(engine.slots)
    for row in slots.values():
        row['store']={k:dict(contract=list(v.contract),value=str(v.value),invocation=v.invocation,
                             organisation=v.organisation) for k,v in row['store'].items()}
    record=dict(schema='joint-mock-checkpoint-v1',cap=engine.meter.cap,spent=engine.meter.spent,
                reservations=engine.meter.reserved,attempts=engine.meter.attempts,slots=slots)
    envelope=dict(record=record,sha256=digest(record))
    with Path(path).open('x') as f:
        json.dump(envelope,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())


def load_checkpoint(path):
    envelope=json.loads(Path(path).read_text());r=envelope['record']
    require(digest(r)==envelope['sha256'] and r['schema']=='joint-mock-checkpoint-v1','checkpoint integrity')
    engine=Engine(Meter(r['cap']));engine.meter.spent=r['spent'];engine.meter.reserved=r['reservations'];engine.meter.attempts=r['attempts']
    require(engine.meter.spent==sum(a['actual'] for a in r['attempts'] if a['actual'] is not None),'checkpoint bills')
    for row in r['slots'].values():
        row['store']={k:Artifact(tuple(v['contract']),Fraction(v['value']),v['invocation'],v['organisation']) for k,v in row['store'].items()}
        require(snapshot_digest(row)==row['snapshot_digest'],'snapshot changed')
    engine.slots=r['slots']
    engine.unclosed_slots={a['slot'] for a in engine.meter.attempts if a['slot'] not in engine.slots}
    return engine


def expenditure(engine):
    phases={}
    for a in engine.meter.attempts:
        row=phases.setdefault(a['phase'],dict(known=0,unknown=0))
        if a['actual'] is None:row['unknown']+=1
        else:row['known']+=a['actual']
    return dict(physical_research=engine.meter.report(),by_phase=phases,
                unit='synthetic_work',currency_conversion=None,
                planning_selection_profiling='separate explicitly labelled resource records')
