#!/usr/bin/env python3
"""Prepare or explicitly approve/submit the first prospective MedQA block pair."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_medqa_block2_worker_launch as launch
from bc_phase2.joint_d1_release import read_evidence

def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare')
    for name in ('planner-run','cluster','partition-record','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('approve')
    for name in ('manifest','approval','output'):a.add_argument('--'+name,type=Path,required=True)
    a=sub.add_parser('submit')
    for name in ('release','output'):a.add_argument('--'+name,type=Path,required=True)
    a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.command=='prepare':
        import os,signal,time
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
        signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second preparation ceiling')))
        cpu=time.process_time();wall=time.monotonic();signal.alarm(300)
        try:result=launch.prepare(args.planner_run,read_evidence(args.cluster),args.partition_record.read_text())
        finally:signal.alarm(0)
        args.output.mkdir(exist_ok=False)
        write(args.output/'MANIFEST.disabled.json',result)
        write(args.output/'qualification.json',result['scope']['cpu_qualification'])
        write(args.output/'preparation-resources.json',dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,model_executed=False))
        write(args.output/'approval.pending.json',dict(schema=launch.KEY+'-approval',scope_digest=result['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        w=result['scope']['wave'];b=w['bundles'][0]
        summary=dict(directory=str(args.output),scope_digest=result['scope_digest'],blockers=result['blockers'],limits=w['limits'],sources=b['sources'],n=4,m=6,K=2,fresh_profile_calls=6,evaluation_call_cap=b['call_bounds']['evaluation_calls'],execution_allowed=False)
        write(args.output/'summary.json',summary);print(json.dumps(summary,indent=2));return
    if args.command=='approve':result=launch.approve(read_evidence(args.manifest),read_evidence(args.approval))
    elif args.command=='submit':result=launch.submit(ROOT,read_evidence(args.release),dry_run=args.dry_run)
    else:
        result=launch.run_allocated(ROOT,args.output);print(json.dumps({k:result.get(k) for k in ('status','totals')}));return
    write(args.output,result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
