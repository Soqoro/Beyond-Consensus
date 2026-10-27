#!/usr/bin/env python3
"""Inspect pinned local MATH-500 bytes without printing problems or gold answers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from bc_phase2.math500 import inspect_local


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = inspect_local(args.data)
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'report': str(args.output), **report}, indent=2))


if __name__ == '__main__':
    main()
