#!/usr/bin/env python3
"""Prepare one reviewed prefix step, execute its approved recipe, or report receipts."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import two_regime_launch as launch, two_regime_results as results
from bc_phase2.joint_schema import require
from bc_phase2.model import digest

def write(path,value):
    with path.open('x') as f:
        json.dump(value,f,indent=2)
        f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    for command in ('review','prepare'):
        a=sub.add_parser(command)
        a.add_argument('--parent',required=True,type=Path,help='prior planner output containing manifest.json')
        a.add_argument('--cell',default='math500-n4-extra')
        a.add_argument('--history',type=Path,help='ordered completed prefix as JSON list')
        a.add_argument('--output',required=True,type=Path)
        if command=='review':
            a.add_argument('--measure',action='store_true',help='measure the next rendered request with the pinned local tokenizer')
        if command=='prepare':
            a.add_argument('--review',type=Path)
            a.add_argument('--alternatives',type=Path)
    for cmd,arg in [('approve','manifest'),('submit','release')]:
        a=sub.add_parser(cmd)
        a.add_argument('--'+arg,type=Path,required=True)
        a.add_argument('--output',type=Path,required=True)
        if cmd=='approve':
            a.add_argument('--approval',type=Path,required=True)
        else:
            a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated')
    a.add_argument('--output',required=True,type=Path)
    a=sub.add_parser('review-plan')
    a.add_argument('--run',type=Path,required=True)
    a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('report')
    a.add_argument('--run',action='append',default=[],type=Path)
    a.add_argument('--medqa-private',type=Path)
    a.add_argument('--math-judgments',type=Path,help='blinded review IDs mapped to true, false or null')
    a.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    if args.command in ('review','prepare'):
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
        signal.alarm(300)
        start=time.process_time()
        wall=time.monotonic()
        slot=launch.cell(args.cell)
        entries=launch.read(args.history) if args.history else []
        if args.command=='review':
            parent=launch.anchor(args.parent,slot['dataset'])
            public=launch.public_rows(parent,slot['dataset'])
            step,overhead=launch.history(slot,public,entries)
            packet=launch.review_card(slot,step['source_id'],public) if step['status']=='next_candidate' else step
            measurement=launch.preview(parent,slot,packet) if args.measure and step['status']=='next_candidate' else None
            write(args.output,dict(step=step['status'],packet=packet,planning_overhead=overhead,measurement=measurement,
                                   cpu_seconds=time.process_time()-start,wall_seconds=time.monotonic()-wall))
        else:
            partition=launch.base.cluster.command(['scontrol','show','partition','HPCAIq','-o'])
            m=launch.prepare(args.parent,slot,entries,launch.read(args.review) if args.review else None,
                             launch.read(args.alternatives) if args.alternatives else [],args.output,partition)
            args.output.mkdir(exist_ok=False)
            write(args.output/'manifest.disabled.json',m)
            s=m['scope']
            a=dict(schema=s['key']+'-approval',scope_digest=m['scope_digest'],decision='pending',reviewer=None,reviewed_at=None)
            flags=('source_worker_transmission','contract_accepted','gpu_recipe_authorized') if 'wave' in s else ('statement_transmission_authorized','GPU_spending_authorized')
            if 'wave' not in s and s['family_review'] is None:
                pub=launch.public_rows({'source_package':s['source_package']},slot['dataset'])
                card=launch.review_card(slot,s['source_ids'][0],pub)
                write(args.output/'source-review.json',card)
                a['family_review']=dict(card_digest=card['card_digest'],decision='pending',reviewer=None,rationale=None)
            write(args.output/'approval.pending.json',dict(a,**dict.fromkeys(flags,False)))
            write(args.output/'preparation.json',dict(scope_digest=m['scope_digest'],source_ids=s['source_ids'],
                limits=s['limits'],verified_requests=s['verified_requests'],execution_allowed=False,
                cpu_seconds=time.process_time()-start,wall_seconds=time.monotonic()-wall))
    elif args.command=='review-plan':
        v=launch.read(args.run/'manifest.json')['release']
        s=v['manifest']['scope']
        require('wave' not in s and s['key']==launch.key(launch.cell(s['cell']),s['source_ids'][0]),'campaign planner result')
        r=launch.read(args.run/'execution/result.json')
        row,=r['rows']
        sid=row['source_id']
        pub=launch.Stage(s).source_records(s)[sid]
        template=dict(decision='admitted',reviewer=None,reviewer_kind=None,reviewed_at=None,
                      public_digest=digest(pub),plan_digest=digest(row.get('raw_response')),
                      substantive_no_answer_leakage=False,tasks=[],outputs=[])
        entry=dict(source_id=sid,family_review=v['approval'].get('family_review',s['family_review']),
                   run=str(args.run.resolve()),decision='review_unresolved',rationale='',contract=template)
        write(args.output,dict(source=pub,row=row,totals=r['totals'],scope_digest=v['manifest']['scope_digest'],
                               previous_prefix=s['history'],entry_for_review=entry))
    elif args.command=='approve':
        m=launch.read(args.manifest)
        write(args.output,launch.Stage(m['scope']).approve(m,launch.read(args.approval)))
    elif args.command=='submit':
        v=launch.read(args.release)
        require(not args.output.exists(),'receipt already exists')
        write(args.output,launch.base.submit(ROOT,v,dry_run=args.dry_run,protocol=launch.Stage(v['manifest']['scope'])))
    elif args.command=='run-allocated':
        m=launch.read(ROOT/'resolved/manifest.json')['release']['manifest']
        r=launch.base.run_allocated(ROOT,args.output,protocol=launch.Stage(m['scope']))
        print(json.dumps(dict(status=r['status'],totals=r['totals'])))
    else:
        rows=results.pending()
        for run in args.run:
            m=launch.read(run/'manifest.json')['release']['manifest']
            s=m['scope']
            require(digest(s)==m['scope_digest'] and s['cell'] in rows and rows[s['cell']]['status']=='reserved_unrun','unique current scope')
            require(s.get('wave',{}).get('condition')==launch.grid.CAMPAIGN,'two-regime worker run')
            path=run/'execution/result.json'
            if not path.is_file():
                path=run/'execution/wave-result.json'
            result=launch.read(path) if path.exists() else {}
            if not result.get('conditions'):
                failure=run/'execution/failure.json'
                evidence=launch.read(failure) if failure.exists() else result
                rows[s['cell']].update(status='halted' if failure.exists() else result.get('status','unrun'),
                                      source_ids=s['source_ids'],worker=evidence.get('totals'),
                                      failure=evidence.get('error_type'),evidence=str(run.resolve()))
                continue
            grade=lambda sid,item:None
            grading='pending'
            if s['cell'].startswith('medqa-') and args.medqa_private:
                require(launch.local.file_hash(args.medqa_private)=='8cb9e441d0a0ae52c8114197a26490b8e81a15a80407e99601ebdf4058997778','pinned evaluator')
                keys=launch.read(args.medqa_private)
                if isinstance(keys,list):
                    keys={x['id']:x for x in keys}
                pub=launch.Stage(s).source_records(s)
                def grade(sid,item):
                    assessment=launch.pipeline.adapters.medqa.grade(item['value'],keys[sid],pub[sid])
                    return False if assessment['status']=='structurally_invalid' else assessment['correct']
                grading='private_key_agreement'
            elif s['cell'].startswith('math500-') and args.math_judgments:
                judgments=launch.read(args.math_judgments)
                require(judgments['kind'] in ('AI-assisted','human') and judgments['reviewer'].strip(),'review provenance')
                known=judgments['artifacts']
                require(all(v is None or type(v) is bool for v in known.values()),'resolved or pending judgments')
                grade=lambda sid,item:known.get(digest([sid,item['value']]))
                grading=judgments['kind']
            rows[s['cell']]=dict(results.summarize(s,result,grade),grading=grading,evidence=str(run.resolve()))
        args.output.mkdir(exist_ok=False)
        write(args.output/'cells.json',list(rows.values()))
        (args.output/'RESULTS.md').write_text(results.table(list(rows.values())))
    if args.command!='run-allocated':
        print(args.output)

if __name__=='__main__':
    main()
