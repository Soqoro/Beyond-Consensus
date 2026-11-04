#!/usr/bin/env python3
"""Supplement one reviewed false-positive request and freeze a disabled 20-call proposal."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from bc_phase2 import d1_natural_screen as screen
from bc_phase2.model import digest
from bc_phase2.joint_schema import require
from bc_phase2.joint_d1_release import read_evidence
import prepare_math500_screening_inputs as inputs
import prepare_math500_screening_cohort as selection

CLEARED='test/prealgebra/105.json'
BLOCKED='test/precalculus/1303.json'
CLEARED_HASH='ecdad8d7b2a1a13309f7bb82a6f1657912ba05844f278b6af22e19c5f442761e'
STATEMENTS_HASH='9e1b6374294104b293ee597a9fbc871f7dd577534638e0ac3ca330ea3192b047'


def validate(prep,cohort,records):
    require(cohort.get('cohort_digest')==inputs.COHORT_DIGEST
            and digest({k:v for k,v in cohort.items() if k!='cohort_digest'})==inputs.COHORT_DIGEST,'exact frozen cohort')
    require(cohort['selected_source_ids'][:14]==list(selection.ORIGINAL_IDS),'original order')
    require(prep.get('schema')=='math500-screening-input-preparation-v1'
            and prep.get('cohort_digest')==inputs.COHORT_DIGEST
            and prep.get('statement_file_sha256')==STATEMENTS_HASH,'prepared source binding')
    expected=[s for s in cohort['selected_source_ids'] if s not in selection.SMOKE and s not in selection.DIAGRAM_IDS]
    require(len(expected)==21 and [r['id'] for r in records]==expected and prep['prepared_source_ids']==expected,'21 remaining sources')
    require([r['source_id'] for r in prep['rows']]==expected,'measurement order')
    model=prep['model_binding']
    require(model['checkpoint']==screen.CHECKPOINT and model['revision']==screen.REVISION
            and model['interface_implementation']==screen.implementation()
            and model['prompt_hash']==digest(screen.PROMPT) and model['schema_hash']==digest(screen.response_schema()),'model/prompt/schema/runtime changed')
    for record,row in zip(records,prep['rows']):
        require(set(record)=={'id','problem'} and type(record['problem']) is str,'statement-only views')
        require(hashlib.sha256(record['problem'].encode()).hexdigest()==row['statement_sha256'],'statement hash')
        if record['id']==CLEARED:
            require(row['statement_sha256']==CLEARED_HASH and row['attachment_flags']==['diagram_reference'],'only reviewed false positive')
        if record['id'] in (CLEARED,BLOCKED):
            require(row['status']=='attachment_review_required_not_rendered' and row['input_tokens'] is None,'original flag status')
        else:
            count=row['input_tokens']
            require(row['attachment_flags']==[] and row['status']=='rendered_fit_observed_attachment_review_pending','unexpected unreviewed attachment')
            require(type(count) is int and 0<count<=screen.CONTEXT-screen.OUTPUT
                    and row['reserved_tokens']==count+3072 and row['output_cap']==3072,'retained token fit')
            require(row['payload_digest']==screen.request(record)['payload_digest'],'retained request changed')
    require(sum(r['reserved_tokens'] or 0 for r in prep['rows'])==81424,'retain all 19 prior reservations')
    return expected


def supplement(prep,records,tokenizer,template_hash):
    source=next(r for r in records if r['id']==CLEARED)
    require(hashlib.sha256(source['problem'].encode()).hexdigest()==CLEARED_HASH,'false-positive exception hash')
    rendered=screen.render_request(tokenizer,screen.request(source),template_hash)
    row={'source_id':CLEARED,'statement_sha256':CLEARED_HASH,'input_tokens':rendered['input_tokens'],
         'output_cap':3072,'reserved_tokens':rendered['input_tokens']+3072,
         'payload_digest':rendered['payload_digest'],'rendered_ids_digest':rendered['rendered_ids_digest']}
    # Preserve existing measurement dictionaries exactly; annotations are separate.
    rows=[deepcopy(row if r['source_id']==CLEARED else r) for r in prep['rows'] if r['source_id']!=BLOCKED]
    return rows,row


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('preparation','cohort','snapshot','output'):parser.add_argument('--'+name,required=True,type=Path)
    a=parser.parse_args();start=time.process_time();wall=time.monotonic()
    prep=read_evidence(a.preparation);cohort=read_evidence(a.cohort)
    parent_hash=hashlib.sha256(a.preparation.read_bytes()).hexdigest()
    raw=Path(prep['statement_file']).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==STATEMENTS_HASH,'exact statement package')
    records=json.loads(raw);validate(prep,cohort,records)
    # Reuse existing guarded metadata/non-thinking inspection, never load weights.
    from prepare_d1_natural_screen import inspect_tokenizer
    observed=inspect_tokenizer(a.snapshot)
    old=prep['model_binding']
    require(all(observed[k]==old[k] for k in ('checkpoint','revision','files','template_check','prompt_hash','schema_hash','interface_implementation')),'tokenizer/runtime changed')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(a.snapshot),local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==old['template_check'],'non-thinking support')
    rows,new=supplement(prep,records,tokenizer,old['template_check']['template_hash'])
    require(hashlib.sha256(a.preparation.read_bytes()).hexdigest()==parent_hash,'preparation changed')
    require(Path(prep['statement_file']).read_bytes()==raw,'statement file changed')
    require(all(hashlib.sha256((a.snapshot/n).read_bytes()).hexdigest()==v['sha256'] for n,v in observed['files'].items()),'metadata changed')
    a.output.mkdir(exist_ok=False)
    eligible=[r for r in records if r['id']!=BLOCKED]
    selection.write(a.output/'statements.json',eligible)
    review={'kind':'assistant_statement_only_attachment_review','source_package_sha256':STATEMENTS_HASH,
            'text_sufficient_source_ids':[r['id'] for r in eligible],
            'false_positive':{'source_id':CLEARED,'statement_sha256':CLEARED_HASH,
                             'reason':'figure skater is a sport description, not a diagram reference'},
            'diagram_blocked_retained':sorted(set(selection.DIAGRAM_IDS)|{BLOCKED}),
            'meaningful_workflow_approval':False,'review_notes_are_not_planner_inputs':True}
    selection.write(a.output/'attachment-review.json',review)
    scope={'condition':'d1-math500-complementary-screen-v1','cohort_digest':inputs.COHORT_DIGEST,
           'source_ids':[r['id'] for r in eligible],'completed_no_rerun':list(selection.SMOKE),
           'blocked_retained':review['diagram_blocked_retained'],'parent_preparation_sha256':parent_hash,
           'statement_file':str((a.output/'statements.json').resolve()),
           'statement_file_sha256':hashlib.sha256((a.output/'statements.json').read_bytes()).hexdigest(),
           'verified_requests':rows,'attachment_review_digest':digest(review),'model_binding':observed,
           'snapshot_path':str(a.snapshot),'prompt_hash':digest(screen.PROMPT),'schema_hash':digest(screen.response_schema()),
           'resources_proposed':{'maximum_calls':20,'calls_per_source':1,'output_cap':3072,'context_limit':16384,
               'aggregate_token_cap':sum(r['reserved_tokens'] for r in rows),'campaign_wall_seconds':3600,
               'physical_gpus':1,'concurrency':1,'cpus':4,'host_memory_gb':128,'minimum_vram_bytes':80000000000,
               'partition':'NA100q','scheduler_config_bound':False},
           'do_sample':False,'thinking':False,'retry_policy':'one_call_per_source_no_retry_no_correction',
           'stop_policy':screen.disabled_manifest()['scope']['stop_policy'],
           'one_hour_may_leave_unrun_sources':True,'D2_D6_enabled':False,
           'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    manifest={'schema':'math500-screening-scope-proposal-v1','scope':scope,'scope_digest':digest(scope),
              'approval':None,'execution_allowed':False,'not_a_live_release':True,
              'remaining':['bind actual cluster configuration and current scheduler evidence',
                           'bind the existing shared-registry launch path to this 20-source scope',
                           'explicit expanded source-transmission and GPU approval']}
    selection.write(a.output/'scope.disabled.json',manifest)
    summary={'directory':str(a.output),'scope_digest':manifest['scope_digest'],'new_measurement':new,
             'preserved_measurement_count':19,'eligible_calls':20,'resources_proposed':scope['resources_proposed'],
             'diagram_blocked_retained':review['diagram_blocked_retained'],
             'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
             'model_executed':False,'execution_allowed':False,'remaining':manifest['remaining']}
    selection.write(a.output/'summary.json',summary)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
