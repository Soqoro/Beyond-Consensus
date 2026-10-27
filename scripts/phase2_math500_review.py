#!/usr/bin/env python3
"""Write local selected-problem review cards; print only non-content summary."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.math500_review import prepare_review


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--proposal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = prepare_review(args.data, args.proposal)
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'report': str(args.output), 'status': report['status'],
        'proposal_digest': report['proposal_digest'],
        'selected_cards': len(report['selected_problem_cards']),
        'candidate_pairs': len(report['candidate_pairs']),
        'unique_pairs_compared': report['unique_pairs_compared'],
        'offline_cpu_seconds': report['offline_cpu_seconds'],
        'model_executed': False, 'task_execution_allowed': False}, indent=2))


if __name__ == '__main__':
    main()
