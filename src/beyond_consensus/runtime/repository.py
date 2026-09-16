"""Bounded, data-only repository transfer. Never execute files on the host."""
from __future__ import annotations

import base64
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import time

from ..util import BCError, digest, file_hash, read_json, strict_keys
from .apptainer import ApptainerSandbox, SandboxFailure, SandboxProfile, absolute

MAX_FILES, MAX_TREE, MAX_FILE = 20000, 268435456, 4194304
FORBIDDEN = {".git", ".hg", ".svn", ".ssh", ".aws", ".env"}


class ToolRejected(BCError):
    """A completed sandbox invocation rejected the candidate action."""


def relative(name: str) -> str:
    if not isinstance(name, str):
        raise BCError("Repository path must be text")
    p = PurePosixPath(name)
    if (not name or name in (".", "..") or p.is_absolute() or str(p) != name or "\\" in name or "\x00" in name or
            set(p.parts) & (FORBIDDEN | {"..", "."})):
        raise BCError("Unsafe repository path")
    return name


def inventory(root: Path) -> dict:
    absolute(str(root))
    if not root.is_dir():
        raise BCError("Missing repository tree")
    result, total = {}, 0
    for path in sorted(root.rglob("*")):
        name = relative(str(path.relative_to(root)))
        st = path.lstat()
        if stat.S_ISDIR(st.st_mode):
            continue
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise BCError("Repository links and special files are forbidden")
        total += st.st_size
        if st.st_size > MAX_FILE or total > MAX_TREE or len(result) >= MAX_FILES:
            raise BCError("Repository size bound exceeded")
        result[name] = {"sha256": file_hash(path), "executable": bool(st.st_mode & 0o111)}
    return result


def copy_tree(source: Path, destination: Path) -> dict:
    expected = inventory(source)
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    for name, meta in expected.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source / name).read_bytes())
        target.chmod(0o700 if meta["executable"] else 0o600)
    if inventory(destination) != expected:
        raise BCError("Repository changed during copy")
    return expected


def apply_changes(root: Path, changes: dict) -> None:
    """Validate an entire untrusted wire response before modifying the candidate."""
    if not isinstance(changes, dict) or len(changes) > MAX_FILES:
        raise BCError("Invalid candidate changes")
    before = inventory(root)
    decoded, total = {}, 0
    names = set(before)
    for name, entry in changes.items():
        relative(name)
        if entry is None:
            if name not in before:
                raise BCError("Deletion names a missing file")
            names.discard(name)
            decoded[name] = None
        else:
            strict_keys(entry, {"data", "executable"}, {"data", "executable"})
            if type(entry["executable"]) is not bool or not isinstance(entry["data"], str):
                raise BCError("Invalid file metadata")
            raw = base64.b64decode(entry["data"], validate=True)
            total += len(raw)
            if len(raw) > MAX_FILE or total > 8388608:
                raise BCError("Candidate changes exceed transport bound")
            decoded[name] = (raw, entry["executable"])
            names.add(name)
    if len(names) > MAX_FILES or any(str(parent) in names for n in names for parent in PurePosixPath(n).parents):
        raise BCError("File/directory collision or file count exceeded")
    size = sum((root / n).stat().st_size for n in before if n not in changes) + total
    if size > MAX_TREE:
        raise BCError("Candidate tree exceeds size bound")
    for name, entry in decoded.items():
        if entry is None:
            (root / name).unlink()
    for name, entry in decoded.items():
        if entry is not None:
            target = root / name
            # Empty old directories may be replaced by a file.
            if target.is_dir():
                target.rmdir()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(entry[0])
            target.chmod(0o700 if entry[1] else 0o600)
    inventory(root)


