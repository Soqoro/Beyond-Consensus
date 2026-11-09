#!/usr/bin/env python3
"""Prepare a disabled six-call interface diagnostic; no models or dispatch."""
import argparse,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    from bc_phase2.composite_derivation_diagnostic import prepare
    start=time.perf_counter();cpu=time.process_time();raw=args.export.read_bytes()
    result=prepare(json.loads(raw))
    packet=dict(proposal=result,input_file_sha256=hashlib.sha256(raw).hexdigest(),cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start)
    with args.output.open('x') as f:json.dump(packet,f,indent=2);f.write('\n')
    print(json.dumps({'report':str(args.output),'execution_allowed':False,'proposal_digest':result['proposal_digest']}))
if __name__=='__main__':main()
