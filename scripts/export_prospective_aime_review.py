#!/usr/bin/env python3
"""Export public statements for either frozen AIME 2025 block review; no keys or models."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from bc_phase2.joint_schema import require
from bc_phase2.model import digest
from bc_phase2.prospective_sources import faithful_identity,freeze
from freeze_prospective_aime import PINNED,read
from export_prospective_math_review import PUBLIC,comparisons
COHORTS={'aime2025':'f694e7676b808418156d909de2ad9a7ec1262793b658954c91ad2c0f84526894','aime2026':'d50880c52146d498db3e81f68eaf103c06fcc5852ed89efc5e7e5a97cf10b05d'}

def public_rows(path,expected):
    rows,h=read(path);require(h==expected,'pinned public file hash')
    require(type(rows)is list,'public row list')
    require(all(type(r)is dict and set(r)=={'id','problem'} and type(r['problem'])is str for r in rows),'statement-only fields')
    public={r['id']:r for r in rows};require(len(public)==len(rows),'unique public IDs')
    return public

def build(packet,converted,math_public,block=1):
    require(type(block) is int and block in (1,2),'frozen AIME block 1 or 2')
    require(packet['status']=='candidate_ids_frozen_family_review_pending','pending inventory')
    require(all(packet[k] is False for k in ('private_keys_read','model_executed','execution_allowed')),'disabled evidence')
    require([d['dataset'] for d in packet['datasets']]==list(COHORTS),'separate frozen years')
    public=public_rows(math_public,PUBLIC);historical=[];prior=[]
    for path,expected in packet['prior_config_hashes'].items():
        require(path in ('configs/phase2/prospective_math_block3_source_review_v1.json','configs/phase2/prospective_medqa_block3_source_review_v1.json'),'prior config path')
        _,h=read(ROOT/path);require(h==expected,'prior source review unchanged')
    require(len(packet['prior_config_hashes'])==2,'prior source reviews')
    math_review,_=read(ROOT/'configs/phase2/prospective_math_block3_source_review_v1.json')
    require(packet['historical_exposure']==math_review['exposure'],'original historical exposure')
    for r in packet['historical_exposure']['records']:
        if r['dataset']=='math500':
            sid=r['source_id'];require(faithful_identity(public[sid])==(r['exact_hash'],r['normalized_hash']),'historical identity')
            historical.append(sid)
    for label in ('math','medqa'):
        review,_=read(ROOT/f'configs/phase2/prospective_{label}_block3_source_review_v1.json')
        prior.extend(dict(r,dataset=review['cohort']['dataset']) for b in review['cohort']['blocks'] for r in b['records'])
    prospective_math=[r['source_id'] for r in prior if r['dataset']=='math500']
    aime_groups={}
    for d in packet['datasets']:
        year=int(d['dataset'][-4:]);revision,sha,policy=PINNED[year]
        require(d['public_sha256']==sha and d['procedure']['procedure_digest']==policy,'pinned source/procedure')
        require(digest({k:v for k,v in d['procedure'].items() if k!='procedure_digest'})==policy,'procedure integrity')
        require(d['family_review']['prior_selected']==prior,'prior candidate preservation')
        c=freeze(d['inventory'],d['dataset'],revision,packet['historical_exposure'],d['procedure'],d['family_review'])
        require(c==d['cohort'] and c['cohort_digest']==COHORTS[d['dataset']],'frozen candidate integrity')
        rows=public_rows(converted/str(year)/'source.public.json',sha)
        require(len(rows)==len(d['inventory'])==30 and set(rows)=={r['source_id'] for r in d['inventory']},'pinned inventory')
        for r in d['inventory']:
            require(faithful_identity(rows[r['source_id']])==(r['exact_hash'],r['normalized_hash']),'AIME public identity')
        public.update(rows)
        selected=[r for b in c['blocks'] for r in b['records']]
        aime_groups[d['dataset']]=[r['source_id'] for r in selected]
        prior.extend(dict(r,dataset=d['dataset']) for r in selected)
    targets=[r['source_id'] for r in packet['datasets'][0]['cohort']['blocks'][block-1]['records']]
    groups={};exported=set(targets);compared=set()
    # Reuse accepted lexical retrieval, independently for each frozen comparison pool.
    for name,ids in [('historical_math',historical),('prospective_math',prospective_math),*aime_groups.items()]:
        rows,_=comparisons(public,targets,ids,[])
        groups[name]=rows
        for sid in targets:
            compared.update(tuple(sorted((sid,other))) for other in ids if sid!=other)
        for row in rows:exported.update(r['source_id'] for r in row['nearest']['historical'])
    result=dict(purpose=f'Reviewer-only AIME 2025 block {block} family and text-sufficiency review; no solutions',
        cohort_digests=COHORTS,source_ids=targets,cards=[public[s] for s in targets],
        comparison_cards=[public[s] for s in sorted(exported-set(targets))],comparisons_by_pool=groups,
        unique_pairs_compared=len(compared),source_review_exposure_ids=sorted(exported),
        similarity_policy='Case-sensitive token-set Jaccard, numbers/operators retained; top three per pool, lexical ID ties. Retrieval only, not semantic clearance.',
        limitations=['No original contest sitting/number inference from release row or problem_idx.',
                    'Historical MATH and frozen MATH/AIME candidates only; no exhaustive semantic clearance.',
                    'MedQA prior identity exclusions retained; cross-domain semantic review not performed.',
                    'Missing attachments or credible family conflicts remain blocked without replacements.'],
        decisions=[],private_keys_read=False,model_executed=False,execution_allowed=False)
    result['packet_digest']=digest(result)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--block',type=int,choices=(1,2),default=1)
    p.add_argument('--inventory',type=Path,required=True)
    p.add_argument('--converted',type=Path,required=True)
    p.add_argument('--math-public',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();cpu=time.process_time();wall=time.monotonic();packet,h=read(a.inventory)
    result=build(packet,a.converted,a.math_public,a.block)
    result['export_resources']=dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall)
    result['inventory_file_sha256']=h
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(report=str(a.output),sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),primary_cards=len(result['cards']),comparison_cards=len(result['comparison_cards']),model_executed=False),indent=2))
if __name__=='__main__':main()