class CodingEnvironment:
    """One explicitly reviewed task/image/base-tree/evaluator configuration."""
    def __init__(self, path: Path, expected_hash: str | None = None):
        self.path = path
        self.data = data = read_json(path)
        strict_keys(data, {"schema", "task_id", "task_hash", "base_root", "base_files", "profile", "approval", "approval_hash",
                           "reviewer", "source_review", "suites"},
                    {"schema", "task_id", "task_hash", "base_root", "base_files", "profile", "approval", "approval_hash",
                     "reviewer", "source_review", "suites"})
        if data["schema"] != "cooper-e0-environment-v1" or not data["reviewer"] or data["source_review"] is not True:
            raise BCError("Coding environment requires explicit source/image/evaluation review")
        self.base = absolute(data["base_root"])
        if not data["base_files"] or inventory(self.base) != data["base_files"]:
            raise BCError("Pristine reviewed base tree changed or is empty")
        self.profile = SandboxProfile(**data["profile"])
        self.approval = absolute(data["approval"])
        if digest(read_json(self.approval)) != data["approval_hash"]:
            raise BCError("Sandbox approval changed since environment review")
        self.hash = digest(data)
        if expected_hash is not None and self.hash != expected_hash:
            raise BCError("Coding environment changed since manifest creation")

    def validate_task(self, task):
        if task.kind != "cooperbench" or task.id != self.data["task_id"] or task.source_hash != self.data["task_hash"]:
            raise BCError("Coding environment does not match the frozen task")
        hidden_hashes = {task.metadata["source_hashes"][name] for name in task.metadata["evaluator_only_files"]}
        if hidden_hashes & {entry["sha256"] for entry in self.data["base_files"].values()}:
            raise BCError("Worker base tree contains a hidden test/reference patch, possibly renamed")
        suites = self.data["suites"]
        if not isinstance(suites, dict) or set(suites) != set(task.required_outputs):
            raise BCError("Evaluation must explicitly cover both selected feature suites")
        for argv in suites.values():
            if not isinstance(argv, list) or not argv or any(not isinstance(x, str) or "\0" in x for x in argv):
                raise BCError("Each reviewed evaluation command must be an argv array")

    def sandbox(self):
        return ApptainerSandbox(self.profile, self.approval)


class RepositorySession:
    def __init__(self, environment: CodingEnvironment, workspace: Path, sandbox=None, cancelled=lambda: False):
        self.environment, self.workspace = environment, workspace
        self.sandbox = sandbox or environment.sandbox()
        self.cancelled = cancelled
        self.last_usage = {}

    def initialize(self):
        return copy_tree(self.environment.base, self.workspace)

    def invoke(self, operation: str, **arguments):
        started = time.monotonic()
        try:
            before = digest(inventory(self.workspace))
            result = self.sandbox.run({"operation": operation, **arguments}, self.workspace, cancelled=self.cancelled)
        except (BCError, OSError, subprocess.SubprocessError) as exc:
            raise SandboxFailure(f"Sandbox infrastructure failed: {exc}") from exc
        self.last_usage = {"wall_seconds": time.monotonic()-started, "input_tree_hash": before,
                           "limits": result.get("limits"), "cleanup": result.get("cleanup")}
        if result.get("failure") == "interrupted":
            from .episode import Interrupted
            raise Interrupted("Sandbox invocation cancelled; descendants cleaned up")
        if result.get("failure") or result["returncode"] != 0:
            raise SandboxFailure(f"Sandbox tool failed: {result.get('failure') or result['returncode']}; "
                                 f"{result.get('stderr', '')[:1000]}")
        try:
            payload = json.loads(result["stdout"])
            if isinstance(payload, dict) and isinstance(payload.get("tool_error"), str):
                raise ToolRejected("Tool rejected; changes discarded: " + payload["tool_error"][:1000])
            strict_keys(payload, {"observation", "changes"}, {"observation", "changes"})
            apply_changes(self.workspace, payload["changes"])
        except (ValueError, KeyError, TypeError, OSError, BCError) as exc:
            if isinstance(exc, ToolRejected):
                raise
            raise SandboxFailure(f"Invalid sandbox output: {exc}") from exc
        self.last_usage["output_tree_hash"] = digest(inventory(self.workspace))
        return payload["observation"]
