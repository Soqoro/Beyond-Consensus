#!/usr/bin/env python3
"""Bind existing metadata receipts only. No source statements, tokenizer, model or scheduler calls."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import d1_natural_binding as binding
from bc_phase2.joint_d1_release import read_evidence


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('verification','inventory-report','cluster','partition-record','output'):
        p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args()
    manifest=binding.bind(read_evidence(a.verification),read_evidence(a.inventory_report),
                          read_evidence(a.cluster),a.partition_record.read_text())
    review=binding.review(manifest)
    a.output.mkdir(exist_ok=False)
    for name,value in [('manifest.disabled.json',manifest),('review.json',review)]:
        with (a.output/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({'directory':str(a.output),**review},indent=2))

if __name__=='__main__':main()
