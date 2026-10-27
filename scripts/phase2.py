#!/usr/bin/env python3
"""Phase II local CPU/mock entry point. This file registers NO live backend."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.model import Invalid,plain
from bc_phase2.template import load
from bc_phase2.planning import validate_disabled,stage_readiness


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('validate-template');a.add_argument('--manifest',default=str(ROOT/'PILOT_MANIFEST_V3.yaml'));a.add_argument('--stage',default='offline_validation')
    a=sub.add_parser('mock-demo');a.add_argument('--manifest',default=str(ROOT/'PILOT_MANIFEST_V3.yaml'));a.add_argument('--output',required=True);a.add_argument('--synthetic-cap',type=int,default=50000);a.add_argument('--repeats',type=int,choices=(1,2),default=2)
    args=p.parse_args();config=load(args.manifest);validate_disabled(config)
    if args.command=='validate-template':report=stage_readiness(config,args.stage)
    else:
        from bc_phase2.campaign import demo
        r=demo(args.output,config,args.synthetic_cap,args.repeats)
        report={'report':str(Path(args.output)/'report.json'),'synthetic':True,'model_executed':False,'planned_slots':len(r['outcomes']),'accounting':r['accounting']}
    print(json.dumps(plain(report),indent=2))


if __name__=='__main__':
    try:main()
    except (Invalid,ValueError,KeyError) as exc:print('phase2: '+str(exc),file=sys.stderr);raise SystemExit(2)
