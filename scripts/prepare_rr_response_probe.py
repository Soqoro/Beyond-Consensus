#!/usr/bin/env python3
"""Prepare a separate three-call mapping response diagnostic, without model loading."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beyond_consensus.experiments.rr_response_probe import build
from beyond_consensus.util import read_json
from reporecourse.common import write_new

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controls',type=Path,required=True)
    p.add_argument('--export',type=Path,required=True)
    p.add_argument('--worker-lock',type=Path,required=True)
    p.add_argument('--planner-lock',type=Path,required=True)
    p.add_argument('--preflight-run',type=Path,required=True)
    p.add_argument('--snapshots',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    m=build(ROOT,read_json(a.export),read_json(a.worker_lock),read_json(a.planner_lock),a.preflight_run,a.snapshots,read_json(a.controls))
    write_new(a.output,m)
    print('Prepared three reconstructed-input calls:',m['experiment_id'])
    print('Manifest:',a.output)
if __name__=='__main__':main()
