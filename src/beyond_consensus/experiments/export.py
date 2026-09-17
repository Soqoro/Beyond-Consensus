"""Small allowlisted JSON exports. No caches, environments, tensors, or trajectories."""

from __future__ import annotations

import io
import json
import os
import re
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from ..util import BCError, canonical, read_json
from ..evaluation.aggregate import aggregate


def sanitize(value: Any, key: str = "") -> Any:
    if re.search(r"token(?!izer)|password|secret|credential|authorization|api.key", key, re.I) and not key.endswith("_tokens"):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: sanitize(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, key) for v in value]
    if isinstance(value, str):
        value = re.sub(r"(?:hf_|ghp_|github_pat_|sk-)[A-Za-z0-9_-]+", "[REDACTED]", value)
        value = re.sub(r"(?i)(Bearer\s+)\S+", r"\1[REDACTED]", value)
        value = re.sub(r"(?i)(token|password|secret|api[_-]?key)([\s=:]+)[^\s,;]+", r"\1\2[REDACTED]", value)
        value = re.sub(r"https?://[^\s/@]+:[^\s/@]+@", "https://[REDACTED]@", value)
        value = re.sub(r"(?:/home|/Users)/[^/\s]+", "/USER", value)
        return value[:8000]
    return value


def export_bundle(output: Path, target: Path, *, dry_run: bool = False) -> dict[str, Any]:
    manifest = read_json(output / "manifest.json")
    summary = aggregate(manifest, output)
    public_manifest = {k: v for k, v in manifest.items() if k != "tasks"}
    public_manifest["tasks"] = [{"id": t["id"], "group": t["group"], "kind": t["kind"]} for t in manifest["tasks"]]
    data_mode = manifest.get("schema") == "bc-manifest-v2"
    if data_mode:
        public_manifest["config"] = {k: v for k, v in public_manifest["config"].items()
            if k not in ("data_manifest", "calibration_file", "fixed_state_file", "coding_environment", "coding_validation")}
    results, failures = [], []
    for row in manifest["episodes"]:
        path = output / "episodes" / row["episode_id"] / "result.json"
        if path.exists():
            result = read_json(path)
            public_result = {key: result[key] for key in ("episode_id", "attempt_id", "status", "success", "error", "metrics", "limitations")}
            if data_mode:
                if public_result["error"]:
                    public_result["error"] = "Details retained in the private journal"
                public_result["costs"] = {k: result["costs"][k] for k in (
                    "cap", "spent", "remaining", "stages", "historical_work", "work_unit", "uncertain_work")}
                provenance = result.get("provenance", {})
                runtime = provenance.get("backend_runtime", {})
                public_result["provenance"] = {"condition": provenance.get("condition"),
                    "source_revision": provenance.get("source_revision"),
                    "model_hash": provenance.get("model_hash"),
                    "runtime": {k: runtime.get(k) for k in ("dependencies", "checkpoint_revision", "tokenizer_revision",
                        "loader", "chat_template", "settings", "model_lock_hash", "model_lock", "slurm_job_id", "slurm_array_job_id",
                        "slurm_array_task_id", "hardware", "compute_capability", "vram_total_bytes", "torch_cuda", "snapshot_id")}}
                checkpoint = path.parent/"checkpoint.json"
                if checkpoint.exists():
                    public_result["generation_diagnostics"] = [e for e in read_json(checkpoint)["store"]["events"]
                        if e["type"] in ("generation_metadata", "context_limit", "observation_limit")]
            results.append(public_result)
        events = output / "episodes" / row["episode_id"] / "events.jsonl"
        if events.exists():
            with events.open(encoding="utf-8") as stream:
                for line in stream:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue  # A crash may leave one incomplete final event.
                    if event.get("type") == "failure":
                        failures.append({"episode_id": row["episode_id"], "error": "Details retained in the private journal" if data_mode else event.get("error"),
                                         "traceback": None if data_mode else event.get("traceback")})
    files = {"summary.json": summary, "manifest.json": public_manifest, "results.json": results,
             "failures.json": failures[-100:]}
    if dry_run:
        return {"files": list(files), "destination": str(target), "written": False}
    if target.exists():
        raise BCError("Export target exists; choose a new bundle path")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {name: (canonical(sanitize(data)) + "\n").encode() for name, data in files.items()}
    if any(len(raw) > 10_000_000 for raw in payload.values()):
        raise BCError("Sanitized bundle item exceeds 10 MB bound")
    fd, temporary = tempfile.mkstemp(dir=target.parent, prefix=".bundle-")
    os.close(fd)
    try:
        with tarfile.open(temporary, "w:gz") as archive:
            for name, raw in payload.items():
                info = tarfile.TarInfo(name)
                info.size, info.mode = len(raw), 0o600
                archive.addfile(info, io.BytesIO(raw))
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {"files": list(files), "destination": str(target), "written": True}
