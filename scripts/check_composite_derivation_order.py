#!/usr/bin/env python3
"""Bounded local-tokenizer/CPU grammar check; never loads weights or dispatches."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def probe(factory,tokenizer,text,eos):
    matcher=factory()
    string_ok=matcher.accept_string(text) and matcher.accept_token(eos)
    ids=tokenizer.encode(text,add_special_tokens=False)
    matcher=factory()
    token_ok=all(matcher.accept_token(t) for t in [*ids,eos])
    return dict(string_plus_eos=bool(string_ok),tokens_plus_eos=bool(token_ok),
                roundtrip_exact=tokenizer.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)==text,
                synthetic_tokens=len(ids)+1)


def check(snapshot,export):
    from bc_phase2.composite_derivation_diagnostic import prepare,candidate_request
    from bc_phase2 import joint_d1_local as local
    from bc_phase2.d1_natural_screen import verify_non_thinking,render_request
    from bc_phase2.joint_schema import require
    from bc_phase2.model import digest
    proposal=prepare(export)
    require(importlib.metadata.version('xgrammar')=='0.1.32','pinned XGrammar required')
    versions={k:importlib.metadata.version(k) for k in local.VERSIONS}
    require(versions==local.VERSIONS,'pinned runtime package versions required')
    for name,h in local.METADATA.items():require(local.file_hash(snapshot/name)==h,'metadata changed: '+name)
    from transformers import AutoTokenizer
    import xgrammar as xgr
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
    template=verify_non_thinking(tokenizer)
    require(template==export['binding']['transport']['template'],'template binding changed')
    config=json.loads((snapshot/'config.json').read_text())
    size=config.get('text_config',config)['vocab_size'];eos=[248046,248044]
    info=xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=size,stop_token_ids=eos)
    compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
    rows=[]
    for row in proposal['tasks']:
        group=next(g for g in export['groups'] if (g['source_id'],g['task_id'])==(row['source_id'],row['task_id']))
        req=candidate_request(group['request']);rendered=render_request(tokenizer,req,template['template_hash'])
        grammar=compiler.compile_json_schema(row['candidate_schema'],any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
        factory=lambda:xgr.GrammarMatcher(grammar)
        values={k:'Synthetic "quoted" text; backslash \\ and newline\nUnicode π.' for k in row['candidate_fields']}
        correct=json.dumps(values,ensure_ascii=False)
        old_order=json.dumps({k:values[k] for k in row['historical_fields']},ensure_ascii=False)
        extra=json.dumps(values|{'unexpected':'x'},ensure_ascii=False)
        observations=[]
        for stop in eos:
            a=probe(factory,tokenizer,correct,stop);b=probe(factory,tokenizer,old_order,stop);c=probe(factory,tokenizer,extra,stop)
            passed=a['string_plus_eos'] and a['tokens_plus_eos'] and a['roundtrip_exact'] and not b['string_plus_eos'] and not b['tokens_plus_eos'] and not c['string_plus_eos'] and not c['tokens_plus_eos']
            observations.append(dict(eos=stop,derivation_first=a,historical_order=b,extra_key=c,passed=passed))
        rows.append(dict(source_id=row['source_id'],task_id=row['task_id'],input_tokens=rendered['input_tokens'],
            reserved_tokens=rendered['input_tokens']+3072,payload_digest=req['payload_digest'],rendered_ids_digest=rendered['rendered_ids_digest'],
            parent_digest=row['parent_digest'],schema_digest=row['candidate_schema_digest'],observations=observations,
            passed=all(x['passed'] for x in observations) and rendered['input_tokens']<=13312))
    return dict(schema='composite-derivation-order-cpu-v1',status='passed_cpu_checks' if all(r['passed'] for r in rows) else 'failed_cpu_checks',
        proposal_digest=proposal['proposal_digest'],rows=rows,total_reservation_tokens=sum(r['reserved_tokens'] for r in rows),
        versions=versions,xgrammar_version='0.1.32',template=template,model_executed=False,execution_allowed=False,gpu_qualified=False,
        limitations=['Synthetic order probes are observed CPU evidence, not mathematical or GPU qualification.','No live approval or dispatch is supplied by this check.'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot',type=Path,required=True)
    parser.add_argument('--export',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['CUDA_VISIBLE_DEVICES']=''
    start=time.perf_counter();cpu=time.process_time()
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second CPU check deadline')))
    with args.output.open('x') as f:
        signal.alarm(300)
        try:
            raw=args.export.read_bytes();result=check(args.snapshot,json.loads(raw))
            result['input_sha256']=hashlib.sha256(raw).hexdigest()
        except Exception as exc:
            result=dict(status='error',error_type=type(exc).__name__,error=str(exc),model_executed=False,execution_allowed=False)
        finally:signal.alarm(0)
        result.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start)
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'report':str(args.output),'status':result['status'],'model_executed':False}))
    return 0 if result['status']=='passed_cpu_checks' else 1
if __name__=='__main__':raise SystemExit(main())
