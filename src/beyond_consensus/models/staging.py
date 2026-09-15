"""Explicit, collision-guarded staging. Batch inference is strictly offline."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..config import ModelConfig
from ..util import BCError, atomic_json, directory_lock, file_hash, read_json


def stage_model(config: ModelConfig, root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    if not root.is_absolute():
        raise BCError("Staging root must be an explicit absolute user-writable directory")
    target = root / config.checkpoint.replace("/", "--")
    if dry_run:
        return {"operation": "model_staging", "checkpoint": config.checkpoint, "destination": str(target),
                "network": "explicit setup only", "resolve_once": True, "downloaded": False}
    target.mkdir(parents=True, exist_ok=True)
    with directory_lock(target / ".download.lock"):
        lock_path = target / "model-lock.json"
        if lock_path.exists():
            lock = read_json(lock_path)
            if config.revision and config.revision != lock["revision"]:
                raise BCError("Staged revision differs; use a new staging root, never mutate running models")
            return lock
        try:
            from huggingface_hub import HfApi, snapshot_download
        except ImportError as exc:
            raise BCError("Install pinned GPU/staging dependencies during explicit setup first") from exc
        try:
            api = HfApi()
            revision = config.revision or api.model_info(config.checkpoint).sha
            tokenizer_revision = config.tokenizer_revision or revision
            for value in (revision, tokenizer_revision):
                if not re.fullmatch(r"[a-f0-9]{40}", value):
                    raise BCError("Hub did not resolve an immutable commit")
            model_path = snapshot_download(config.checkpoint, revision=revision,
                cache_dir=str(root / "hub"), allow_patterns=["*.safetensors", "*.json", "*.jinja", "*.model", "*.txt"])
            tokenizer_path = model_path if tokenizer_revision == revision else snapshot_download(
                config.checkpoint, revision=tokenizer_revision, cache_dir=str(root / "hub"),
                allow_patterns=["*.json", "*.jinja", "*.model", "*.txt"])
        except Exception as exc:
            raise BCError("Model staging failed. Check HTTPS access and available storage. For gated models, "
                          "accept the license on the official model page and configure Hugging Face authentication "
                          "outside this repository; never put credentials in arguments or logs. "
                          f"Failure class: {type(exc).__name__}") from exc
        metadata_files = {str(p.relative_to(model_path)): file_hash(p) for p in Path(model_path).rglob("*")
                          if p.is_file() and p.suffix in (".json", ".jinja")}
        lock = {"schema": "bc-model-lock-v1", "checkpoint": config.checkpoint, "revision": revision,
                "tokenizer_revision": tokenizer_revision, "model_path": str(model_path),
                "tokenizer_path": str(tokenizer_path), "metadata_hashes": metadata_files,
                "status": "staged_not_gpu_validated"}
        atomic_json(lock_path, lock)
        return lock


def resolve_model_config(config: ModelConfig, lock_path: Path) -> ModelConfig:
    from dataclasses import replace
    lock = read_json(lock_path)
    if lock.get("schema") != "bc-model-lock-v1" or lock["checkpoint"] != config.checkpoint:
        raise BCError("Model lock does not match checkpoint")
    if config.revision and config.revision != lock["revision"]:
        raise BCError("Configured checkpoint revision differs from staged lock")
    if config.tokenizer_revision and config.tokenizer_revision != lock["tokenizer_revision"]:
        raise BCError("Configured tokenizer revision differs from staged lock")
    return replace(config, revision=lock["revision"], tokenizer_revision=lock["tokenizer_revision"])
