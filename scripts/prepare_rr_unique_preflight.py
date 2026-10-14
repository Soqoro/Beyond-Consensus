"""Prepare three task-free worker GPU probes using a qualified unique-key lock."""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from beyond_consensus.experiments.rr_unique_preflight import build
from beyond_consensus.util import read_json
from reporecourse.common import write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-lock', type=Path, required=True)
    parser.add_argument('--controls', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = build(ROOT, read_json(args.model_lock), read_json(args.controls))
    write_new(args.output, manifest)
    print('Prepared:', manifest['experiment_id'])
    print('Manifest:', args.output)


if __name__ == '__main__':main()
