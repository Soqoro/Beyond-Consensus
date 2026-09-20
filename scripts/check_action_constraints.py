"""Offline CPU/tokenizer qualification of the optional constrained decoder.

No model weights, SQL, task files or reference answers are loaded. Requires the
optional decoder stack; ordinary CPU functionality and --help remain stdlib.
"""
from pathlib import Path
import argparse
import json
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from beyond_consensus.models.action_schema import contract, validate_action
from beyond_consensus.util import BCError, digest, file_hash, read_json


def controls():
    column = {"column": "demo_value"}
    call = {"call": {"name": "sum", "args": [column]}}
    case = {"case": {"when": [[{"binary": [">", column, {"literal": 5}]}, {"literal": "high"}]],
                     "else": {"literal": "low"}}}
    def query(expr):
        return {"tool": "run_read_query", "permitted_artifact_versions": {}, "select_sql": {
            "columns": [{"expr": expr, "as": "demo_result"}], "from": {"table": "demo_rows"}}}
    aggregate = query(call)
    aggregate["select_sql"]["group_by"] = [column]
    join = query(column)
    join["select_sql"]["joins"] = [{"kind": "inner", "source": {"table": "demo_other"},
        "on": {"binary": ["=", {"column": "demo_rows.demo_value"}, {"column": "demo_other.demo_value"}]}}]
    view = {"tool": "submit_view_definition", "artifact_name": "demo_view",
            "permitted_artifact_versions": {}, "select_sql": query(column)["select_sql"]}
    good = [{"tool": "read_source", "name": "demo-contract"}, aggregate, join, query(case), view,
            {"tool": "submit_required_artifact", "artifact_id": "not-an-actual-artifact"}]
    bad = [
        '{"tool":"run_read_query",',
        json.dumps(query({"function": "sum", "column": "demo_value"})),
        json.dumps(query({"case": {"when": [{"condition": column, "value": {"literal": 1}}], "else": {"literal": 0}}})),
        '{"tool":"read_source","tool":"read_source","name":"demo"}',
    ]
    return good, bad


# Fixed offline synthetic controls; never used by model prompts or task grammars.
def col(name):
    return {"column": name}


def synthetic_probe_trees():
    order = lambda name: [{"expr": col(name), "direction": "asc"}]
    return {
        "aggregate": {"columns": [{"expr": col("department_id")},
            {"expr": {"call": {"name": "sum", "args": [col("amount")]}}, "as": "total_amount"},
            {"expr": {"call": {"name": "count", "args": [col("id")]}}, "as": "entry_count"}],
            "from": {"table": "entries"}, "group_by": [col("department_id")], "order_by": order("department_id")},
        "join": {"columns": [{"expr": col("e.id"), "as": "entry_id"},
            {"expr": col("d.name"), "as": "department_name"}, {"expr": col("e.amount"), "as": "amount"}],
            "from": {"table": "entries", "as": "e"},
            "joins": [{"kind": "inner", "source": {"table": "departments", "as": "d"},
                "on": {"binary": ["=", col("e.department_id"), col("d.id")]}}], "order_by": order("e.id")},
        "case": {"columns": [{"expr": col("id")}, {"expr": {"case": {"when": [
            [{"binary": [">", col("amount"), {"literal": 0}]}, {"literal": "positive"}],
            [{"binary": ["<", col("amount"), {"literal": 0}]}, {"literal": "negative"}]],
            "else": {"literal": "zero"}}}, "as": "sign_label"}],
            "from": {"table": "entries"}, "order_by": order("id")},
        "view": {"columns": [{"expr": col("id")},
            {"expr": {"binary": ["+", col("amount"), {"literal": 3}]}, "as": "adjusted_amount"}],
            "from": {"table": "entries"}},
    }


