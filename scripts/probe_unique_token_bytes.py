"""Synthetic tokenizer byte round trips only: no model, matcher, or qualification."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beyond_consensus.models.unique_keys import synthetic_controls
from beyond_consensus.util import BCError, read_json, file_hash, digest


def compare(index, text, decoded, hf_decoded):
    original = text.encode('utf-8')
    return dict(case=index, roundtrip=original == decoded,
                native_matches_hf=decoded == hf_decoded.encode('utf-8'),
                hf_matches_original=hf_decoded == text,
                original_is_nfc=unicodedata.normalize('NFC', text) == text,
                native_matches_nfc=decoded == unicodedata.normalize('NFC', text).encode('utf-8'),
                synthetic_text=text, native_hex=decoded.hex(), hf_decoded=hf_decoded)


def probe(lock_path):
    lock = read_json(lock_path)
    if lock.get('schema') != 'bc-model-lock-v1':
        raise BCError('Unknown model lock')
    if not os.environ.get('SLURM_JOB_ID'):
        raise BCError('Tokenizer probe requires a CPU batch allocation')
    for relative, expected in lock['metadata_hashes'].items():
        if file_hash(Path(lock['model_path']) / relative) != expected:
            raise BCError('Staged metadata changed')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    from transformers import AutoTokenizer
    from beyond_consensus.models.constrained import load_xgrammar
    from beyond_consensus.models.competence import versions
    packages = versions()
    if packages['transformers'] != '5.3.0':
        raise BCError('Pinned Transformers 5.3.0 required')
    xgr, _ = load_xgrammar()
    tokenizer = AutoTokenizer.from_pretrained(lock['tokenizer_path'], local_files_only=True, trust_remote_code=False)
    config = read_json(Path(lock['model_path']) / 'config.json')
    vocab = config.get('text_config', config)['vocab_size']
    generation = read_json(Path(lock['model_path']) / 'generation_config.json')
    from beyond_consensus.models.transformers_backend import generation_tokens
    from types import SimpleNamespace
    stops = generation_tokens(tokenizer, SimpleNamespace(
        eos_token_id=generation.get('eos_token_id'), pad_token_id=generation.get('pad_token_id')))['eos_token_id']
    info = xgr.TokenizerInfo.from_huggingface(tokenizer, vocab_size=vocab, stop_token_ids=stops)
    decoded_vocab = info.decoded_vocab
    good, bad = synthetic_controls()
    rows = []
    for index, text in enumerate(good + bad):
        ids = tokenizer.encode(text, add_special_tokens=False)
        native = b''.join(decoded_vocab[t] for t in ids)
        hf = tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        rows.append(compare(index, text, native, hf))
    normalizer = json.loads(tokenizer.backend_tokenizer.to_str()).get('normalizer')
    return dict(schema='rr-unique-token-bytes-v1', status='observed', normalizer=normalizer,
                cases=rows, packages=packages, controls_hash=digest([good, bad]),
                model_lock_sha256=file_hash(lock_path), script_sha256=file_hash(Path(__file__)),
                model_executed=False, sql_executed=False, task_inputs_used=False,
                qualification_issued=False, task_execution_allowed=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-lock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise BCError('Use a fresh report path')
    start = time.process_time()
    report = probe(args.model_lock)
    report['analysis_cpu_seconds'] = time.process_time() - start
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)
        handle.write('\n')
    print(json.dumps(dict(report=str(args.output), status=report['status'], normalizer=report['normalizer'],
                         mismatches=[row for row in report['cases'] if not row['roundtrip']]), indent=2))


if __name__ == '__main__':
    main()
