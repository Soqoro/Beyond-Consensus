"""Immutable Phase II contracts; standard-library imports only."""
from dataclasses import dataclass, asdict, is_dataclass
from fractions import Fraction
from typing import Optional
import hashlib
import json
from bc_phase1.core import closure, Invalid  # Existing traversal, unchanged.


def plain(x):
    if isinstance(x, Fraction): return str(x)
    if is_dataclass(x): return plain(asdict(x))
    if isinstance(x, dict): return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [plain(v) for v in x]
    return x


def digest(x):
    return hashlib.sha256(json.dumps(plain(x), sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def rational(value, positive=True):
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        raise Invalid('costs require exact integers, decimal strings or rational strings; floats rejected')
    try: result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc: raise Invalid('invalid rational') from exc
    if result < 0 or positive and result == 0: raise Invalid('positive cost / nonnegative threshold required')
    return result


@dataclass(frozen=True)
class Task:
    id: str
    parents: tuple = ()
    inputs: tuple = ()
    base: int = 1
    synthetic_cost: int = 1
    call_cap: int = 8
    description: str = 'Compute the declared integer transformation.'
    schema: str = 'integer-v1'
    tool_config: str = 'declared-read-only-v1'

    def __post_init__(self):
        if not isinstance(self.parents,tuple) or not isinstance(self.inputs,tuple):raise Invalid('immutable task contracts required')


@dataclass(frozen=True)
class Workflow:
    source: str
    tasks: tuple
    outputs: tuple
    sources: tuple = ()  # (immutable input name, integer fixture value)
    version: str = 'synthetic-workflow-v1'

    def __post_init__(self):
        if not all(isinstance(v,tuple) for v in (self.tasks,self.outputs,self.sources)) or any(not isinstance(v,tuple) for v in self.sources):raise Invalid('immutable workflow contracts required')
        ids = [t.id for t in self.tasks]
        if not ids or any(type(t) is not Task for t in self.tasks) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
            raise Invalid('unique named tasks required')
        if not isinstance(self.source, str) or not self.source: raise Invalid('source identity required')
        if not self.outputs or len(set(self.outputs)) != len(self.outputs) or not set(self.outputs) <= set(ids): raise Invalid('required outputs')
        names = [k for k, v in self.sources]
        if len(set(names)) != len(names) or any(type(v) is not int for k,v in self.sources): raise Invalid('immutable sources')
        for t in self.tasks:
            if len(set(t.parents)) != len(t.parents) or not set(t.parents) <= set(ids) or t.id in t.parents: raise Invalid('parents')
            if len(set(t.inputs)) != len(t.inputs) or not set(t.inputs) <= set(names): raise Invalid('source permissions')
            if type(t.base) is not int or type(t.synthetic_cost) is not int or t.synthetic_cost <= 0: raise Invalid('synthetic operation')
            if type(t.call_cap) is not int or t.call_cap < t.synthetic_cost or t.schema != 'integer-v1': raise Invalid('task limits/schema')
        self.order()
        if closure(self.outputs, self.edges, reverse=True) != set(ids): raise Invalid('unused padding prohibited')

    @property
    def edges(self): return tuple((p, t.id) for t in self.tasks for p in t.parents)
    @property
    def ids(self): return tuple(sorted(t.id for t in self.tasks))
    @property
    def key(self): return digest(self)
    def task(self, name): return next(t for t in self.tasks if t.id == name)
    def order(self):
        left = {t.id: set(t.parents) for t in self.tasks}; result = []
        while left:
            ready = sorted(t for t, ps in left.items() if not ps)
            if not ready: raise Invalid('cyclic task DAG')
            t = ready[0]; result.append(t); del left[t]
            for ps in left.values(): ps.discard(t)
        return tuple(result)


def groups(workflow, n, allocation):
    if type(n) is not int or not n <= len(workflow.tasks) <= 2*n: raise Invalid('n <= m <= 2n')
    if len(allocation) != n or any(len(g) not in (1,2) for g in allocation): raise Invalid('n nonempty singleton/pair groups')
    flat = [t for g in allocation for t in g]
    if len(flat) != len(set(flat)) or set(flat) != set(workflow.ids): raise Invalid('exact task coverage')
    return tuple(sorted(tuple(sorted(g)) for g in allocation))


@dataclass(frozen=True)
class Allocation:
    workflow: str
    n: int
    groups: tuple
    estimator: str
    method: str
    seed: int
    draw: int = 0
    prompt_binding: str = 'local-no-model'
    def __post_init__(self):
        if (type(self.n) is not int or self.n<=0 or not isinstance(self.groups,tuple) or
                len(self.groups)!=self.n or any(not isinstance(g,tuple) or len(g) not in (1,2) for g in self.groups)):
            raise Invalid('immutable nonempty singleton/pair allocation required')
        flat=[t for g in self.groups for t in g]
        if any(not isinstance(t,str) or not t for t in flat) or len(flat)!=len(set(flat)):
            raise Invalid('unique allocation task IDs required')
        object.__setattr__(self,'groups',tuple(sorted(tuple(sorted(g)) for g in self.groups)))
    @property
    def partition(self): return digest([self.workflow, self.n, self.groups])
    @property
    def key(self): return digest(self)
    def owner(self, group):
        if tuple(group) not in self.groups: raise Invalid('unknown canonical owner')
        return digest([self.partition, group])


@dataclass(frozen=True)
class Artifact:
    task: str
    value: int
    version: str
    parent_versions: tuple
    invocation: str
    input_digest: str


@dataclass(frozen=True)
class Usage:
    actual: Optional[int]
    status: str = 'complete'
    unit: str = 'synthetic_work'
    synthetic: bool = True
    cached: int = 0
    uncached: Optional[int] = None


def fixture(m=6, source='synthetic:chain'):
    return Workflow(source, tuple(Task(f't{i:02d}', (f't{i-1:02d}',) if i else (), base=i+1,
                                      synthetic_cost=1+i%3, call_cap=8) for i in range(m)), (f't{m-1:02d}',))
