#!/usr/bin/env python3
"""No-skip CPU controls for the synthetic semantic adapter."""
import argparse
from pathlib import Path
import sys
import time
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src')); sys.path.insert(0, str(ROOT))
from beyond_consensus.experiments.rr_semantic_run import hashes, PATTERNS
from beyond_consensus.experiments.manifest import source_revision
from reporecourse.common import write_new
from reporecourse.qualification import runtime_versions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh output path')
    suite = unittest.TestSuite()
    for pattern in PATTERNS:
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=pattern))
    start = time.process_time()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    ok = result.wasSuccessful() and not result.skipped
    write_new(args.output, dict(schema='rr-semantic-run-controls-v1', status='passed' if ok else 'failed',
        source_revision=source_revision(ROOT), implementation_hashes=hashes(ROOT), runtime_versions=runtime_versions(),
        patterns=list(PATTERNS), tests=result.testsRun, skipped=len(result.skipped), errors=len(result.errors),
        failures=len(result.failures), model_executed=False, task_execution_allowed=False,
        evidence='CPU doubles plus production child controls; not model competence', analysis_cpu_seconds=time.process_time()-start))
    return 0 if ok else 2


if __name__ == '__main__':
    raise SystemExit(main())
