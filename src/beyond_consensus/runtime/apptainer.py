"""Opt-in Apptainer execution with cgroup v2 limits and node-bound approval.

No host fallback, GPU bind, network, writable host bind or inherited environment.
The installation and the image must be reviewed trusted software. Qualification
executes only the project's fixed probes, never arbitrary candidate programs.
"""
from __future__ import annotations

import os
import platform
import selectors
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..util import BCError, atomic_json, digest, file_hash, read_json, strict_keys

GUEST = Path(__file__).with_name("container_guest.py")
BOOTSTRAP = Path(__file__).with_name("cgroup_exec.py")
SCHEMA = "apptainer-cgroup-v1"
CHECKS = {"private_network", "host_paths_hidden", "evaluator_hidden", "environment_clean",
          "no_scheduler", "no_privileged_sockets", "no_capabilities", "private_pid",
          "readonly_input", "work_write", "memory_limit", "pid_limit", "cpu_limit",
          "timeout_cleanup", "descendant_cleanup", "readonly_cgroup", "private_tmpfs",
          "no_new_privileges", "evaluator_separation"}


def absolute(value: str, *, check_links: bool = True) -> Path:
    if not isinstance(value, str) or not Path(value).is_absolute() or any(c in value for c in ",:\n\0"):
        raise BCError("Sandbox paths must be absolute and contain no bind separators")
    path = Path(value)
    if check_links and any(p.is_symlink() for p in (path, *path.parents)):
        raise BCError(f"Symlinked sandbox path: {path}")
    return path


def runtime_hash(root: Path) -> str:
    """Fingerprint private runtime helpers/configuration as well as its wrapper."""
    entries = {}
    for path in sorted(root.rglob("*")):
        name = str(path.relative_to(root))
        if path.is_symlink():
            if not path.resolve().is_relative_to(root.resolve()):
                raise BCError(f"Runtime link escapes private installation: {name}")
            entries[name] = {"link": os.readlink(path)}
        elif path.is_file():
            entries[name] = {"sha256": file_hash(path), "mode": path.stat().st_mode & 0o7777}
        elif not path.is_dir():
            raise BCError("Runtime installation contains a special file")
    if not entries:
        raise BCError("Empty runtime installation")
    return digest(entries)


@dataclass(frozen=True)
class SandboxProfile:
    runtime_root: str
    runtime_sha256: str
    image: str
    image_sha256: str
    scratch_root: str
    cgroup_parent: str = "current"
    python: str = "/usr/local/bin/python3"
    memory_bytes: int = 2147483648
    pids: int = 128
    cpu_quota: int = 100000
    timeout_seconds: int = 60
    output_bytes: int = 16777216

    def __post_init__(self):
        for key in ("runtime_root", "image", "scratch_root"):
            absolute(getattr(self, key))
        absolute(self.python, check_links=False)  # Container path, not a host executable.
        if self.cgroup_parent != "current":
            absolute(self.cgroup_parent)
        for key in ("runtime_sha256", "image_sha256"):
            value = getattr(self, key)
            if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
                raise BCError(f"Set a measured {key}")
        for key in ("memory_bytes", "pids", "cpu_quota", "timeout_seconds", "output_bytes"):
            if type(getattr(self, key)) is not int or getattr(self, key) < 1:
                raise BCError(f"Positive integer required: {key}")
        if self.timeout_seconds > 600 or self.output_bytes > 67108864:
            raise BCError("Sandbox timeout/output exceed development limits")

    @classmethod
    def load(cls, path: Path):
        data = read_json(path)
        strict_keys(data, set(cls.__dataclass_fields__))
        return cls(**data)

    def identity(self) -> dict[str, Any]:
        if runtime_hash(absolute(self.runtime_root)) != self.runtime_sha256:
            raise BCError("Private Apptainer runtime changed; requalify")
        if file_hash(absolute(self.image)) != self.image_sha256:
            raise BCError("Container image changed; requalify")
        return {"schema": SCHEMA, "profile_hash": digest(self), "guest_hash": file_hash(GUEST),
                "bootstrap_hash": file_hash(BOOTSTRAP), "adapter_hash": file_hash(Path(__file__)),
                "hostname": platform.node(), "kernel": platform.release(), "uid": os.getuid()}


def cgroup_parent(profile: SandboxProfile) -> Path:
    rows = Path("/proc/self/cgroup").read_text().splitlines()
    unified = [row[3:] for row in rows if row.startswith("0::")]
    if len(unified) != 1 or ".." in Path(unified[0]).parts:
        raise BCError("A visible unified cgroup v2 hierarchy is required")
    current = Path("/sys/fs/cgroup") / unified[0].lstrip("/")
    if profile.cgroup_parent == "current":
        # A populated leaf cannot distribute memory to children. Find the nearest
        # already-enabled delegated ancestor; never enable controllers or move
        # the orchestrator out of its scheduler-managed leaf ourselves.
        candidates = [p for p in (current, *current.parents) if p.is_relative_to("/sys/fs/cgroup")]
    else:
        parent = absolute(profile.cgroup_parent)
        if not parent.is_relative_to(Path("/sys/fs/cgroup")) or not current.is_relative_to(parent):
            raise BCError("Delegated cgroup parent must be an ancestor of this process under /sys/fs/cgroup")
        candidates = [parent]
    for parent in candidates:
        enabled = set((parent / "cgroup.subtree_control").read_text().split())
        if {"memory", "pids", "cpu"} <= enabled and os.access(parent, os.W_OK) and os.access(parent / "cgroup.procs", os.W_OK):
            return parent
    raise BCError("No delegated cgroup v2 parent with memory,pids,cpu enabled; "
                  "site delegation is required. Basic namespace probes do not establish this capability")


