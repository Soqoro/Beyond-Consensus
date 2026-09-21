"""Bounded read-only analyses and opt-in manifest preparation, no submissions."""
from dataclasses import replace
from pathlib import Path

from .util import BCError, atomic_json, digest, plain, read_json

COMMANDS = {"sqlite-readiness", "planning-audit", "allocation-audit", "allocation-reproduce", "silo-analyze",
    "silo-battery", "silo-boundaries", "validation-config", "measurement-plan", "measurement-report", "diagnostic-costs"}


def add_parsers(sub):
    native = sub.add_parser("sqlite-readiness", help="Sanitized per-task readiness; no SQL or model execution")
    native.add_argument("--staged", type=Path)
    native.add_argument("--output", type=Path, required=True)
    planning = sub.add_parser("planning-audit", help="Count actual decompositions separately from backup masks; no model")
    planning.add_argument("--config", type=Path, required=True)
    planning.add_argument("--output", type=Path, required=True)
    for name in ("allocation-audit", "silo-analyze", "silo-boundaries", "diagnostic-costs"):
        p = sub.add_parser(name, help="Read existing immutable results; write a separately identified diagnostic")
        if name == "diagnostic-costs":
            inputs = p.add_mutually_exclusive_group(required=True)
            inputs.add_argument("--run", type=Path)
            inputs.add_argument("--manifest", type=Path, help="Report planned bounds before submission; measured costs stay null")
        else:
            p.add_argument("--run", type=Path, required=True)
        p.add_argument("--output", type=Path, required=True)
    allocation = sub.add_parser("allocation-reproduce", help="Current finite allocator only; supplied predicted costs, no model")
    allocation.add_argument("--config", type=Path, required=True)
    allocation.add_argument("--cold", type=float, required=True)
    allocation.add_argument("--prepare", type=float, required=True)
    allocation.add_argument("--prepared", type=float, required=True)
    allocation.add_argument("--output", type=Path, required=True)
    for name, default in (("silo-battery", 1000), ("measurement-plan", 2000)):
        p = sub.add_parser(name, help="Freeze fresh development data; no model calls or submissions")
        p.add_argument("--output-root", type=Path, required=True)
        p.add_argument("--seed-start", type=int, default=default)
        p.add_argument("--exclude", type=Path, nargs="*", default=[])
        if name == "silo-battery":
            p.add_argument("--full-only", action="store_true", help="Prepare only eight full controls; no local/boundary/confirmation campaign")
            p.add_argument("--reuse-full", type=Path, help="Reuse an existing frozen eight-source full manifest with --full-only")
    config = sub.add_parser("validation-config", help="Write an explicit opt-in config for validated/frozen development data")
    config.add_argument("--data-manifest", type=Path, required=True)
    config.add_argument("--profile", choices=("qwen35-4b-control", "qwen35-4b-reasoning", "qwen35-9b-later", "qwen35-27b-sql-competence", "qwen35-27b-native-context16k", "qwen35-27b-native-context16k-actions24"), default="qwen35-4b-control")
    config.add_argument("--revision", help="Mandatory explicit resolved 9B revision; no lookup/download")
    config.add_argument("--interface", choices=("original", "submitted_final_value_v1"), default="original")
    config.add_argument("--measurement", action="store_true")
    config.add_argument("--output", type=Path, required=True)
    measurement = sub.add_parser("measurement-report", help="Compare operation costs on disjoint development holdout sources")
    measurement.add_argument("--training", type=Path, required=True)
    measurement.add_argument("--holdout", type=Path, required=True)
    measurement.add_argument("--output", type=Path, required=True)


def write_new(path, data):
    from .tasks.sqlite_tasks import _outside_git
    path = _outside_git(path)
    if path.exists():
        raise BCError("Use a new diagnostic output path; previous observations are immutable")
    atomic_json(path, data)


