"""D1 readiness only: no provider, source-content loader, or approval verifier."""
from copy import deepcopy
import hashlib
from pathlib import Path
from .joint_schema import require
from .joint_pipeline_contracts import PROMPT,generate_neutral
from .joint_pipeline_sources import source_binding
from .model import digest

SMOKE=('test/algebra/2743.json','test/algebra/101.json','test/counting_and_probability/508.json')
PROMPT_VERSION='joint-d1-neutral-v1'
NEUTRAL_PROMPT=PROMPT+(' Pilot only: n=4, K=2, 4<=m<=8. Exactly four substantive tasks and no '
    'alternative choices are valid. Do not add formatting-only, duplicate whole-solution or '
    'unused checking tasks. Sequential reasoning is allowed; parallelism is not required. '
    'Preserve every required output and source artifact provenance. Return unsupported rather '
    'than pad. Do not assign owners yet. No fitted costs, gold answers or recovery gains are '
    'available. One initial response and at most one correction for structural errors only; '
    'valid weak plans and unsupported responses stop. Human admissibility review is separate.')
CORRECTION_PROMPT=('joint-d1-structural-correction-v1: Correct only the recorded schema, capacity or artifact-contract errors in the first response. Preserve source ID and task meaning; do not consult gold, costs or recovery gains. This is the final permitted decomposition response. Return unsupported if a meaningful conforming blueprint is unavailable.')
RUBRIC=('schema_and_capacity','artifact_provenance','substantive_task_meaning',
        'genuine_alternatives_or_none','no_padding_or_duplicate_solutions',
        'required_output_preservation','no_solved_trusted_inputs','human_review_pending')
CAPS=('per_request_calls','campaign_calls','per_request_input_tokens','per_request_output_tokens',
      'campaign_total_tokens','per_request_money','campaign_money')
BINDINGS=('source_statement_receipts','statement_access_authorization','source_family_review',
          'provider','model','model_revision','tokenizer_revision','sampling','tools',
          'metering','currency','tariff_provenance','cache_policy','retry_policy','approval')


def identities(root):
    paths=['src/bc_phase2/joint_schema.py','src/bc_phase2/joint_pipeline_contracts.py',
           'src/bc_phase2/joint_d1_readiness.py']
    validators={p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in paths}
    schema=dict(version='joint-blueprint-v1',statuses=['plan','unsupported'],
                plan_fields=['schema','status','blueprint'],unsupported_fields=['schema','status','reason'],
                blueprint='joint-domain-v1 without mode initial/replay prices; no ownership selection',
                validation_implementation=validators,structural_prices='placeholders_not_estimates',
                pilot=dict(n=4,K=2,min_tasks=4,max_tasks=8),qualitative_review_separate=True)
    return dict(correction_prompt_sha256=hashlib.sha256(CORRECTION_PROMPT.encode()).hexdigest(),prompt_version=PROMPT_VERSION,prompt_sha256=hashlib.sha256(NEUTRAL_PROMPT.encode()).hexdigest(),
                schema=schema,schema_sha256=digest(schema))


def template(root):
    return dict(schema='joint-d1-readiness-v1',stage='D1',enabled=False,source_ids=list(SMOKE),
                pilot=dict(n=4,K=2,min_tasks=4,max_tasks=8),
                decomposition=dict(initial=1,structural_corrections=1,semantic_retries=0),
                identities=identities(root),rubric=list(RUBRIC),
                boundaries=dict(public_fields=['id','problem'],protected_fields=[
                    'answer','solution','grader_notes','reviewer_material','family_review','future_replay_bills'],
                    worker_required=False,estimator_required=False,answer_evaluator_required=False),
                bindings={k:None for k in BINDINGS},ceilings={k:None for k in CAPS})


