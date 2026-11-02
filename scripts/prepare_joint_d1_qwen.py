#!/usr/bin/env python3
"""Disabled configuration preparation/preflight only; never loads source statements."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.joint_d1_qwen import configuration, preflight
from bc_phase2.joint_schema import decode


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','bind','preflight'))
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--receipt',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='bind':
        if not args.receipt or args.manifest:parser.error('bind requires --receipt only')
        from bc_phase2.joint_d1_local import bind_receipt,read_json
        value=bind_receipt(ROOT,read_json(args.receipt))
    elif args.command=='prepare':
        if args.manifest or args.receipt:parser.error('prepare has no input manifest/receipt')
        value=configuration(ROOT)
    else:
        if not args.manifest or args.receipt:parser.error('preflight requires --manifest only')
        with args.manifest.open('rb') as handle:raw=handle.read(65537)
        if len(raw)>65536:parser.error('manifest exceeds 65536 bytes')
        value=preflight(decode(raw.decode('utf8')),ROOT)
    with args.output.open('x') as handle:
        json.dump(value,handle,indent=2);handle.write('\n')
    print(json.dumps(dict(report=str(args.output),execution_allowed=False,model_executed=False)))

if __name__=='__main__':main()
