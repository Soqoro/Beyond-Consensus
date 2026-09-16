from __future__ import annotations

import signal
import traceback
from pathlib import Path
from typing import Any

from ..models.base import Backend
from ..models.mock import MockBackend
from ..runtime.episode import EpisodeEngine
from ..runtime.persistence import EpisodeJournal
from ..runtime.budget import BudgetLedger
from ..schemas import EpisodeResult
from ..util import BCError, atomic_json, digest, directory_lock, read_json
from .manifest import episode_from, source_revision, task_from, validate_manifest

TERMINAL = {"completed", "budget_exhausted", "blocked_sandbox", "ineligible", "scoring_unavailable", "blocked_capability", "blocked_prerequisite", "execution_limit"}
RETRYABLE = {"interrupted", "infrastructure_failed"}


def run_manifest(manifest: dict[str, Any], output: Path, root: Path, *, shard: int | None = None,
                 backend: Backend | None = None, model_lock: Path | None = None,
                 retry_failures: bool = False) -> list[dict[str, Any]]:
    config = validate_manifest(manifest)
    if config.model.backend == "mock" and config.task_kind in ("sqlite_native", "sqlite_pair") and backend is None:
        raise BCError("Mock compilation is only a labelled fixture/SILO test worker; native tasks require the model adapter")
    if source_revision(root) != manifest["source_revision"]:
        raise BCError("Source changed since manifest creation; create a new manifest/run")
    if config.calibration_file and digest(read_json(config.calibration_file)) != manifest["calibration_hash"]:
        raise BCError("Calibration changed since manifest creation")
    if config.fixed_state_file and digest(read_json(config.fixed_state_file)) != manifest["fixed_state_hash"]:
        raise BCError("Fixed state changed since manifest creation")
    if shard is not None and not 0 <= shard < config.shards:
        raise BCError("Shard index outside manifest")
    output.mkdir(parents=True, exist_ok=True)
    existing = output / "manifest.json"
    if existing.exists():
        if digest(read_json(existing)) != digest(manifest):
            raise BCError("Output directory belongs to different provenance; choose a new output directory")
    else:
        with directory_lock(output / ".manifest.lock"):
            if existing.exists() and digest(read_json(existing)) != digest(manifest):
                raise BCError("Output directory belongs to different provenance; choose a new output directory")
            if not existing.exists():
                atomic_json(existing, manifest)
    if config.task_kind == "cooperbench":
        from ..runtime.sandbox import require_repository_sandbox
        require_repository_sandbox(config, tasks=[task_from(t) for t in manifest["tasks"]])
    selected = [e for e in manifest["episodes"] if shard is None or e["shard"] == shard]
    stopped = [False]
    previous_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        previous_handlers[sig] = signal.signal(sig, lambda *_: stopped.__setitem__(0, True))
    results = []
    try:
        for row in selected:
            journal = EpisodeJournal(output, row["episode_id"])
            with directory_lock(journal.path / ".lock"):
                result_path = journal.path / "result.json"
                if result_path.exists():
                    prior = read_json(result_path)
                    if prior["provenance"]["manifest_hash"] != digest(row):
                        raise BCError("Result provenance mismatch")
                    if prior["status"] in TERMINAL or not retry_failures:
                        results.append(prior)
                        continue
                    if prior["status"] not in RETRYABLE:
                        raise BCError("Result status is not eligible for retry")
                if stopped[0]:
                    break
                episode = episode_from(row)
                attempt = journal.begin(digest(episode))
                if backend is None:
                    try:
                        if config.model.backend == "mock":
                            backend = MockBackend()
                        else:
                            from ..models.transformers_backend import TransformersBackend
                            backend = TransformersBackend(config.model, model_lock)
                    except Exception as exc:
                        error = f"Model initialization failed: {type(exc).__name__}: {exc}"
                        journal.event("failure", error=error, traceback=traceback.format_exc())
                        result = EpisodeResult(episode.episode_id, attempt, episode.experiment_id,
                            episode.protocol, episode.mode, "infrastructure_failed", None, episode.task_id,
                            episode.group, episode.policy, episode.attack.family, episode.seed,
                            BudgetLedger(config.budget.total, config.budget).summary(), {},
                            {"manifest_hash": digest(episode)}, error=error)
                        journal.result(result)
                        results.append(read_json(result_path))
                        # One failed backend initialization is enough to stop this shard;
                        # remaining planned episodes stay explicitly missing.
                        break
                task = task_from(next(t for t in manifest["tasks"] if t["id"] == episode.task_id))
                engine_type = EpisodeEngine
                if config.task_kind == "cooperbench":
                    from ..runtime.coding_episode import CodingEpisodeEngine
                    engine_type = CodingEpisodeEngine
                engine = engine_type(task, episode, config, backend, journal, attempt, lambda: stopped[0])
                result = engine.run()
                results.append(read_json(result_path))
                if result.status == "interrupted":
                    break
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    return results
