"""Versioned read-only adapter for the official directory/subset schema.

No upstream scripts are executed. Only feature.md enters TaskInstance.sources.
Golden patches, tests, runners, setup scripts and Git histories are never worker tools.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..schemas import TaskInstance
from ..util import BCError, atomic_json, digest, directory_lock, file_hash, plain, read_json

ADAPTER_VERSION = "cooperbench-directory-v1"
INSPECTED_UPSTREAM = "4913c4ebb84d2606cdb5628936b88529f3e181df"
DATASET = "CooperBench/cooperbench-dataset"


def safe_file(root: Path, relative: str) -> Path:
    path = root / relative
    symlinked = path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != root)
    if symlinked or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise BCError(f"Missing, symlinked, or escaping dataset file: {relative}")
    return path


def import_dataset(root: Path, subset_file: Path, upstream_commit: str, dataset_revision: str) -> dict[str, Any]:
    for rev in (upstream_commit, dataset_revision):
        if not re.fullmatch(r"[a-f0-9]{40}", rev):
            raise BCError("CooperBench upstream and dataset revisions must be immutable 40-character commits")
    subset = read_json(subset_file)
    if not isinstance(subset.get("tasks"), list):
        raise BCError("Official subset schema requires tasks[{repo,task_id,pairs}]")
    tasks, hashes = [], {}
    for item in subset["tasks"]:
        repo, task_id = item.get("repo"), item.get("task_id")
        if not isinstance(repo, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", repo) or type(task_id) is not int or task_id < 0:
            raise BCError("Invalid upstream repo/task_id")
        prefix = f"{repo}/task{task_id}"
        setup = safe_file(root, f"{prefix}/setup.sh").read_text(encoding="utf-8")
        commits = set(re.findall(r'BASE_COMMIT=[\"\x27]?([a-f0-9]{40})', setup))
        if not commits:
            commits = set(re.findall(r'git checkout\s+[\"\x27]?([a-f0-9]{40})', setup))
        urls = set(re.findall(r'git clone\s+(https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)', setup))
        if len(commits) != 1 or len(urls) != 1:
            raise BCError(f"{prefix}: cannot unambiguously extract repository/base commit; adapter review required")
        base, url = next(iter(commits)), next(iter(urls)).removesuffix(".git")
        task_dir = root / prefix
        feature_ids = sorted(int(p.name[7:]) for p in task_dir.iterdir()
                             if p.is_dir() and re.fullmatch(r"feature\d+", p.name))
        if len(feature_ids) < 2:
            raise BCError(f"{prefix}: fewer than two features in pool")
        pool = {str(i): file_hash(safe_file(root, f"{prefix}/feature{i}/feature.md")) for i in feature_ids}
        hashes.update({f"{prefix}/feature{i}/feature.md": pool[str(i)] for i in feature_ids})
        environment = {}
        for name in ("setup.sh", "run_tests.sh", "Dockerfile", "runner.sh"):
            path = safe_file(root, f"{prefix}/{name}")
            hashes[str(path.relative_to(root))] = file_hash(path)
            environment[name] = hashes[str(path.relative_to(root))]
        if not isinstance(item.get("pairs"), list) or not item["pairs"]:
            raise BCError(f"{prefix}: missing actual pair selection")
        for pair in item["pairs"]:
            if not isinstance(pair, list) or len(pair) != 2 or any(type(i) is not int for i in pair) or len(set(pair)) != 2:
                raise BCError(f"{prefix}: pair must contain two distinct integer feature IDs")
            pair = sorted(pair)
            if not set(pair) <= set(feature_ids):
                raise BCError(f"{prefix}: selected feature is not in the actual pool")
            sources, evaluator_files = {}, []
            for feature in pair:
                for name in ("feature.md", "feature.patch", "tests.patch"):
                    relative = f"{prefix}/feature{feature}/{name}"
                    path = safe_file(root, relative)
                    hashes[relative] = file_hash(path)
                    if name == "feature.md":
                        sources[f"feature{feature}"] = path.read_text(encoding="utf-8")
                    else:
                        evaluator_files.append(relative)
            identifier = f"{prefix}/features_{pair[0]}_{pair[1]}"
            tasks.append(TaskInstance(identifier, "cooperbench", digest([url, base]),
                "Implement both requested features jointly in one integrated repository result.",
                sources, tuple(sources), (),
                {"adapter_version": ADAPTER_VERSION, "upstream_commit": upstream_commit,
                 "dataset_revision": dataset_revision, "repository": url, "base_commit": base,
                 "feature_pool_id": digest(pool), "feature_ids": pair, "pair_id": identifier,
                 "environment_requirements": environment, "evaluator_only_files": evaluator_files,
                 "source_hashes": {name: hashes[name] for name in hashes if name.startswith(prefix+"/")},
                 "public_tests": "none separately designated by this adapter",
                 "evaluation": "both feature test patches on one integrated candidate; sandbox required"}))
    if not tasks or len({t.id for t in tasks}) != len(tasks):
        raise BCError("Empty or duplicate CooperBench pair selection")
    return plain({"schema": ADAPTER_VERSION, "root": str(root.resolve()), "upstream_commit": upstream_commit,
                  "dataset_revision": dataset_revision, "subset_hash": file_hash(subset_file),
                  "selection_rule": "upstream subset order; no comparative-result selection",
                  "file_hashes": hashes, "tasks": tasks})


def validate_manifest(path: Path) -> list[TaskInstance]:
    from ..experiments.manifest import task_from
    data = read_json(path)
    if data.get("schema") != ADAPTER_VERSION:
        raise BCError("Unknown CooperBench adapter version")
    root = Path(data["root"])
    for name, expected in data["file_hashes"].items():
        if file_hash(safe_file(root, name)) != expected:
            raise BCError(f"Staged data changed: {name}; new manifest required")
    tasks = [task_from(t) for t in data["tasks"]]
    if not tasks or len({t.id for t in tasks}) != len(tasks):
        raise BCError("Empty or duplicated CooperBench pair manifest")
    for task in tasks:
        if task.kind != "cooperbench" or len(task.required_outputs) != 2:
            raise BCError("CooperBench requires both requested features")
        if any(not k.startswith("feature") for k in task.sources):
            raise BCError("Only public feature descriptions may enter worker sources")
        if task.group != digest([task.metadata["repository"], task.metadata["base_commit"]]):
            raise BCError("Repository/base grouping mismatch")
        prefix = task.metadata["pair_id"].split("/features_")[0]
        for feature, description in task.sources.items():
            if not re.fullmatch(r"feature\d+", feature):
                raise BCError("Invalid feature source key")
            if safe_file(root, f"{prefix}/{feature}/feature.md").read_text(encoding="utf-8") != description:
                raise BCError("Task descriptions differ from staged public source")
    return tasks


def stage_dataset(root: Path, revision: str | None = None, *, dry_run: bool = False) -> dict[str, Any]:
    if not root.is_absolute():
        raise BCError("Data staging requires an explicit absolute writable root")
    if dry_run:
        return {"dataset": DATASET, "root": str(root), "revision": revision or "resolve-once",
                "downloaded": False, "execution": "none"}
    root.mkdir(parents=True, exist_ok=True)
    with directory_lock(root / ".dataset.lock"):
        lock_path = root / "dataset-lock.json"
        if lock_path.exists():
            lock = read_json(lock_path)
            if revision and revision != lock["revision"]:
                raise BCError("Dataset already staged at another revision; use a new root")
            return lock
        try:
            from huggingface_hub import HfApi, snapshot_download
            resolved = revision or HfApi().dataset_info(DATASET).sha
            if not re.fullmatch(r"[a-f0-9]{40}", resolved):
                raise BCError("Dataset did not resolve to a commit")
            path = snapshot_download(DATASET, repo_type="dataset", revision=resolved,
                                     cache_dir=str(root / "hub"), local_dir=str(root / "data" / resolved))
        except Exception as exc:
            raise BCError(f"Dataset staging failed ({type(exc).__name__}); check setup dependencies, HTTPS and storage") from exc
        lock = {"dataset": DATASET, "revision": resolved, "path": path}
        atomic_json(lock_path, lock)
        return lock
