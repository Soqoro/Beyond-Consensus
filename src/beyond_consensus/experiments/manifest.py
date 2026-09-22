"""Full planned coverage, frozen inputs, and repository/base-pool grouping."""

from __future__ import annotations

import itertools
import re
import subprocess
from pathlib import Path
from typing import Any

from ..config import RunConfig, from_dict
from ..schemas import AttackSpec, EpisodeManifest, TaskInstance
from ..tasks.workflow import fixtures
from ..util import BCError, digest, file_hash, plain, read_json


def source_revision(root: Path) -> str:
    marker = root / "snapshot.json"
    if marker.exists():
        return read_json(marker)["source_revision"]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "uncommitted"
    files = {str(p.relative_to(root)): file_hash(p) for directory in ("src", "scripts", "experiments", "configs")
             for p in (root / directory).rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and not p.name.endswith(".local.json")}
    files.update({p.name: file_hash(p) for p in [root / "pyproject.toml", *root.glob("requirements*.txt")]
                  if p.is_file()})
    return f"{commit}:{digest(files)}"


def task_from(data: dict[str, Any]) -> TaskInstance:
    return TaskInstance(**{**data, "required_outputs": tuple(data["required_outputs"]),
                           "public_cases": tuple(data["public_cases"])})


def grouped_split(group: str) -> str:
    bucket = int(digest(["group-hash-v1", group])[:8], 16) % 10
    return "development" if bucket < 6 else ("validation" if bucket < 8 else "test")


def validate_splits(assignments: dict[str, list[TaskInstance]]) -> None:
    seen = {}
    for split, tasks in assignments.items():
        for task in tasks:
            keys = ["group:"+task.group]
            keys += ["source:"+s for s in task.metadata.get("source_ids", [])]
            keys += ["requirement:"+s for s in task.metadata.get("requirement_hashes", [])]
            if task.metadata.get("base_hash"):
                keys.append("base:"+task.metadata["base_hash"])
            for key in keys:
                if key in seen and seen[key] != split:
                    raise BCError(f"Base-feature-pool/shared-source leakage: {key}")
                seen[key] = split
    documents = []
    for split, tasks in assignments.items():
        for task in tasks:
            if task.kind in ("sqlite_native", "sqlite_pair"):
                for source in task.sources.values():
                    words = set(re.findall(r"[a-z0-9]+", source["requirement"].lower()))
                    for other_split, other in documents:
                        if split != other_split and min(len(words), len(other)) >= 8 and len(words & other)/len(words | other) >= .9:
                            raise BCError("Near-duplicate requirement across database splits; review and group shared sources")
                    documents.append((split, words))


def load_tasks(config: RunConfig) -> list[TaskInstance]:
    if config.task_kind == "workflow_fixture":
        return fixtures(config.task_count)
    if config.task_kind == "sqlite_fixture":
        if config.sqlite_fixture_suite == "tool_correction_v1":
            from ..tasks.sqlite_correction import tasks
            return tasks()
        if config.sqlite_fixture_suite == "tool_compatibility_v1":
            from ..tasks.sqlite_compatibility import tasks
            return tasks()
        from ..tasks.sqlite_tasks import fixtures as sqlite_fixtures
        return sqlite_fixtures(config.task_count)
    if not config.data_manifest:
        raise BCError(f"{config.task_kind} requires a validated staged data_manifest; fixtures are never substituted")
    if config.task_kind == "cooperbench":
        from ..tasks.cooperbench import validate_manifest
        tasks = validate_manifest(Path(config.data_manifest))
    else:
        from ..tasks.data_manifest import validate_data
        tasks = validate_data(Path(config.data_manifest))
        if any(t.kind != config.task_kind for t in tasks):
            raise BCError("Configured environment differs from staged tasks")
    tasks = [task for task in tasks if grouped_split(task.group) == config.data_split]
    if len(tasks) < config.task_count:
        raise BCError(f"Planned {config.task_count} tasks, but only {len(tasks)} were staged")
    return tasks[:config.task_count]


