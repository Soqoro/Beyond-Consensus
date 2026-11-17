#!/usr/bin/env python3
"""Offline exact-label grading of the completed block 2 result; no model or dispatch."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_medqa_block2_worker_launch as worker
from bc_phase2.joint_schema import require

def pinned(path,expected):
    with Path(path).open('rb') as f:raw=f.read(8*1024*1024+1)
    require(len(raw)<=8*1024*1024 and hashlib.sha256(raw).hexdigest()==expected,'grading input hash/size')
    return json.loads(raw)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('result','public','private','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();cpu=time.process_time();wall=time.monotonic()
    rh='284ae82c2832d9e2c678842bd335429bae4370eb78e735785985aece4872d66b'
    kh='8cb9e441d0a0ae52c8114197a26490b8e81a15a80407e99601ebdf4058997778'
    r=pinned(a.result,rh);pub=pinned(a.public,worker.planner.PUBLIC_HASH);keys=pinned(a.private,kh)
    require(isinstance(pub,list),'public list');by={v['id']:v for v in pub}
    if isinstance(keys,list):keys={v['id']:v for v in keys}
    require(isinstance(keys,dict),'private key map')
    grading=worker.grade_results(r,by,keys)
    summary={}
    for method in ('NEUTRAL','JOINT'):
        summary[method]={}
        for slot in ['clean']+['owner/o'+str(i) for i in range(4)]:
            rows=[v for v in grading['rows'] if v['method']==method and v['slot']==slot]
            summary[method][slot]=dict(records=len(rows),graded=sum(v['grade']['status']=='graded' for v in rows),correct=sum(v['grade'].get('correct') is True for v in rows),all_sources_key_correct=len(rows)==4 and all(v['grade'].get('correct') is True for v in rows))
    report=dict(purpose='Offline exact-label grading; private answer map excluded',scope_digest='79f820f324041f6149ba49e98a575b78ff5ea55b2701810df0a18a66f0200622',result_sha256=rh,evaluator_sha256=kh,summary=summary,grading=grading,cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,model_executed=False,historical_results_changed=False)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(report=str(a.output),summary=summary,model_executed=False),indent=2))
if __name__=='__main__':main()
