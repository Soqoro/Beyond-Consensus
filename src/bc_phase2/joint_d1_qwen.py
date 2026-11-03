"""D1 joint-blueprint preparation. Real loading and dispatch remain disabled.

Reuse QwenTransport's measured token boundary and MockPlannerSession's atomic,
locked ledger. The only session admitted here uses injected doubles and mock IDs.
No benchmark loader, job launcher, solver, worker or provider registry is added.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import time
from pathlib import Path

from .model import Invalid, digest
from .joint_schema import require
from .joint_pipeline_contracts import planner_payload, generate_neutral
from .joint_d1_readiness import SMOKE, identities, NEUTRAL_PROMPT, CORRECTION_PROMPT, PROMPT_VERSION
from .planner_ledger import MockPlannerSession, MAX_LEDGER_BYTES, _encoded, CONTEXT, OUTPUT
from .planner_qwen import QwenTransport, CHECKPOINT, REVISION

MAX_RESPONSE_BYTES = 65536


def settings():
    return dict(backend='local_transformers', checkpoint=CHECKPOINT, revision=REVISION,
                tokenizer_revision=REVISION, dtype='bfloat16', thinking=True,
                do_sample=False, context_limit=CONTEXT, output_cap=OUTPUT,
                attention='sdpa', num_beams=1, num_return_sequences=1,
                tools=[], action_constraint='none_strict_joint_blueprint_parser')


def limits():
    return dict(calls=6, calls_per_source=2, input_tokens=CONTEXT-OUTPUT,
                output_tokens=OUTPUT, total_tokens=6*CONTEXT,
                campaign_wall_seconds=3600, physical_gpus=1, concurrency=1,
                host_memory_gb=128, external_fee_status='unverified_local_backend',
                monetary_ceiling=None, currency=None)


def implementation(root):
    names=('joint_d1_qwen.py','joint_d1_readiness.py','joint_pipeline_contracts.py',
           'joint_schema.py','joint_core.py','model.py','planner_qwen.py','planner_ledger.py',
           'joint_d1_local.py')
    paths=['src/bc_phase2/'+name for name in names]
    paths+=['src/beyond_consensus/models/transformers_backend.py']
    return {p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in paths}


def configuration(root):
    """Complete disabled configuration shape; unavailable source bindings stay null."""
    scope=dict(stage='D1', source_ids=list(SMOKE), pilot=dict(n=4,K=2,min_tasks=4,max_tasks=8),
               identities=identities(root), implementation=implementation(root),
               model=settings(), limits=limits(), initial_calls=1, structural_corrections=1,
               semantic_retries=0, source_receipts=None, source_access_permission=None,
               statement_transmission_permission=None, local_inventory=None,
               settings_accepted=False, limits_accepted=False,
               cache_policy='no_response_cache_reuse', retry_policy='no_transport_retry_no_ambiguous_replay',
               tools=[], later_stages_enabled=False)
    return dict(schema='joint-d1-qwen-execution-preparation-v1', enabled=False,
                scope=scope, scope_digest=digest(scope), approval=None)


def validate_configuration(value, root):
    expected=configuration(root)
    require(type(value) is dict and set(value)==set(expected),'D1 configuration fields')
    require(value['schema']==expected['schema'] and value['enabled'] is False,'D1 release disabled')
    scope=value['scope']; require(type(scope) is dict and set(scope)==set(expected['scope']),'scope fields')
    # This preparation binds recommendations, not arbitrary settings or an enabling flag.
    for key in set(scope)-{'source_receipts','source_access_permission',
                          'statement_transmission_permission','local_inventory',
                          'settings_accepted','limits_accepted'}:
        require(scope[key]==expected['scope'][key],'scope mismatch: '+key)
    require(type(scope['settings_accepted']) is bool and type(scope['limits_accepted']) is bool,'acceptance flags')
    require(value['scope_digest']==digest(scope),'scope digest changed')
    return scope


def approval_matches(value, receipt, root):
    """Integrity/scope match only, never authenticates consent or enables a release."""
    scope=validate_configuration(value,root)
    if type(receipt) is not dict or set(receipt)!={'schema','stage','decision','scope_digest','reviewer','reviewed_at'}:
        return False
    return (receipt['schema']=='joint-d1-qwen-approval-v1' and receipt['stage']=='D1'
            and receipt['decision']=='approved' and receipt['scope_digest']==digest(scope)
            and all(type(receipt[k]) is str and bool(receipt[k].strip()) for k in ('reviewer','reviewed_at')))


def preflight(value, root):
    scope=validate_configuration(value,root)
    blockers=[]
    for key in ('source_receipts','source_access_permission','statement_transmission_permission','local_inventory'):
        # Presence is not faithful extraction, source permission, or inventory verification.
        if key=='source_access_permission':
            from .joint_d1_local import SOURCE_PERMISSION
            if scope[key]==SOURCE_PERMISSION:
                continue
        blockers.append(('missing:' if scope[key] is None else 'unverified:')+key)
    for key in ('settings_accepted','limits_accepted'):
        if not scope[key]: blockers.append('pending:'+key)
    if not approval_matches(value,value['approval'],root): blockers.append('exact_approval_missing_or_mismatched')
    blockers+=['live_dispatch_release_disabled']
    return dict(status='disabled',stage='D1',scope_digest=value['scope_digest'],blockers=blockers,
                execution_allowed=False,D1_APPROVED_TO_RUN=False,model_executed=False,next_stage_authorized=False,
                limitations=['current_D1_fit_unmeasured_not_a_prior_live_probe_requirement'],
                live_stages={f'D{i}':'disabled' for i in range(1,7)})


def open_live(*args, **kwargs):
    """No model imports, allocation checks, inventory reads or provider calls."""
    raise Invalid('D1 real loading and dispatch disabled; source/limit/approval review pending')


def mock_request(record):
    require(type(record) is dict and set(record)=={'id','problem'},'statement-only fields required')
    require(type(record['id']) is str and record['id'].startswith('mock:'),'only mock IDs in offline session')
    require(type(record['problem']) is str and bool(record['problem'].strip()),'nonempty statement')
    payload=planner_payload(record,4,2)
    payload.update(prompt=NEUTRAL_PROMPT,prompt_version=PROMPT_VERSION)
    return dict(payload=payload,payload_digest=digest(payload))


class JointQwenSession(MockPlannerSession):
    """Joint response semantics with existing durable reservation primitives.

    Exception after reservation leaves unresolved usage and blocks ALL dispatch.
    Restart never repeats a completed valid/unsupported call or uncertain call.
    Fake transport output tokens include reasoning and EOS via QwenTransport.
    """
    def __init__(self,directory,records,transport):
        require(type(transport) is QwenTransport and transport.evidence=='injected_offline_double',
                'only injected Qwen transport doubles permitted')
        for key, expected in dict(checkpoint=CHECKPOINT, revision=REVISION, context_limit=CONTEXT,
                                  output_cap=OUTPUT, do_sample=False, thinking=True).items():
            require(transport.binding.get(key)==expected,'transport model/settings mismatch: '+key)
        require(type(records) is list and len(records)==3,'three synthetic requests')
        requests=[mock_request(r) for r in records]
        require(len({r['payload']['source']['id'] for r in requests})==3,'unique sources')
        self._initialize(directory,requests,transport)

    def _initialize(self,directory,requests,transport,scope_binding=None,started_at=None):
        self.transport=transport
        self.binding=dict(schema='joint-d1-qwen-offline-binding-v1',requests=requests,
                          transport=deepcopy(transport.binding),settings=settings(),limits=limits(),
                          implementation=implementation(Path(__file__).resolve().parents[2]),
                          real_execution_allowed=False)
        if scope_binding is not None:self.binding['execution_scope']=deepcopy(scope_binding)
        require(len(_encoded(self.binding))<MAX_LEDGER_BYTES//2,'binding too large')
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True)
        with self._locked():
            if self.path.exists():self._read()
            else:self._save(dict(schema='joint-d1-qwen-offline-ledger-v1',binding=self.binding,
                                 binding_digest=digest(self.binding),attempts=[],started_at=time.time() if started_at is None else started_at,
                                 model_executed=False,task_execution_allowed=False,evidence=self.transport.evidence))

    def _check_transport(self):
        require(type(self.transport) is QwenTransport and self.transport.evidence=='injected_offline_double'
                and self.transport.binding==self.binding['transport'],'transport changed')

    def _model_executed(self):
        return False

    def _render_request(self,request):
        return self.transport.render(request)

    def advance(self,source_id):
        self._check_transport()
        with self._locked():
            state=self._read();attempts=state['attempts']
            require(all(a['state']=='completed' for a in attempts),'unresolved/violated usage; no replay')
            require(len(attempts)<6,'campaign call ceiling')
            age=time.time()-state['started_at']
            require(0<=age<limits()['campaign_wall_seconds'],'campaign wall limit or clock regression')
            req=next((r for r in self.binding['requests'] if r['payload']['source']['id']==source_id),None)
            require(req is not None,'source outside scope')
            prior=[a for a in attempts if a['source_id']==source_id]
            outbound=deepcopy(req)
            if prior:
                require(len(prior)==1 and prior[0]['review']['status']=='invalid'
                        and not prior[0].get('boundary_error'),'no eligible structural correction')
                outbound['payload'].update(correction_prompt=CORRECTION_PROMPT,
                    first_response=prior[0]['raw'],structural_error=prior[0]['review']['history'][0]['structural_error'])
                outbound['payload_digest']=digest(outbound['payload'])
            rendered=self._render_request(outbound)
            count=rendered['input_tokens'];require(type(count) is int and 0<count<=CONTEXT-OUTPUT,'input cap')
            reservation=count+OUTPUT
            require(sum(a['actual_tokens'] or 0 for a in attempts)+reservation<=6*CONTEXT,'campaign token cap')
            a=dict(source_id=source_id,attempt=len(prior),state='reserved',outbound_payload=outbound['payload'],
                   payload_digest=outbound['payload_digest'],rendered=rendered,input_tokens=count,
                   reservation_tokens=reservation,actual_tokens=None,raw=None,reserved_at=datetime.now(timezone.utc).isoformat())
            attempts.append(a)
            if self._model_executed():
                state['model_executed']=None
                state['model_dispatch_attempted']=True
            self._save(state)
            # No retry/catch-reset. A failure here preserves the durable reservation.
            observed=self.transport.generate(rendered)
            a['observation']=deepcopy(observed)
            usage=observed.get('output_tokens');inp=observed.get('input_tokens')
            a['boundary_error']=observed.get('boundary_error')
            if type(usage) is not int or usage<0 or type(inp) is not int or inp!=count:
                a['state']='uncertain'
            else:
                a['actual_tokens']=count+usage
                a['state']='usage_violation' if usage>OUTPUT else 'completed'
            text=observed.get('final_text')
            for key in ('raw_decoded','final_text'):
                val=a['observation'].get(key)
                if type(val) is str and len(val.encode('utf8'))>MAX_RESPONSE_BYTES:
                    a['observation'][key]=None;a['observation'][key+'_digest']=digest(val)
            if type(text) is str and len(text.encode('utf8'))<=MAX_RESPONSE_BYTES:
                a['raw']=text
            else:a['boundary_error']=a['boundary_error'] or 'missing_or_oversized_final_text'
            if observed.get('finish_reason')!='eos':
                a['boundary_error']=a['boundary_error'] or 'non_eos_response'
            if a['boundary_error'] and a['state']=='completed':
                a['state']='response_boundary_error'
            a['review']=generate_neutral(req['payload']['source'],4,2,
                [p['raw'] for p in prior]+[a['raw'] or ''],synthetic=False)
            a['admitted']=False
            state['model_executed']=self._model_executed()
            a['observed_at']=datetime.now(timezone.utc).isoformat()
            if time.time()-state['started_at']>=limits()['campaign_wall_seconds']:
                a['state']='wall_limit_exceeded'
            self._save(state)
            return deepcopy(dict(a,totals=self._totals(state),model_executed=self._model_executed()))
