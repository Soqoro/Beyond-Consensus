"""Immutable workload/design/operation contracts and deterministic replay."""
from dataclasses import dataclass, asdict
from fractions import Fraction
import hashlib
import json


class Invalid(ValueError):
    pass


class Infeasible(Invalid):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def seed(*parts):
    return int(digest(parts)[:16], 16)


def exact(x):
    f = Fraction(x)
    return {'numerator': f.numerator, 'denominator': f.denominator}


def topo(nodes, edges):
    nodes = set(nodes)
    if any(u not in nodes or v not in nodes or u == v for u, v in edges):
        raise Invalid('invalid edge')
    parents = {v: set() for v in nodes}
    for u, v in edges:
        parents[v].add(u)
    result = []
    while parents:
        ready = sorted(v for v, ps in parents.items() if not ps)
        if not ready:
            raise Invalid('cycle')
        result.extend(ready)
        for v in ready:
            del parents[v]
        for ps in parents.values():
            ps.difference_update(ready)
    return result


def closure(seeds, edges, reverse=False):
    adjacent = {}
    for u, v in edges:
        if reverse:
            u, v = v, u
        adjacent.setdefault(u, set()).add(v)
    found = set(seeds)
    todo = list(found)
    while todo:
        for v in adjacent.get(todo.pop(), ()):
            if v not in found:
                found.add(v)
                todo.append(v)
    return found


@dataclass(frozen=True)
class Workload:
    dimension: str
    tasks: tuple
    owners: tuple
    costs: dict
    sources: dict
    prerequisites: dict
    coefficients: dict
    output_contract: dict  # terminal operation -> required result keys
    constraints: dict

    def record(self):
        return asdict(self)

    def validate(self):
        if len(set(self.tasks)) != len(self.tasks) or len(set(self.owners)) != len(self.owners):
            raise Invalid('duplicate task/owner')
        if set(self.costs) != set(self.tasks) or set(self.sources) != set(self.tasks):
            raise Invalid('task map mismatch')
        if any(type(c) is not int or c <= 0 for c in self.costs.values()):
            raise Invalid('positive integer task costs required')
        if any(type(x) is not int for x in self.sources.values()):
            raise Invalid('integer sources required')
        if set(self.prerequisites) != set(self.tasks):
            raise Invalid('prerequisite task map mismatch')
        n = len(self.owners)
        if self.dimension in ('A', 'B', 'C', 'joint'):
            copies = 2 if self.dimension in ('B', 'joint') else 1
            prices = sorted(self.costs.values())
            if len(self.tasks) != copies*n or (prices != [1]*(copies*n) and
                    prices != sorted(list(range(1,n+1))*copies)):
                raise Invalid('invalid task-count/cost multiset for dimension')
        edges = [(u, t) for t, us in self.prerequisites.items() for u in us]
        topo(self.tasks, edges)
        if any(type(self.coefficients.get(f'{u}->{t}')) is not int or
               self.coefficients[f'{u}->{t}'] <= 0 for u, t in edges):
            raise Invalid('positive prerequisite coefficients required')
        if not self.output_contract or any(not keys or not set(keys) <= set(self.tasks)
                                           for keys in self.output_contract.values()):
            raise Invalid('output contract')

    def reference(self):
        """Compute semantic results from Q alone, independent of execution routing."""
        edges = [(u, t) for t, us in self.prerequisites.items() for u in us]
        values = {}
        for t in topo(self.tasks, edges):
            values[t] = self.sources[t] + sum(
                self.coefficients[f'{u}->{t}'] * values[u] for u in self.prerequisites[t])
        return values


@dataclass(frozen=True)
class Operation:
    id: str
    task: str
    owner: str
    round: int
    cost: int
    parents: tuple  # actual consumed operation artifact identities, version zero
    kind: str = 'atomic_carrier'


@dataclass(frozen=True)
class Design:
    operations: tuple
    permissions: tuple = ()
    metadata: dict = None

    def record(self):
        return asdict(self)


@dataclass(frozen=True)
class Policy:
    id: str = 'required_output_replay_v2'
    common_overhead: int = 0
    transport_price: int = 0
    context: str = 'fresh_stateless_per_operation'

    def __post_init__(self):
        if self.id not in ('required_output_replay_v2', 'full_history_replay'):
            raise Invalid('unknown policy')
        if type(self.common_overhead) is not int or self.common_overhead < 0:
            raise Invalid('invalid common overhead')
        if self.transport_price != 0 or self.context != 'fresh_stateless_per_operation':
            raise Invalid('unsupported execution policy')


