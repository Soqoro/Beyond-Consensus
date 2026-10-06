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
    for name in ('proposal', 'model-lock', 'planner-lock', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--planner-output-cap', type=int, choices=(2048, 4096), default=2048)
    p.add_argument('--measure', action='store_true', help='Offline tokenizer/grammar CPU measurement; no weights')
    a = p.parse_args()
    if a.output.exists(): p.error('Use a fresh output path')
    root = Path(__file__).resolve().parents[1]
    report = (measure_cpu if a.measure else prepare)(root, load(a.proposal), load(a.model_lock), load(a.planner_lock), planner_output_cap=a.planner_output_cap)
    write_new(a.output, report)
    print(json.dumps(dict(report=str(a.output), status=report['status'], packet_id=report['packet_id'],
        model_executed=False, cases=[dict(id=r['id'], **r['measurement']) for r in report['cases']]), indent=2))
    return 2 if report['status'] == 'failed_cpu_cases' else 0


if __name__ == '__main__':
    raise SystemExit(main())
