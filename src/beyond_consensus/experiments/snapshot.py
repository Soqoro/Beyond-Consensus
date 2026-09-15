"""Immutable commit archives with resolved inputs and checked imports."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

from ..util import BCError, atomic_json, digest, directory_lock, file_hash, read_json
from .manifest import source_revision


def environment_inventory(python: str) -> dict[str, Any]:
    script = (
        "import importlib.metadata as m,json,sys; "
        "ds=list(m.distributions()); "
        "print(json.dumps({'python':sys.version.split()[0],"
        "'packages':{d.metadata['Name']:d.version for d in ds if d.metadata['Name']},"
        "'editable':sorted(d.metadata['Name'] for d in ds if "
        "json.loads(d.read_text('direct_url.json') or '{}').get('dir_info',{}).get('editable'))},sort_keys=True))"
    )
    try:
        result = subprocess.run([python, "-I", "-c", script], capture_output=True, text=True,
                                timeout=30, check=True)
        inventory = json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise BCError("Cannot inventory the configured Python environment; complete setup before submission") from exc
    if inventory["editable"]:
        raise BCError(f"Cluster environment contains editable installs: {inventory['editable']}; use a fixed environment")
    return inventory


def verify_snapshot(root: Path) -> dict[str, Any]:
    marker = read_json(root / "snapshot.json")
    for name, expected in marker["files"].items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or file_hash(path) != expected:
            raise BCError(f"Snapshot file changed: {name}")
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
              and p.name != "snapshot.json" and "__pycache__" not in p.parts}
    if actual != set(marker["files"]):
        raise BCError("Snapshot contains unexpected or missing files")
    return marker


def create_snapshot(repo: Path, root: Path, manifest: dict[str, Any], cluster: dict[str, Any],
                    model_lock: dict[str, Any]) -> Path:
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=normal"], cwd=repo, text=True)
    if dirty.strip():
        raise BCError("Commit reviewed local changes and pull that commit before submission; snapshot requires a clean checkout")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    if source_revision(repo) != manifest["source_revision"]:
        raise BCError("Manifest source differs from submission checkout")
    key = digest([commit, manifest, cluster, model_lock])
    destination = root / key
    with directory_lock(root / f".{key}.lock"):
        if destination.exists():
            verify_snapshot(destination)
            return destination
        archive = subprocess.check_output(["git", "archive", "--format=tar", commit], cwd=repo)
        destination.mkdir(parents=True)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            for member in tar.getmembers():
                if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
                    raise BCError("Snapshot refuses symlinks and special files")
                if not (destination / member.name).resolve().is_relative_to(destination.resolve()):
                    raise BCError("Unsafe archive path")
            tar.extractall(destination, filter="data")
        inputs = destination / "resolved"
        atomic_json(inputs / "manifest.json", manifest)
        atomic_json(inputs / "cluster.json", cluster)
        atomic_json(inputs / "model-lock.json", model_lock)
        atomic_json(inputs / "environment.json", environment_inventory(cluster.get("python", sys.executable)))
        files = {str(p.relative_to(destination)): file_hash(p) for p in destination.rglob("*") if p.is_file()}
        atomic_json(destination / "snapshot.json", {"commit": commit, "source_revision": manifest["source_revision"],
                    "manifest_hash": digest(manifest), "cluster_hash": digest(cluster), "files": files,
                    "activation_hash": file_hash(Path(cluster["activation_script"])) if cluster.get("activation_script") else None})
        for path in destination.rglob("*"):
            path.chmod(0o555 if path.is_dir() or path.suffix in (".sh", ".sbatch") else 0o444)
        destination.chmod(0o555)
    return destination
