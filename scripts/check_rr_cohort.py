#!/usr/bin/env python3
"""No-skip CPU controls for prospective scheduling, scoped JIT and rich references."""
import argparse
from pathlib import Path
import sys,time,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT))
from reporecourse.qualification import runtime_versions
from reporecourse.track_f_controls import PINS
from reporecourse.common import write_new
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.experiments.rr_cohort import control_hashes


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('Use a fresh output path')
    versions=runtime_versions()
    if any(versions.get(k)!=v for k,v in PINS.items()):p.error('Pinned CPU dependencies required')
    suite=unittest.TestSuite()
    patterns=('test_rr_cohort.py','test_rr_rich_tasks.py','test_reporecourse_v2.py','test_reporecourse_scoped.py','test_rr_open_clean.py','test_rr_open_fault.py')
    for pattern in patterns:suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    start=time.process_time();r=unittest.TextTestRunner(verbosity=2).run(suite)
    ok=r.wasSuccessful() and not r.skipped
    write_new(a.output,dict(schema='rr-cohort-controls-v1',status='passed' if ok else 'failed',
        source_revision=source_revision(ROOT),implementation_hashes=control_hashes(ROOT),runtime_versions=versions,
        tests=r.testsRun,skipped=len(r.skipped),failures=len(r.failures),errors=len(r.errors),patterns=list(patterns),
        model_executed=False,sql_executed=True,task_execution_allowed=False,
        evidence='CPU doubles and actual trusted-child reference tests; not model competence',analysis_cpu_seconds=time.process_time()-start))
    return 0 if ok else 2

if __name__=='__main__':raise SystemExit(main())
