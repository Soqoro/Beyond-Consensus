#!/usr/bin/env python3
"""Reconcile 1117531 and prepare one disabled replacement; separate approval required."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import composite_scaling_replacement as r
from bc_phase2.joint_d1_release import read_evidence


def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('reconcile');a.add_argument('--run',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('prepare')
    for name in ('previous-release','reconciliation','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('approve')
    for name in ('manifest','approval','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('submit');a.add_argument('--release',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.command=='run-allocated':
        value=r.run_allocated(ROOT,args.output);print(json.dumps(dict(status=value.get('status'),totals=value.get('totals'))));return
    r.require(not args.output.exists(),'preserve existing output/receipt')
    if args.command=='reconcile':value=r.inspect(args.run,r.base.cluster.registry_root()/'registry.json',r.accounting())
    elif args.command=='prepare':
        value=r.prepare(read_evidence(args.previous_release),read_evidence(args.reconciliation),args.output.parent/'outputs')
        args.output.mkdir();write(args.output/'SCALING_REPLACEMENT_MANIFEST.disabled.json',value)
        write(args.output/'approval.pending.json',dict(schema='composite-scaling-replacement-approval-v1',scope_digest=value['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        print(json.dumps(dict(directory=str(args.output),scope_digest=value['scope_digest'],blockers=value['blockers'],limits=value['scope']['limits'],wave_id=value['scope']['wave']['wave_id'],execution_allowed=False),indent=2));return
    elif args.command=='approve':value=r.approve(read_evidence(args.manifest),read_evidence(args.approval))
    else:value=r.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
    write(args.output,value);print(json.dumps(value,indent=2))

if __name__=='__main__':main()
