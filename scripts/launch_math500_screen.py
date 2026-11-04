#!/usr/bin/env python3
"""Explicit approval/submit for the twenty-call scope; no implicit approval or chaining."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import math500_screen_launch as launch
from bc_phase2.joint_d1_release import read_evidence


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('bind')
    for name in ('proposal','inventory-report','cluster','partition-record','output'):
        p.add_argument('--'+name,required=True,type=Path)
    p=sub.add_parser('approve')
    p.add_argument('--manifest',required=True,type=Path);p.add_argument('--approval',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p=sub.add_parser('submit');p.add_argument('--release',required=True,type=Path)
    p.add_argument('--dry-run',action='store_true');p.add_argument('--output',required=True,type=Path)
    p=sub.add_parser('run-allocated');p.add_argument('--output',required=True,type=Path)
    a=parser.parse_args()
    if a.command=='run-allocated':
        result=launch.run_allocated(ROOT,a.output)
        print(json.dumps({k:result[k] for k in ('sources','halted','model_executed','stage_resources')},indent=2))
        return int(result['halted'])
    if a.command=='bind':
        value=launch.bind(read_evidence(a.proposal),read_evidence(a.inventory_report),
                          read_evidence(a.cluster),a.partition_record.read_text())
        summary=launch.review(value)
        a.output.mkdir(exist_ok=False)
        for name,record in (('manifest.disabled.json',value),('review.json',summary)):
            with (a.output/name).open('x') as handle:
                json.dump(record,handle,indent=2);handle.write('\n')
        print(json.dumps({'directory':str(a.output),**summary},indent=2))
        return 0
    with a.output.open('x') as handle:
        if a.command=='approve':
            value=launch.approve(read_evidence(a.manifest),read_evidence(a.approval))
        else:value=launch.submit(ROOT,read_evidence(a.release),dry_run=a.dry_run)
        json.dump(value,handle,indent=2);handle.write('\n')
    print(json.dumps({'report':str(a.output),'submitted':value.get('submitted',False),
                      'release_digest':value.get('release_digest'),'scope_digest':value.get('scope_digest')}))
    return 0

if __name__=='__main__':raise SystemExit(main())
