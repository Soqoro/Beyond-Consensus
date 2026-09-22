#!/usr/bin/env python3
"""CPU synthetic compiler qualification. Requires the optional pinned parser."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.runtime.sql_text import VERSION, contract
from beyond_consensus.util import file_hash


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): raise SystemExit('Use a fresh report path')
    if importlib.metadata.version('sqlglot')!=VERSION: raise SystemExit('Wrong SQLGlot version')
    started=time.process_time()
    suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_sql_text')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    root=Path(__file__).resolve().parents[1]
    report={'schema':'bc-sql-frontend-qualification-v1','status':'passed' if result.wasSuccessful() and not result.skipped else 'failed',
            'tests':result.testsRun,'skipped':len(result.skipped),'contract':contract(),
            'implementation_hashes':{name:file_hash(root/name) for name in (
                'src/beyond_consensus/runtime/sql_text.py','src/beyond_consensus/runtime/sqlite_executor.py','tests/test_sql_text.py')},
            'model_executed':False,'sql_executed':True,'inputs':'synthetic_only',
            'parent_cpu_seconds':time.process_time()-started,'native_reference_approval':False}
    with args.output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':sys.exit(main())
