"""CPU-safe command line. Expensive dependencies load only in explicit commands."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from .config import load_config, from_dict
from .util import BCError, atomic_json, digest, plain, read_json

ROOT = Path(__file__).resolve().parents[2]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bc", description="Beyond Consensus E0/E1 development foundation")
    sub = p.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run a labelled CPU mock demonstration")
    demo.add_argument("--output", type=Path, default=Path("outputs/mock-demo"))
    demo.add_argument("--config", type=Path, default=ROOT / "configs/mock-demo.json")
    make = sub.add_parser("manifest", help="Freeze a planned grid; runs no episodes")
    make.add_argument("--config", type=Path, required=True)
    make.add_argument("--output", type=Path, required=True)
    make.add_argument("--model-lock", type=Path)
    make.add_argument("--data-manifest", type=Path, help="Explicit validated SQLite/SILO manifest override")
    run = sub.add_parser("run", help="Run/resume complete episodes from a pinned manifest")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--shard", type=int)
    run.add_argument("--model-lock", type=Path)
    run.add_argument("--retry-failures", action="store_true")
    for name in ("aggregate", "status"):
        item = sub.add_parser(name, help="Report all planned episode statuses")
        item.add_argument("--output", type=Path, required=True)
        if name == "status":
            item.add_argument("--jobs", nargs="*", default=[])
            item.add_argument("--dry-run", action="store_true")
    freeze = sub.add_parser("freeze-primary", help="Execute and freeze one common primary trace for Protocol B")
    freeze.add_argument("--config", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    diagnostic = sub.add_parser("diagnostic-manifest", help="Create Protocol B policy comparisons from a frozen primary")
    diagnostic.add_argument("--fixed-state", type=Path, required=True)
    diagnostic.add_argument("--output", type=Path, required=True)
    stage = sub.add_parser("stage-model", help="Explicit model staging; may download large model weights")
    stage.add_argument("--config", type=Path, required=True)
    stage.add_argument("--root", type=Path, required=True)
    stage.add_argument("--dry-run", action="store_true")
    data = sub.add_parser("stage-data", help="Legacy CooperBench download; new data paths use sqlite-stage/silo-generate")
    data.add_argument("--root", type=Path, required=True)
    data.add_argument("--revision")
    data.add_argument("--dry-run", action="store_true")
    coop = sub.add_parser("cooper-import", help="Validate actual upstream pairs and construct a versioned data manifest")
    for name in ("root", "subset", "output"):
        coop.add_argument("--"+name, type=Path, required=True)
    coop.add_argument("--upstream-commit", required=True)
    coop.add_argument("--dataset-revision", required=True)
    doctor = sub.add_parser("doctor", help="Lightweight login/data-executor capabilities; no model loading")
    doctor.add_argument("--dry-run", action="store_true")
    doctor.add_argument("--cluster", type=Path)
    probe = sub.add_parser("sandbox-probe", help="Qualify fixed container probes; never approves repository execution")
    probe.add_argument("--profile", type=Path, required=True)
    probe.add_argument("--output", type=Path, required=True)
    approval = sub.add_parser("sandbox-approve", help="Record explicit image/site review of passing qualification reports")
    approval.add_argument("--reports", type=Path, nargs="+", required=True)
    approval.add_argument("--reviewer", required=True)
    approval.add_argument("--image-reviewed", action="store_true")
    approval.add_argument("--output", type=Path, required=True)
    inspect = sub.add_parser("sandbox-inspect", help="Read-only runtime/image fingerprints and cgroup delegation check")
    inspect.add_argument("--runtime-root", type=Path, required=True)
    inspect.add_argument("--image", type=Path, required=True)
    profile = sub.add_parser("sandbox-profile", help="Fingerprint a private runtime/image; writes no approval")
    for name in ("runtime-root", "image", "scratch-root", "output"):
        profile.add_argument("--"+name, type=Path, required=True)
    profile.add_argument("--python", default="/usr/local/bin/python3")
    profile.add_argument("--cgroup-parent", default="current")
    environment = sub.add_parser("cooper-environment", help="Record explicitly reviewed pristine source and joint test commands")
    for name in ("data-manifest", "base-root", "profile", "approval", "suites", "output"):
        environment.add_argument("--"+name, type=Path, required=True)
    environment.add_argument("--task-id", required=True)
    environment.add_argument("--reviewer", required=True)
    environment.add_argument("--source-reviewed", action="store_true")
    validation = sub.add_parser("cooper-validate-environment", help="Run baseline and reference controls inside an approved sandbox")
    for name in ("environment", "data-manifest", "output"):
        validation.add_argument("--"+name, type=Path, required=True)
    submit = sub.add_parser("submit", help="Guarded Slurm submission; explicit user action only")
    submit.add_argument("--cluster", type=Path, required=True)
    submit.add_argument("--manifest", type=Path, required=True)
    submit.add_argument("--model-lock", type=Path, required=True)
    submit.add_argument("--concurrency", type=int, default=1)
    submit.add_argument("--mode", choices=("run", "preflight"), default="run")
    submit.add_argument("--dry-run", action="store_true")
    submit.add_argument("--serialize", action="store_true")
    retry = sub.add_parser("resubmit", help="Resubmit only missing/retryable shards from an unchanged snapshot")
    retry.add_argument("--snapshot", type=Path, required=True)
    retry.add_argument("--concurrency", type=int, default=1)
    retry.add_argument("--dry-run", action="store_true")
    batch = sub.add_parser("batch", help=argparse.SUPPRESS)
    batch.add_argument("--snapshot", type=Path, required=True)
    batch.add_argument("--output", type=Path, required=True)
    batch.add_argument("--mode", choices=("run", "preflight"), required=True)
    batch.add_argument("--retry", action="store_true")
    preflight = sub.add_parser("gpu-preflight", help="One-device smoke test; requires an allocation and staged model")
    preflight.add_argument("--manifest", type=Path, required=True)
    preflight.add_argument("--model-lock", type=Path, required=True)
    preflight.add_argument("--output", type=Path, required=True)
    export = sub.add_parser("export", help="Create a small sanitized browser-download bundle")
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--bundle", type=Path, required=True)
    export.add_argument("--dry-run", action="store_true")
    calibration = sub.add_parser("calibrate", help="Measure cold/index/prepared operations on development task groups")
    calibration.add_argument("--config", type=Path, required=True)
    calibration.add_argument("--output", type=Path, required=True)
    calibration.add_argument("--model-lock", type=Path)
    from .data_cli import add_parsers
    add_parsers(sub)
    from .diagnostic_cli import add_parsers as add_diagnostics
    add_diagnostics(sub)
    return p


def dispatch(args: argparse.Namespace) -> Any:
    from .diagnostic_cli import COMMANDS as DIAGNOSTICS, dispatch as dispatch_diagnostics
    if args.command in DIAGNOSTICS:
        return dispatch_diagnostics(args)
    from .data_cli import COMMANDS, dispatch as dispatch_data
    if args.command in COMMANDS:
        return dispatch_data(args)
    from .experiments.manifest import build_manifest, validate_manifest
    if args.command == "manifest":
        config = load_config(args.config)
        if args.data_manifest:
            config = replace(config, data_manifest=str(args.data_manifest.resolve()))
        if config.coding_environment:
            from .runtime.repository import CodingEnvironment
            environment = CodingEnvironment(Path(config.coding_environment), config.coding_environment_hash)
            config = replace(config, coding_environment_hash=environment.hash)
        if config.coding_validation:
            measured_hash = digest(read_json(config.coding_validation))
            if config.coding_validation_hash and config.coding_validation_hash != measured_hash:
                raise BCError("Coding validation changed; update configuration explicitly")
            config = replace(config, coding_validation_hash=measured_hash)
        if args.model_lock:
            from .models.staging import resolve_model_config
            config = replace(config, model=resolve_model_config(config.model, args.model_lock))
        if config.model.backend == "transformers" and not config.model.revision:
            raise BCError("Real manifests require --model-lock from explicit staging")
        manifest = build_manifest(config, ROOT)
        atomic_json(args.output, manifest)
        return {"planned_episodes": manifest["planned_episodes"], "manifest": str(args.output),
                "experiment_id": manifest["experiment_id"], "executed": 0}
    if args.command in ("run", "demo"):
        from .experiments.runner import run_manifest
        from .evaluation.aggregate import aggregate
        if args.command == "demo":
            config = load_config(args.config)
            if config.model.backend != "mock" or config.task_kind not in ("workflow_fixture", "sqlite_fixture", "silo"):
                raise BCError("demo only accepts the mock backend and labelled fixtures/SILO adaptation")
            manifest = build_manifest(config, ROOT)
            rows = run_manifest(manifest, args.output, ROOT)
        else:
            manifest = read_json(args.manifest)
            rows = run_manifest(manifest, args.output, ROOT, shard=args.shard,
                                model_lock=args.model_lock, retry_failures=args.retry_failures)
        summary = aggregate(manifest, args.output)
        summary["command_failed"] = any(r["status"] not in ("completed", "budget_exhausted") for r in rows)
        return summary
    if args.command in ("aggregate", "status"):
        from .evaluation.aggregate import aggregate
        from .experiments.cluster import command, failed_shard_ids
        manifest = read_json(args.output / "manifest.json")
        result = aggregate(manifest, args.output)
        result["missing_or_retryable_shards"] = failed_shard_ids(manifest, args.output)
        if args.command == "status" and args.jobs:
            if any(not j.isdecimal() for j in args.jobs):
                raise BCError("Use specified numeric project job IDs")
            commands = [["squeue", "--jobs", ",".join(args.jobs)],
                        ["sacct", "--jobs", ",".join(args.jobs), "--format=JobID,State,ExitCode,Elapsed,AllocTRES"]]
            result["scheduler"] = commands if args.dry_run else [command(c) for c in commands]
        return result
    if args.command == "freeze-primary":
        from .models.mock import MockBackend
        from .runtime.episode import EpisodeEngine
        from .runtime.persistence import EpisodeJournal
        from .experiments.manifest import episode_from, task_from
        config = load_config(args.config)
        if (config.model.backend != "mock" or config.task_count != 1 or len(config.policies) != 1
                or len(config.attacks) != 1 or len(config.seeds) != 1 or config.protocol != "A"):
            raise BCError("Initial fixed-state capture supports one mock task/policy/attack/seed in Protocol A")
        manifest = build_manifest(config, ROOT)
        row = episode_from(manifest["episodes"][0])
        journal = EpisodeJournal(args.output.parent / "primary-trace", row.episode_id)
        engine = EpisodeEngine(task_from(manifest["tasks"][0]), row, config, MockBackend(), journal, journal.begin(digest(row)))
        frozen = engine.freeze_primary()
        frozen["origin_config"] = plain(config)
        atomic_json(args.output, frozen)
        return {"fixed_state": str(args.output), "hash": digest(frozen), "final_evaluation": "not run"}
    if args.command == "diagnostic-manifest":
        frozen = read_json(args.fixed_state)
        config = from_dict({**frozen["origin_config"], "protocol": "B",
            "fixed_state_file": str(args.fixed_state.resolve()), "policies": ["ordinary", "jit", "replication", "recovery"]})
        manifest = build_manifest(config, ROOT)
        atomic_json(args.output, manifest)
        return {"manifest": str(args.output), "planned": manifest["planned_episodes"], "protocol": "B"}
    if args.command == "stage-model":
        from .models.staging import stage_model
        return stage_model(load_config(args.config).model, args.root, dry_run=args.dry_run)
    if args.command == "stage-data":
        from .tasks.cooperbench import stage_dataset
        return stage_dataset(args.root, args.revision, dry_run=args.dry_run)
    if args.command == "cooper-import":
        from .tasks.cooperbench import import_dataset
        data = import_dataset(args.root, args.subset, args.upstream_commit, args.dataset_revision)
        atomic_json(args.output, data)
        return {"task_pairs": len(data["tasks"]), "manifest": str(args.output), "execution": "blocked_pending_sandbox"}
    if args.command == "doctor":
        from .experiments.cluster import doctor, load_cluster
        return doctor(load_cluster(args.cluster) if args.cluster else None) if not args.dry_run else {
            "operations": ["scheduler/module/storage capability inspection"], "model_loaded": False}
    if args.command == "sandbox-inspect":
        from .runtime.apptainer import runtime_hash, absolute, cgroup_parent
        from .util import file_hash
        result = {"runtime_sha256": runtime_hash(absolute(str(args.runtime_root))),
                  "image_sha256": file_hash(absolute(str(args.image))), "repository_execution": False}
        try:
            result["cgroup_membership"] = Path("/proc/self/cgroup").read_text()
            result["cgroup_mount_controllers"] = Path("/sys/fs/cgroup/cgroup.controllers").read_text().strip()
            from types import SimpleNamespace
            result["delegated_cgroup_parent"] = str(cgroup_parent(SimpleNamespace(cgroup_parent="current")))
            result["delegated_cgroup_available"] = True
        except (OSError, BCError) as exc:
            result["cgroup_error"] = str(exc)
            result["delegated_cgroup_available"] = False
        return result
    if args.command == "sandbox-profile":
        from .runtime.apptainer import SandboxProfile, runtime_hash, absolute
        from .util import file_hash
        if args.output.exists():
            raise BCError("Use a new sandbox profile path; do not overwrite a pinned profile")
        profile = SandboxProfile(str(absolute(str(args.runtime_root))), runtime_hash(args.runtime_root),
            str(absolute(str(args.image))), file_hash(args.image), str(absolute(str(args.scratch_root))),
            cgroup_parent=args.cgroup_parent, python=args.python)
        atomic_json(args.output, profile)
        return {"profile": str(args.output), "profile_hash": digest(profile), "approved": False}
    if args.command == "sandbox-probe":
        from .runtime.apptainer import SandboxProfile, qualify
        return qualify(SandboxProfile.load(args.profile), args.output)
    if args.command == "sandbox-approve":
        from .runtime.apptainer import approve
        return approve(args.reports, args.reviewer, args.image_reviewed, args.output)
    if args.command in ("cooper-environment", "cooper-validate-environment"):
        from .tasks.cooperbench import validate_manifest as validate_data
        from .runtime.repository import CodingEnvironment, inventory
        from .runtime.apptainer import SandboxProfile
        tasks = validate_data(args.data_manifest)
        if args.command == "cooper-environment":
            if not args.source_reviewed or not args.reviewer.strip() or args.output.exists():
                raise BCError("Use a new output and explicitly review source/base commit and suite commands")
            task = next((t for t in tasks if t.id == args.task_id), None)
            if task is None:
                raise BCError("Task was not imported from the staged dataset")
            data = {"schema": "cooper-e0-environment-v1", "task_id": task.id, "task_hash": task.source_hash,
                "base_root": str(args.base_root.resolve()), "base_files": inventory(args.base_root.resolve()),
                "profile": plain(SandboxProfile.load(args.profile)), "approval": str(args.approval.resolve()),
                "approval_hash": digest(read_json(args.approval)),
                "reviewer": args.reviewer, "source_review": True, "suites": read_json(args.suites)}
            atomic_json(args.output, data)
            try:
                CodingEnvironment(args.output).validate_task(task)
            except Exception:
                args.output.unlink()
                raise
            return {"environment": str(args.output), "hash": digest(data), "execution": "not run"}
        environment = CodingEnvironment(args.environment)
        task = next((t for t in tasks if t.id == environment.data["task_id"]), None)
        if task is None:
            raise BCError("Environment task is missing from the imported dataset")
        from .evaluation.cooperbench import validate_environment
        return validate_environment(environment, task, args.data_manifest, args.output)
    if args.command == "submit":
        from .experiments.cluster import submit, load_cluster
        return submit(ROOT, load_cluster(args.cluster), read_json(args.manifest), read_json(args.model_lock),
                      args.concurrency, mode=args.mode, dry_run=args.dry_run, serialize=args.serialize)
    if args.command == "resubmit":
        from .experiments.cluster import submit, load_cluster, failed_shard_ids
        config = load_cluster(args.snapshot / "resolved/cluster.json")
        manifest = read_json(args.snapshot / "resolved/manifest.json")
        shards = failed_shard_ids(manifest, Path(config.output_root) / manifest["experiment_id"])
        if not shards:
            return {"submitted": False, "reason": "No missing or eligible failed shards"}
        return submit(ROOT, config, manifest, read_json(args.snapshot / "resolved/model-lock.json"), args.concurrency,
                      dry_run=args.dry_run, existing_snapshot=args.snapshot, failed_shards=shards)
    if args.command == "batch":
        from .experiments.cluster import batch
        return batch(args.snapshot, args.output, args.mode, args.retry)
    if args.command == "gpu-preflight":
        from .models.transformers_backend import preflight
        config = validate_manifest(read_json(args.manifest))
        result = preflight(config.model, args.model_lock)
        if config.task_kind in ("sqlite_fixture", "sqlite_native", "sqlite_pair"):
            import tempfile
            from .runtime.sqlite_executor import execute
            from .tasks.sqlite_tasks import fixture_database, read_query
            with tempfile.TemporaryDirectory(prefix="bc-sql-preflight-") as temporary:
                database = fixture_database(Path(temporary)/"source.sqlite", 0)
                result["sqlite_executor"] = execute(database, ["measurements"], [], [read_query("measurements", ["id", "value"])])
            result["command_failed"] = result["sqlite_executor"]["status"] != "ok"
        atomic_json(args.output, result)
        return result
    if args.command == "export":
        from .experiments.export import export_bundle
        return export_bundle(args.output, args.bundle, dry_run=args.dry_run)
    if args.command == "calibrate":
        from .planning.calibration import calibrate
        from .experiments.manifest import load_tasks
        from .models.mock import MockBackend
        config = load_config(args.config)
        if config.model.backend == "mock":
            backend = MockBackend()
        else:
            from .models.staging import resolve_model_config
            from .models.transformers_backend import TransformersBackend
            if not args.model_lock:
                raise BCError("Real calibration requires a staged model lock and a GPU allocation")
            config = replace(config, model=resolve_model_config(config.model, args.model_lock))
            backend = TransformersBackend(config.model, args.model_lock)
        result = calibrate(config, backend, load_tasks(config))
        atomic_json(args.output, result["calibration"])
        atomic_json(args.output.with_suffix(".measurements.json"), result["measurements"])
        return {"calibration_id": result["calibration"]["id"], "samples": len(result["measurements"]),
                "output": str(args.output), "confirmatory": False}
    raise BCError("Unknown command")


def main(argv: list[str] | None = None) -> int:
    try:
        result = dispatch(parser().parse_args(argv))
        print(json.dumps(plain(result), indent=2, sort_keys=True, allow_nan=False))
        return 1 if isinstance(result, dict) and result.get("command_failed") else 0
    except (BCError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"bc: {exc}", file=sys.stderr)
        return 2
