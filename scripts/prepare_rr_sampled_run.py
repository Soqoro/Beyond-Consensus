#!/usr/bin/env python3
"""Prepare, review, approve or export a bounded sampled study; never submit."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beyond_consensus.experiments import rr_sampled_run as adapter
from beyond_consensus.experiments.rr_open_clean import load_control_record as load
from reporecourse.common import write_new


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    measure=sub.add_parser('footprint');build=sub.add_parser('proposal')
    for x in (measure,build):
        x.add_argument('--catalog',type=Path,required=True);x.add_argument('--sources',type=Path,required=True)
        x.add_argument('--worker-lock',type=Path,required=True)
    for name in ('normal-audit','controls','footprint'):build.add_argument('--'+name,type=Path,required=True)
    review=sub.add_parser('review');approve=sub.add_parser('approve')
    for x in (review,approve):
        x.add_argument('--manifest',type=Path,required=True);x.add_argument('--worker-lock',type=Path,required=True)
    approve.add_argument('--approval',type=Path,required=True)
    export=sub.add_parser('export');export.add_argument('--run',type=Path,required=True)
    for x in (measure,build,review,approve,export):x.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Use a fresh output path; records are immutable')
    if a.command=='footprint':r=adapter.measure_footprint(load(a.catalog),a.sources,load(a.worker_lock))
    elif a.command=='proposal':r=adapter.build(ROOT,a.sources,load(a.catalog),load(a.worker_lock),load(a.normal_audit),load(a.controls),load(a.footprint))
    elif a.command=='export':r=adapter.export(a.run)
    else:
        m=load(a.manifest);worker=load(a.worker_lock)
        if a.command=='approve':r=adapter.authorize(m,load(a.approval),ROOT,worker)
        else:
            adapter.verify(m,ROOT,worker)
            r=dict(experiment_id=m['experiment_id'],planned_configurations=6,planned_conditions=12,
                task_execution_allowed=m['task_execution_allowed'],approval_template=adapter.approval_template(m),
                source_groups={k:v['card']['source_group'] for k,v in m['task_bindings'].items()},
                physical_model_planner_calls=0,blockers=['exact_twelve_condition_approval_required'] if not m['approval'] else [],
                review_status='development_reviews_deferred_not_clearance',limitations=m['limitations'])
    write_new(a.output,r)
    print(json.dumps(dict(report=str(a.output),command=a.command,experiment_id=r.get('experiment_id'),
        status=r.get('status'),model_executed=False,submitted=False),indent=2))
    if a.command=='review':print(json.dumps(r,indent=2))


if __name__=='__main__':main()
