#!/usr/bin/env python3
"""Run repository regressions excluding legacy Phase I large-domain execution."""
import hashlib,json,sys,time,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))

def result_record(result, registration, wall_seconds, cpu_seconds):
    return {'status':'passed' if result.wasSuccessful() else 'failed',
            'tests':result.testsRun,
            'skipped':[(str(t),reason) for t,reason in result.skipped],
            'failures':[(str(t),msg) for t,msg in result.failures],
            'errors':[(str(t),msg) for t,msg in result.errors],
            'wall_seconds':wall_seconds,'cpu_seconds':cpu_seconds,
            'NOT_RUN_PERMISSION':registration['NOT_RUN_PERMISSION'],
            'full_discovery_executed':False}

def main():
    out=Path(sys.argv[1])/(sys.argv[2] if len(sys.argv)>2 else 'safe-tests-01');out.mkdir(exist_ok=False)
    excluded={'test_phase1.py','test_phase1_n7.py','test_phase1_reporting.py','test_phase1_v31.py'}
    paths=sorted((ROOT/'tests').glob('test*.py'))
    registration={'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'NOT_RUN_PERMISSION':{name:'Legacy Phase I file withheld conservatively: contains or depends on larger-domain scoring/solving; not a pass or unittest skip.' for name in sorted(excluded)}}
    (out/'manifest.json').write_text(json.dumps(registration,indent=2))
    suite=unittest.TestSuite();loader=unittest.TestLoader()
    for p in paths:
        if p.name not in excluded:suite.addTests(loader.discover(str(ROOT/'tests'),pattern=p.name,top_level_dir=str(ROOT)))
    start=time.monotonic();cpu=time.process_time()
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    record=result_record(result,registration,time.monotonic()-start,time.process_time()-cpu)
    encoded=json.dumps(record,indent=2)
    with (out/'results.json').open('x') as handle:handle.write(encoded)
    return not result.wasSuccessful()
if __name__=='__main__':raise SystemExit(main())
