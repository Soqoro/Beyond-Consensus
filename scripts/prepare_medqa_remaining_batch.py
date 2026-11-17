#!/usr/bin/env python3
"""Prepare one bounded remaining-MedQA campaign proposal; never approve or dispatch."""
import argparse,hashlib,json,re,sys,time
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_medqa_block2_launch as planner
from bc_phase2 import prospective_medqa_block2_worker_launch as worker
from bc_phase2 import prospective_sources as sources, prospective_pipeline as pipeline
from bc_phase2.model import digest
from bc_phase2.joint_schema import require

HISTORICAL_HASH='c38c5fd2b9b4d5661810fe4eac0f267490244ccdbe6ac6d1a360fa8ce16edb4b'

def read_public(path,expected):
    with Path(path).open('rb') as f:raw=f.read(4*1024*1024+1)
    require(len(raw)<=4*1024*1024 and hashlib.sha256(raw).hexdigest()==expected,'public file hash/size')
    return json.loads(raw)

def token_set(r):
    return set(re.findall(r'\d+(?:\.\d+)?|[A-Za-z]+|[^\sA-Za-z\d]',r['question']+'\n'+'\n'.join(r['options'][k] for k in 'ABCD')))

def review_packet(public,historical,c):
    # Historical intake is a public envelope in the original frozen export.
    if isinstance(historical,dict):
        historical=historical.get('records',historical.get('sources'))
    require(isinstance(public,list) and isinstance(historical,list),'public record lists')
    require(len(public)==1273 and len(historical)==12,'pinned pool/cohort counts')
    allrows=public+historical
    for r in allrows:
        require(set(r)=={'id','question','options'},'public fields only')
        pipeline.adapters.medqa.assert_public(r)
    by={r['id']:r for r in allrows};require(len(by)==1285,'unique public source IDs')
    selected=[r for b in c['blocks'] for r in b['records']]
    for r in selected:
        require(sources.faithful_identity(by[r['source_id']])==(r['exact_hash'],r['normalized_hash']),'prospective source identity')
    exp=json.loads((ROOT/planner.CONFIG).read_text())['exposure']['records']
    for r in exp:
        if r['dataset']=='medqa':require(sources.faithful_identity(by[r['source_id']])==(r['exact_hash'],r['normalized_hash']),'historical exposure identity')
    target=[r['source_id'] for r in c['blocks'][2]['records']]
    prior=[r['id'] for r in historical];prospective=[r['source_id'] for r in selected]
    sets={sid:token_set(by[sid]) for sid in set(prior+prospective)}
    comparisons=[];pairs=set();exported=set(target)
    for sid in target:
        nearest={}
        for label,ids,n in [('historical',prior,3),('prospective',prospective,2)]:
            ranking=[]
            for other in ids:
                if other==sid:continue
                pairs.add(tuple(sorted((sid,other))))
                union=sets[sid]|sets[other]
                ranking.append((Fraction(len(sets[sid]&sets[other]),len(union)) if union else Fraction(0),other))
            ranking.sort(key=lambda x:(-x[0],x[1]))
            nearest[label]=[dict(source_id=other,token_jaccard=str(score)) for score,other in ranking[:n]]
            exported.update(row['source_id'] for row in nearest[label])
        comparisons.append(dict(source_id=sid,nearest=nearest))
    packet=dict(purpose='Reviewer-only MedQA block 3 family and text-sufficiency review',block=3,
        cohort_digest=c['cohort_digest'],procedure_digest=c['procedure_digest'],source_ids=target,
        frozen_blocks=[dict(slot=b['slot'],source_ids=[r['source_id'] for r in b['records']]) for b in c['blocks']],
        cards=[by[sid] for sid in target],comparison_cards=[dict(by[sid],role='historical' if sid in prior else 'other_frozen_prospective') for sid in sorted(exported-set(target))],
        comparisons=comparisons,unique_pairs_compared=len(pairs),source_review_exposure_ids=sorted(exported),
        private_keys_read=False,model_executed=False,execution_allowed=False)
    packet['packet_digest']=digest(packet);return packet

