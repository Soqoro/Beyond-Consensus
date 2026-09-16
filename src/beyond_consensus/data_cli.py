"""CPU-only staging/validation commands for restricted data adapters."""
from pathlib import Path

from .util import BCError, atomic_json, read_json


def add_parsers(sub):
    sub.add_parser("data-capabilities", help="Inspect the fixed SQLite CPU executor; no model or container")
    stage = sub.add_parser("sqlite-stage", help="Register already downloaded SQLite files outside Git; no network")
    for name in ("root", "output"):
        stage.add_argument("--"+name, type=Path, required=True)
    stage.add_argument("--materials", type=Path)
    stage.add_argument("--review", type=Path)
    inspect = sub.add_parser("sqlite-inspect", help="Show staged/missing/reviewed prerequisites; does not score")
    inspect.add_argument("--staged", type=Path, required=True)
    review = sub.add_parser("sqlite-review-template", help="Write an unapproved scaffold with exact source/material hashes")
    review.add_argument("--staged", type=Path, required=True)
    review.add_argument("--task-ids", nargs="+", required=True)
    review.add_argument("--output", type=Path, required=True)
    native = sub.add_parser("sqlite-validate", help="Validate exactly N approved native references and negative controls")
    native.add_argument("--staged", type=Path, required=True)
    native.add_argument("--task-ids", nargs="+")
    native.add_argument("--count", type=int, default=10)
    native.add_argument("--output", type=Path, required=True)
    pair = sub.add_parser("sqlite-pairs", help="Validate and freeze explicit candidates; retain rejections")
    for name in ("staged", "candidates", "output"):
        pair.add_argument("--"+name, type=Path, required=True)
    silo = sub.add_parser("silo-generate", help="Generate pinned four-worker SILO data; no model calls")
    silo.add_argument("--family", choices=("II-11", "II-20"), required=True)
    silo.add_argument("--seeds", nargs="+", type=int, default=[0])
    silo.add_argument("--access", choices=("protected_original_shards", "no_recovery_copy"), default="protected_original_shards")
    silo.add_argument("--output", type=Path, required=True)
    validation = sub.add_parser("silo-validate", help="Validate a pinned generated manifest or original upstream JSON record")
    validation.add_argument("--input", type=Path, required=True)


COMMANDS = {"data-capabilities", "sqlite-stage", "sqlite-inspect", "sqlite-review-template", "sqlite-validate", "sqlite-pairs", "silo-generate", "silo-validate"}


def dispatch(args):
    if args.command == "data-capabilities":
        from .runtime.sqlite_executor import capabilities
        return capabilities()
    if args.command in ("sqlite-stage", "sqlite-inspect"):
        from .tasks.sqlite_tasks import stage, inspect
        return stage(args.root, args.output, args.materials, args.review) if args.command == "sqlite-stage" else inspect(read_json(args.staged))
    if args.command == "silo-validate":
        from .tasks.silo import validate_record
        from .tasks.data_manifest import validate_data
        data = read_json(args.input)
        if data.get("schema") == "bc-data-v2":
            if data.get("environment") != "silo":
                raise BCError("silo-validate expects the SILO environment")
            tasks = validate_data(args.input)
            return {"status": "validated", "tasks": len(tasks), "environment": "silo", "model_executed": False}
        parsed = validate_record(data)
        return {k: parsed[k] for k in ("family", "workers", "source_hash")} | {
            "status": "upstream_data_scorer_parity", "four_worker_runnable": parsed["workers"] == 4}
    if args.output.exists():
        raise BCError("Use a new data manifest path; preserve prior validation/selection")
    from .tasks.sqlite_tasks import _outside_git
    _outside_git(args.output)
    if args.command == "sqlite-review-template":
        from .tasks.sqlite_tasks import review_template, _outside_git
        _outside_git(args.output)
        result = review_template(read_json(args.staged), args.task_ids)
        atomic_json(args.output, result)
        return {"review_template": str(args.output), "approved": False, "tasks": len(result["tasks"])}
    if args.command == "silo-generate":
        from .tasks.silo import generate_manifest
        result = generate_manifest(args.family, args.seeds, args.access)
    elif args.command == "sqlite-validate":
        from .tasks.data_manifest import validate_native
        if args.count < 1:
            raise BCError("Validation count must be positive")
        result = validate_native(read_json(args.staged), args.task_ids, args.count)
    else:
        from .tasks.data_manifest import validate_pairs
        result = validate_pairs(read_json(args.staged), read_json(args.candidates))
    atomic_json(args.output, result)
    return {"manifest": str(args.output), "environment": result["environment"],
        "tasks": len(result["tasks"]), "status": result.get("status", "written"),
        "reports": result.get("reports", []), "command_failed": result.get("command_failed", False),
        "model_executed": False}
