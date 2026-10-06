#!/usr/bin/env python3
"""Offline snapshot/report audit. No model imports, scheduler commands or SQL."""
from pathlib import Path
import argparse
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from beyond_consensus.experiments.rr_v2_evidence import audit, audit_normal
from reporecourse.common import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normal-run', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stress-run', type=Path)
    mode.add_argument('--normal-only', action='store_true',
                      help='Audit only the observed sequence; does not qualify stress geometry')
    parser.add_argument('--snapshots', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh audit output path; historical reports are immutable')
    report = (audit_normal(args.normal_run, args.snapshots) if args.normal_only
              else audit(args.normal_run, args.stress_run, args.snapshots))
    write_new(args.output, report)
    print(json.dumps({'report': str(args.output), 'status': report['status'],
                      'errors': report['errors'], 'model_executed': False}, indent=2))
    return 0 if report['status'] == 'verified_internal_bindings_review_pending' else 2


if __name__ == '__main__':
    raise SystemExit(main())