def dispatch(args):
    import time
    start = time.process_time()
    from .experiments.manifest import source_revision
    root = Path(__file__).resolve().parents[2]
    if args.command in ("silo-battery", "measurement-plan"):
        from .tasks.sqlite_tasks import _outside_git
        destination = _outside_git(args.output_root)
        if destination.exists():
            raise BCError("Use a new directory for the frozen development plan")
        from .tasks.silo_diagnostics import battery, fresh_sources, data_manifest
        if args.command == "silo-battery":
            if args.reuse_full and not args.full_only:
                raise BCError("--reuse-full requires --full-only")
            if args.full_only:
                from .tasks.silo_diagnostics import full_control
                results = full_control(args.seed_start, args.exclude, args.reuse_full)
            else:
                results = battery(args.seed_start, args.exclude)
        else:
            tasks, selection = fresh_sources(args.seed_start, 4, args.exclude)
            results = {"training": data_manifest(tasks[:2], selection=selection),
                "holdout": data_manifest(tasks[2:], selection=selection),
                "plan": {"schema": "bc-measurement-plan-v1", "executions": 4, "units": 16,
                    "operations_per_unit": 6, "planned_operations": 96, "model_executed": False,
                    "selection": selection, "order": ["training", "holdout", "measurement-report"],
                    "measured_cost_estimate": None, "automatic_calibration_activation": False}}
        for name, data in results.items():
            if name == "plan":
                data["preparation_cpu_seconds"] = time.process_time()-start
                data["preparation_accounting"] = "Offline data freezing, reported separately from per-execution token/tool caps; include in end-to-end cost claims."
            write_new(destination/(name+".json"), data)
        return {"output_root": str(destination), **results["plan"]}
    if args.command == "validation-config":
        from .config import from_dict
        from .tasks.data_manifest import validate_data
        tasks = validate_data(args.data_manifest)
        if not tasks:
            raise BCError("No validated tasks; keep the unavailable denominator and finish the prerequisite gate")
        from .experiments.manifest import grouped_split
        if any(grouped_split(t.group) != "development" for t in tasks):
            raise BCError("This cycle only admits development sources")
        profile = read_json(root/"configs"/"validation"/(args.profile+".json"))
        if args.profile == "qwen35-9b-later":
            import re
            if not args.revision or not re.fullmatch(r"[a-f0-9]{40}", args.revision):
                raise BCError("Later 9B profile requires an explicit resolved 40-hex revision, staging and fresh preflight")
            profile["model"].update(revision=args.revision, tokenizer_revision=args.revision)
        elif args.revision:
            raise BCError("4B control/reasoning profiles retain the exact recorded revision")
        profile.update(task_kind=tasks[0].kind, task_count=len(tasks), data_manifest=str(args.data_manifest.resolve()),
            shards=min(4, len(tasks)), silo_interface=args.interface, operation_measurement=args.measurement)
        if args.profile in ("qwen35-27b-sql-competence", "qwen35-27b-native-context16k", "qwen35-27b-native-context16k-actions24"):
            if {t.id for t in tasks} != {"solar_2", "solar_M_3"} or args.measurement:
                raise BCError("27B native gate requires exactly the two renewed individual solar tasks")
            profile["shards"] = 1
        if args.measurement:
            if len(tasks)>2:
                raise BCError("Operation measurement manifests contain at most two fresh sources each")
            profile["budget"] = {"total": 500000}
        result = plain(from_dict(profile))
    elif args.command == "sqlite-readiness":
        from .diagnostics.native import readiness
        result = readiness(read_json(args.staged) if args.staged else None)
    elif args.command == "allocation-audit":
        from .diagnostics.allocation import inspect_output
        result = inspect_output(args.run)
    elif args.command == "planning-audit":
        from .config import load_config
        from .experiments.manifest import load_tasks
        from .diagnostics.planning import audit
        config = load_config(args.config)
        result = audit(load_tasks(config), config)
    elif args.command == "allocation-reproduce":
        from .config import load_config
        from .experiments.manifest import load_tasks
        from .planning.costs import CostEstimates
        from .diagnostics.allocation import reproduce
        config = load_config(args.config)
        result = reproduce(config, load_tasks(config)[0], CostEstimates(args.cold, args.prepare, args.prepared, "explicit_diagnostic_prediction"))
    elif args.command == "silo-analyze":
        from .diagnostics.silo import analyze_output
        result = analyze_output(args.run)
    elif args.command == "silo-boundaries":
        from .tasks.silo_diagnostics import freeze_boundaries
        result = freeze_boundaries(args.run)
    elif args.command == "measurement-report":
        from .diagnostics.measurement import compare
        result = compare(args.training, args.holdout)
    else:
        from .diagnostics.allocation import inspect_output
        if args.manifest:
            manifest, costs = read_json(args.manifest), []
        else:
            audit = inspect_output(args.run)
            manifest = read_json(args.run/"manifest.json")
            costs = [e["reconciliation"]["entry_total"] for e in audit["episodes"] if e.get("reconciliation")]
        from .experiments.manifest import validate_manifest
        validate_manifest(manifest)
        unit_counts = {t["id"]: len(t["required_outputs"]) for t in manifest["tasks"]}
        operation_factor = 6 if manifest["config"].get("operation_measurement") else 1
        result = {"schema": "bc-diagnostic-costs-v1", "manifest_hash": digest(manifest),
            "planned_executions": len(manifest["episodes"]), "executions_with_ledgers": len(costs),
            "actual_charged_work": sum(costs) if costs else None, "mean_observed_work": sum(costs)/len(costs) if costs else None,
            "maximum_work_from_caps": len(manifest["episodes"])*manifest["config"]["budget"]["total"],
            "primary_action_bound": sum(unit_counts[e["task_id"]] for e in manifest["episodes"])*manifest["config"]["max_actions"]*operation_factor,
            "per_call_output_tokens_including_reasoning": manifest["config"]["model"]["max_new_tokens"],
            "context_limit": manifest["config"]["model"]["context_limit"],
            "prediction": "Observed full execution costs are not measured local/boundary costs; no unmeasured savings assumed.",
            "per_condition_max_executions": len(manifest["episodes"]),
            "estimate_status": "observed_run_costs" if costs else "unmeasured_caps_and_action_bounds_only",
            "proposed_additional_executions": 0}
    if args.command not in ("validation-config", "silo-boundaries"):
        result["analysis_source_revision"] = source_revision(root)
        result["analysis_cpu_seconds"] = time.process_time()-start
        result["report_id"] = digest(result)
    elif args.command == "silo-boundaries":
        result["preparation_cpu_seconds"] = time.process_time()-start
        result["preparation_source_revision"] = source_revision(root)
    write_new(args.output, result)
    return {"report": str(args.output), "schema": result.get("schema"), "status": result.get("status", "written"),
        "summary": result.get("summary"), "model_executed": False,
        **({"planned": result["planned"], "unavailable": result["unavailable"], "denominator": result["denominator"]} if args.command == "silo-boundaries" else {})}
