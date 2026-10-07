#!/usr/bin/env python3
"""CPU-only conditional fault adapter controls; a skipped integration test blocks qualification."""
import argparse
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
sys.path.insert(0, str(ROOT))
from beyond_consensus.experiments.rr_open_fault import control_hashes
from beyond_consensus.experiments.manifest import source_revision
from reporecourse.common import write_new
from reporecourse.qualification import runtime_versions
from reporecourse.track_f_controls import PINS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): parser.error('Use a fresh report path')
    versions = runtime_versions()
    if any(versions.get(k) != v for k,v in PINS.items()): parser.error('Pinned optional CPU dependencies required')
    start = time.process_time()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_rr_open_fault.py'))
    passed = result.wasSuccessful() and not result.skipped
    write_new(args.output, dict(schema='rr-open-fault-controls-v1', status='passed' if passed else 'failed',
        source_revision=source_revision(ROOT), implementation_hashes=control_hashes(ROOT), runtime_versions=versions,
        tests=result.testsRun, skipped=len(result.skipped), failures=len(result.failures), errors=len(result.errors),
        model_executed=False, sql_executed=True, evidence='CPU doubles and trusted restricted SQL controls only',
        task_execution_allowed=False, analysis_cpu_seconds=time.process_time()-start))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
