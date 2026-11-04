#!/usr/bin/env python3
"""Frozen-cohort statement-only extraction and local-tokenizer fit; no inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
import prepare_math500_screening_cohort as selection
from bc_phase2 import d1_natural_screen as screen
from bc_phase2.joint_d1_release import read_evidence
from bc_phase2.joint_schema import require
from bc_phase2.model import digest,Invalid
from bc_phase2.response_boundary import decode_response

COHORT_DIGEST='069667602f25dbb547e4bb09651831c62763826cf0f25bb3b2689948a2dafe15'
FLAGS={
    'asy_markup':r'\[\s*/?asy\s*\]',
    'latex_figure':r'\\(?:includegraphics|begin\{(?:tikzpicture|picture|figure)\})',
    'image_markup':r'!\[[^\]]*\]\(|<img\b',
    'external_reference':r'https?://',
    'diagram_reference':r'\b(?:diagram|figure|pictured|shown\s+(?:below|above)|following\s+(?:graph|picture))\b',
}


def project(raw,ids):
    """Only ID/problem survives projection. Never use gold fields for selection/review."""
    found={}
    for line in raw.decode('utf8').splitlines():
        if not line.strip():continue
        row=decode_response(line)
        source=row.get('unique_id')
        if source not in ids:continue
        require(source not in found,'duplicate selected source')
        problem=row.get('problem')
        require(type(problem) is str and problem.strip(),'missing selected statement')
        found[source]={'id':source,'problem':problem}
    require(set(found)==set(ids),'selected source missing')
    return [found[source] for source in ids]


def attachment_flags(problem):
    return [name for name,pattern in FLAGS.items() if re.search(pattern,problem,re.I)]


def measure(records,tokenizer,template_hash):
    output=[]
    for row in records:
        require(set(row)=={'id','problem'},'statement-only view')
        flags=attachment_flags(row['problem'])
        entry={'source_id':row['id'],'statement_sha256':hashlib.sha256(row['problem'].encode()).hexdigest(),
               'attachment_flags':flags,'attachment_review':'pending','execution_allowed':False}
        if flags:
            entry.update(status='attachment_review_required_not_rendered',input_tokens=None,reserved_tokens=None)
        else:
            req=screen.request(row)
            try:
                rendered=screen.render_request(tokenizer,req,template_hash)
            except Invalid as exc:
                entry.update(status='render_rejected_no_truncation',error=str(exc),input_tokens=None,reserved_tokens=None)
            else:
                entry.update(status='rendered_fit_observed_attachment_review_pending',
                    payload_digest=req['payload_digest'],rendered_ids_digest=rendered['rendered_ids_digest'],
                    input_tokens=rendered['input_tokens'],reserved_tokens=rendered['input_tokens']+screen.OUTPUT,
                    output_cap=screen.OUTPUT)
        output.append(entry)
    return output


def prepare(data,cohort_path,snapshot,output):
    start=time.process_time();wall=time.monotonic()
    cohort_hash=hashlib.sha256(Path(cohort_path).read_bytes()).hexdigest()
    cohort=read_evidence(cohort_path)
    require(hashlib.sha256(Path(cohort_path).read_bytes()).hexdigest()==cohort_hash,'cohort changed while reading')
    require(cohort.get('cohort_digest')==COHORT_DIGEST,'only the frozen 26-source cohort')
    # Reuse the existing selector to verify every candidate and the complete digest.
    expected=selection.cohort(selection.read_metadata(data))
    require(cohort==expected,'cohort/ranking/metadata changed')
    with Path(data).open('rb') as f:raw=f.read(selection.MAX_FILE_BYTES+1)
    require(hashlib.sha256(raw).hexdigest()==selection.SHA256,'dataset changed during preparation')
    ids=[s for s in cohort['selected_source_ids'] if s not in selection.SMOKE and s not in selection.DIAGRAM_IDS]
    require(len(ids)==21,'exact remaining selected questions')
    records=project(raw,ids)
    output.mkdir(exist_ok=False)
    with (output/'statements.review-only.json').open('x') as f:
        json.dump(records,f,ensure_ascii=False,indent=2);f.write('\n')
    # Existing inspector enforces local-only metadata hashes, no weights/network,
    # and actual non-thinking support. A second local tokenizer instance is used
    # solely to render the remaining views; there is no model transport.
    from prepare_d1_natural_screen import inspect_tokenizer
    inspected=inspect_tokenizer(snapshot)
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==inspected['template_check'],'tokenizer/template changed')
    rows=measure(records,tokenizer,inspected['template_check']['template_hash'])
    # Recheck metadata after rendering without reading any weight bytes.
    require(all(hashlib.sha256((snapshot/name).read_bytes()).hexdigest()==meta['sha256']
                for name,meta in inspected['files'].items()),'tokenizer metadata changed')
    statement_bytes=(output/'statements.review-only.json').read_bytes()
    require(json.loads(statement_bytes)==records,'statement export changed')
    require(hashlib.sha256(Path(cohort_path).read_bytes()).hexdigest()==cohort_hash,'cohort changed during preparation')
    report={'schema':'math500-screening-input-preparation-v1','status':'prepared_review_pending',
            'cohort_digest':COHORT_DIGEST,'dataset_sha256':selection.SHA256,
            'cohort_file_sha256':cohort_hash,
            'source_access_basis':'user-authorized preparation of fixed selected cohort; not live transmission approval',
            'statement_file':str((output/'statements.review-only.json').resolve()),
            'statement_file_sha256':hashlib.sha256(statement_bytes).hexdigest(),
            'prepared_source_ids':ids,'historical_completed_no_rerun':list(selection.SMOKE),
            'known_diagram_blocked_retained':sorted(selection.DIAGRAM_IDS),
            'model_binding':inspected,'rows':rows,
            'potential_calls_after_attachment_and_scope_review':sum(r['input_tokens'] is not None for r in rows),
            'observed_reservation_sum_for_rendered_rows':sum(r['reserved_tokens'] or 0 for r in rows),
            'attachment_heuristics_are_not_semantic_clearance':True,
            'source_family_flags':[{'source_ids':['test/precalculus/190.json','test/precalculus/697.json'],
                                   'status':'prior_candidate_relation_unresolved_both_retained'}],
            'remaining':['attachment/text-eligibility review','exact additional-call resource and scheduler scope',
                         'explicit expanded D1 source-transmission/GPU approval'],
            'cpu_seconds':time.process_time()-start,'wall_seconds':time.monotonic()-wall,
            'accounting':'offline source/tokenizer preparation, not model usage',
            'model_calls':0,'model_executed':False,'execution_allowed':False,'D2_D6_enabled':False,
            'implementation':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
                'scripts/prepare_math500_screening_inputs.py','scripts/prepare_math500_screening_cohort.py',
                'scripts/prepare_d1_natural_screen.py')},
            'review_notes_are_not_planner_inputs':True}
    selection.write(output/'preparation.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('data','cohort','snapshot','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=prepare(a.data,a.cohort,a.snapshot,a.output)
    print(json.dumps({'report':str(a.output/'preparation.json'),**{k:r[k] for k in (
        'status','cohort_digest','statement_file','statement_file_sha256','rows',
        'potential_calls_after_attachment_and_scope_review','observed_reservation_sum_for_rendered_rows',
        'cpu_seconds','wall_seconds','model_executed','execution_allowed','remaining')}},indent=2))

if __name__=='__main__':main()
