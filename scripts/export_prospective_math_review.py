#!/usr/bin/env python3
"""Read-only, statement-only family review export for a selected frozen MATH block.

No model, network, reference answer, admission or cohort replacement.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.model import digest
from bc_phase2.joint_schema import require
from bc_phase2.prospective_sources import faithful_identity,freeze

INVENTORY='9d8dc3eb403b4519d737242a8008cf557fa48d191374930ba0c8ebb2dc357fb5'
PROCEDURE='6b9e50c64b3809139cf1dfabb2a58a0a829c4fb903788460cd55eaa8ae61981c'
COHORT='af4de0e7d23e9147c0117659169b3d329d65cf50f29d9b533aec6760e60672c5'
PUBLIC='b7ebe540f9c4b91d5bcf07b4e797f1de405982e748be3162721aaf3dfe82e5dd'
REVISION='6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be'

def tokens(text):
    # Numbers, operators and case are retained. No numeric masking or solutions.
    return set(re.findall(r'\d+(?:\.\d+)?|[A-Za-z]+|[^\sA-Za-z\d]',text))

def comparisons(public, targets, historical, prospective):
    """Rank similarities only; no threshold is a semantic clearance decision."""
    sets={sid:tokens(r['problem']) for sid,r in public.items()}
    rows=[];compared=set()
    for sid in targets:
        groups={}
        for name,ids,limit in (('historical',historical,3),('prospective',prospective,2)):
            ranked=[]
            for other in ids:
                if other==sid:continue
                compared.add(tuple(sorted((sid,other))))
                union=sets[sid]|sets[other]
                score=Fraction(len(sets[sid]&sets[other]),len(union)) if union else Fraction(0)
                ranked.append((score,other))
            ranked.sort(key=lambda r:(-r[0],r[1]))
            groups[name]=[dict(source_id=other,token_jaccard=str(score)) for score,other in ranked[:limit]]
        rows.append(dict(source_id=sid,nearest=groups))
    return rows,len(compared)

def export(inv,public_raw,exposure,block=1):
    require(type(block) is int and 1<=block<=3,'frozen block 1..3')
    require(inv['dataset']=='math500' and inv['revision']==REVISION,'pinned dataset')
    require(digest(inv['records'])==INVENTORY and len(inv['records'])==500,'received inventory')
    proc=inv['procedure']
    require(proc['procedure_digest']==PROCEDURE==digest({k:v for k,v in proc.items() if k!='procedure_digest'}),'frozen procedure')
    require(inv['access_receipt']['read_authorized'] is True,'local source access')
    require(hashlib.sha256(public_raw).hexdigest()==PUBLIC==inv['access_receipt']['sha256'],'public extraction bytes')
    require(len(public_raw)<=4*1024*1024,'bounded public extraction')
    records=json.loads(public_raw);require(type(records)is list and len(records)==500,'public record count')
    public={r['id']:r for r in records};require(len(public)==500,'unique source IDs')
    by={r['source_id']:r for r in inv['records']}
    require(set(public)==set(by),'same public identities')
    for sid,row in public.items():
        require(set(row)=={'id','problem'},'no protected fields in export input')
        require(faithful_identity(row)==(by[sid]['exact_hash'],by[sid]['normalized_hash']),'statement hashes')
    exp=deepcopy(exposure)
    historical=[]
    for row in exp['records']:
        if row['dataset']=='math500':
            sid=row['source_id'];historical.append(sid)
            for k in ('canonical_id','exact_hash','normalized_hash'):row[k]=by[sid][k]
    require(len(historical)==len(set(historical))==64,'frozen historical exclusions')
    review=dict(dataset='math500',revision=REVISION,inventory_digest=INVENTORY,
        reviewer='Codex metadata audit; not semantic family clearance',reviewed_at='2026-11-15',decisions={},prior_selected=[])
    cohort=freeze(inv['records'],'math500',REVISION,exp,proc,review)
    require(cohort['cohort_digest']==COHORT,'candidate blocks unchanged')
    ids=[r['source_id'] for b in cohort['blocks'] for r in b['records']]
    first=[r['source_id'] for r in cohort['blocks'][block-1]['records']]
    pairs,count=comparisons(public,first,historical,ids)
    exported=set(first)
    for row in pairs:
        for group in row['nearest'].values():exported.update(r['source_id'] for r in group)
    value=dict(purpose='Reviewer-only source family and text-sufficiency review; no solutions',
        inventory_digest=INVENTORY,procedure_digest=PROCEDURE,cohort_digest=COHORT,
        public_file_sha256=PUBLIC,block=block,source_ids=first,
        frozen_blocks=[dict(slot=b['slot'],source_ids=[r['source_id'] for r in b['records']]) for b in cohort['blocks']],
        cards=[public[sid] for sid in first],comparison_cards=[dict(public[sid],role='historical' if sid in historical else 'other_frozen_prospective') for sid in sorted(exported-set(first))],
        comparisons=pairs,unique_pairs_compared=count,
        similarity_policy=('case-sensitive token-set Jaccard; retain numbers/operators; top 3 historical and top 2 prospective per block-one source; lexical tie by ID' if block==1 else f'case-sensitive token-set Jaccard; retain numbers/operators; top 3 historical and top 2 prospective per block-{block} source; lexical tie by ID'),
        source_review_exposure_ids=sorted(exported),
        limitations=['Similarity is retrieval support, not proof of semantic disjointness.',
                     'Only named historical exclusions and frozen prospective candidates compared; no global family clearance.',
                     'Comparison-card inspection is reviewer exposure, not a planner invocation.',
                     'Unknown diagrams/attachments and credible family conflicts remain blocked; no replacement.'],
        decisions=[],execution_allowed=False,model_executed=False,private_keys_read=False)
    value['packet_digest']=digest(value)
    return value

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preparation',required=True,type=Path)
    ap.add_argument('--output',required=True,type=Path)
    ap.add_argument('--block',type=int,choices=(1,2,3),default=1)
    args=ap.parse_args();start=time.process_time();wall=time.monotonic()
    inv=json.loads((args.preparation/'inventory.json').read_text())
    exposure=json.loads((ROOT/'configs/phase2/prospective_exposure_v1.json').read_text())
    value=export(inv,(args.preparation/'math.public.json').read_bytes(),exposure,args.block)
    value['export_resources']=dict(cpu_seconds=time.process_time()-start,wall_seconds=time.monotonic()-wall)
    with args.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(dict(report=str(args.output),sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
        primary_cards=len(value['cards']),comparison_cards=len(value['comparison_cards']),unique_pairs_compared=value['unique_pairs_compared'],
        model_executed=False,execution_allowed=False),indent=2))
if __name__=='__main__':main()