def merge(records):
    out = {}
    for record in records:
        for key, value in record.items():
            if key in out and out[key] != value:
                raise Invalid('conflicting duplicate record')
            out[key] = value
    return out


def compute(w, op, records):
    # Every invocation gets only immutable sources and explicitly supplied artifacts.
    data = merge(records)
    if op.kind == 'atomic_carrier':
        if not set(w.prerequisites[op.task]) <= data.keys():
            raise Infeasible('missing mandatory prerequisite')
        value = w.sources[op.task] + sum(w.coefficients[f'{u}->{op.task}'] * data[u]
                                        for u in w.prerequisites[op.task])
        data = merge([data, {op.task: value}])
    elif op.kind == 'source_state':
        if records or op.round != 0:
            raise Invalid('source state must be initial')
        data = {op.task: w.sources[op.task]}
    elif op.kind != 'merge_state':
        raise Invalid('unknown operation kind')
    return data


def validate(w, d):
    w.validate()
    ops = {op.id: op for op in d.operations}
    if len(ops) != len(d.operations) or not ops:
        raise Invalid('duplicate/empty operation IDs')
    if {op.owner for op in d.operations} != set(w.owners):
        raise Invalid('all active owners must execute work')
    if not set(w.output_contract) <= ops.keys():
        raise Invalid('missing terminal operation')
    if w.dimension in ('A', 'B'):
        expected_count = 1 if w.dimension == 'A' else 2
        if (len(ops) != len(w.tasks) or {op.task for op in d.operations} != set(w.tasks) or
            any(sum(op.owner == owner for op in d.operations) != expected_count for owner in w.owners)):
            raise Invalid('dimension task/ownership counts changed')
    for op in d.operations:
        if op.task not in w.tasks or type(op.cost) is not int or op.cost != w.costs[op.task]:
            raise Invalid('intrinsic task price changed')
        if type(op.round) is not int or op.round < 0 or len(set(op.parents)) != len(op.parents):
            raise Invalid('invalid round/duplicate consumed input')
        cap = w.constraints.get('fanin')
        if cap is not None and len(op.parents) > cap:
            raise Infeasible('input artifact fan-in exceeded')
        for p in op.parents:
            if p not in ops:
                raise Invalid('missing consumed artifact')
            if op.kind == 'merge_state' and ops[p].round != op.round - 1:
                raise Invalid('nonchronological state dependency')
    return topo(ops, [(p, op.id) for op in d.operations for p in op.parents])


def accepted(w, artifacts):
    reference = w.reference()
    failures = []
    for terminal, keys in w.output_contract.items():
        data = artifacts.get(terminal, {})
        missing = sorted(set(keys) - data.keys())
        wrong = [k for k in keys if k in data and data[k] != reference[k]]
        if w.constraints.get('exact_terminal_map') and set(data) != set(keys):
            missing = missing + ['unexpected_map_keys']
        if missing or wrong:
            failures.append({'terminal': terminal, 'missing': missing, 'wrong_values': wrong})
    return failures


def execute(w, d):
    order = validate(w, d)
    ops = {op.id: op for op in d.operations}
    artifacts, ledger = {}, []
    for oid in order:
        op = ops[oid]
        artifacts[oid] = compute(w, op, [artifacts[p] for p in op.parents])
        ledger.append({**asdict(op), 'input_artifacts': [f'{p}@clean' for p in op.parents],
                       'artifact': f'{oid}@clean', 'value': artifacts[oid],
                       'required_output_keys': w.output_contract.get(oid, []),
                       'produced_projection': {k: artifacts[oid][k] for k in w.output_contract.get(oid, [])
                                               if k in artifacts[oid]},
                       'payload_records': len(artifacts[oid]),
                       'input_payload_records': sum(len(artifacts[p]) for p in op.parents)})
    return {'operations': ledger, 'artifacts': artifacts, 'order': order,
            'acceptance_failures': accepted(w, artifacts),
            'C_exec': sum(op.cost for op in d.operations),
            'consumed_artifact_count': sum(len(op.parents) for op in d.operations),
            'messages': sum(ops[p].owner != op.owner for op in d.operations for p in op.parents),
            'message_payload_records': sum(len(artifacts[p]) for op in d.operations for p in op.parents
                                           if ops[p].owner != op.owner),
            'payload_records_transferred': sum(x['input_payload_records'] for x in ledger)}


