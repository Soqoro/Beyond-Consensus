#!/usr/bin/env python3
"""NEUTRAL versus JOINT development recipe. Preparation never authorizes dispatch."""
import argparse,json,sys,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import composite_joint as r, composite_joint_launch as l
from bc_phase2.joint_d1_release import read_evidence

def write(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('prepare')
 for n in ('parent-release','cluster','qualification','output'):a.add_argument('--'+n,required=True,type=Path)
 a=sub.add_parser('qualify-json');a.add_argument('--snapshot',required=True,type=Path);a.add_argument('--output',required=True,type=Path)
 a=sub.add_parser('approve')
 for n in ('manifest','approval','output'):a.add_argument('--'+n,required=True,type=Path)
 a=sub.add_parser('submit');a.add_argument('--release',required=True,type=Path);a.add_argument('--dry-run',action='store_true');a.add_argument('--output',required=True,type=Path)
 a=sub.add_parser('run-allocated');a.add_argument('--output',required=True,type=Path)
 sub.add_parser('deployment');a=sub.add_parser('describe');a.add_argument('--output',required=True,type=Path)
 args=p.parse_args()
 if args.command=='deployment':print(json.dumps(l.base.deployment(),indent=2));return 0
 if args.command=='describe':
  args.output.mkdir(exist_ok=False)
  write(args.output/'FROZEN_DOMAIN_AND_SCOPE.json',dict(status='disabled_unbound',domain=r.domain(),blueprint=r.blueprint(),execution_allowed=False,remaining=['execution-host qualification and binding','exact source/contract/GPU approval']))
  write(args.output/'FROZEN_TWO_ARM_DESIGNS.json',dict(methods={'NEUTRAL':r.selection(r.domain()),'JOINT':None},prices=None,status='pending_profile'))
  r.write_csv(args.output,r.pending_result());return 0
 if args.command=='qualify-json':
  signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('300-second qualification limit')));signal.alarm(300)
  try:v=l.qualify(args.snapshot);write(args.output,v)
  finally:signal.alarm(0)
  print(json.dumps(dict(report=str(args.output),status=v['status'],model_executed=False)));return int(v['status']!='passed')
 if args.command=='run-allocated':
  v=l.run_allocated(ROOT,args.output);print(json.dumps({k:v.get(k) for k in ('status','totals','shared_observations')}));return 0
 if args.command=='prepare':
  v=l.prepare(read_evidence(args.parent_release),read_evidence(args.cluster),read_evidence(args.qualification));args.output.mkdir(exist_ok=False)
  write(args.output/'FROZEN_DOMAIN_AND_SCOPE.json',v)
  write(args.output/'FROZEN_TWO_ARM_DESIGNS.json',dict(methods={'NEUTRAL':r.selection(r.domain()),'JOINT':None},prices=None,status='pending_profile'))
  write(args.output/'approval.pending.json',dict(schema='composite-joint-approval-v1',decision='pending',scope_digest=v['scope_digest'],reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
  r.write_csv(args.output,r.pending_result());print(json.dumps(dict(directory=str(args.output),scope_digest=v['scope_digest'],blockers=v['blockers'],execution_allowed=False),indent=2));return 0
 v=l.approve(read_evidence(args.manifest),read_evidence(args.approval)) if args.command=='approve' else l.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
 write(args.output,v);print(json.dumps(dict(report=str(args.output),submitted=v.get('submitted',False))));return 0
if __name__=='__main__':raise SystemExit(main())
