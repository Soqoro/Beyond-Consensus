#!/usr/bin/env python3
"""One MedQA worker composite; CPU qualification and disabled binding precede approval."""
import argparse,json,os,signal,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import medqa_worker_launch as launch
from bc_phase2.joint_d1_release import read_evidence

def write(p,v):
    with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('qualify');a.add_argument('--snapshot',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('prepare')
    for n in ('parent-release','cluster','qualification','output'):a.add_argument('--'+n,type=Path,required=True)
    a=sub.add_parser('approve')
    for n in ('manifest','approval','output'):a.add_argument('--'+n,type=Path,required=True)
    a=sub.add_parser('submit')
    for n in ('release','output'):a.add_argument('--'+n,type=Path,required=True)
    a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('grade')
    for n in ('result','public','protected','output'):a.add_argument('--'+n,type=Path,required=True)
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='qualify':
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
        signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second CPU qualification cap')));signal.alarm(300)
        try:r=launch.qualify(a.snapshot)
        finally:signal.alarm(0)
    elif a.command=='prepare':
        r=launch.prepare(read_evidence(a.parent_release),read_evidence(a.cluster),read_evidence(a.qualification));a.output.mkdir(exist_ok=False)
        write(a.output/'MANIFEST.disabled.json',r)
        write(a.output/'approval.pending.json',dict(schema=launch.KEY+'-approval',scope_digest=r['scope_digest'],decision='pending',reviewer=None,reviewed_at=None,source_worker_transmission=False,contract_accepted=False,gpu_recipe_authorized=False))
        print(json.dumps(dict(directory=str(a.output),scope_digest=r['scope_digest'],blockers=r['blockers'],limits=r['scope']['limits'],execution_allowed=False),indent=2));return
    elif a.command=='grade':
        public=read_evidence(a.public);sources={r['id']:r for r in public['records']}
        r=launch.grade_results(read_evidence(a.result),sources,read_evidence(a.protected))
    elif a.command=='approve':r=launch.approve(read_evidence(a.manifest),read_evidence(a.approval))
    elif a.command=='submit':r=launch.submit(ROOT,read_evidence(a.release),dry_run=a.dry_run)
    else:
        r=launch.run_allocated(ROOT,a.output);print(json.dumps({k:r.get(k) for k in ('status','totals')}));return
    write(a.output,r);print(json.dumps(dict(report=str(a.output),status=r.get('status'),submitted=r.get('submitted',False))))
if __name__=='__main__':main()
