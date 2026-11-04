#!/usr/bin/env python3
"""Disabled natural-subtask pilot preparation and optional local tokenizer inspection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from bc_phase2 import d1_natural_screen as pilot


def write(path,value):
    with path.open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')


def inspect_tokenizer(snapshot,statements=None,cluster=None):
    # Metadata/tokenizer only. Never call the old full-inventory function: it hashes weights.
    from bc_phase2.joint_d1_local import METADATA,TEMPLATE_HASH
    from bc_phase2.model import digest
    if not snapshot.is_absolute() or snapshot.name!=pilot.REVISION:raise ValueError('exact pinned snapshot required')
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
    def guard(event,args):
        if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network forbidden')
        if event=='open' and isinstance(args[0],(str,bytes)) and os.fsdecode(args[0]).endswith(('.safetensors','.bin','.pt','.pth')):
            raise RuntimeError('weight access forbidden')
    sys.addaudithook(guard)
    files={}
    for name in ('config.json','tokenizer.json','tokenizer_config.json','chat_template.jinja'):
        raw=(snapshot/name).read_bytes();h=hashlib.sha256(raw).hexdigest()
        if h!=METADATA[name]:raise ValueError('metadata mismatch: '+name)
        files[name]={'sha256':h,'bytes':len(raw)}
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
    if digest(tokenizer.chat_template)!=TEMPLATE_HASH:raise ValueError('selected template differs from prior binding')
    check=pilot.verify_non_thinking(tokenizer)
    record={'id':'mock:template-probe','problem':'Synthetic placeholder; describe a single symbolic transformation.'}
    req=pilot.request(record);rendered=pilot.render_request(tokenizer,req,check['template_hash'])
    result={'status':'synthetic_non_thinking_template_observed','checkpoint':pilot.CHECKPOINT,'revision':pilot.REVISION,
            'files':files,'template_check':check,'synthetic_input_tokens':rendered['input_tokens'],
            'synthetic_rendered_ids_digest':rendered['rendered_ids_digest'],'output_reservation_tokens':pilot.OUTPUT,
            'real_source_counts':None,'model_executed':False,'execution_allowed':False,
            'note':'Template observation only; no generated response or real-source fit qualification.'}
    if statements is not None:
        # Explicit path only: no dataset discovery and no original-record access.
        # Use only under the user's existing permission for these exact extracted views.
        from bc_phase2.joint_d1_local import statement_records,STATEMENTS_HASH,STATEMENT_HASHES,file_hash
        rows=statement_records(statements,pilot.SMOKE,STATEMENTS_HASH,STATEMENT_HASHES)
        measured=[]
        for row in rows:
            req=pilot.request(row);view=pilot.render_request(tokenizer,req,check['template_hash'])
            measured.append({'source_id':row['id'],'statement_sha256':STATEMENT_HASHES[row['id']],
                             'payload_digest':req['payload_digest'],'rendered_ids_digest':view['rendered_ids_digest'],
                             'input_tokens':view['input_tokens'],'reserved_tokens':view['input_tokens']+pilot.OUTPUT})
        if file_hash(statements)!=STATEMENTS_HASH:raise ValueError('source changed during verification')
        result.update(status='three_statement_requests_tokenized_no_model',real_source_counts=measured,
                      statements_file=str(statements.resolve()),statements_file_sha256=STATEMENTS_HASH,
                      source_access_basis='explicit_invocation_for_previously_authorized_exact_extracted_views',
                      statement_transmission_performed=False)
    if cluster is not None:
        import re,subprocess
        raw=cluster.read_bytes();cfg=json.loads(raw);partition=cfg.get('partition')
        if not isinstance(partition,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',partition):raise ValueError('one explicit partition required')
        if cfg.get('time')!='01:00:00' or cfg.get('memory_gb')!=128:
            raise ValueError('cluster must match proposed one-hour/128GB ceiling; no silent resource adjustment')
        completed=subprocess.run(['scontrol','show','partition',partition,'-o'],capture_output=True,text=True,timeout=20,check=True)
        result['scheduler']={'cluster_path':str(cluster.resolve()),'cluster_sha256':hashlib.sha256(raw).hexdigest(),
                             'partition':partition,'query_argv':completed.args,'partition_record':completed.stdout,
                             'requested_cpus':4,'requested_gpus':1,'requested_memory_gb':128,'requested_wall_seconds':3600,
                             'physical_gpu_type_and_vram_verified':False,'allocation_tested':False,'submitted':False}
        result['note']='Read-only partition record is not a current allocation guarantee or GPU VRAM verification.'
    result['interface_implementation']=pilot.implementation()
    result['prompt_hash']=digest(pilot.PROMPT)
    result['schema_hash']=digest(pilot.response_schema())
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','preflight','approval-template','inspect-tokenizer'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--statements',type=Path,help='Exact previously authorized statement-only file; never original dataset')
    parser.add_argument('--cluster',type=Path,help='Optional one-hour/128GB cluster JSON; read-only scontrol query')
    args=parser.parse_args()
    if args.command=='prepare':
        args.output.mkdir(exist_ok=False)
        manifest=pilot.disabled_manifest()
        write(args.output/'PILOT_DISABLED_MANIFEST.json',manifest)
        write(args.output/'D1_NATURAL_SCREEN_V1_SCHEMA.json',pilot.response_schema())
        (args.output/'D1_NATURAL_SCREEN_V1_PROMPT.txt').write_text(pilot.PROMPT+'\n')
        write(args.output/'SOURCE_RECEIPTS_STATUS.json',dict(manifest['scope']['source_package'],
              source_ids=manifest['scope']['source_ids'],source_bytes_read=False,permission_status='new_scope_permission_missing'))
        write(args.output/'PREFLIGHT.json',pilot.preflight(manifest))
        print(json.dumps({'directory':str(args.output),'status':'prepared_disabled','model_executed':False}))
        return
    if args.output.exists():parser.error('output already exists')
    if args.command=='inspect-tokenizer':
        if args.snapshot is None:parser.error('--snapshot required')
        result=inspect_tokenizer(args.snapshot,args.statements,args.cluster)
    else:
        if args.manifest is None:parser.error('--manifest required')
        manifest=json.loads(args.manifest.read_text());status=pilot.preflight(manifest)
        if args.command=='preflight':result=status
        else:result={'schema':'D1-natural-screen-v1-approval-template','decision':'pending',
                     'proposal_digest':manifest['scope_digest'],'final_scope_digest':None,
                     'source_read_and_transmit':False,'maximum_calls':3,'calls_per_source':1,
                     'missing':status['blockers'],'execution_allowed':False,
                     'note':'Not signable as a dispatch receipt until source/tokenizer/resource scope is complete.'}
    write(args.output,result)
    print(json.dumps({'report':str(args.output),'status':result.get('status',result.get('decision')),'execution_allowed':False}))

if __name__=='__main__':main()