def proposal(manifest,review):
    s=worker.validate_manifest(manifest)
    require(not manifest['blockers'],'worker preparation blockers')
    require(review['packet_digest']==digest({k:v for k,v in review.items() if k!='packet_digest'}),'review packet integrity')
    c=planner.cohort();ids=[r['source_id'] for r in c['blocks'][2]['records']]
    require(review['source_ids']==ids and review['cohort_digest']==c['cohort_digest'],'frozen review scope')
    stages=[dict(stage='block2_worker',scope_digest=manifest['scope_digest'],source_ids=s['wave']['bundles'][0]['sources'],maximum_calls=38,token_cap=622592,wall_seconds=14400,status='bound_disabled'),
            dict(stage='block3_planner',source_ids=ids,maximum_calls=8,token_cap=131072,wall_seconds=3600,status='source_review_and_binding_pending'),
            dict(stage='block3_worker',candidate_source_ids=ids,maximum_calls=88,profile_calls=8,evaluation_calls=80,token_cap=1441792,wall_seconds=14400,status='planner_contract_review_and_binding_pending')]
    value=dict(schema='remaining-medqa-campaign-proposal-v1',procedure_digest=c['procedure_digest'],cohort_digest=c['cohort_digest'],
        model=s['model'],source_package=s['source_package'],block3_review_packet_digest=review['packet_digest'],stages=stages,
        total_limits=dict(maximum_calls=134,token_cap=2195456,allocated_wall_seconds=32400,maximum_submissions=3,concurrent_campaign_jobs=1,
            physical_gpus_per_job=1,maximum_user_gpus=4,cpus_per_job=4,host_memory_gb_per_job=128,minimum_vram_bytes=80000000000,
            input_cap=13312,output_cap=3072,context=16384,solver_seconds_per_pair=30,solver_threads=1,solver_seed=0),
        review_delegation_proposed='AI-assisted source/contract review under frozen procedure; derived exact stage manifests retained. No new approval for compliant transitions after explicit campaign consent.',
        restrictions=['Exactly NEUTRAL versus JOINT; n=4 K=2 mean-first all-owner R0.',
            'At most one pair per block; no replacements, retries, additional planner calls or cross-block recycling.',
            'Blocked block2 rows 233 and 874 stay blocked; block1 and historical results unchanged.',
            'Fixed MedQA base task mode and direct-parent communication; no new A/C alternatives.',
            'Freeze each neutral before profiling; no price/outcome-informed admission or prompt changes.',
            'No private keys in planning or workers; offline grading only.',
            'Stop on uncertain accounting/dispatch, integrity failure or exhausted caps; no batch self-submission.'],
        remaining=['Review block3 source packet before its planner dispatch.','Bind block3 planner and derived worker manifests to unchanged scientific procedure and stage ceilings.','Explicit single campaign approval of final scope including review delegation.'],
        execution_allowed=False,model_executed=False,submitted=False)
    value['proposal_digest']=digest(value);return value

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('worker-manifest','public','historical-public','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();cpu=time.process_time();wall=time.monotonic()
    c=planner.cohort();review=review_packet(read_public(a.public,planner.PUBLIC_HASH),read_public(a.historical_public,HISTORICAL_HASH),c)
    value=proposal(worker.read(a.worker_manifest),review)
    a.output.mkdir(exist_ok=False)
    for name,obj in [('CAMPAIGN_PROPOSAL.disabled.json',value),('block3-source-review.json',review),('preparation-resources.json',dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,model_executed=False))]:
        with (a.output/name).open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
    print(json.dumps(dict(directory=str(a.output),proposal_digest=value['proposal_digest'],stages=value['stages'],limits=value['total_limits'],execution_allowed=False),indent=2))
if __name__=='__main__':main()
