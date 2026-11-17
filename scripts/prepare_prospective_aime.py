#!/usr/bin/env python3
"""Inspect an explicitly authorised local pinned AIME JSON/JSONL package; no network or dispatch."""
import argparse,hashlib,json,os,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import prospective_adapters as adapter, prospective_pipeline as pipeline
from bc_phase2.joint_schema import decode,require
from bc_phase2.model import digest
CAP=16*1024*1024

def inspect(source,receipt):
    # Permission/provenance is checked before opening question-bearing bytes.
    require(receipt.get('read_authorized') is True and isinstance(receipt.get('authorization_reference'),str) and receipt['authorization_reference'].strip(),'explicit source-specific local read authorization')
    year=receipt.get('year');require(type(year) is int and year in (2025,2026),'separate AIME year')
    require(receipt.get('dataset')==f'aime{year}' and receipt.get('repository')==f'MathArena/aime_{year}','reviewed candidate repository/year; other packages need explicit adapter review')
    require(re.fullmatch('[0-9a-f]{40}',receipt.get('revision','')) is not None,'pinned revision')
    require(re.fullmatch('[0-9a-f]{64}',receipt.get('sha256','')) is not None,'pinned source hash')
    require(receipt.get('format') in ('json','jsonl') and receipt.get('upstream_path') and receipt.get('split'),'actual source format/path/split')
    with Path(source).open('rb') as f:raw=f.read(CAP+1)
    require(len(raw)<=CAP and hashlib.sha256(raw).hexdigest()==receipt['sha256'],'source size/hash')
    rows=decode(raw.decode('utf8')) if receipt['format']=='json' else [decode(line) for line in raw.decode('utf8').splitlines() if line.strip()]
    require(type(rows) is list and 0<len(rows)<=10000,'bounded records')
    public=[];private=[];metadata=[];issues=[]
    for index,row in enumerate(rows,1):
        require(type(row) is dict,'source row object')
        pub,key,meta=adapter.aime(row,year,receipt['revision'],index)
        public.append(pub);private.append(key);metadata.append(meta)
        if key['status']!='known':issues.append(dict(source_id=pub['id'],issue='unknown_reference'))
    procedure=pipeline.procedure(f'aime{year}')
    summary=dict(status='local_structure_inspected_not_admitted',dataset=f'aime{year}',repository=receipt['repository'],revision=receipt['revision'],source_sha256=receipt['sha256'],upstream_path=receipt['upstream_path'],split=receipt['split'],records=len(rows),field_presence={k:sum(k in r for r in rows) for k in sorted(set().union(*(set(r) for r in rows)))},unknown_reference_count=len(issues),issues=issues,identity_policy='one-based release row qualified by year and revision; problem_idx is retained, not inferred to be contest number',rights_review=receipt.get('rights_review','unresolved'),original_contest_identity_verified=False,family_review_verified=False,cohort_selected=False,execution_allowed=False,model_executed=False,procedure_digest=procedure['procedure_digest'])
    return public,private,metadata,procedure,summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('source','receipt','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();cpu=time.process_time();wall=time.monotonic()
    with a.receipt.open('rb') as f:raw=f.read(65537)
    require(len(raw)<=65536,'bounded access receipt')
    receipt=decode(raw.decode('utf8'))
    public,private,metadata,procedure,summary=inspect(a.source,receipt)
    a.output.mkdir(exist_ok=False)
    hashes={}
    # Private references stay outside public inventory and planner requests.
    for name,value in [('source.public.json',public),('evaluator.private.json',private),('source.metadata.json',metadata),('procedure.disabled.json',procedure)]:
        data=(json.dumps(value,indent=2)+'\n').encode()
        path=a.output/name
        with open(path,'xb',opener=lambda p,flags:os.open(p,flags,0o600)) as f:f.write(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    summary.update(file_hashes=hashes,access_receipt_sha256=hashlib.sha256(raw).hexdigest(),cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall)
    with (a.output/'inspection.json').open('x') as f:json.dump(summary,f,indent=2);f.write('\n')
    print(json.dumps(dict(report=str(a.output/'inspection.json'),**summary),indent=2))
if __name__=='__main__':main()
