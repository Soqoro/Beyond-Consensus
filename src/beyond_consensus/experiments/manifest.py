"""Full planned coverage, frozen inputs, and repository/base-pool grouping."""

from __future__ import annotations

import itertools
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
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
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
            if task.group in seen and seen[task.group] != split:
                raise BCError(f"Base-feature-pool leakage: {task.group}")
            seen[task.group] = split


def load_tasks(config: RunConfig) -> list[TaskInstance]:
    if config.task_kind == "workflow_fixture":
        return fixtures(config.task_count)
    if not config.data_manifest:
        raise BCError("CooperBench requires a validated, staged data_manifest; fixtures are never substituted")
    from ..tasks.cooperbench import validate_manifest
    tasks = validate_manifest(Path(config.data_manifest))
    tasks = [task for task in tasks if grouped_split(task.group) == config.data_split]
    if len(tasks) < config.task_count:
        raise BCError(f"Planned {config.task_count} tasks, but only {len(tasks)} were staged")
    return tasks[:config.task_count]


def build_manifest(config: RunConfig, root: Path, tasks: list[TaskInstance] | None = None) -> dict[str, Any]:
    tasks = load_tasks(config) if tasks is None else tasks
    if len(tasks) != config.task_count or len({t.id for t in tasks}) != len(tasks):
        raise BCError("Task count/uniqueness does not match the planned configuration")
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
    return plain({"schema": "bc-manifest-v1", "experiment_id": experiment, "config": config,
                  "source_revision": source, "config_hash": config_hash, "data_hash": data_hash,
                  "model_hash": model_hash, "fixed_state_hash": fixed_hash,
                  "calibration_hash": calibration_hash, "tasks": tasks, "episodes": episodes,
                  "planned_episodes": len(episodes), "planned_only": True})


def validate_manifest(data: dict[str, Any]) -> RunConfig:
    if data.get("schema") != "bc-manifest-v1":
        raise BCError("Unknown experiment manifest schema")
    config = from_dict(data["config"])
    # Hash the serialized configuration so older immutable fixture reports remain
    # readable when optional fields are added to RunConfig. New runs still hash
    # the fully resolved dataclass; source checks prevent resuming old code here.
    if digest(data["config"]) != data["config_hash"] or digest(data["tasks"]) != data["data_hash"]:
        raise BCError("Manifest config/data hash mismatch")
    if digest(config.model) != data["model_hash"]:
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
