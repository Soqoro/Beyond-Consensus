#!/usr/bin/env python3
"""Exact fresh-profile derivation-first wave; preparation never dispatches."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import composite_common_derivation_launch as launch
from bc_phase2.joint_d1_release import read_evidence

def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare')
    for name in ('parent-run','cluster','qualification','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('approve')
    for name in ('manifest','approval','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('submit')
    for name in ('release','output'):a.add_argument('--'+name,type=Path,required=True)
    a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.command=='prepare':
        result=launch.prepare(read_evidence(args.parent_run/'manifest.json')['release'],read_evidence(args.cluster),read_evidence(args.qualification))
        args.output.mkdir(exist_ok=False);write(args.output/'MANIFEST.disabled.json',result)
        write(args.output/'approval.pending.json',dict(schema=launch.KEY+'-approval',scope_digest=result['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        summary=dict(directory=str(args.output),scope_digest=result['scope_digest'],blockers=result['blockers'],limits=result['scope']['limits'],fresh_profile_calls=16,reused_profiles=0,execution_allowed=False)
        write(args.output/'summary.json',summary);print(json.dumps(summary,indent=2));return
    if args.command=='approve':result=launch.approve(read_evidence(args.manifest),read_evidence(args.approval))
    elif args.command=='submit':result=launch.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
    else:
        result=launch.run_allocated(ROOT,args.output);print(json.dumps({k:result.get(k) for k in ('status','totals')}));return
    write(args.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