class InvocationGroup:
    def __init__(self, profile: SandboxProfile):
        self.path = cgroup_parent(profile) / ("bc-" + os.urandom(12).hex())
        self.profile = profile

    def __enter__(self):
        self.path.mkdir(mode=0o700)
        try:
            for name, value in (("memory.max", self.profile.memory_bytes), ("memory.swap.max", 0),
                                ("pids.max", self.profile.pids),
                                ("cpu.max", f"{self.profile.cpu_quota} 100000")):
                (self.path / name).write_text(str(value))
                if (self.path / name).read_text().strip() != str(value):
                    raise BCError(f"Cgroup did not retain {name}")
            if not (self.path / "cgroup.kill").exists():
                raise BCError("cgroup.kill is required for descendant cleanup")
        except BaseException:
            self.path.rmdir()
            raise
        return self

    def kill(self):
        (self.path / "cgroup.kill").write_text("1")

    def __exit__(self, *_):
        self.kill()
        deadline = time.monotonic() + 10
        while "populated 1" in (self.path / "cgroup.events").read_text():
            if time.monotonic() >= deadline:
                raise BCError("Sandbox descendants did not exit; manual cgroup cleanup required")
            time.sleep(0.05)
        self.path.rmdir()


class SandboxFailure(BCError):
    """Infrastructure failure; must never become a scientific failure/observation."""