def preflight(manifest,root):
    expected=template(root)
    require(type(manifest) is dict and set(manifest)==set(expected),'D1 exact manifest fields')
    require(type(manifest['enabled']) is bool,'enabled boolean')
    for k in ('schema','stage','source_ids','pilot','decomposition','identities','rubric','boundaries'):
        require(manifest[k]==expected[k],'D1 scope/identity mismatch: '+k)
    require(type(manifest['bindings']) is dict and set(manifest['bindings'])==set(BINDINGS),'binding fields; secret fields forbidden')
    require(type(manifest['ceilings']) is dict and set(manifest['ceilings'])==set(CAPS),'exact ceilings')
    blockers=[]
    for k,v in manifest['bindings'].items():
        if v is None:blockers.append('UNRESOLVED:'+k)
        else:
            # Configuration is evidence to review, never accepted live qualification.
            require(type(v) in (str,dict,list) and bool(v),'nonempty explicit binding: '+k)
            blockers.append('UNVERIFIED:'+k)
    for k,v in manifest['ceilings'].items():
        if v is None:blockers.append('UNRESOLVED:'+k)
        elif k.endswith('money'):
            from fractions import Fraction
            require(type(v) is str,'money ceiling exact decimal/rational string')
            try:amount=Fraction(v)
            except (ValueError,ZeroDivisionError):require(False,'invalid money ceiling')
            require(amount>=0,'nonnegative money ceiling')
        else:require(type(v) is int and v>0,'positive integer ceiling: '+k)
    calls=manifest['ceilings']['per_request_calls']
    require(calls is None or calls==1,'one invocation per request')
    require(manifest['ceilings']['campaign_calls'] is None or manifest['ceilings']['campaign_calls']<=6,'three sources; at most two decomposition calls each')
    blockers+=['SOURCE_INPUT_UNAVAILABLE','REVIEW_UNRESOLVED','live_planner_adapter_not_registered',
               'exact_D1_scope_bound_approval_verifier_absent']
    if not manifest['enabled']:blockers.append('disabled_manifest')
    return dict(schema='joint-d1-preflight-v1',preparation='D1_OFFLINE_PREPARED',status='D1_BLOCKED',
                execution_allowed=False,D1_APPROVED_TO_RUN=False,blockers=blockers,
                scope_hash=digest({k:v for k,v in manifest.items() if k!='enabled'}),
                required_approval_evidence=['explicit user D1-only decision','exact manifest scope hash',
                    'ordered cohort and qualified statement hashes','provider/model/revision/sampling',
                    'prompt/schema identities','call/token/money ceilings and metering/tariffs',
                    'cache/retry policy','reviewer identity and review time'],
                model_executed=False,next_stage_authorized=False)


def ledger(root):
    binding=source_binding(root)
    require(tuple(binding['frozen_smoke_ids'])==SMOKE,'historical smoke selection mismatch')
    return dict(schema='joint-d1-admission-ledger-v1',source_binding=binding,
                rows=[dict(source_id=s,selected=s in SMOKE,attempted=False,raw_responses=[],
                      input_status='SOURCE_INPUT_UNAVAILABLE',diagram_blocked=s in binding['diagram_blocked'],
                      plan_status='unstarted',human_review='REVIEW_UNRESOLVED',admitted=False,
                      reason='No statement access/qualification bound in this preparation; no synthetic replacement.')
                      for s in binding['original_ids']],admitted_count=0,model_executed=False)


def screen_mock(record,responses):
    """Only fabricated TEST identities; cannot supply benchmark source text."""
    require(type(record) is dict and type(record.get('id')) is str and record['id'].startswith('mock:'),
            'SOURCE_INPUT_UNAVAILABLE: benchmark content adapter is not registered')
    require(type(record.get('problem')) is str and bool(record['problem'].strip()),'missing mock statement')
    require(type(responses) is list and all(type(s) is str for s in responses),'prerecorded mock responses only')
    # Accepted parser supplies the two-response structural policy. The D1 prompt
    # is attached to this offline request record; no provider is invoked.
    r=generate_neutral(record,4,2,responses,synthetic=True)
    r['payload']['prompt']=NEUTRAL_PROMPT;r['payload']['prompt_version']=PROMPT_VERSION
    r.update(source_id=record['id'],attempted=bool(r['history']),admitted=False,
             human_review='REVIEW_UNRESOLVED',evidence='synthetic_only',discarded_unrequested_responses=max(0,len(responses)-len(r['history'])))
    return r


def prepare(root):
    m=template(root)
    return dict(manifest=m,preflight=preflight(m,root),ledger=ledger(root),prompt=NEUTRAL_PROMPT,correction_prompt=CORRECTION_PROMPT,
                identities=m['identities'],rubric=list(RUBRIC))
