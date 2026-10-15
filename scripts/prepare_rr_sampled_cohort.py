"""Prepare a blocked twelve-condition sampled-organization proposal, never submit."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reporecourse.common import load,write_new,Rejected
from beyond_consensus.experiments.rr_open_clean import load_control_record
from reporecourse.tasks import load_task
from reporecourse.sampled_cohort import proposal,approval_template,TASKS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog',type=Path,required=True)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--worker-lock',type=Path)
    p.add_argument('--normal-qualification',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--approval-template',type=Path,required=True)
    args=p.parse_args();publics={}
    for task in TASKS:
        try:publics[task]=load_task(task,args.sources)[1]
        except (Rejected,OSError):pass
    value=proposal(load_control_record(args.catalog),publics,
        worker_lock=load(args.worker_lock) if args.worker_lock else None,
        normal_qualification=load_control_record(args.normal_qualification) if args.normal_qualification else None)
    write_new(args.output,value);write_new(args.approval_template,approval_template(value))
    print('Proposal:',args.output)
    print('Status:',value['status'])
    print('Blockers:',', '.join(value['blockers']))
    print('No execution authorized or submitted.')

if __name__=='__main__':main()
