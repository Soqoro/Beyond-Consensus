#!/usr/bin/env python3
"""Offline public-source inventory, fixed cohort and reviewed block preparation. No dispatch."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_sources as s, prospective_pipeline as p, prospective_adapters as a
from bc_phase2.joint_schema import decode,require
from bc_phase2.model import digest

def read(path):
    raw=path.read_bytes();require(len(raw)<=64*1024*1024,'bounded input');return decode(raw.decode())
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    q=sub.add_parser('extract-math')
    for x in ('source','output'):q.add_argument('--'+x,type=Path,required=True)
    q.add_argument('--local-source-read-authorized',action='store_true')
    q=sub.add_parser('inventory')
    for x in ('public','access-receipt','output'):q.add_argument('--'+x,type=Path,required=True)
    q=sub.add_parser('freeze')
    for x in ('inventory','exposure','family-review','output'):q.add_argument('--'+x,type=Path,required=True)
    q=sub.add_parser('block-plan')
    for x in ('cohort','public','output'):q.add_argument('--'+x,type=Path,required=True)
    q.add_argument('--slot',type=int,required=True)
    q=sub.add_parser('block')
    for x in ('cohort','dispositions','output'):q.add_argument('--'+x,type=Path,required=True)
    q.add_argument('--slot',type=int,required=True)
    args=ap.parse_args();start=time.process_time()
    if args.command=='extract-math':
        require(args.local_source_read_authorized,'explicit local source read permission')
        raw=args.source.read_bytes()
        require(hashlib.sha256(raw).hexdigest()=='35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132','pinned MATH-500 bytes')
        rows=[decode(line) for line in raw.decode().splitlines()]
        require(len(rows)==500 and len({r['unique_id'] for r in rows})==500,'pinned unique records')
        result=[{'id':r['unique_id'],'problem':r['problem']} for r in rows]
    elif args.command=='inventory':
        receipt=read(args.access_receipt);raw=args.public.read_bytes()
        require(receipt.get('read_authorized') is True and receipt.get('authorization_reference'), 'source-specific read permission')
        require(hashlib.sha256(raw).hexdigest()==receipt['sha256'],'source package hash')
        require(receipt['dataset'] in s.SIZES and receipt.get('revision'), 'pinned release')
        require(receipt['dataset']!='medqa' or receipt.get('split')=='test' or receipt.get('explicit_pool_amendment'),
                'MedQA test pool or explicit new pool amendment; historical dev exception is insufficient')
        rows=read(args.public);require(type(rows)is list and len(rows)<=10000,'public records list')
        metadata=[]
        for row in rows:
            exact,normal=s.faithful_identity(row)
            if 'options' in row:
                require(len(set(' '.join(v.split()) for v in row['options'].values()))==4,'distinct options')
            metadata.append(dict(source_id=row['id'],canonical_id=receipt['dataset']+':'+row['id'],
                                 exact_hash=exact,normalized_hash=normal,family_id='',status='eligible'))
        result=dict(dataset=receipt['dataset'],revision=receipt['revision'],records=metadata,access_receipt=receipt,
                    procedure=p.procedure(receipt['dataset']),execution_allowed=False)
    elif args.command=='freeze':
        inv=read(args.inventory)
        result=s.freeze(inv['records'],inv['dataset'],inv['revision'],read(args.exposure),inv['procedure'],read(args.family_review))
    elif args.command=='block-plan':result=p.planning_packet(read(args.cohort),args.slot,{r['id']:r for r in read(args.public)})
    else:result=p.wave(read(args.cohort),args.slot,read(args.dispositions))
    write(args.output,result)
    print(json.dumps(dict(report=str(args.output),status=result.get('status','prepared_offline') if isinstance(result,dict) else 'public_extraction',
                         cpu_seconds=time.process_time()-start,model_executed=False,execution_allowed=False)))
if __name__=='__main__':main()
