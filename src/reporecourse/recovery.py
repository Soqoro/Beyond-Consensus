"""Track R: common frozen state, labelled equal-remaining diagnostic only."""
from copy import deepcopy
from .common import Rejected,digest
from .resources import Resources


def freeze(engine, alarm):
    if engine.env.finished or engine.phase!='repair':raise Rejected('fixed_state_phase')
    if not isinstance(alarm,dict) or set(alarm)!={'unavailable','localization'} or alarm['localization'] not in ('announced_loss','public_alarm'):
        raise Rejected('localization_contract')
    if set(alarm['unavailable'])!=engine.env.unavailable:raise Rejected('alarm_trace_mismatch')
    if alarm['localization']=='public_alarm' and not engine.public_alarm:raise Rejected('alarm_trace_mismatch')
    if alarm['localization']=='announced_loss' and not engine.env.unavailable:raise Rejected('alarm_trace_mismatch')
    body={'schema':'rr-fixed-state-v1','plan':deepcopy(engine.plan),'public_hash':digest(engine.public),
        'primary':engine.checkpoint(),'alarm':deepcopy(alarm),'historical_resources':engine.env.resources.summary(),
        'corruption_state_hash':digest(engine.env.state()),'reference_access':False}
    return {**body,'fixed_state_hash':digest(body)}


def resume(engine,snapshot,token_allowance,cpu_allowance):
    if snapshot['fixed_state_hash']!=digest({k:v for k,v in snapshot.items() if k!='fixed_state_hash'}):raise Rejected('fixed_state_integrity')
    if digest(engine.plan)!=digest(snapshot['plan']) or digest(engine.public)!=snapshot['public_hash']:
        raise Rejected('fixed_state_graph_mismatch')
    state=deepcopy(snapshot['primary']);state['environment']['track']='R';state['environment']['finished']=False
    # Preserve historical cost separately. Charge new restoration/materialization
    # to the remaining allowance rather than resetting it after restoration.
    remaining=Resources(token_allowance,cpu_allowance)
    state['resources']=deepcopy(vars(remaining))
    state['alarm_resources']=deepcopy(remaining.summary())
    engine.env.track='R';engine.env.target=state['environment']['target'];engine.restore(state)
    engine.historical_resources=deepcopy(snapshot['historical_resources'])
    engine.phase='repair'
