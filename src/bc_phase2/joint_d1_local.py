"""Authorized local D1 source/inventory preparation, never a model executor.

Tokenization is injected by callers; this module and CLI help stay stdlib-only.
The CLI uses local AutoTokenizer only, never AutoModel or generation.
"""
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path
from types import SimpleNamespace

from .joint_schema import require, decode
from .joint_d1_readiness import SMOKE, NEUTRAL_PROMPT, PROMPT_VERSION
from .joint_pipeline_contracts import planner_payload
from .joint_d1_qwen import configuration, implementation
from .planner_qwen import CHECKPOINT, REVISION, render_qwen_request
from .model import digest

DATASET_HASH='35dc41080a3680858b27fa7e0533d2d547825316fc5dafe5d316f4ccc5a06132'
STATEMENTS_HASH='2fa5ec1bb789920d11cbf991707aeb5a65529a2b7f8e4aed9a65b021bd4cdc66'
STATEMENT_HASHES=dict(zip(SMOKE,(
 'ad5b14b23ed9a9ea6232a345705013fe97fcefb1c39c4080305c21c38291cddd',
 '30257ce512a9dbe4ce54665865cbef81235971574bf2ddf89c2eecd7980ac380',
 '3808c227b8b95556a87934db0d3956810196a7af033fa45845ba3c21d32cc310')))
METADATA={
 'config.json':'f8d190c5b89c1521220f935d2567a587d6e291ed69066a45a106560b05a2174c',
 'generation_config.json':'303aba891d66ab63908a7b3cc9163bcb835fdf8b9f6301c73216f3f1eb3992dd',
 'tokenizer.json':'5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42',
 'tokenizer_config.json':'316230d6a809701f4db5ea8f8fc862bc3a6f3229c937c174e674ff3ca0a64ac8',
 'model.safetensors.index.json':'b3737e9d00bda0e37f0b873629d98bf9b407bef35735b9193c23d9844bcc96a6',
 'chat_template.jinja':'a4aee8afcf2e0711942cf848899be66016f8d14a889ff9ede07bca099c28f715'}
VERSIONS={'torch':'2.10.0+cu126','transformers':'5.3.0','tokenizers':'0.22.2',
          'huggingface-hub':'1.5.0','safetensors':'0.7.0'}
TEMPLATE_HASH='12de9034d5269e8b1fe6012b3538374fcb3941bf93c95fc81b0cf5acf3f08ce4'
SOURCE_PERMISSION={'status':'confirmed_by_user','scope':'inspect_and_extract_three_frozen_statements',
                   'execution_authorized':False}


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def read_json(path,cap=2*1024*1024):
    with Path(path).open('rb') as handle:raw=handle.read(cap+1)
    require(len(raw)<=cap,'input byte bound')
    return decode(raw.decode('utf8'))


def validate_receipt(receipt):
    require(type(receipt) is dict,'receipt object')
    require(receipt.get('status')=='statement_extraction_and_metadata_inspection_complete','receipt status')
    require(receipt.get('source_ids')==list(SMOKE),'frozen source order')
    require(receipt.get('dataset_sha256')==DATASET_HASH,'dataset hash')
    require(receipt.get('statements_file_sha256')==STATEMENTS_HASH and
            receipt.get('statement_hashes')==STATEMENT_HASHES,'statement receipt hashes')
    require(receipt.get('checkpoint')==CHECKPOINT and receipt.get('revision')==REVISION,'model identity')
    require(type(receipt.get('model_path')) is str and Path(receipt['model_path']).name==REVISION,'snapshot locator')
    require(type(receipt.get('directory')) is str and Path(receipt['directory']).is_absolute(),'receipt directory')
    for name,h in METADATA.items():
        require(receipt.get('metadata',{}).get(name,{}).get('sha256')==h,'metadata hash: '+name)
    for name,v in VERSIONS.items():require(receipt.get('packages',{}).get(name)==v,'package version: '+name)
    require(receipt.get('execution_allowed') is False and receipt.get('model_executed') is False,'receipt not execution')
    return receipt


def bind_receipt(root,receipt):
    """Record supplied evidence without falsely claiming remote content verification."""
    validate_receipt(receipt)
    value=configuration(root);scope=value['scope']
    scope['source_receipts']={'status':'reported_extraction_hashes','receipt_digest':digest(receipt),
        'directory':receipt['directory'],'source_ids':list(SMOKE),'dataset_sha256':DATASET_HASH,
        'statements_file_sha256':STATEMENTS_HASH,'statement_hashes':dict(STATEMENT_HASHES)}
    scope['source_access_permission']=dict(SOURCE_PERMISSION)
    # Final transmission is covered by the later exact D1 execution approval.
    scope['statement_transmission_permission']=None
    scope['settings_accepted']=True;scope['limits_accepted']=True
    scope['local_inventory']={'status':'metadata_reported_weights_unverified',
        'checkpoint':CHECKPOINT,'revision':REVISION,'local_path':receipt['model_path'],
        'metadata_hashes':dict(METADATA),'receipt_digest':digest(receipt)}
    value['scope_digest']=digest(scope)
    return value


