"""Protected CPU mock scheduler, physical replay and append-only local attempts.

These interfaces are application-level controls, not an OS security boundary.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
import fcntl
import json
import random
import threading
import time
from .model import Artifact, Usage, Invalid, closure, digest, groups, plain


class BudgetStop(Exception): pass


class Budget:
    """Atomic reservations; missing usage remains reserved and blocks dispatch."""
    def __init__(self,cap):
        if type(cap) is not int or cap<0:raise Invalid('explicit synthetic campaign cap required')
        self.cap=cap;self.spent=0;self.reserved={};self.unresolved=set();self.lock=threading.Lock()
    def reserve(self,key,maximum):
        with self.lock:
            if type(maximum) is not int or maximum<=0:raise Invalid('call limit')
            if key in self.reserved or self.unresolved:raise BudgetStop('unresolved/duplicate reservation')
            if self.spent+sum(self.reserved.values())+maximum>self.cap:raise BudgetStop('campaign cap')
            self.reserved[key]=maximum
    def finish(self,key,usage):
        with self.lock:
            maximum=self.reserved[key]
            if usage.status!='complete' or usage.actual is None:
                self.unresolved.add(key);return
            if type(usage.actual) is not int or usage.actual<0:
                self.unresolved.add(key);raise Invalid('usage')
            del self.reserved[key];self.spent+=usage.actual
            if usage.actual>maximum:raise Invalid('usage exceeds reservation: actual spend still charged')


class Access:
    """Only parent artifacts and immutable source entries handed to one task."""
    def __init__(self,parents,sources):
        self._parents=MappingProxyType(dict(parents));self._sources=MappingProxyType(dict(sources));self.reads=[]
    def parent(self,name):
        if name not in self._parents:raise Invalid('undeclared artifact read')
        self.reads.append(('parent',name));return self._parents[name]
    def source(self,name):
        if name not in self._sources:raise Invalid('undeclared immutable source read')
        self.reads.append(('source',name));return self._sources[name]


@dataclass(frozen=True)
class Executor:
    backend: str = 'deterministic_mock'
    config: str = 'integer-worker-v1'
    unit: str = 'synthetic_work'
    @property
    def key(self):return digest(self)


class MockWorker:
    """Stateless values depend on actual inputs; seeded variant varies usage."""
    def invoke(self,payload,access,stream):
        value=payload['base']+sum((i+1)*access.parent(p).value for i,p in enumerate(payload['parents']))
        value+=sum(access.source(k) for k in payload['inputs'])
        extra=random.Random(int(stream,16)).randrange(3) if payload['stochastic'] else 0
        cost=payload['synthetic_cost']+extra
        return value,Usage(cost,uncached=cost)


def worker_for(config):
    if config.backend not in ('deterministic_mock','seeded_mock') or config.unit!='synthetic_work':
        raise Invalid('only synthetic mock backends registered; approvals/env cannot enable real execution')
    return MockWorker()


def payload(w,t,executor):
    return {'task':t.id,'parents':tuple(sorted(t.parents)),'inputs':tuple(sorted(t.inputs)),
            'base':t.base,'synthetic_cost':t.synthetic_cost,'call_cap':t.call_cap,
            'schema':t.schema,'tools':t.tool_config,'description':t.description,
            'stochastic':executor.backend=='seeded_mock','executor':executor.key}


def invariance(w,allocations,executor):
    worker_for(executor)
    for a in allocations:
        if a.workflow!=w.key:raise Invalid('workflow drift')
        groups(w,a.n,a.groups)
    # Build each assignment view and compare; assignments never enter payloads.
    views=[]
    for a in allocations:
        assigned={t:g for g in a.groups for t in g}
        views.append([(t,payload(w,w.task(t),executor)) for t in w.order() if t in assigned])
    if not views or any(digest(v)!=digest(views[0]) for v in views):raise Invalid('shared clean invariance failed')
    return {'status':'passed','workflow':w.key,'executor':executor.key,'payload_digest':digest(views[0]),
            'allocation_keys':tuple(a.key for a in allocations),'design':'common baseline; not independent provider runs'}


def stream_id(w,executor,repeat,task,phase,attempt,allocation=None,group=None,coupling=None):
    if repeat<0 or attempt<0:raise Invalid('repeat/attempt')
    if phase!='clean' and (allocation is None or group is None):raise Invalid('incident identity required')
    identity=[w.key,executor.key,repeat,task,phase,attempt]
    if phase!='clean':identity += [allocation.partition,allocation.owner(tuple(group)),coupling]
    return digest(identity)


def grade(w,artifacts):
    """Isolated synthetic evaluator; reference values never appear in payloads."""
    values={};inputs=dict(w.sources)
    for name in w.order():
        t=w.task(name);values[name]=t.base+sum((i+1)*values[p] for i,p in enumerate(sorted(t.parents)))+sum(inputs[k] for k in t.inputs)
    got={a.task:a.value for a in artifacts}
    if not set(w.outputs)<=got.keys():return 'unknown'
    return 'valid' if all(got[t]==values[t] for t in w.outputs) else 'invalid'


@dataclass(frozen=True)
class Trace:
    workflow: str
    executor: str
    repeat: int
    phase: str
    artifacts: tuple
    events: tuple
    execution: str
    schema: str
    semantic: str
    usage: str
    observed_spend: int
    full_cost: object
    required_tasks: tuple
    attempted: tuple
    @property
    def key(self):return digest(self)


def execute(w,executor,repeat,budget,*,phase='clean',allocation=None,group=None,retained=(),
            todo=None,worker=None,mutate=False,sham=False,abort_after=None,coupling=None,event_sink=None,attempt=0):
    default_worker=worker_for(executor);worker=worker or default_worker
    if allocation is not None:
        if allocation.workflow!=w.key:raise Invalid('allocation workflow drift')
        groups(w,allocation.n,allocation.groups);allocation.owner(tuple(group))
    artifacts={a.task:a for a in retained};todo=set(w.ids if todo is None else todo)
    if set(artifacts)&todo or not todo<=set(w.ids) or not set(artifacts)<=set(w.ids):raise Invalid('stale affected artifact or task set')
    events=[];attempted=[];execution='completed';schema='valid';known=0;usage='complete'
    emit=lambda row: event_sink(plain(row)) if event_sink else None
    for name in w.order():
        if name not in todo:continue
        if abort_after is not None and len(attempted)>=abort_after:execution='resource_stopped';break
        task=w.task(name)
        if not set(task.parents)<=artifacts.keys():execution='protocol_violation';break
        pp=payload(w,task,executor)
        key=stream_id(w,executor,repeat,name,phase,attempt,allocation,group,coupling)
        invocation=digest([key,'physical-invocation'])
        if mutate:
            # Coupled RNG is intentional; the sham and attack are still two billed calls.
            invocation=digest([key,'physical-invocation','sham' if sham else 'attack'])
        try:budget.reserve(invocation,task.call_cap)
        except BudgetStop:execution='resource_stopped';break
        attempted.append(name);emit({'type':'call_start','invocation':invocation,'task':name,'reservation':task.call_cap})
        access=Access({p:artifacts[p] for p in task.parents},{k:dict(w.sources)[k] for k in task.inputs})
        worker_started=time.process_time()
        try:
            value,u=worker.invoke(MappingProxyType(pp),access,key)
        except Exception as exc:
            u=Usage(None,'missing');budget.finish(invocation,u);usage='missing';schema='unknown';execution='protocol_violation' if isinstance(exc,Invalid) else 'infrastructure_failure'
            row={'task':name,'invocation':invocation,'stream':key,'usage':u,'error':type(exc).__name__,'worker_cpu_seconds':time.process_time()-worker_started};events.append(row);emit({'type':'call_end',**row});break
        worker_cpu=time.process_time()-worker_started
        if (not isinstance(u,Usage) or u.unit!=executor.unit or u.synthetic is not True or
                (u.actual is not None and (type(u.actual) is not int or u.actual<0))):
            u=Usage(None,'missing');budget.finish(invocation,u);execution='protocol_violation';usage='missing'
            row={'task':name,'invocation':invocation,'stream':key,'usage':u,'error':'invalid_usage',
                 'worker_cpu_seconds':worker_cpu};events.append(row);emit({'type':'call_end',**row});break
        try:budget.finish(invocation,u)
        except Invalid:execution='protocol_violation'
        known+=u.actual if u.actual is not None else 0
        if u.actual is None or u.status!='complete':usage='missing'
        valid=type(value) is int
        read_parents={v for kind,v in access.reads if kind=='parent'}
        if read_parents!=set(task.parents):execution='protocol_violation'
        applied=bool(mutate and name in group and valid)
        if applied and not sham:value+=1000  # bounded owner-output hook, no protected state provided
        row={'task':name,'invocation':invocation,'stream':key,'usage':u,'worker_cpu_seconds':worker_cpu,'reads':tuple(access.reads),
             'mutation_attempted':applied,'mutation_changed':applied and not sham,'schema_valid':valid}
        events.append(row);emit({'type':'call_end',**row})
        if not valid:execution='task_error';schema='invalid';break
        if execution=='protocol_violation':break
        pv=tuple((p,artifacts[p].version) for p in sorted(task.parents));inp=digest([pp,pv])
        artifacts[name]=Artifact(name,value,digest([invocation,value,pv]),pv,invocation,inp)
        if usage!='complete':execution='resource_stopped';break
    if execution=='completed' and not todo<=artifacts.keys():execution='task_error'
    complete=execution=='completed' and usage=='complete'
    arts=tuple(artifacts[k] for k in sorted(artifacts))
    return Trace(w.key,executor.key,repeat,phase,arts,tuple(events),execution,schema,grade(w,arts),usage,
                 known,known if complete else None,tuple(sorted(todo)),tuple(attempted))


def ownership_view(trace,allocation):
    if trace.workflow!=allocation.workflow:raise Invalid('binding drift')
    return {'trace':trace.key,'partition':allocation.partition,'groups':allocation.groups,
            'provenance':'separate immutable view; original artifacts unchanged'}


def repair(w,executor,repeat,budget,baseline,allocation,group,**kwargs):
    if baseline.phase!='clean':raise Invalid('repair requires original clean snapshot, not a previous incident')
    if baseline.workflow!=w.key or baseline.executor!=executor.key or baseline.repeat!=repeat:raise Invalid('snapshot provenance')
    if baseline.execution!='completed' or set(a.task for a in baseline.artifacts)!=set(w.ids):
        return {'execution':'no_clean_snapshot','full_cost':None,'semantic':'unknown','usage':'missing'}
    affected=closure(group,w.edges);retained=tuple(a for a in baseline.artifacts if a.task not in affected)
    trace=execute(w,executor,repeat,budget,phase='repair',allocation=allocation,group=group,retained=retained,todo=affected,**kwargs)
    return {'trace':trace,'execution':trace.execution,'full_cost':trace.full_cost,'semantic':trace.semantic,
            'usage':trace.usage,'baseline_semantic':baseline.semantic,'restored_from_valid_clean':baseline.semantic=='valid',
            'reconstruction_tasks':tuple(sorted(affected)),'completion_tasks':()}


def corrupt_and_restore(w,executor,repeat,budget,clean,allocation,group,*,abort_after=None,sham=False,worker=None,coupling=None):
    if clean.phase!='clean' or clean.workflow!=w.key or clean.executor!=executor.key or clean.repeat!=repeat or clean.execution!='completed':raise Invalid('complete matching clean checkpoint required')
    order=w.order();first=min(order.index(t) for t in group);prefix=set(order[:first])
    retained=tuple(a for a in clean.artifacts if a.task in prefix)
    # Clean prefix reuse exact snapshot; both sham/attack continue physically.
    phase='paired_continuation' if coupling=='declared_common_random_numbers_v1' else ('sham' if sham else 'attack')
    if coupling not in (None,'declared_common_random_numbers_v1'):raise Invalid('undeclared coupling')
    attacked=execute(w,executor,repeat,budget,phase=phase,allocation=allocation,group=group,retained=retained,
                     todo=set(w.ids)-prefix,mutate=True,sham=sham,abort_after=abort_after,worker=worker,coupling=coupling)
    E={a.task for a in attacked.artifacts};D=closure(group,w.edges);missing=set(w.ids)-E;U=D|missing
    repaired=execute(w,executor,repeat,budget,phase='sham_repair' if sham else 'attack_repair',allocation=allocation,group=group,
                     retained=tuple(a for a in attacked.artifacts if a.task not in D),todo=U)
    changed={e['task'] for e in attacked.events if e.get('mutation_changed')}
    reads=[(e['task'],p) for e in attacked.events for kind,p in e.get('reads',()) if kind=='parent' and p in changed]
    def priced_tasks(names):
        entries=[e for e in repaired.events if e['task'] in names]
        if any(e['usage'].actual is None or e['usage'].status!='complete' for e in entries):return None
        return sum(e['usage'].actual for e in entries)
    return {'continuation':attacked,'repair':repaired,
            'continuation_observed_spend':attacked.observed_spend,
            'reconstruction_observed_spend':priced_tasks(D&E),
            'completion_observed_spend':priced_tasks(missing),
            'combined_full_cost':repaired.full_cost,
            'reconstruction_tasks':tuple(sorted(D&E)),
            'completion_tasks':tuple(sorted(missing)),'repair_tasks':tuple(sorted(U)),
            'preserved_tasks':tuple(sorted(E-D)),'downstream_reads':reads,'direct_output_exposure':sorted(changed&set(w.outputs)),
            'theorem_complete_work_cost_applicable':E==set(w.ids),'prefix_reuse':clean.key,'sham':sham}


class Journal:
    """Single-host append-only attempts, guarded by flock. Ambiguity never retries."""
    def __init__(self,path,spec):
        self.root=Path(path);self.root.mkdir(parents=True,exist_ok=True)
        p=self.root/'spec.json';encoded=json.dumps(plain(spec),sort_keys=True)
        try:
            with p.open('x') as f:f.write(encoded)
        except FileExistsError:
            if p.read_text()!=encoded:raise Invalid('resume specification drift')
        self.path=self.root/'events.jsonl'
    def locked(self):return self.path.open('a+')
    def events(self):
        if not self.path.exists():return []
        return [json.loads(line) for line in self.path.read_text().splitlines()]
    def append(self,event):
        with self.locked() as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.write(json.dumps(plain(event),sort_keys=True)+'\n');f.flush()
            import os
            os.fsync(f.fileno())
    def begin(self,slot,attempt=0,retry_limit=0):
        with self.locked() as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);rows=[json.loads(v) for v in f if v.strip()]
            prior=[r for r in rows if r.get('slot')==slot and r['type'] in ('start','finish')]
            finishes=[r for r in prior if r['type']=='finish']
            starts=[r for r in prior if r['type']=='start']
            if finishes and finishes[-1]['outcome']['execution']=='completed':return False
            if starts and len(finishes)!=len(starts):raise Invalid('unclosed attempt; preserve uncertain usage, no automatic retry')
            if attempt!=len(starts) or attempt>retry_limit:raise Invalid('attempt sequence or retry bound')
            if starts and finishes[-1]['outcome']['execution']!='infrastructure_failure':raise Invalid('semantic/schema/resource retries forbidden')
            f.seek(0,2);f.write(json.dumps({'type':'start','slot':slot,'attempt':attempt})+'\n');f.flush()
            import os
            os.fsync(f.fileno())
            return True
    def finish(self,slot,attempt,outcome):
        with self.locked() as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);rows=[json.loads(v) for v in f if v.strip()]
            started=sum(r.get('slot')==slot and r.get('attempt')==attempt and r['type']=='start' for r in rows)
            done=any(r.get('slot')==slot and r.get('attempt')==attempt and r['type']=='finish' for r in rows)
            if started!=1 or done:raise Invalid('duplicate or unstarted physical finish')
            f.seek(0,2);f.write(json.dumps(plain({'type':'finish','slot':slot,'attempt':attempt,'outcome':outcome}))+'\n');f.flush()
            import os
            os.fsync(f.fileno())


def trace_from_record(record):
    """Rehydrate completed mock checkpoints without invoking workers."""
    row=dict(record)
    row['artifacts']=tuple(Artifact(**{**a,'parent_versions':tuple(tuple(v) for v in a['parent_versions'])}) for a in row['artifacts'])
    row['events']=tuple({**e,'usage':Usage(**e['usage'])} for e in row['events'])
    row['required_tasks']=tuple(row['required_tasks']);row['attempted']=tuple(row['attempted'])
    return Trace(**row)