def build_manifest(config: RunConfig, root: Path, tasks: list[TaskInstance] | None = None) -> dict[str, Any]:
    tasks = load_tasks(config) if tasks is None else tasks
    if len(tasks) != config.task_count or len({t.id for t in tasks}) != len(tasks):
        raise BCError("Task count/uniqueness does not match the planned configuration")
    if any(t.kind != config.task_kind for t in tasks):
        raise BCError("Manifest task environment mismatch")
    if config.organization != "legacy":
        from ..policies.core import require_boundary_variation
        for task in tasks:
            require_boundary_variation(task)
        if config.model.backend != "mock" and not config.calibration_file:
            raise BCError("Organization conditions require compatible measured calibration before a real-model manifest")
    from ..runtime.data_domain import DATA_KINDS
    data_mode = config.task_kind in DATA_KINDS
    if data_mode:
        from ..tasks.data_manifest import regime
        if len({digest(regime(t)) for t in tasks}) != 1:
            raise BCError("Cannot mix task/scorer/access regimes in one manifest")
        if any(t.metadata.get("diagnostic_mode") for t in tasks) and (
                config.policies != ("single",) or config.attacks != ("clean",) or config.protocol != "A"):
            raise BCError("SILO diagnostic modes require their own single/clean Protocol A manifest")
        if config.task_kind in ("sqlite_native", "sqlite_pair") and any(
                t.metadata.get("readiness") != "reference_validated" or not t.metadata.get("validation_hash") for t in tasks):
            raise BCError("Scored native/pair manifests require completed reference validation")
        if config.task_kind != "silo":
            from copy import deepcopy
            from ..runtime.sqlite_executor import capabilities
            tasks = deepcopy(tasks)
            runtime = capabilities()
            for task in tasks:
                validated = task.metadata.get("validated_sqlite_runtime")
                if validated and validated != runtime:
                    raise BCError("SQLite validation runtime changed; rerun native/pair validation in this environment")
                task.metadata["executor_runtime"] = runtime
    if config.coding_environment:
        from ..runtime.coding_episode import require_coding_e0, validate_coding_task
        environment = require_coding_e0(config)
        for task in tasks:
            validate_coding_task(config, environment, task)
    if config.protocol == "B" and (len(tasks) != 1 or len(config.seeds) != 1 or len(config.attacks) != 1):
        raise BCError("Each Protocol B manifest compares policies on exactly one frozen task/seed/alarm")
    source = source_revision(root)
    config_hash, data_hash, model_hash = digest(config), digest(tasks), digest(config.model)
    fixed_hash = digest(read_json(config.fixed_state_file)) if config.fixed_state_file else None
    calibration_hash = digest(read_json(config.calibration_file)) if config.calibration_file else None
    experiment = digest([source, config_hash, data_hash, model_hash, fixed_hash, calibration_hash])
    episodes = []
    for (i, task), policy, attack, seed in itertools.product(enumerate(tasks), config.policies, config.attacks, config.seeds):
        # Paired attack selection uses no policy name. Evaluation seed is a separate domain.
        attack_seed = int(digest([task.id, seed, "attack-selection"])[:8], 16)
        eval_seed = int(digest([task.id, seed, "hidden-evaluation"])[:8], 16)
        identifier = digest([experiment, task.source_hash, policy, attack, seed])
        episodes.append(EpisodeManifest(identifier, experiment, source, config_hash, data_hash, model_hash,
            task.id, task.group, policy, AttackSpec(attack, selection_seed=attack_seed), seed, eval_seed,
            config.protocol, config.mode, i % config.shards, fixed_hash))
    constraints = {}
    if config.model.checkpoint == "Qwen/Qwen3.5-27B":
        from ..diagnostics.competence import fingerprints
        constraints["competence_interface_hashes"] = fingerprints(root)
        if config.task_kind == "sqlite_native" and {t.id for t in tasks} != {"solar_2", "solar_M_3"}:
            raise BCError("27B native gate permits only renewed solar_2 and solar_M_3")
    if config.model.action_constraint != "none":
        from ..models.action_schema import contract
        constraints["action_constraint"] = contract()
    return plain({"schema": "bc-manifest-v2" if data_mode else "bc-manifest-v1", **constraints,
                  **({"data_regime": regime(tasks[0])} if data_mode else {}),
                  "experiment_id": experiment, "config": config,
                  "source_revision": source, "config_hash": config_hash, "data_hash": data_hash,
                  "model_hash": model_hash, "fixed_state_hash": fixed_hash,
                  "calibration_hash": calibration_hash, "tasks": tasks, "episodes": episodes,
                  "planned_episodes": len(episodes), "planned_only": True})


