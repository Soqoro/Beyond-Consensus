#!/usr/bin/env python3
"""Composite scaling wave one. Offline preparation never authorizes real dispatch."""
import argparse
import json
from pathlib import Path
import signal
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import composite_scaling as spec, composite_scaling_runtime as runtime, composite_scaling_launch as launch
from bc_phase2.joint_d1_release import read_evidence


def write(path,value):
    with path.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')


def profiles(run,bank,additional=None):
    manifest=read_evidence(run/'manifest.json')
    exported={'files':{'release/approved-release.json':{'content':manifest['release']}}}
    for name in ('execution/journal/ledger.json','execution/profile.json'):
        exported['files'][name]={'content':read_evidence(run/name)}
    values=runtime.import_profiles(exported,spec.reviewed(bank))
    if additional is not None:
        ab={'files':{'release/approved-release.json':{'content':read_evidence(additional/'manifest.json')['release']}}}
        for name in ('execution/journal/ledger.json','execution/profile_algebraic.json'):
            ab['files'][name]={'content':read_evidence(additional/name)}
        more=runtime.import_ab_profiles(ab,spec.reviewed(bank))
        for key,row in more.items():
            if key not in values:values[key]=row
    return values


def emit(directory,wave):
    directory.mkdir(exist_ok=False)
    write(directory/'COMPONENT_BANK.json',wave['bank'])
    write(directory/'COMPOSITE_REGISTRY.json',wave['bundles'])
    write(directory/'RUN_MATRIX.json',wave['matrix'])
    write(directory/'PROFILE_COVERAGE.json',dict(keys=wave['profile_coverage'],consumers=wave['profile_consumers'],reuse=wave['reused_profiles'],missing_schedule=wave['profile_schedule']))
    write(directory/'WAVE1.disabled.json',wave)
    write(directory/'RESULTS.unrun.json',runtime.pending_rows(wave))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for cmd in ('describe','qualify','prepare'):
        a=sub.add_parser(cmd);a.add_argument('--bank',type=Path,default=ROOT/'configs/phase2/composite_scaling_bank_v2.json')
        a.add_argument('--profile-run',type=Path,required=True);a.add_argument('--additional-profile-run',type=Path); a.add_argument('--output',type=Path,required=True)
        if cmd=='qualify':a.add_argument('--snapshot',type=Path,required=True)
        if cmd=='prepare':
            for arg in ('parent-release','cluster','qualification'):a.add_argument('--'+arg,type=Path,required=True)
    a=sub.add_parser('approve')
    for arg in ('manifest','approval','output'):a.add_argument('--'+arg,type=Path,required=True)
    a=sub.add_parser('submit');a.add_argument('--release',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    sub.add_parser('deployment')
    args=p.parse_args()
    if args.command=='deployment':print(json.dumps(launch.base.deployment(),indent=2));return
    if args.command=='run-allocated':
        result=launch.run_allocated(ROOT,args.output);print(json.dumps({k:result.get(k) for k in ('status','totals')}));return
    if args.command in ('describe','qualify','prepare'):
        bank=read_evidence(args.bank);reuse=profiles(args.profile_run,bank,args.additional_profile_run);wave=launch.make_wave(bank,reuse)
        if args.command=='describe':emit(args.output,wave);print(json.dumps(dict(directory=str(args.output),wave_id=wave['wave_id'],limits=wave['limits'])));return
        if args.command=='qualify':
            signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('300s CPU qualification cap')));signal.alarm(300)
            try:result=launch.qualify(args.snapshot,bank,reuse);write(args.output,result)
            finally:signal.alarm(0)
            print(json.dumps(dict(report=str(args.output),status=result['status'],model_executed=False)))
            if result['status']!='passed':raise SystemExit(1)
            return
        result=launch.prepare(read_evidence(args.parent_release),bank,reuse,read_evidence(args.cluster),read_evidence(args.qualification));emit(args.output,wave)
        write(args.output/'SCALING_MANIFEST.disabled.json',result)
        write(args.output/'approval.pending.json',dict(schema='composite-scaling-approval-v2',scope_digest=result['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        print(json.dumps(dict(directory=str(args.output),scope_digest=result['scope_digest'],blockers=result['blockers'],limits=wave['limits'],execution_allowed=False),indent=2));return
    if args.command=='approve':result=launch.approve(read_evidence(args.manifest),read_evidence(args.approval))
    else:result=launch.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
    write(args.output,result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
