#!/usr/bin/env python3
"""Bounded synthetic CPU diagnostics, never a qualification pass or live dispatch."""
import argparse
import hashlib
import json
from pathlib import Path
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def trace_tokens(factory,ids,eos,tokenizer):
    matcher=factory()
    for index,token in enumerate([*ids,eos]):
        if not matcher.accept_token(token):
            return dict(accepted=False,first_rejected_index=index,first_rejected_id=token,
                rejection_stage='eos' if index==len(ids) else 'content',
                token_text=tokenizer.decode([token],skip_special_tokens=False,clean_up_tokenization_spaces=False),
                accepted_prefix_tail=tokenizer.decode(ids[:index],skip_special_tokens=False,clean_up_tokenization_spaces=False)[-160:])
    return dict(accepted=True,first_rejected_index=None,first_rejected_id=None,rejection_stage=None)


def inspect(snapshot,failed):
    from bc_phase2 import composite_math as recipe, composite_math_decoder as decoder, joint_d1_local as local
    from bc_phase2.model import digest
    from bc_phase2.joint_schema import require
    from beyond_consensus.models.constrained import load_xgrammar
    require(failed['schema']=='composite-json-cpu-v1' and failed['status']=='failed','original failed qualification required')
    require(failed['condition']==recipe.CONDITION,'condition changed')
    for task,row in zip(recipe.TASKS,failed['rows']):require(row['schema_hash']==digest(decoder.schema(task)),'grammar changed')
    require(len(failed['rows'])==5,'five failed controls')
    require(all(local.file_hash(snapshot/k)==v for k,v in local.METADATA.items()),'pinned metadata')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
    cfg=json.loads((snapshot/'config.json').read_text());size=cfg.get('text_config',cfg)['vocab_size']
    xgr,_=load_xgrammar();eos=[248046,248044]
    info=xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=size,stop_token_ids=eos)
    compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
    fixtures=[('original','Synthetic "quoted" text; backslash \\ and newline\nUnicode π.'),
              ('plain','Synthetic text.'),('quote','Synthetic "quoted" text.'),
              ('backslash','Synthetic \\ text.'),('newline','Synthetic\ntext.'),('unicode','Synthetic π.')]
    rows=[]
    for task in recipe.TASKS:
        grammar=compiler.compile_json_schema(decoder.schema(task),any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
        for name,value in fixtures:
            text=json.dumps({f:value for f in task['fields']},ensure_ascii=False)
            recipe.parse_artifact(text,task)
            ids=tokenizer.encode(text,add_special_tokens=False)
            decoded=tokenizer.decode(ids,skip_special_tokens=False,clean_up_tokenization_spaces=False)
            direct=xgr.GrammarMatcher(grammar);text_ok=direct.accept_string(text)
            direct_eos=direct.accept_token(eos[0]) if text_ok else False
            row=dict(task=task['id'],fixture=name,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                     input_tokens=len(ids),roundtrip_exact=decoded==text,
                     text_accepted=text_ok,text_plus_eos_accepted=direct_eos,
                     token_trace=trace_tokens(lambda:xgr.GrammarMatcher(grammar),ids,eos[0],tokenizer))
            # A second independent EOS observation only when the content tokens passed.
            if row['token_trace']['rejection_stage']=='eos':
                row['alternate_eos_trace']=trace_tokens(lambda:xgr.GrammarMatcher(grammar),ids,eos[1],tokenizer)
            rows.append(row)
    return dict(schema='composite-json-cpu-diagnostic-v1',status='observed_not_qualification',
        condition=recipe.CONDITION,model_executed=False,gpu_qualified=False,execution_allowed=False,
        grammar_parameters=dict(any_whitespace=True,max_whitespace_cnt=2,strict_mode=True),
        vocab_size=size,stop_ids=eos,add_prefix_space=getattr(info,'add_prefix_space',None),rows=rows)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('snapshot','failed-report','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();raw=a.failed_report.read_bytes();failed=json.loads(raw)
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second diagnostic ceiling')))
    start=time.monotonic();cpu=time.process_time();signal.alarm(300)
    with a.output.open('x') as handle:
        try:
            r=inspect(a.snapshot,failed)
        except Exception as exc:
            r=dict(status='diagnostic_error',error_type=type(exc).__name__,error=str(exc),model_executed=False,execution_allowed=False)
        finally:signal.alarm(0)
        r.update(failed_report_sha256=hashlib.sha256(raw).hexdigest(),wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu)
        json.dump(r,handle,indent=2);handle.write('\n')
    print(json.dumps(r,indent=2));return int(r['status']=='diagnostic_error')
if __name__=='__main__':raise SystemExit(main())