class ApptainerSandbox:
    def __init__(self, profile: SandboxProfile, approval: Path | None = None):
        self.profile, self.approval = profile, approval

    def require_approval(self):
        if self.approval is None:
            raise BCError("A reviewed sandbox approval is required for repository execution")
        approval = read_json(self.approval)
        if approval.get("schema") != SCHEMA or not approval.get("reviewer") or approval.get("image_reviewed") is not True:
            raise BCError("Missing explicit sandbox review")
        identity = self.profile.identity()
        matches = [r for r in approval.get("reports", []) if r.get("identity") == identity]
        if not matches or not all(r.get("checks", {}).get(k) is True for k in CHECKS for r in matches):
            raise BCError("No passing qualification for this image/runtime/profile/node/kernel")
        cgroup_parent(self.profile)

    def argv(self, request: Path, input_tree: Path, evaluator: Path | None = None) -> list[str]:
        p = self.profile
        argv = [str(absolute(p.runtime_root) / "bin/apptainer"), "exec", "--userns", "--containall",
                "--cleanenv", "--no-eval", "--no-home", "--no-mount", "hostfs,bind-paths,cwd",
                "--net", "--network", "none", "--drop-caps", "ALL", "--pwd", "/tmp",
                "--bind", f"{absolute(str(input_tree))}:/bc/input:ro",
                "--bind", f"{absolute(str(request))}:/bc/request.json:ro",
                "--bind", f"{absolute(str(GUEST))}:/bc/guest.py:ro"]
        if evaluator is not None:
            argv += ["--bind", f"{absolute(str(evaluator))}:/bc/evaluator:ro"]
        return argv + [p.image, p.python, "-I", "-S", "/bc/guest.py"]

    def run(self, request: dict, input_tree: Path, evaluator: Path | None = None,
            *, qualification: bool = False, cancelled=lambda: False) -> dict:
        if qualification:
            if request.get("operation") not in ("probe", "probe_evaluator", "linger") or (
                    evaluator is not None and request.get("operation") != "probe_evaluator"):
                raise BCError("Qualification only permits fixed trusted probes")
            self.profile.identity()
        else:
            self.require_approval()
        p = self.profile
        scratch = absolute(p.scratch_root)
        scratch.mkdir(parents=True, exist_ok=True, mode=0o700)
        started = time.monotonic()
        # Cleanup completes before TemporaryDirectory removes host staging data.
        with tempfile.TemporaryDirectory(prefix="invocation-", dir=scratch) as tmp:
            root = Path(tmp)
            atomic_json(root / "request.json", request)
            for name in ("home", "cache", "tmp"):
                (root / name).mkdir()
            env = {"PATH": "/usr/bin:/bin", "HOME": str(root / "home"), "LANG": "C.UTF-8",
                   "APPTAINER_CACHEDIR": str(root / "cache"), "APPTAINER_TMPDIR": str(root / "tmp")}
            with InvocationGroup(p) as group:
                argv = [sys.executable, "-I", "-S", str(BOOTSTRAP), str(group.path / "cgroup.procs"),
                        *self.argv(root / "request.json", input_tree, evaluator)]
                proc = subprocess.Popen(argv, env=env, cwd=root, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
                chunks = {"stdout": bytearray(), "stderr": bytearray()}
                failure = None
                try:
                    with selectors.DefaultSelector() as selector:
                        for name in chunks:
                            selector.register(getattr(proc, name), selectors.EVENT_READ, name)
                        deadline = time.monotonic() + (3 if request.get("operation") == "linger" else p.timeout_seconds)
                        while selector.get_map():
                            if cancelled():
                                failure = "interrupted"
                                break
                            if time.monotonic() >= deadline:
                                failure = "timeout"
                                break
                            for key, _ in selector.select(0.1):
                                data = os.read(key.fd, 65536)
                                if not data:
                                    selector.unregister(key.fileobj)
                                else:
                                    chunks[key.data].extend(data)
                            if sum(map(len, chunks.values())) > p.output_bytes:
                                failure = "output_limit"
                                break
                        if failure is None:
                            try:
                                proc.wait(timeout=max(0.01, deadline-time.monotonic()))
                            except subprocess.TimeoutExpired:
                                failure = "timeout"
                finally:
                    group.kill()  # Includes setsid/double-fork descendants, even after successful exit.
                    proc.wait(timeout=10)
                    proc.stdout.close()
                    proc.stderr.close()
                limits = {name: (group.path / name).read_text().strip()
                          for name in ("memory.max", "pids.max", "cpu.max")}
            result = {"returncode": proc.returncode, "failure": failure,
                      **{k: bytes(v).decode("utf-8", errors="replace") for k, v in chunks.items()},
                      "wall_seconds": time.monotonic()-started, "limits": limits, "cleanup": True}
        return result


def qualify(profile: SandboxProfile, output: Path) -> dict:
    """Reports observed checks only; it never writes an approval."""
    report = {"schema": SCHEMA, "identity": profile.identity(), "checks": {}, "approved": False}
    try:
        sandbox = ApptainerSandbox(profile)
        root = absolute(profile.scratch_root)
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="qualification-", dir=root) as tmp:
            path = Path(tmp)
            (path / "input").mkdir()
            (path / "input/marker").write_text("public probe input")
            (path / "outside").write_text("private probe canary")
            result = sandbox.run({"operation": "probe", "outside": [str(path / "outside"),
                str(Path.home() / ".ssh"), str(Path.home() / ".local/state/beyond-consensus")],
                "host_net": os.readlink("/proc/self/ns/net"),
                "host_pid": os.readlink("/proc/self/ns/pid")}, path / "input", qualification=True)
            report["probe"] = result
            if result["returncode"] != 0 or result["failure"]:
                raise BCError("Container qualification command failed; inspect probe output")
            import json
            observed = json.loads(result["stdout"])
            report["checks"].update({k: observed.get(k) is True for k in CHECKS if k in observed})
            (path / "private").mkdir()
            (path / "private/marker").write_text("evaluator-only probe canary")
            # Unlike a candidate command, this invokes a fixed trusted check only.
            evaluator = sandbox.run({"operation": "probe_evaluator"}, path / "input",
                                    path / "private", qualification=True)
            report["checks"]["evaluator_separation"] = (evaluator["returncode"] == 0 and
                not evaluator["failure"] and json.loads(evaluator["stdout"]).get("evaluator_visible") is True and
                report["checks"].get("evaluator_hidden") is True)
            for check, name, expected in (("memory_limit", "memory.max", str(profile.memory_bytes)),
                                         ("pid_limit", "pids.max", str(profile.pids)),
                                         ("cpu_limit", "cpu.max", f"{profile.cpu_quota} 100000")):
                report["checks"][check] = result["limits"][name] == expected
            linger = sandbox.run({"operation": "linger"}, path / "input", qualification=True)
            report["cleanup_probe"] = linger
            report["checks"]["timeout_cleanup"] = linger["failure"] == "timeout" and linger["cleanup"]
            report["checks"]["descendant_cleanup"] = report["checks"]["timeout_cleanup"] and "child-ready" in linger["stdout"]
    except (BCError, OSError, ValueError, subprocess.SubprocessError) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    report["passed"] = all(report["checks"].get(k) is True for k in CHECKS)
    report["command_failed"] = not report["passed"]
    atomic_json(output, report)
    return report


def approve(reports: list[Path], reviewer: str, image_reviewed: bool, output: Path) -> dict:
    if not reviewer.strip() or not image_reviewed or output.exists():
        raise BCError("A new approval needs a reviewer and explicit image-content review")
    values = [read_json(path) for path in reports]
    if not values or any(r.get("schema") != SCHEMA or not r.get("passed") or
                         any(r.get("checks", {}).get(k) is not True for k in CHECKS) for r in values):
        raise BCError("All qualification reports must pass every required check")
    approval = {"schema": SCHEMA, "reviewer": reviewer, "image_reviewed": True, "reports": values}
    atomic_json(output, approval)
    return {"approval": str(output), "nodes": [r["identity"]["hostname"] for r in values]}