def validate_manifest(data: dict[str, Any]) -> RunConfig:
    if data.get("schema") not in ("bc-manifest-v1", "bc-manifest-v2"):
        raise BCError("Unknown experiment manifest schema")
    config = from_dict(data["config"])
    if config.model.action_constraint != "none":
        from ..models.action_schema import contract
        if data.get("action_constraint") != contract():
            raise BCError("Constrained action contract changed; create a new manifest")
    elif "action_constraint" in data:
        raise BCError("Unexpected action constraint metadata")
    if config.task_kind in ("sqlite_fixture", "sqlite_native", "sqlite_pair", "silo") and data["schema"] != "bc-manifest-v2":
        raise BCError("Restricted data workflows require a v2 manifest")
    if data["schema"] == "bc-manifest-v2":
        from ..tasks.data_manifest import regime
        if not data["tasks"] or any(regime(task_from(t)) != data["data_regime"] for t in data["tasks"]):
            raise BCError("Versioned data regime mismatch")
    # Hash the serialized configuration so older immutable fixture reports remain
    # readable when optional fields are added to RunConfig. New runs still hash
    # the fully resolved dataclass; source checks prevent resuming old code here.
    if digest(data["config"]) != data["config_hash"] or digest(data["tasks"]) != data["data_hash"]:
        raise BCError("Manifest config/data hash mismatch")
    if digest(data["config"]["model"]) != data["model_hash"]:
        raise BCError("Manifest model hash mismatch")
    experiment = digest([data["source_revision"], data["config_hash"], data["data_hash"], data["model_hash"],
                         data["fixed_state_hash"], data["calibration_hash"]])
    if experiment != data["experiment_id"]:
        raise BCError("Experiment provenance mismatch")
    ids = [e["episode_id"] for e in data["episodes"]]
    if len(ids) != len(set(ids)) or len(ids) != data["planned_episodes"]:
        raise BCError("Duplicate/missing planned episode rows")
    expected_count = config.task_count * len(config.policies) * len(config.attacks) * len(config.seeds)
    if len(ids) != expected_count:
        raise BCError("Planned grid is incomplete")
    expected_grid = set(itertools.product((t["id"] for t in data["tasks"]), config.policies, config.attacks, config.seeds))
    actual_grid = {(r["task_id"], r["policy"], r["attack"]["family"], r["seed"]) for r in data["episodes"]}
    if expected_grid != actual_grid or len(data["tasks"]) != config.task_count:
        raise BCError("Planned tasks/policy/attack/seed coverage differs from configuration")
    for row in data["episodes"]:
        task = next((t for t in data["tasks"] if t["id"] == row["task_id"]), None)
        if task is None or row["episode_id"] != digest([experiment, digest(task), row["policy"], row["attack"]["family"], row["seed"]]):
            raise BCError("Logical episode identity mismatch")
        if not 0 <= row["shard"] < config.shards or row["protocol"] != config.protocol or row["mode"] != config.mode:
            raise BCError("Shard/protocol/mode mismatch")
        expected_attack = plain(AttackSpec(row["attack"]["family"], selection_seed=int(digest(
            [row["task_id"], row["seed"], "attack-selection"])[:8], 16)))
        if (row["attack"] != expected_attack or row["evaluation_seed"] != int(digest(
                [row["task_id"], row["seed"], "hidden-evaluation"])[:8], 16) or row["group"] != task["group"]):
            raise BCError("Episode attack/evaluation seed or group mismatch")
        for field in ("experiment_id", "source_revision", "config_hash", "data_hash", "model_hash", "fixed_state_hash"):
            if row[field] != data[field]:
                raise BCError(f"Episode {field} mismatch")
        if row["shard"] != next(i for i, t in enumerate(data["tasks"]) if t["id"] == row["task_id"]) % config.shards:
            raise BCError("Episode was moved to a different task shard")
    return config


def episode_from(data: dict[str, Any]) -> EpisodeManifest:
    return EpisodeManifest(**{**data, "attack": AttackSpec(**data["attack"])})
