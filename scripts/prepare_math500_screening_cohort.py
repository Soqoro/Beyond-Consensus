#!/usr/bin/env python3
"""Metadata-only prospective selection. Never extracts statements, answers or dispatches."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.math500 import DATASET,REVISION,SHA256,MAX_FILE_BYTES,SUBJECTS,_development_proposal
from bc_phase2.planner_first import ORIGINAL_IDS,DIAGRAM_IDS
from bc_phase2.joint_d1_readiness import SMOKE
from bc_phase2.model import digest,Invalid
from bc_phase2.response_boundary import decode_response
from types import SimpleNamespace

POLICY={
    'schema':'math500-complementary-screen-selection-v1','seed':0,'additional_count':12,
    'dataset':DATASET,'revision':REVISION,'dataset_sha256':SHA256,
    'original_source_ids':list(ORIGINAL_IDS),'known_diagram_blocked_ids':sorted(DIAGRAM_IDS),
    'eligibility':'All 500 pinned IDs except original 14; original remainder was unused/unassigned, not final heldout.',
    'ranking':'Repeat 12 times: minimize (additional subject count, additional level count, SHA256 canonical JSON [policy schema, seed, dataset, revision, source_id, subject, level], source_id). Counts start at zero.',
    'metadata_fields':['source_id','subject','level'],
    'replacement_policy':'none; retain all selected sources even if blocked, invalid or unsuitable',
    'original_proposal_digest':'750bae7686e2818b1e10ff219e1be164356cce9e587f06efa6c03e3f61e02f6c',
    'heldout_policy':'prospective development exclusion only; never edit the historical reserved list or designate remaining sources as final test',
    'model_execution_authorized':False,
}


def select(metadata):
    ids=[r['source_id'] for r in metadata]
    if len(ids)!=len(set(ids)) or not set(ORIGINAL_IDS)<=set(ids):raise Invalid('unique metadata and original cohort required')
    for r in metadata:
        if set(r)!=set(POLICY['metadata_fields']) or r['subject'] not in SUBJECTS or type(r['level']) is not int or not 1<=r['level']<=5:
            raise Invalid('allowlisted metadata only')
    subject_counts=Counter();level_counts=Counter();chosen=[]
    candidates=[r for r in metadata if r['source_id'] not in ORIGINAL_IDS]
    if len(candidates)<12:raise Invalid('insufficient fixed candidate pool; no replacement')
    def rank_hash(r):return digest([POLICY['schema'],0,DATASET,REVISION,r['source_id'],r['subject'],r['level']])
    for index in range(12):
        r=min(candidates,key=lambda r:(subject_counts[r['subject']],level_counts[r['level']],rank_hash(r),r['source_id']))
        chosen.append({**r,'additional_selection_index':index,'rank_hash':rank_hash(r),
                       'subject_count_before':subject_counts[r['subject']],'level_count_before':level_counts[r['level']]})
        candidates.remove(r);subject_counts[r['subject']]+=1;level_counts[r['level']]+=1
    return chosen


def read_metadata(path):
    with Path(path).open('rb') as f:raw=f.read(MAX_FILE_BYTES+1)
    if len(raw)>MAX_FILE_BYTES or hashlib.sha256(raw).hexdigest()!=SHA256:raise Invalid('pinned dataset bytes mismatch')
    metadata=[]
    # The pinned JSONL co-locates public/private fields. Parse mechanically, retain
    # only metadata; never inspect problem/answer/solution values for selection.
    for line in raw.decode('utf8').splitlines():
        if not line.strip():continue
        row=decode_response(line)
        metadata.append({'source_id':row['unique_id'],'subject':row['subject'],'level':row['level']})
    if len(metadata)!=500:raise Invalid('expected 500 records')
    original=_development_proposal([SimpleNamespace(**r) for r in metadata])
    if [r['source_id'] for r in original['development']]!=list(ORIGINAL_IDS):raise Invalid('original source order differs')
    return metadata


def cohort(metadata):
    additional=select(metadata);by_id={r['source_id']:r for r in metadata}
    ids=list(ORIGINAL_IDS)+[r['source_id'] for r in additional]
    rows=[]
    for index,source in enumerate(ids):
        rows.append({**by_id[source],'cohort_index':index,
                     'origin':'original_14' if index<14 else 'prospective_additional_12',
                     'source_status':'diagram_blocked' if source in DIAGRAM_IDS else 'pilot_statement_verified' if source in SMOKE else 'statement_access_and_attachment_review_pending',
                     'planner_status':'completed_historical_pilot_no_rerun' if source in SMOKE else 'blocked' if source in DIAGRAM_IDS else 'unrun',
                     'meaningful_task_count':None,'task_execution_allowed':False})
    result={'schema':'math500-complementary-screen-cohort-v1','status':'metadata_cohort_frozen_execution_disabled',
            'policy':POLICY,'policy_digest':digest(POLICY),'metadata_digest':digest(sorted(metadata,key=lambda r:r['source_id'])),
            'selected_source_ids':ids,'selected_count':26,'additional':additional,'questions':rows,
            'development_only':True,'prior_completed':3,'known_diagram_blocked':2,
            'maximum_text_eligible':24,'maximum_new_calls_if_all_remaining_text_eligible':21,
            'text_eligibility_verified':False,'heldout_overlap_review':'pending_new_cohort; no final heldout inferred',
            'remaining_unselected_count':len(metadata)-26,'historical_proposal_modified':False,
            'old_three_call_approval_reusable':False,'model_executed':False,'execution_allowed':False}
    result['cohort_digest']=digest(result)
    return result


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();args.output.mkdir(exist_ok=False)
    # Save the exact rule before reading the dataset or selecting any additions.
    write(args.output/'SELECTION_RULE.json',POLICY)
    start=time.process_time();wall=time.monotonic()
    report=cohort(read_metadata(args.data))
    write(args.output/'MATH500_SCREENING_COHORT.json',report)
    write(args.output/'metadata-accounting.json',{'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
        'ledger':'offline_metadata_selection_separate_from_model_usage','model_calls':0,'dataset_sha256':SHA256,
        'selection_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print(json.dumps({'report':str(args.output/'MATH500_SCREENING_COHORT.json'),
        **{k:report[k] for k in ('status','cohort_digest','selected_count','selected_source_ids','additional','maximum_new_calls_if_all_remaining_text_eligible','execution_allowed')}},indent=2))

if __name__=='__main__':main()
