#!/usr/bin/env python3
"""Read-only planner allowance scenarios from a measured CPU footprint packet."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.experiments.rr_planner_capacity import review
from beyond_consensus.util import BCError, file_hash, digest
from reporecourse.common import load, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packet', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--planner-caps', type=int, nargs='+', default=[2048,3072,4096])
    parser.add_argument('--non-action-reserves', type=int, nargs='+', default=[0,512,1024,2048],
                        help='Hypothetical reasoning/delimiter/formatting tokens, not measured reasoning')
    args = parser.parse_args()
    if args.output.exists(): parser.error('Use a fresh report path; previous evidence is immutable')
    try:
        before = file_hash(args.packet)
        result = review(load(args.packet), args.planner_caps, args.non_action_reserves)
        if file_hash(args.packet) != before: raise BCError('Input packet changed during review')
        result['input_file'] = dict(path=str(args.packet.resolve()), sha256=before)
        result['report_id'] = digest({k:v for k,v in result.items() if k != 'report_id'})
        write_new(args.output, result)
    except (BCError, OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f'Capacity review failed: {exc}\n')
    print(json.dumps(dict(report=str(args.output), status=result['status'],
        worker_output_cap_unchanged=result['worker_output_cap_unchanged'],
        selected_planner_output_cap=None,
        comparisons=[dict(planner_output_cap=c['planner_output_cap'],
            maximum_planner_input_tokens=c['maximum_planner_input_tokens'],
            plan_24=c['cases'][2]) for c in result['comparisons']]), indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
