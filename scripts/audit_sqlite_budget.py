"""Read-only reference representation audit; never a worker tool or scorer.

Default operation uses only the standard library and repository CPU code.
Optional tokenization runs in an explicitly supplied existing environment,
offline, loading the tokenizer only. No reference text is printed or saved.
"""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from beyond_consensus.runtime.sqlite_executor import compile_select
from beyond_consensus.tasks.data_manifest import validate_data
from beyond_consensus.util import BCError, canonical, file_hash


TOKENIZE = '''
import json, sys, time
start = time.process_time()
from transformers import AutoTokenizer
data = json.load(sys.stdin)
tokenizer = AutoTokenizer.from_pretrained(data["path"], local_files_only=True, trust_remote_code=False)
counts = [len(tokenizer.encode(s, add_special_tokens=False)) for s in data["texts"]]
print(json.dumps({"counts": counts, "cpu_seconds": time.process_time()-start}))
'''


def inspect_tasks(tasks, action_cap):
    """Compile existing reviewed trees without executing them or selecting reads."""
    rows, texts = [], []
    for task in tasks:
        if task.kind != "sqlite_native" or len(task.required_outputs) != 1:
            raise ValueError("Audit requires individual native SQLite tasks")
        unit = task.required_outputs[0]
        artifact = task.metadata["evaluation"][unit]["artifact"]
        kind = artifact["kind"]
        if kind not in ("query", "view"):
            raise ValueError("Unsupported artifact kind")
        compile_select(artifact["select"], task.metadata["harness"]["tables"])
        action = {"tool": "run_read_query" if kind == "query" else "submit_view_definition"}
        if kind == "view":
            action["artifact_name"] = artifact["name"]
        action.update(permitted_artifact_versions={}, select_sql=artifact["select"])
        # Compact, insertion-preserving envelope, with bindings before the tree.
        text = json.dumps(action, ensure_ascii=False, separators=(",", ":"))
        texts.append(text)
        pages = {}
        for name, doc in task.metadata["harness"]["documents"].items():
            body = doc if isinstance(doc, str) else canonical(doc)
            pages[name] = max(1, (len(body) + 3999) // 4000)
        catalogue = max(1, (len(pages) + 63) // 64)
        # Contract + schema + create/query + submit; assumes first attempt works.
        fixed = 4
        rows.append({"task_id": task.id, "kind": kind,
            "reference_action_characters": len(text),
            "reference_action_utf8_bytes": len(text.encode()),
            "public_document_pages": pages,
            "full_catalogue_actions": catalogue,
            "assumed_fixed_actions": fixed,
            "document_page_slots_after_full_catalogue": action_cap-fixed-catalogue,
            "actions_reading_all_documents_once": fixed+catalogue+sum(pages.values()),
            "actions_reading_schema_and_columns_once": (
                fixed+catalogue+pages["schema"]+pages["columns"]
                if {"schema", "columns"} <= pages.keys() else None)})
    return rows, texts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--action-cap", type=int, default=12)
    parser.add_argument("--output-cap", type=int, default=768)
    parser.add_argument("--model-lock", type=Path)
    parser.add_argument("--tokenizer-python", type=Path)
    args = parser.parse_args()
    if min(args.action_cap, args.output_cap) < 1:
        parser.error("Caps must be positive")
    if bool(args.model_lock) != bool(args.tokenizer_python):
        parser.error("Supply both --model-lock and --tokenizer-python, or neither")
    root = Path(__file__).resolve().parents[1]
    if args.output.resolve().is_relative_to(root):
        parser.error("Write the audit outside the checkout")
    if args.output.exists():
        parser.error("Use a new output path; previous observations are immutable")
    start, wall = time.process_time(), time.monotonic()
    rows, texts = inspect_tasks(validate_data(args.data_manifest), args.action_cap)
    token_cpu = None
    if args.model_lock:
        lock = json.loads(args.model_lock.read_text())
        if lock["tokenizer_revision"] != lock["revision"] or lock["tokenizer_path"] != lock["model_path"]:
            raise ValueError("Separate tokenizer snapshot requires a separately verified metadata inventory")
        hashes = lock["metadata_hashes"]
        if not {"tokenizer.json", "tokenizer_config.json"} <= hashes.keys():
            raise ValueError("Locked tokenizer metadata inventory is incomplete")
        for relative, expected in hashes.items():
            if file_hash(Path(lock["model_path"]) / relative) != expected:
                raise ValueError("Locked metadata hash mismatch")
        proc = subprocess.run([str(args.tokenizer_python), "-I", "-c", TOKENIZE],
            input=json.dumps({"path": lock["tokenizer_path"], "texts": texts}),
            text=True, capture_output=True, timeout=180,
            env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                 "CUDA_VISIBLE_DEVICES": "", "TOKENIZERS_PARALLELISM": "false"})
        if proc.returncode:
            raise ValueError("Offline tokenizer subprocess failed; no reference text or stderr disclosed")
        measured = json.loads(proc.stdout)
        if len(measured["counts"]) != len(rows) or any(type(n) is not int or n < 1 for n in measured["counts"]):
            raise ValueError("Tokenizer result count mismatch")
        token_cpu = measured["cpu_seconds"]
        for row, count in zip(rows, measured["counts"]):
            row.update(reference_action_tokens=count, content_plus_one_stop_tokens=count+1,
                content_plus_one_stop_fits=args.output_cap >= count+1)
    report = {"schema": "bc-sqlite-budget-audit-v1", "model_executed": False,
        "sql_executed": False, "worker_reference_access": False,
        "data_manifest_sha256": file_hash(args.data_manifest),
        "audit_script_sha256": file_hash(Path(__file__)),
        "model_lock_sha256": file_hash(args.model_lock) if args.model_lock else None,
        "action_cap": args.action_cap, "output_cap": args.output_cap,
        "token_measurement": "offline_tokenizer" if args.model_lock else "unmeasured",
        "analysis_cpu_seconds": time.process_time()-start,
        "tokenizer_process_cpu_seconds": token_cpu, "wall_seconds": time.monotonic()-wall,
        "tasks": rows,
        "limitations": ["Reviewed reference serialization, not a shortest valid solution or model competence test.",
            "One stop token is included; extra reasoning, delimiters and alternate tokenizations are not measured.",
            "Page scenarios are conditional arithmetic, not gold-selected worker read plans or necessary minima.",
            "Analysis costs are separate from historical episode work; no calibration or runtime budgets are changed."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (BCError, ValueError, KeyError, OSError, subprocess.SubprocessError):
        raise SystemExit("Audit failed: check validated manifest, locked metadata and tokenizer environment; private details suppressed") from None
