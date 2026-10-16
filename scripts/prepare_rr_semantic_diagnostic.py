#!/usr/bin/env python3
"""Prepare a synthetic design or run trusted CPU controls; never load models or submit."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beyond_consensus.experiments.rr_semantic_diagnostic import packet, production_controls
from reporecourse.common import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--production-controls', action='store_true')
    args = parser.parse_args()
    result = production_controls() if args.production_controls else packet()
    if not args.production_controls and result['controls']['status'] != 'passed':
        raise SystemExit('Synthetic mechanism controls failed')
    write_new(args.output, result)
    print('Status:', result.get('status', 'design_prepared'))
    print('Report:', args.output)
    print('GPU execution remains blocked.')
    if args.production_controls and result['status'] != 'passed':
        raise SystemExit(2)


if __name__ == '__main__':
    main()
