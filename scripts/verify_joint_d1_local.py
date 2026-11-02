#!/usr/bin/env python3
"""Local-only D1 weight hashing/tokenizer inspection; never model loading or inference."""
import argparse
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def local_tokenizer(*args,**kwargs):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(*args,**kwargs)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--statements',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('output already exists; preserve previous evidence')
    from bc_phase2.joint_d1_local import read_json,verify_local
    # Applies only to this verification process; does not alter shell or host configuration.
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    os.environ['CUDA_VISIBLE_DEVICES']=''
    # Fail closed if any dependency attempts network, even with local-only options.
    def audit(event,arguments):
        if event in {'socket.connect','socket.getaddrinfo'}:
            raise RuntimeError('network forbidden during D1 local verification')
    sys.addaudithook(audit)
    print('Hashing local snapshot and inspecting tokenizer; no model loading.',flush=True)
    try:
        result=verify_local(read_json(args.receipt),args.statements,local_tokenizer)
    except Exception as exc:
        failure={'status':'failed_local_verification','error_type':type(exc).__name__,
                 'error':str(exc),'model_executed':False,'execution_allowed':False}
        with args.output.open('x') as handle:json.dump(failure,handle,indent=2);handle.write('\n')
        raise
    with args.output.open('x') as handle:json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps({'report':str(args.output),**{k:result[k] for k in ('status','initial_requests','correction_fit','model_executed','execution_allowed')},
        'weight_shards':len(result['inventory']['weight_shards']),
        'trusted_weight_reference_compared':False},indent=2))

if __name__=='__main__':main()
