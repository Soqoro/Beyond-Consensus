#!/usr/bin/env python3
"""Freeze pinned AIME candidate IDs with family review pending; no keys, network or models."""
import argparse,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_sources as sources,prospective_pipeline as pipeline
from bc_phase2.model import digest
from bc_phase2.joint_schema import require
PINNED={2025:('c94da77eb22bbd6439e62a323bec18493a421302','ae23ae32a86157958d6d22b88e2a495bca7d9c9c072f6a01fecde92bd19015d2','2dab4e8b3f0928b780257ec6651ae22e1a4205b3a4af004392fc70ffa2e2b2cf'),2026:('d61f486805306e6e6b5913504c07763a99e1b112','d5a1cb06d9a14b757e098aac3b46818b6fe29ed1a89c36015b8d1b0fc4a66cc6','6167d81357e094dffe1385a4f29b5100d0a450ab81e3b2a7ade4a469c337b4f9')}

def read(path):
    with path.open('rb') as f:raw=f.read(4*1024*1024+1)
    require(len(raw)<=4*1024*1024,'bounded source/config file')
    return json.loads(raw),hashlib.sha256(raw).hexdigest()

def prepare(converted):
    cpu=time.process_time();started=datetime.now(timezone.utc).isoformat();hashes={};prior=[]
    reviews={}
    for label,dataset in [('math','math500'),('medqa','medqa')]:
        path=ROOT/f'configs/phase2/prospective_{label}_block3_source_review_v1.json'
        review,h=read(path);hashes[str(path.relative_to(ROOT))]=h
        require(review['review_bundle_digest']==digest({k:v for k,v in review.items() if k!='review_bundle_digest'}),'prior review integrity')
        cohort=review['cohort'];require(cohort['cohort_digest']==digest({k:v for k,v in cohort.items() if k!='cohort_digest'}),'prior cohort integrity')
        reviews[label]=review
        prior.extend(dict(r,dataset=dataset) for b in cohort['blocks'] for r in b['records'])
    # Use the enriched historical record identities, preserve the original cutoff.
    exposure=reviews['math']['exposure']
    datasets=[]
    for year,(revision,sha,policy) in PINNED.items():
        dataset=f'aime{year}';path=converted/str(year)/'source.public.json';public,h=read(path)
        require(h==sha,'pinned public source hash')
        require(type(public) is list and len(public)==30,'pinned source count')
        records=[]
        for i,row in enumerate(public,1):
            require(set(row)=={'id','problem'} and row['id']==f'aime/{year}/{revision}/row/{i}','public fields/year/release/row identity')
            exact,normal=sources.faithful_identity(row)
            records.append(dict(source_id=row['id'],canonical_id=dataset+':'+row['id'],exact_hash=exact,normalized_hash=normal,family_id='',status='eligible'))
        proc=pipeline.procedure(dataset);require(proc['procedure_digest']==policy,'converted procedure unchanged')
        family=dict(dataset=dataset,revision=revision,inventory_digest=digest(records),reviewer='offline preparation; semantic review NOT performed',reviewer_kind='automated_metadata_only',reviewed_at=started,decisions={},prior_selected=list(prior),limitations=['All selected family decisions pending; no semantic clearance implied.','Exact and whitespace-normalized comparisons only. Historical evidence coverage is limited to recorded inventories.'])
        cohort=sources.freeze(records,dataset,revision,exposure,proc,family)
        selected=[r for b in cohort['blocks'] for r in b['records']]
        require(all(r['status']=='blocked' and r['family_review']=='pending' for r in selected),'pending sources cannot dispatch')
        datasets.append(dict(dataset=dataset,public_path=str(path),public_sha256=h,inventory=records,procedure=proc,family_review=family,cohort=cohort))
        prior.extend(dict(r,dataset=dataset) for r in selected)
    return dict(status='candidate_ids_frozen_family_review_pending',datasets=datasets,historical_exposure=exposure,prior_config_hashes=hashes,cpu_seconds=time.process_time()-cpu,private_keys_read=False,model_executed=False,execution_allowed=False,limitations=['No AIME statements exported by this metadata packet.','Previously blocked and unsupported MATH/MedQA candidates remain in prior-cohort comparison set.','Unresolved source families and attachments require statement-only review before planning.','Missing original sitting IDs remain unknown; no row-order inference.'])

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--converted',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=prepare(a.converted);a.output.mkdir(exist_ok=False)
    def save(name,value):
        with (a.output/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    save('inventory-and-cohorts.json',report)
    for d in report['datasets']:
        for kind in ('cohort','family_review','procedure'):save(d['dataset']+'.'+kind+'.json',d[kind])
    summary=dict(status=report['status'],directory=str(a.output),datasets=[dict(dataset=d['dataset'],cohort_digest=d['cohort']['cohort_digest'],procedure_digest=d['procedure']['procedure_digest'],selected_count=sum(len(b['records']) for b in d['cohort']['blocks']),excluded_count=len(d['cohort']['excluded']),reserved_count=len(d['cohort']['reserved_ids']),blocks=[dict(slot=b['slot'],source_ids=[r['source_id'] for r in b['records']]) for b in d['cohort']['blocks']]) for d in report['datasets']],cpu_seconds=report['cpu_seconds'],private_keys_read=False,model_executed=False,execution_allowed=False)
    save('summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
