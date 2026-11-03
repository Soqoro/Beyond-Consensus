#!/usr/bin/env python3
"""Prepare exact D1 release, inspect submission, or run its registered allocated job."""
import argparse
import getpass
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.joint_d1_release import read_evidence
from bc_phase2 import joint_d1_launch as launch


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('submit');p.add_argument('--release',type=Path,required=True)
    p.add_argument('--statements',type=Path,required=True);p.add_argument('--cluster',type=Path,required=True)
    p.add_argument('--dry-run',action='store_true');p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('run-allocated');p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='run-allocated':
        result=launch.run_allocated(ROOT,args.output)
        print(json.dumps(result,indent=2))
        return 1 if result['halted'] else 0
    # Exclusive creation happens before any possible submission. An ambiguous
    # failure leaves the record and shared registry for manual reconciliation.
    with args.output.open('x') as handle:
        if args.command=='prepare':
            result=launch.prepare(ROOT,read_evidence(args.manifest),reviewer=getpass.getuser())
            summary=launch.summary(ROOT,result)
        else:
            result=launch.submit(ROOT,read_evidence(args.release),args.statements,
                launch.cluster.load_cluster(args.cluster),dry_run=args.dry_run)
            summary=result
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({'report':str(args.output),**summary},indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
