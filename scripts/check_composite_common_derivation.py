#!/usr/bin/env python3
"""Synthetic CPU checks for the common interface; no statements, weights or dispatch."""
import argparse
import hashlib
import importlib.util
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def load_probe():
    spec=importlib.util.spec_from_file_location('order_probe',ROOT/'scripts/check_composite_derivation_order.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.probe


def fixtures(fields):
    value='Synthetic "quoted" text; backslash \\ and newline\nUnicode π.'
    obj={k:value for k in fields}
    return {
        'derivation_first':json.dumps(obj,ensure_ascii=False),
        'derivation_last':json.dumps({k:obj[k] for k in fields[1:]+fields[:1]},ensure_ascii=False),
        'extra_key':json.dumps(obj|{'unexpected':'x'},ensure_ascii=False),
        'missing_field':json.dumps({k:obj[k] for k in fields[:-1]},ensure_ascii=False),
        'malformed':'{"'+fields[0]+'":"unescaped "quote"}',
    }


def controls(factory,tokenizer,fields,eos):
    probe=load_probe();observations=[]
    for stop in eos:
        checks={name:probe(factory,tokenizer,text,stop) for name,text in fixtures(fields).items()}
        good=checks['derivation_first']
        passed=all(good[k] is True for k in ('string_plus_eos','tokens_plus_eos','roundtrip_exact'))
        passed=passed and all(not checks[name][k] for name in checks if name!='derivation_first' for k in ('string_plus_eos','tokens_plus_eos'))
        observations.append(dict(eos=stop,checks=checks,passed=passed))
    return observations


def check(snapshot,bank):
    from bc_phase2.composite_derivation_interface import freeze
    from bc_phase2.composite_math_decoder import schema
    from bc_phase2 import joint_d1_local as local
    from bc_phase2.d1_natural_screen import verify_non_thinking
    from bc_phase2.joint_schema import require
    from bc_phase2.model import digest
    frozen=freeze(bank)
    require(importlib.metadata.version('xgrammar')=='0.1.32','pinned XGrammar required')
    versions={k:importlib.metadata.version(k) for k in local.VERSIONS}
    require(versions==local.VERSIONS,'pinned versions required')
    for name,h in local.METADATA.items():require(local.file_hash(snapshot/name)==h,'metadata changed: '+name)
    from transformers import AutoTokenizer
    import xgrammar as xgr
    tokenizer=AutoTokenizer.from_pretrained(str(snapshot),local_files_only=True,trust_remote_code=False)
    template=verify_non_thinking(tokenizer)
    require(template['template_hash']==local.TEMPLATE_HASH,'pinned template')
    config=json.loads((snapshot/'config.json').read_text());size=config.get('text_config',config)['vocab_size'];eos=[248046,248044]
    info=xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=size,stop_token_ids=eos)
    compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
    unique={}
    for task in frozen['transport_tasks']:
        h=digest(schema(task));row=unique.setdefault(h,dict(schema_hash=h,schema=schema(task),fields=task['fields'],consumers=[]))
        row['consumers'].append(dict(source_id=task['source_id'],task_id=task['id']))
    rows=[]
    for h,row in sorted(unique.items()):
        grammar=compiler.compile_json_schema(row['schema'],any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
        observations=controls(lambda:xgr.GrammarMatcher(grammar),tokenizer,row['fields'],eos)
        rows.append(dict(row,observations=observations,passed=all(o['passed'] for o in observations)))
    return dict(schema='composite-common-derivation-cpu-v1',status='passed_cpu_checks' if all(r['passed'] for r in rows) else 'failed_cpu_checks',
        interface_digest=frozen['interface_digest'],historical_bank_id=bank['bank_id'],task_count=len(frozen['transport_tasks']),distinct_schemas=len(rows),
        profile_entries=len(frozen['profile_coverage']),rows=rows,template=template,versions=versions,xgrammar_version='0.1.32',
        metadata=local.METADATA,model_executed=False,execution_allowed=False,gpu_qualified=False,
        full_request_fit_verified=False,limitations=['Synthetic schema probes only; no mathematical qualification.','Fresh profiling and live campaign approval remain outstanding.'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot','bank','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='')
    start=time.perf_counter();cpu=time.process_time()
    signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('300-second CPU deadline')))
    with a.output.open('x') as f:
        signal.alarm(300)
        try:
            raw=a.bank.read_bytes();r=check(a.snapshot,json.loads(raw));r['bank_file_sha256']=hashlib.sha256(raw).hexdigest()
            r['implementation_hashes']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('scripts/check_composite_common_derivation.py','scripts/check_composite_derivation_order.py','src/bc_phase2/composite_derivation_interface.py','src/bc_phase2/composite_math_decoder.py')}
        except Exception as exc:r=dict(status='error',error_type=type(exc).__name__,error=str(exc),model_executed=False,execution_allowed=False)
        finally:signal.alarm(0)
        r.update(cpu_seconds=time.process_time()-cpu,wall_seconds=time.perf_counter()-start)
        json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps({'report':str(a.output),'status':r['status'],'model_executed':False}))
    return 0 if r['status']=='passed_cpu_checks' else 1
if __name__=='__main__':raise SystemExit(main())
