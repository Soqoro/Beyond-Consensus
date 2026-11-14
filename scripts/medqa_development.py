#!/usr/bin/env python3
"""Offline, explicitly local MedQA intake/review/grading. Never dispatches models."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import medqa_development as m
from bc_phase2.joint_schema import require

def read(p):
    raw=p.read_bytes();require(len(raw)<=64*1024*1024,'bounded local JSON');return json.loads(raw)
def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('intake')
    for k in ('source','provenance','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('reviewed-wave')
    for k in ('cohort','plans','reviews','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('grade')
    for k in ('public','protected','response','output'):a.add_argument('--'+k,type=Path,required=True)
    args=p.parse_args()
    if args.command=='intake':
        provenance=read(args.provenance);require(provenance.get('read_authorized') is True,'source read not authorized')
        cohort,private=m.intake(args.source.read_bytes(),provenance);args.output.mkdir(exist_ok=False)
        write(args.output/'cohort.public.json',cohort);write(args.output/'evaluator.private.json',private)
        write(args.output/'requests.public.json',[m.planner_request(r) for r in cohort['records']])
        write(args.output/'planning.disabled.json',dict(cohort_digest=cohort['cohort_digest'],limits=m.PLAN_LIMITS,execution_allowed=False,remaining=['exact source/model/tokenizer/scheduler binding and planning approval','human contract review before worker release']))
        print(json.dumps({k:cohort[k] for k in ('status','cohort_digest','selected_count','eligible_count')}));return
    if args.command=='reviewed-wave':
        cohort=read(args.cohort);plans=read(args.plans);reviews=read(args.reviews)
        require(cohort['cohort_digest']==m.digest({k:v for k,v in cohort.items() if k!='cohort_digest'}),'cohort binding')
        require(plans['cohort_digest']==reviews['cohort_digest']==cohort['cohort_digest'],'review batch binding')
        decisions=reviews['rows'];require(len(decisions)==12 and len({r['source_id'] for r in decisions})==12,'one complete review batch; retain rejection')
        publics={r['id']:r for r in cohort['records']};raw={r['source_id']:r for r in plans['rows']}
        require(set(raw)==set(publics)=={r['source_id'] for r in decisions},'same frozen source IDs')
        cs=[m.admit(publics[r['source_id']],raw[r['source_id']],r) for r in decisions if r['decision']=='admitted']
        wave=m.freeze_bundles(cs);write(args.output,wave);print(json.dumps(dict(wave_id=wave['wave_id'],bundles=len(wave['bundles']),limits=wave['limits'],execution_allowed=False)));return
    result=m.grade(args.response.read_text(),read(args.protected),read(args.public));write(args.output,result);print(json.dumps(result))
if __name__=='__main__':main()