def check(lock_path):
    start = time.process_time()
    wall_start = time.monotonic()
    lock = read_json(lock_path)
    if lock.get("schema") != "bc-model-lock-v1":
        raise BCError("Unknown model lock")
    for relative, expected in lock["metadata_hashes"].items():
        if file_hash(Path(lock["model_path"])/relative) != expected:
            raise BCError("Staged model metadata changed")
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    if lock['checkpoint'] == 'Qwen/Qwen3.5-27B' and not os.environ.get('SLURM_JOB_ID'):
        raise BCError('27B tokenizer qualification requires a CPU batch allocation')
    import torch
    from transformers import AutoTokenizer
    from beyond_consensus.models.constrained import ActionConstraint
    from beyond_consensus.models.transformers_backend import verify_thinking_template
    tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True, trust_remote_code=False)
    template = verify_thinking_template(tokenizer, True)
    metadata = read_json(Path(lock["model_path"])/"config.json")
    text_config = metadata.get("text_config", metadata)
    vocab = text_config["vocab_size"]
    from types import SimpleNamespace
    from beyond_consensus.models.transformers_backend import generation_tokens
    generation = read_json(Path(lock['model_path'])/'generation_config.json')
    tokens = generation_tokens(tokenizer, SimpleNamespace(
        eos_token_id=generation.get('eos_token_id'), pad_token_id=generation.get('pad_token_id')))
    eos = tokens['eos_token_id']
    rendered = tokenizer.apply_chat_template([
        {'role': 'system', 'content': 'Use exactly one JSON tool action per turn, no Markdown.'},
        {'role': 'user', 'content': 'Synthetic qualification only.'}], tokenize=False,
        add_generation_prompt=True, enable_thinking=True)
    if '<tool_call>' in rendered or '<tools>' in rendered or not rendered.rstrip().endswith('<think>'):
        raise BCError('Rendered prompt contradicts JSON protocol or lacks generation thinking opener')
    from beyond_consensus.models.competence import qualification_key, versions
    packages = versions()
    if packages['transformers'] != '5.3.0':
        raise BCError('Qualification requires the reviewed Transformers 5.3.0 stack')
    constraint = ActionConstraint(tokenizer, vocab, eos)
    good, bad = controls()
    if lock['checkpoint'] == 'Qwen/Qwen3.5-27B':
        # Offline qualification only. Never supplied to a worker or per-task grammar.
        for probe, tree in synthetic_probe_trees().items():
            action = {'tool': 'submit_view_definition' if probe == 'view' else 'run_read_query',
                      'permitted_artifact_versions': {}, 'select_sql': tree}
            if probe == 'view':
                action = {'tool': 'submit_view_definition', 'artifact_name': 'entry_adjusted',
                          'permitted_artifact_versions': {}, 'select_sql': tree}
            good.append(action)
    closing = tokenizer.convert_tokens_to_ids("</think>")
    for action in good:
        text = json.dumps(action, separators=(",", ":"))
        validate_action(text)
        ids = tokenizer.encode(text, add_special_tokens=False)
        # A closing token in the prompt must not activate the matcher.
        prefix = [closing]
        processor = constraint.processor(len(prefix), closing)
        scores = torch.zeros((1,vocab), dtype=torch.float32)
        unchanged = processor(torch.tensor([prefix]), scores.clone())
        if not torch.equal(scores, unchanged) or processor.active:
            raise BCError("Prompt reasoning delimiter activated action constraints")
        prefix.append(closing)
        for token in [*ids, eos[0]]:
            masked = processor(torch.tensor([prefix]), scores.clone())
            if not torch.isfinite(masked[0,token]).item():
                raise BCError("Valid action token was masked")
            prefix.append(token)
        matcher = constraint.xgr.GrammarMatcher(constraint.compiled)
        if not matcher.accept_string(text) or not matcher.accept_token(eos[0]):
            raise BCError("Complete public action failed grammar acceptance")
    for text in bad:
        matcher = constraint.xgr.GrammarMatcher(constraint.compiled)
        if matcher.accept_string(text) and matcher.accept_token(eos[0]):
            raise BCError("Invalid action accepted by grammar")
    # Empty/incomplete action cannot terminate; scores are on CPU throughout.
    processor = constraint.processor(1, None)
    masked = processor(torch.tensor([[closing]]), torch.zeros((1,vocab)))
    if any(torch.isfinite(masked[0,token]).item() for token in eos):
        raise BCError("EOS is allowed before the action is complete")
    return {"schema": "bc-action-constraint-check-v1", "status": "passed",
        "qualification_key": qualification_key(lock, packages), "packages": packages,
        "effective_generation_tokens": tokens, "vocab_size": vocab,
        "rendered_prompt_hash": digest(rendered), "prompt_supplies_thinking_opener": True,
        "native_tool_template_injected": False, "wall_seconds": time.monotonic()-wall_start,
        "model_executed": False, "sql_executed": False, "device": "cpu", "task_inputs_used": False,
        "positive_controls": len(good), "negative_controls": len(bad), "contract": contract(),
        "model_lock_sha256": file_hash(lock_path), "script_sha256": file_hash(Path(__file__)),
        "runtime": constraint.runtime, "thinking_template": template,
        "control_hash": digest([good,bad]), "analysis_cpu_seconds": time.process_time()-start}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qualified-lock", type=Path, help="Write a new lock embedding this qualification")
    args = parser.parse_args()
    if args.qualified_lock and args.qualified_lock.exists():
        raise BCError("Qualified lock already exists; use a fresh path")
    if args.output.exists():
        raise BCError("Use a new report path; previous observations are immutable")
    result = check(args.model_lock)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    if args.qualified_lock:
        lock = read_json(args.model_lock)
        lock['decoder_qualification'] = result
        with args.qualified_lock.open('x') as stream:
            json.dump(lock, stream, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (BCError, ImportError) as exc:
        raise SystemExit(str(exc))
