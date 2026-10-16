#!/usr/bin/env python3
"""Prepare, review, or approve the three-call synthetic diagnostic; never submit."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from beyond_consensus.experiments import rr_semantic_run as adapter
from beyond_consensus.experiments.rr_open_clean import load_control_record as load
from reporecourse.common import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    measure = commands.add_parser('footprint')
    proposal = commands.add_parser('proposal')
    review = commands.add_parser('review')
    approve = commands.add_parser('approve')
    for p in (measure, proposal, review, approve):
        p.add_argument('--worker-lock', type=Path, required=True)
        p.add_argument('--output', type=Path, required=True)
    for name in ('production-controls', 'adapter-controls', 'footprint', 'normal-run', 'snapshots'):
        proposal.add_argument('--'+name, type=Path, required=True)
    for p in (review, approve):
        p.add_argument('--manifest', type=Path, required=True)
    approve.add_argument('--approval', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh output path')
    worker = load(args.worker_lock)
    if args.command == 'footprint':
        result = adapter.footprint(worker)
    elif args.command == 'proposal':
        result = adapter.build(ROOT, worker, load(args.production_controls), load(args.adapter_controls),
                               load(args.footprint), args.normal_run, args.snapshots)
    else:
        m = load(args.manifest)
        if args.command == 'approve':
            result = adapter.authorize(m, load(args.approval), ROOT, worker)
        else:
            adapter.verify(m, ROOT, worker)
            result = dict(experiment_id=m['experiment_id'], approval_template=adapter.approval_template(m),
                          blockers=['exact_three_call_approval_required'] if m['approval'] is None else [],
                          task_execution_allowed=m['task_execution_allowed'])
    write_new(args.output, result)
    print('Report:', args.output)
    print('No model executed or job submitted.')


if __name__ == '__main__':
    main()
