"""Proposed external conversion utility. Requires approved isolated pyarrow environment."""
import argparse,hashlib,importlib.metadata,json,os,signal,sys,time
from pathlib import Path

def write(path,value):
    raw=(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
    with open(path,'xb',opener=lambda p,f:os.open(p,f,0o600)) as handle:handle.write(raw)
    return hashlib.sha256(raw).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--approved-isolated-conversion',action='store_true')
    args=p.parse_args()
    if not args.approved_isolated_conversion:raise SystemExit('STOP: isolated conversion exception not recorded')
    cpu=time.process_time();wall=time.monotonic()
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(TimeoutError('conversion wall ceiling')));signal.alarm(300)
    if importlib.metadata.version('pyarrow')!='22.0.0':raise RuntimeError('pinned parser version')
    import pyarrow.parquet as pq
    import importlib.util
    spec=importlib.util.spec_from_file_location('aime_intake',args.repo/'scripts/prepare_prospective_aime.py')
    intake=importlib.util.module_from_spec(spec);spec.loader.exec_module(intake)
    sources=[(2025,'c94da77eb22bbd6439e62a323bec18493a421302',14313,'9f9066ff48ad2e31f9bf1b1ac6d5e80693195f987985f2859f89dd25ffa51c2d','2025-c94da77eb22b.e116gx4a'),(2026,'d61f486805306e6e6b5913504c07763a99e1b112',10062,'ae72853349a46c5f08666feb42db2d09fb4ac4fd4768c726b29702df21c7768e','2026-d61f48680530.4wn6b9z6')]
    args.output.mkdir(exist_ok=False);summaries=[]
    for year,rev,size,sha,directory in sources:
        source=Path('/dataset/suaq0001/beyond-consensus/datasets/aime')/directory/'source.parquet'
        with source.open('rb') as f:raw=f.read(size+1)
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:raise RuntimeError('source size/hash mismatch')
        # Parse the same verified bytes, not a subsequently reopened file.
        import pyarrow as pa
        table=pq.read_table(pa.BufferReader(raw),use_threads=False)
        expected={'problem_idx':'int64','problem':'string','answer':'int64'}
        if year==2025:expected['problem_type']='list'
        fields={f.name:f.type for f in table.schema}
        if table.num_rows!=30 or set(fields)!=set(expected):raise RuntimeError('unreviewed row count/schema')
        for name,kind in expected.items():
            if kind=='list':
                if not pa.types.is_list(fields[name]) or not pa.types.is_string(fields[name].value_type):raise RuntimeError('problem_type schema')
            elif str(fields[name])!=kind:raise RuntimeError('source field type')
        rows=table.to_pylist();target=args.output/str(year);target.mkdir()
        derived=target/'source.converted.private.json';derived_sha=write(derived,rows)
        receipt=dict(dataset=f'aime{year}',year=year,repository=f'MathArena/aime_{year}',revision=rev,sha256=derived_sha,format='json',upstream_path='data/train-00000-of-00001.parquet',split='train',read_authorized=True,authorization_reference='User approved local parsing after receipt verification; isolated parser exception separately approved',rights_review='publisher_declares_CC_BY_NC_SA_4_0',original_parquet_sha256=sha,conversion='pyarrow22_to_pylist_order_preserved')
        write(target/'access-receipt.json',receipt)
        pub,keys,meta,proc,summary=intake.inspect(derived,receipt)
        hashes={name:write(target/name,value) for name,value in [('source.public.json',pub),('evaluator.private.json',keys),('source.metadata.json',meta),('procedure.disabled.json',proc)]}
        summary.update(original_parquet_sha256=sha,converted_json_sha256=derived_sha,parser_version='22.0.0',file_hashes=hashes,source_directory=str(source.parent),original_rows_preserved=True)
        write(target/'inspection.json',summary);summaries.append(dict(directory=str(target),**summary))
    report=dict(status='local_conversion_and_structure_complete',years=summaries,cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,model_executed=False,execution_allowed=False,cohort_selected=False)
    write(args.output/'summary.json',report);print(json.dumps(report,indent=2));signal.alarm(0)
if __name__=='__main__':main()
