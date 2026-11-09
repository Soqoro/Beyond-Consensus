#!/usr/bin/env python3
"""Approval-bound six-call diagnostic; preparation and help never load models."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))

def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare')
    for k in ('parent-release','export','qualification','cluster','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('approve')
    for k in ('manifest','approval','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('submit')
    for k in ('release','output'):a.add_argument('--'+k,type=Path,required=True)
    a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    from bc_phase2 import composite_derivation_launch as l
    from bc_phase2.joint_d1_release import read_evidence as read
    if args.command=='prepare':
        m=l.prepare(read(args.parent_release),args.export,read(args.qualification),read(args.cluster))
        args.output.mkdir(exist_ok=False);write(args.output/'manifest.disabled.json',m)
        write(args.output/'approval.pending.json',dict(schema='composite-derivation-approval-v1',scope_digest=m['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        print(json.dumps(dict(directory=str(args.output),scope_digest=m['scope_digest'],blockers=m['blockers'],limits=m['scope']['limits'],measured_reservation=m['scope']['cpu_qualification']['total_reservation_tokens'],execution_allowed=False),indent=2));return
    if args.command=='approve':result=l.approve(read(args.manifest),read(args.approval))
    elif args.command=='submit':result=l.submit(ROOT,read(args.release),dry_run=args.dry_run)
    else:
        result=l.run_allocated(ROOT,args.output);print(json.dumps({'status':result['status'],'totals':result['totals']}));return
    write(args.output,result);print(json.dumps({'report':str(args.output),'submitted':result.get('submitted',False)}))
if __name__=='__main__':main()