def statement_records(path,expected_ids,expected_file_hash,expected_hashes):
    """Exact statement-only file boundary, also testable with synthetic IDs/hashes."""
    require(file_hash(path)==expected_file_hash,'statement file hash changed')
    rows=read_json(path)
    require(type(rows) is list and len(rows)==len(expected_ids),'statement count')
    require(all(type(r) is dict and set(r)=={'id','problem'} for r in rows),'protected/unknown statement fields')
    require([r['id'] for r in rows]==list(expected_ids),'statement order')
    for row in rows:
        require(type(row['problem']) is str and bool(row['problem'].strip()),'statement text')
        require(hashlib.sha256(row['problem'].encode('utf8')).hexdigest()==expected_hashes[row['id']],
                'statement content changed')
    return rows


def render_statements(tokenizer,rows,template_hash):
    results=[]
    for row in rows:
        payload=planner_payload(row,4,2);payload.update(prompt=NEUTRAL_PROMPT,prompt_version=PROMPT_VERSION)
        request={'payload':payload,'payload_digest':digest(payload)}
        rendered=render_qwen_request(tokenizer,request,template_hash)
        results.append({'source_id':row['id'],'payload_digest':request['payload_digest'],
                        'rendered_ids_digest':digest(rendered['input_ids']),
                        'input_tokens':rendered['input_tokens'],'output_reservation_tokens':6144})
    return results


def snapshot_inventory(root,expected_metadata):
    """Hash local files, including HF symlink targets; no weight deserialization.

    Weight digests are observations unless independently compared to trusted hashes.
    Reject subdirectories/foreign payloads instead of loading unbound templates/code.
    """
    root=Path(root)
    require(root.is_dir(),'local snapshot missing')
    entries=sorted(root.iterdir())
    require(all(p.is_file() for p in entries),'snapshot contains directories or nonfiles')
    allowed={'.json','.jinja','.safetensors','.txt','.md','.model','.tiktoken'}
    require(all(p.suffix.lower() in allowed for p in entries),'unexpected snapshot file type')
    files={p.name:file_hash(p) for p in entries}
    require(all(files.get(n)==h for n,h in expected_metadata.items()),'snapshot metadata differs')
    index=read_json(root/'model.safetensors.index.json')
    mapping=index.get('weight_map')
    require(type(mapping) is dict and bool(mapping),'weight map')
    shards=sorted(set(mapping.values()))
    require(all(type(n) is str and Path(n).name==n and n.endswith('.safetensors') and n in files for n in shards),
            'missing or unsafe shard name')
    return {'files':files,'weight_shards':shards,'weight_bytes':sum((root/n).stat().st_size for n in shards),
            'weight_hashes_observed':True,'trusted_weight_reference_compared':False}


def verify_local(receipt,statements,tokenizer_loader):
    """Called only by explicit verification CLI. No model import or execution."""
    wall_start=time.monotonic();cpu_start=time.process_time()
    validate_receipt(receipt)
    root=Path(receipt['model_path'])
    versions={name:importlib.metadata.version(name) for name in VERSIONS}
    require(versions==VERSIONS,'current environment differs from receipt')
    rows=statement_records(statements,SMOKE,STATEMENTS_HASH,STATEMENT_HASHES)
    inventory=snapshot_inventory(root,METADATA)
    # No extra tokenizer files may appear during loading.
    tokenizer=tokenizer_loader(str(root),local_files_only=True,trust_remote_code=False)
    from beyond_consensus.models.transformers_backend import verify_thinking_template,generation_tokens
    template=verify_thinking_template(tokenizer,True)
    require(template['template_hash']==TEMPLATE_HASH,'runtime template mismatch')
    gc=read_json(root/'generation_config.json')
    tokens=generation_tokens(tokenizer,SimpleNamespace(eos_token_id=gc.get('eos_token_id'),pad_token_id=gc.get('pad_token_id')))
    require(tokens=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop configuration changed')
    closing=tokenizer.convert_tokens_to_ids('</think>')
    require(type(closing) is int and closing>=0 and closing not in tokens['eos_token_id']
            and tokenizer.encode('</think>',add_special_tokens=False)==[closing],'thinking delimiter')
    calls=render_statements(tokenizer,rows,template['template_hash'])
    # Small metadata recheck; full weight rehash will be a future load-bound check.
    require(all(file_hash(root/n)==h for n,h in METADATA.items()),'metadata changed while tokenizing')
    return {'schema':'joint-d1-local-verification-v1','status':'local_inventory_and_initial_tokenization_observed',
            'receipt_digest':digest(receipt),'source_ids':list(SMOKE),'statements_file_sha256':STATEMENTS_HASH,
            'statement_hashes':dict(STATEMENT_HASHES),
            'implementation':implementation(Path(__file__).resolve().parents[2]),
            'accounting':{'ledger':'offline_preparation_not_model_usage','cpu_seconds':time.process_time()-cpu_start,
                          'wall_seconds':time.monotonic()-wall_start},
            'local_path':str(root),'checkpoint':CHECKPOINT,'revision':REVISION,'inventory':inventory,
            'template':template,'generation_tokens':tokens,'packages':versions,'initial_requests':calls,
            'correction_fit':'checked_at_dispatch_not_worst_case_qualified','model_executed':False,
            'execution_allowed':False,'gpu_used':False,'worst_case_fit_established':False}
