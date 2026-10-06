"""Bounded common public repair extension; no evaluator or compromise truth."""
from copy import deepcopy
import time
from .common import Rejected


def reuse_consumer(engine,unit,worker):
    start=time.process_time();index=len(engine.env.resources.events)
    try:return _reuse_consumer(engine,unit,worker)
    finally:
        try:engine.env.resources.parent_overhead('jit_candidate_search',start,index)
        except Rejected:engine.status='resource_exhausted'


def _reuse_consumer(engine,unit,worker):
    env=engine.env
    if not unit['outputs'] or all(o in env.bound for o in unit['outputs']):return False
    terminal=unit.get('terminal_bindings',{o:o for o in unit['outputs']})
    candidates=[(v,a) for v,a in env.artifacts.items() if a['name'] in terminal.values() and a['bindings']
        and (not env.scopes or a.get('producer_unit')==unit['id'])]
    if not candidates:return False
    # One latest public candidate per assignment; never search private correctness.
    version,artifact=max(candidates,key=lambda pair:pair[1]['sequence'])
    bindings={}
    for alias,old in artifact['bindings'].items():
        name=env.artifacts[old]['name']
        choices=[(v,a) for v,a in env.artifacts.items() if a['name']==name and (not env.scopes or a.get('producer_unit')==env.artifacts[old].get('producer_unit'))]
        bindings[alias]=max(choices,key=lambda p:p[1]['sequence'])[0]
    if bindings==artifact['bindings']:return False
    obligations=[o for o in unit['outputs'] if terminal[o]==artifact['name']]
    if not obligations:return False
    action={'tool':'rebind_artifact','version':version,'name':artifact['name'],'bindings':bindings,'obligations':obligations}
    env.assignment[worker]=deepcopy(unit)
    before=env.observation(worker);start=time.process_time();index=len(env.resources.events);result=None
    try:
        result=env.action(worker,action)
        checked=env.check_public()
        for o in obligations:
            if not checked[o]:env.bound.pop(o,None)
        env.events.append({'type':'jit_reexecute','worker':worker,'unit':unit['id'],'public_pass':all(checked[o] for o in obligations)})
    except Rejected as exc:
        result={'error':str(exc)}
        engine.failures.append({'unit':unit['id'],'stage':'repair','category':str(exc)})
        for o in obligations:env.bound.pop(o,None)
        if str(exc) in ('token_cap','cpu_cap'):engine.status='resource_exhausted'
    finally:
        try:env.resources.parent_overhead('jit_rebind_search',start,index)
        except Rejected:engine.status='resource_exhausted'
        engine.trajectories.append(dict(actor=worker,stage='repair',unit=unit['id'],observation=before,
            action=action,tool_result=result,costs=deepcopy(env.resources.events[index:]),next_observation=env.observation(worker)))
        engine.checkpoint()
    return all(o in env.bound for o in unit['outputs'])
