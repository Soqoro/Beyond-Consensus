"""CPU-only synthetic matcher/parser audit; no model, task inputs, or new lock."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from beyond_consensus.models.action_schema import validate_action
from beyond_consensus.util import BCError, digest, file_hash, read_json

MODE = 'reporecourse-json-reliable-v1-pool-7'


def cases():
    prefix = '{"tool":"publish","name":"demo","format":"mapping","content":'
    suffix = ',"bindings":{},"obligations":[]}'
    good = prefix + '{"fields":{"demo":{"path":["id"]}},"output_schema":{"type":"object"}}' + suffix
    return {
        'valid_mapping': good,
        'duplicate_envelope': good.replace('"name":"demo"', '"name":"demo","name":"demo"'),
        'duplicate_nested': prefix + '{"fields":{"demo":1,"demo":2},"output_schema":{}}' + suffix,
        'escaped_duplicate_nested': prefix + r'{"fields":{"demo":1,"\u0064emo":2},"output_schema":{}}' + suffix,
        'incomplete_action': '{"tool":',
    }


def parser_accepts(text):
    try:
        validate_action(text, MODE)
        return True
    except BCError:
        return False


def masked_path(constraint, tokenizer, torch, text, closing, stop, vocab, reasoning):
    # Prompt delimiter is deliberately present; it must not activate the gate.
    prefix = [closing]
    processor = constraint.processor(1, closing if reasoning else None)
    scores = torch.zeros((1, vocab), dtype=torch.float32)
    if reasoning:
        before = processor(torch.tensor([prefix]), scores.clone())
        if processor.active or not torch.equal(before, scores):
            raise BCError('Prompt delimiter activated matcher')
        prefix.append(closing)
    ids = tokenizer.encode(text, add_special_tokens=False)
    for index, token in enumerate([*ids, stop]):
        masked = processor(torch.tensor([prefix]), scores.clone())
        if not torch.isfinite(masked[0, token]).item():
            return dict(accepted=False, blocked_index=index, blocked_stop=index == len(ids),
                        mask_calls=processor.mask_calls)
        prefix.append(token)
    return dict(accepted=True, blocked_index=None, blocked_stop=False, mask_calls=processor.mask_calls)


def run(lock_path):
    # Reuse the existing offline metadata/version checks and baseline controls.
    import importlib.util
    spec = importlib.util.spec_from_file_location("boundary_baseline", ROOT / "scripts/check_action_constraints.py")
    baseline_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline_module)
    baseline = baseline_module.check(lock_path, 16384, MODE, 2048)
    import torch
    from transformers import AutoTokenizer
    from beyond_consensus.models.constrained import ActionConstraint
    lock = read_json(lock_path)
    tokenizer = AutoTokenizer.from_pretrained(lock['tokenizer_path'], local_files_only=True, trust_remote_code=False)
    stops = baseline['effective_generation_tokens']['eos_token_id']
    vocab = baseline['vocab_size']
    closing = tokenizer.convert_tokens_to_ids('</think>')
    constraint = ActionConstraint(tokenizer, vocab, stops, MODE)
    rows = []
    errors = []
    for name, text in cases().items():
        accepted = parser_accepts(text)
        for stop in stops:
            matcher = constraint.xgr.GrammarMatcher(constraint.compiled)
            string_ok = matcher.accept_string(text)
            direct = bool(string_ok and matcher.accept_token(stop))
            paths = {label: masked_path(constraint, tokenizer, torch, text, closing, stop, vocab, thinking)
                     for label, thinking in (('after_think_close', True), ('without_reasoning', False))}
            row = dict(id=name, stop_token_id=stop, parser_accepted=accepted,
                       matcher_string_accepted=string_ok, matcher_stop_accepted=direct,
                       paths=paths, synthetic_text_sha256=digest(text))
            rows.append(row)
            if any(p['accepted'] != direct for p in paths.values()):
                errors.append(f'{name}:{stop}:matcher_processor_disagreement')
            if name == 'valid_mapping' and (not accepted or not direct):
                errors.append(f'{name}:{stop}:positive_rejected')
            if name == 'incomplete_action' and direct:
                errors.append(f'{name}:{stop}:incomplete_stop_allowed')
            if name != 'valid_mapping' and accepted:
                errors.append(f'{name}:{stop}:strict_parser_accepted_invalid_control')
    return dict(schema='rr-decoder-boundary-audit-v1', status='failed_controls' if errors else 'observed',
                errors=errors, cases=rows, baseline=baseline, model_executed=False, sql_executed=False,
                task_inputs_used=False, task_execution_allowed=False, qualification_issued=False,
                historical_scores_changed=False,
                interpretation='Synthetic grammar/parser differential; duplicate acceptance is an observation, not a parser waiver or historical attribution.',
                controls_hash=digest(cases()), model_lock_sha256=file_hash(lock_path),
                script_sha256=file_hash(Path(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-lock', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise BCError('Use a fresh report path')
    start = time.process_time()
    report = run(args.model_lock)
    report['analysis_cpu_seconds'] = time.process_time() - start
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'report': str(args.output), 'status': report['status'], 'errors': report['errors']}))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
