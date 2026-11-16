#!/usr/bin/env python3
"""Prepare/approve/submit only the fixed second prospective MATH planning block."""
import argparse,json,os,signal,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_block2_launch as launch
from bc_phase2.joint_d1_release import read_evidence

def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare')
    for k in ('public','inventory-report','cluster','partition-record','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('approve')
    for k in ('manifest','approval','output'):a.add_argument('--'+k,type=Path,required=True)
    a=sub.add_parser('submit')
    for k in ('release','output'):a.add_argument('--'+k,type=Path,required=True)
    a.add_argument('--dry-run',action='store_true')
    a=sub.add_parser('run-allocated');a.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='prepare':
        start=time.process_time();wall=time.monotonic()
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
        signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second CPU preparation ceiling')))
        signal.alarm(300)
        try:value=launch.prepare(a.public,read_evidence(a.inventory_report),read_evidence(a.cluster),a.partition_record.read_text())
        finally:signal.alarm(0)
        a.output.mkdir(exist_ok=False);write(a.output/'manifest.disabled.json',value)
        pending=dict(schema=launch.KEY+'-approval',scope_digest=value['scope_digest'],decision='pending',reviewer=None,
            reviewed_at=None,statement_transmission_authorized=False,GPU_spending_authorized=False)
        write(a.output/'approval.pending.json',pending)
        write(a.output/'preparation-resources.json',dict(cpu_seconds=time.process_time()-start,wall_seconds=time.monotonic()-wall,model_executed=False))
        print(json.dumps(dict(directory=str(a.output),scope_digest=value['scope_digest'],blockers=value['blockers'],
            source_ids=value['scope']['source_ids'],limits=value['scope']['limits'],verified_requests=value['scope']['verified_requests'],
            model_executed=False,execution_allowed=False),indent=2));return
    if a.command=='approve':value=launch.approve(read_evidence(a.manifest),read_evidence(a.approval))
    elif a.command=='submit':value=launch.submit(ROOT,read_evidence(a.release),dry_run=a.dry_run)
    else:
        value=launch.run_allocated(ROOT,a.output);print(json.dumps({'status':value['status'],'totals':value['totals']}));return
    write(a.output,value);print(json.dumps(dict(report=str(a.output),submitted=value.get('submitted',False))))
if __name__=='__main__':main()
