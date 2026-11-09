"""Offline preparation only: reorder existing fields, never dispatch or repair answers."""
from copy import deepcopy
from .model import digest
from .joint_schema import require
from .composite_math_decoder import schema

VERSION = 'composite-derivation-first-diagnostic-v1'
TARGETS = (
    ('test/geometry/1097.json', 't0'),
    ('test/counting_and_probability/1003.json', 't4'),
    ('test/number_theory/533.json', 't0'),
    ('test/intermediate_algebra/1166.json', 't0'),
    ('test/precalculus/190.json', 't0'),
    ('test/precalculus/675.json', 't0'),
)

def reordered(fields):
    require(type(fields) is list and all(type(x) is str for x in fields), 'field list')
    require(len(fields)==len(set(fields)), 'duplicate fields')
    reasoning=[x for x in fields if x in ('derivation','justification')]
    require(len(reasoning)==1, 'exactly one existing derivation field required')
    return reasoning+[x for x in fields if x not in reasoning]

def candidate_request(request):
    require(digest(request['payload'])==request['payload_digest'], 'request digest')
    payload=deepcopy(request['payload'])
    payload['required_string_fields']=reordered(payload['required_string_fields'])
    return dict(payload=payload,payload_digest=digest(payload))

def prepare(export):
    binding=export['binding'];transport=binding['transport']
    require(transport['checkpoint']=='Qwen/Qwen3.5-27B' and transport['revision']=='fc05daec18b0a78c049392ed2e771dde82bdf654', 'model binding')
    require(transport['thinking'] is False and transport['do_sample'] is False and transport['output']==3072 and transport['context']==16384,'frozen generation settings')
    groups=export['groups']
    require(len(groups)==6 and {(g['source_id'],g['task_id']) for g in groups}==set(TARGETS),'exact six task groups')
    rows=[]
    for sid,tid in TARGETS:
        g=next(g for g in groups if (g['source_id'],g['task_id'])==(sid,tid))
        content={k:g[k] for k in ('source_id','task_id','request','raw_decoded','final_text')}
        require(digest(content)==g['content_digest'],'export content digest')
        old=g['request'];payload=old['payload']
        require((payload['source']['id'],payload['task_id'])==(sid,tid),'source/task binding')
        old_schema=schema({'fields':payload['required_string_fields']})
        require(digest(old_schema)==transport['schema_hashes'][sid+':'+tid],'historical schema binding')
        new=candidate_request(old);fields=new['payload']['required_string_fields']
        # Reusing supplied parents is intentional for this isolated interface probe.
        # Never treat these calls as fresh full-workflow execution or calibration.
        rows.append(dict(source_id=sid,task_id=tid,original_request_digest=old['payload_digest'],
            candidate_request_digest=new['payload_digest'],parent_digest=digest(payload['parent_artifacts']),
            historical_fields=payload['required_string_fields'],candidate_fields=fields,
            candidate_schema=schema({'fields':fields}),candidate_schema_digest=digest(schema({'fields':fields})),
            requested_emission_order=fields,emission_order_verified=False,
            parent_policy='exact historical parent payload; no new prerequisite calls'))
    result=dict(schema=VERSION,status='disabled_pending_tokenizer_and_grammar_order_checks',
        parent_scope=binding['scope'],model_binding=deepcopy(transport),tasks=rows,
        historical_outputs_used_for_prompt=False,prompt_policy='unchanged instruction, responsibility, source and parents; only required field order changes',
        limits=dict(maximum_calls=6,calls_per_task=1,input_cap=13312,output_cap=3072,context=16384,
                    token_cap=98304,wall_seconds=3600,physical_gpus=1,cpus=4,host_memory_gb=128,minimum_vram_bytes=80000000000),
        blockers=['pinned local tokenizer rendered-request measurement','XGrammar 0.1.32 actual derivation-first emission-order qualification','scope-bound scheduler and inventory verification','exact live approval and shared-registry launch binding'],
        execution_allowed=False,model_executed=False,qualification=False,
        limitations=['selected known failures; no general accuracy estimate','historical control rather than concurrent randomized comparison','old profile prices are not valid for a changed worker interface','changing order does not certify semantic consistency'])
    result['proposal_digest']=digest(result)
    return result