def forward(w, d, policy=Policy()):
    validate(w, d)
    ops = {op.id: op for op in d.operations}
    edges = [(p, op.id) for op in d.operations for p in op.parents]
    terminals = set(ops) if policy.id == 'full_history_replay' else set(w.output_contract)
    live = closure(terminals, edges, reverse=True)
    rows = []
    for owner in w.owners:
        seeds = {op.id for op in d.operations if op.owner == owner}
        invalid = closure(seeds, edges)
        replay = invalid & live
        rows.append({'owner': owner, 'seeds': sorted(seeds), 'all_invalidated': sorted(invalid),
                     'replayed': sorted(replay), 'R': sum(ops[v].cost for v in replay),
                     'invalidated_required_outputs': sorted(invalid & terminals)})
    return live, rows


def reverse(w, d, policy=Policy()):
    """Independent topological owner-incidence propagation and reverse live traversal."""
    order = validate(w, d)
    ops = {op.id: op for op in d.operations}
    live = set(ops) if policy.id == 'full_history_replay' else set(w.output_contract)
    for v in reversed(order):
        if v in live:
            live.update(ops[v].parents)
    incidence, total = {}, dict.fromkeys(w.owners, 0)
    for v in order:
        incidence[v] = {ops[v].owner}
        for p in ops[v].parents:
            incidence[v].update(incidence[p])
        if v in live:
            for owner in incidence[v]:
                total[owner] += ops[v].cost
    return [total[o] for o in w.owners]


def replay(w, d, clean, row, stale_parent=None, policy=Policy()):
    """Independent target scenario; old invalid versions remain quarantined."""
    invalid, redo = set(row['all_invalidated']), set(row['replayed'])
    values = {k: dict(v) for k, v in clean['artifacts'].items() if k not in invalid}
    versions = {k: f'{k}@clean' for k in values}
    ledger = []
    ops = {op.id: op for op in d.operations}
    for v in clean['order']:
        if v not in redo:
            continue
        op = ops[v]
        inputs = []
        for p in op.parents:
            binding = f'{p}@clean' if p == stale_parent else versions.get(p)
            if p not in values or (p in invalid and binding == f'{p}@clean'):
                raise Invalid('quarantined/stale input version')
            inputs.append(binding)
        values[v] = compute(w, op, [values[p] for p in op.parents])
        versions[v] = f'{v}@repair:{row["owner"]}'
        ledger.append({'operation': v, 'input_artifacts': inputs, 'artifact': versions[v],
                       'value': values[v], 'cost': op.cost, 'fresh_context': True,
                       'produced_projection': {k: values[v][k] for k in w.output_contract.get(v, [])
                                               if k in values[v]}})
    failures = accepted(w, values)
    required = set(w.output_contract)
    if policy.id == 'full_history_replay':
        required = set(clean['artifacts'])
        if any(values.get(v) != clean['artifacts'][v] for v in required):
            failures.append({'full_history': 'replayed values differ from deterministic clean execution'})
    if failures:
        raise Invalid('repaired required outputs rejected')
    if sum(x['cost'] for x in ledger) != row['R']:
        raise Invalid('replay accounting mismatch')
    return {'operations': ledger, 'required_artifacts': {v: versions[v] for v in sorted(required)},
            'acceptance': 'passed', 'quarantined': [f'{v}@clean' for v in sorted(invalid)]}


def coverage(cost, vector, total_budget, overhead=0):
    work = Fraction(total_budget) - overhead
    return {'B_total': exact(total_budget), 'B_work': exact(work),
            'S': exact(Fraction(sum(cost + r <= work for r in vector), len(vector))),
            'G': all(cost + r <= work for r in vector)}


def evaluate(w, d, policy=Policy(), budgets=()):
    clean = execute(w, d)
    if clean['acceptance_failures']:
        return {'status': 'infeasible', 'clean': clean, 'reason': 'required outputs rejected'}
    live, rows = forward(w, d, policy)
    vector = [row['R'] for row in rows]
    if vector != reverse(w, d, policy):
        raise Invalid('forward/reverse disagreement')
    cost = clean['C_exec']
    for row in rows:
        row['total_work'] = cost + row['R']
        row['repair'] = replay(w, d, clean, row, policy=policy)
    if any(r > cost for r in vector):
        raise Invalid('recovery exceeds original work')
    return {'status': 'valid', 'clean': clean, 'live': sorted(live), 'targets': rows,
            'C_exec': cost, 'R': vector, 'mean': exact(Fraction(sum(vector), len(vector))),
            'worst': max(vector), 'worst_targets': [o for o, r in zip(w.owners, vector) if r == max(vector)],
            'per_owner_workload': {o: sum(op.cost for op in d.operations if op.owner == o) for o in w.owners},
            'thresholds': sorted(set(cost + r for r in vector)),
            'budgets': [coverage(cost, vector, b, policy.common_overhead) for b in budgets],
            'policy': asdict(policy), 'claim': 'analytical_control'}
