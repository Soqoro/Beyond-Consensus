#!/usr/bin/env python3
"""Audit saved normal qualification and current decoder compatibility; never submit."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from beyond_consensus.experiments.rr_unique_review import inspect
from reporecourse.common import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--snapshots', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():parser.error('Use a fresh audit path')
    report = inspect(args.run, args.snapshots, ROOT)
    write_new(args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if report['current_compatibility']['status'] == 'compatible' else 2


if __name__ == '__main__':
    raise SystemExit(main())
