"""Construct public task-grounded plans; optionally certify private CPU references."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reporecourse.organization_sampler import qualify_catalog
from reporecourse.common import write_new


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sources',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pool',type=int,default=7)
    p.add_argument('--candidate-limit',type=int,default=12)
    p.add_argument('--qualify',action='store_true')
    a=p.parse_args();report=qualify_catalog(a.sources,a.pool,a.candidate_limit,a.qualify)
    write_new(a.output,report)
    print(json.dumps(dict(report=str(a.output),catalog_id=report['catalog_id'],status=report['status'],
        tasks=[dict(task=r['task'],selected=len(r['selected']),qualified=r['qualified_plans'],blockers=r['blockers']) for r in report['tasks']],
        model_executed=False,task_execution_allowed=False),indent=2))

if __name__=='__main__':main()
