#!/usr/bin/env python3
"""One composite recipe: disabled preparation, external approval, shared-registry dispatch."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import composite_math as r, composite_math_launch as l
from bc_phase2.joint_d1_release import read_evidence

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('prepare')
 for name in ('screen-release','screen-result','statements','cluster','output'):a.add_argument('--'+name,required=True,type=Path)
 a.add_argument('--decoder-qualification',type=Path)
 a=sub.add_parser('qualify-json');a.add_argument('--snapshot',required=True,type=Path);a.add_argument('--output',required=True,type=Path)
 a=sub.add_parser('approve')
 for name in ('manifest','approval','output'):a.add_argument('--'+name,required=True,type=Path)
 a=sub.add_parser('submit');a.add_argument('--release',required=True,type=Path);a.add_argument('--dry-run',action='store_true');a.add_argument('--output',required=True,type=Path)
 a=sub.add_parser('run-allocated');a.add_argument('--output',required=True,type=Path)
 sub.add_parser('deployment')
 args=p.parse_args()
 if args.command=='qualify-json':
  import signal
  from bc_phase2.composite_math_decoder import qualify
  signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('300-second CPU qualification wall bound')))
  signal.alarm(300)
  try:
   with args.output.open('x') as f:
    value=qualify(args.snapshot);json.dump(value,f,indent=2);f.write('\n')
  finally:signal.alarm(0)
  print(json.dumps(dict(report=str(args.output),status=value['status'],model_executed=False),indent=2));return int(value['status']!='passed')
 if args.command=='deployment':print(json.dumps(l.deployment(),indent=2));return 0
 if args.command=='run-allocated':
  result=l.run_allocated(ROOT,args.output);print(json.dumps({k:result.get(k) for k in ('status','totals','identical_design')},indent=2));return 0
 if args.command=='prepare':
  v=l.prepare(read_evidence(args.screen_release),args.statements,read_evidence(args.cluster),args.screen_result,read_evidence(args.decoder_qualification) if args.decoder_qualification else None)
  args.output.mkdir(exist_ok=False)
  pending=dict(schema='composite-r0-approval-v1',scope_digest=v['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False)
  for name,data in [('COMPOSITE_R0_MANIFEST.json',v),('COMPOSITE_BLUEPRINT.json',r.blueprint()),('approval.pending.json',pending)]:
   with (args.output/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
  print(json.dumps(dict(directory=str(args.output),scope_digest=v['scope_digest'],blockers=v['blockers'],execution_allowed=False),indent=2));return 0
 with args.output.open('x') as f:
  v=l.approve(read_evidence(args.manifest),read_evidence(args.approval)) if args.command=='approve' else l.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
  json.dump(v,f,indent=2);f.write('\n')
 print(json.dumps(dict(report=str(args.output),submitted=v.get('submitted',False)),indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
