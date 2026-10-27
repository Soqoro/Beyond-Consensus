#!/usr/bin/env python3
"""Run bounded local review commands and preserve each command's actual exit."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--local-dependencies');args=p.parse_args()
    out=Path(args.output).resolve();out.mkdir(exist_ok=False)
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1'
    if args.local_dependencies:env['PYTHONPATH']=str(Path(args.local_dependencies).resolve())
    cmds=[
        ('help-stdlib',[sys.executable,'-S','scripts/phase2.py','--help']),
        ('template-stdlib',[sys.executable,'-S','scripts/phase2.py','validate-template']),
        ('phase2-tests',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_phase2_v3.py','-v']),
        ('exact-binding-timing',[sys.executable,'scripts/phase2_validate.py','--output',str(out/'verification')]),
        ('mock-demo',[sys.executable,'scripts/phase2.py','mock-demo','--output',str(out/'mock')]),
        ('mock-resume',[sys.executable,'scripts/phase2.py','mock-demo','--output',str(out/'mock')]),
        ('scoped-regression',[sys.executable,'scripts/phase1_exhaustive_safe_tests.py',str(out),'regression']),
        ('shell-checks',[sys.executable,'scripts/check_shell.py'])]
    started=time.monotonic();records=[]
    for name,cmd in cmds:
        remaining=600-(time.monotonic()-started)
        if remaining<=0:break
        begin=time.monotonic();log=out/(name+'.log')
        with log.open('x') as handle:
            try:
                result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=handle,stderr=subprocess.STDOUT,timeout=min(180,remaining),check=False)
                code=result.returncode
            except subprocess.TimeoutExpired:code='timeout'
        rec={'name':name,'argv':cmd,'exit_status':code,'wall_seconds':time.monotonic()-begin,'log':str(log),'sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
        records.append(rec)
        with (out/'commands.json').open('w') as handle:json.dump(records,handle,indent=2)
        print(json.dumps({k:v for k,v in rec.items() if k in ('name','exit_status','wall_seconds')}),flush=True)
        if code!=0:break
    status='passed' if len(records)==len(cmds) and all(r['exit_status']==0 for r in records) else 'incomplete_or_failed'
    (out/'review-status.json').write_text(json.dumps({'status':status,'commands':len(records),'wall_seconds':time.monotonic()-started,'limits':{'total_wall_seconds':600,'per_command_wall_seconds':180},'real_execution':False},indent=2))
    return status!='passed'
if __name__=='__main__':raise SystemExit(main())
