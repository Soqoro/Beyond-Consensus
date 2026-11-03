#!/usr/bin/env python3
"""Freeze/review D1 scope using existing verification; no tokenizer/model/job calls."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.joint_d1_release import read_evidence,freeze,review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('freeze','review'))
    parser.add_argument('--receipt',type=Path)
    parser.add_argument('--verification',type=Path)
    parser.add_argument('--statements',type=Path)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    if a.output.exists():parser.error('output exists; preserve previous evidence')
    if a.command=='freeze':
        if not all((a.receipt,a.verification,a.statements)) or a.manifest:parser.error('freeze requires receipt, verification, statements only')
        result=freeze(ROOT,read_evidence(a.receipt),read_evidence(a.verification),a.statements)
        summary=review(ROOT,result)
    else:
        if not a.manifest or any((a.receipt,a.verification,a.statements)):parser.error('review requires manifest only')
        result=review(ROOT,read_evidence(a.manifest));summary=result
    with a.output.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({'report':str(a.output),**summary},indent=2))

if __name__=='__main__':main()
