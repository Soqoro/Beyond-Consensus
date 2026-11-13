"""Prospective interface overlay; historical bank, baseline and launch remain untouched."""
from copy import deepcopy
from . import composite_scaling as spec, composite_scaling_runtime as runtime
from .composite_derivation_diagnostic import reordered,candidate_request
from .model import digest
from .joint_schema import require

VERSION='composite-common-derivation-first-v1'

def task(original):
    value=deepcopy(original);value['fields']=reordered(value['fields']);return value

def transport_tasks(components):
    return [dict(task(t),source_id=c['source_id']) for c in components for t in c['tasks']]

def descriptor(c,t,mode):
    value=deepcopy(spec.descriptor(c,t,mode))
    value['task']=task(value['task'])
    value['worker_interface']=VERSION
    return value

def coverage(components):
    return [dict(source_id=c['source_id'],task_id=t['id'],mode=a,descriptor=descriptor(c,t,a),
                 key=digest(descriptor(c,t,a)),historical_key=spec.key(c,t,a),status='fresh_profile_required')
            for c in components for a in c['A_modes'] for t in c['tasks']]

def check_profile(receipt,entry):
    require(receipt.get('kind')=='new_profile','historical and evaluation prices forbidden')
    require(receipt.get('key')==entry['key'] and receipt.get('descriptor')==entry['descriptor'],'exact interface profile key required')
    require(type(receipt.get('tokens')) is int and receipt['tokens']>0,'actual positive tokens')
    require(receipt.get('invocation') and receipt.get('ledger_digest'),'profile provenance')

class Engine(runtime.Engine):
    """Same mathematical responsibilities/parents; reordered wire fields for either arm."""
    def task_for_operation(self,op):return task(super().task_for_operation(op))
    def make_request(self,t,store):return candidate_request(super().make_request(t,store))

def freeze(bank):
    components=spec.reviewed(bank)
    entries=coverage(components)
    require(all(e['key']!=e['historical_key'] for e in entries),'profile version separation')
    out=dict(schema=VERSION,status='prospective_interface_frozen_not_campaign_authorization',
        historical_bank_id=bank['bank_id'],methods=list(spec.METHODS),
        component_contract_ids=[c['contract_id'] for c in components],
        transport_tasks=transport_tasks(components),profile_coverage=entries,
        workload_policy='same previously frozen source sets, task graphs and NEUTRAL ownership; no outcome-driven redraw',
        runtime_domain_policy='unchanged A/C permissions and general-K optimiser; new worker/profile/condition bindings',
        profile_policy='all permitted modes freshly profiled; own fresh prerequisites; no diagnostic or evaluation prices or artifacts',
        execution_allowed=False,model_executed=False,
        remaining=['remaining task-schema CPU qualification','component-boundary limitations and unresolved gecko review','exact new profile/evaluation schedule and scope approval'])
    out['interface_digest']=digest(out);return out
