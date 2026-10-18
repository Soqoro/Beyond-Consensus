#!/usr/bin/env python3
"""Prepare finite worker-selection stages; submission remains scripts/bc.py."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beyond_consensus.experiments import worker_selection as w
from beyond_consensus.models import worker_profiles as profiles,worker_staging as staging
from reporecourse.common import write_new


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('profile','metadata','feasibility','stage','native','inventory','controls','proposal','review','approve','report','compare','allocation'):
        q=sub.add_parser(name);q.add_argument('--output',type=Path,required=True)
        if name in ('profile','metadata','native','proposal'):q.add_argument('--profile',choices=w.MODELS,required=True)
        if name in ('feasibility','stage'):q.add_argument('--assets',type=Path,required=True);q.add_argument('--destination',type=Path,required=True)
        if name=='feasibility':q.add_argument('--partition')
        if name=='stage':q.add_argument('--approval',type=Path)
        if name in ('native','proposal','approve'):q.add_argument('--model-lock',type=Path,required=True)
        if name=='proposal':
            q.add_argument('--stage',choices=('Q','A','B','C'),required=True)
            for key in ('controls','qualification','prior','catalog','sources'):q.add_argument('--'+key,type=Path)
        if name in ('review','approve'):q.add_argument('--manifest',type=Path,required=True)
        if name=='approve':q.add_argument('--approval',type=Path,required=True)
        if name=='report':q.add_argument('--run',type=Path,required=True)
        if name=='compare':q.add_argument('--runs',type=Path,nargs=2,required=True)
        if name=='allocation':q.add_argument('--run',type=Path,required=True);q.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Use a fresh output path; reports and attempts are immutable')
    load=w.load
    if a.command=='profile':r=profiles.profile(a.profile)
    elif a.command=='metadata':r=staging.metadata(a.profile)
    elif a.command=='feasibility':r=staging.feasibility(load(a.assets),a.destination,a.partition)
    elif a.command=='stage':r=staging.stage(load(a.assets),a.destination,load(a.approval) if a.approval else None)
    elif a.command=='native':
        lock=load(a.model_lock);r=dict(lock,worker_qualification=profiles.qualify(profiles.profile(a.profile),lock))
    elif a.command=='inventory':
        r=w.design.inventory()
        r['presentation_audits']={c['id']:w.audit(w.messages(c)) for c in w.design.cases()}
        r['private_file']=True
    elif a.command=='controls':r=w.controls()
    elif a.command=='proposal':r=w.build(ROOT,a.profile,load(a.model_lock),a.stage,
        controls_record=load(a.controls) if a.controls else None,qualification=load(a.qualification) if a.qualification else None,
        prior=load(a.prior) if a.prior else None,catalog=load(a.catalog) if a.catalog else None,sources=a.sources)
    elif a.command=='review':
        m=load(a.manifest);w.validate(m);r=dict(approval_template=w.approval_template(m),stage=m['stage'],whole_stage_rows=len(m['rows']),
            profile=m['profile'],task_execution_allowed=False,implementation=m['implementation'])
    elif a.command=='approve':r=w.authorize(load(a.manifest),load(a.approval),ROOT,load(a.model_lock))
    elif a.command=='report':r=w.aggregate(load(a.run/'manifest.json'),a.run)
    elif a.command=='allocation':r=w.allocation(load(a.run/'manifest.json'),load(a.receipt),a.run)
    else:r=w.compare([load(x/'manifest.json') for x in a.runs],[w.aggregate(load(x/'manifest.json'),x) for x in a.runs])
    write_new(a.output,r);print(json.dumps(dict(report=str(a.output),status=r.get('status'),model_executed=False,submitted=False),indent=2))
    if a.command=='controls' and r['status']!='passed':return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
