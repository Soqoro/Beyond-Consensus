#!/usr/bin/env python3
"""Prepare immutable task-free footprint cases; --measure uses an offline CPU allocation."""
import argparse
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments.rr_open_footprint import prepare, measure_cpu
from reporecourse.common import load, write_new


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proposal',type=Path)
    for name in ('model-lock', 'planner-lock', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--planner-output-cap', type=int, choices=(2048, 4096, 6144), default=2048)
    p.add_argument('--interface-profile',choices=('rr-interface-reliability-v1',))
    p.add_argument('--measure', action='store_true', help='Offline tokenizer/grammar CPU measurement; no weights')
    a = p.parse_args()
    if a.output.exists(): p.error('Use a fresh output path')
    root = Path(__file__).resolve().parents[1]
    if a.proposal:
        proposal=load(a.proposal)
    elif a.interface_profile:
        from beyond_consensus.experiments.rr_cohort import model_settings
        from reporecourse.common import digest
        from reporecourse.interface import mode
        model=model_settings(a.interface_profile)
        proposal=dict(schema='rr-open-engineering-proposal-v1',task_execution_allowed=False,campaign_allowed=False,
            worker_config={'model':model},planner_config={'model':dict(model,action_constraint=mode('plan'))})
        proposal['proposal_id']=digest(proposal)
    else:p.error('--proposal is required for legacy footprint profiles')
    report = (measure_cpu if a.measure else prepare)(root, proposal, load(a.model_lock), load(a.planner_lock), planner_output_cap=a.planner_output_cap,interface_profile=a.interface_profile)
    write_new(a.output, report)
    print(json.dumps(dict(report=str(a.output), status=report['status'], packet_id=report['packet_id'],
        model_executed=False, cases=[dict(id=r['id'], **r['measurement']) for r in report['cases']]), indent=2))
    return 2 if report['status'] == 'failed_cpu_cases' else 0


if __name__ == '__main__':
    raise SystemExit(main())
