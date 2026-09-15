"""Slurm command construction and one shared per-user GPU campaign guard."""

from __future__ import annotations

import getpass
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..util import BCError, atomic_json, digest, directory_lock, plain, read_json, strict_keys
from .snapshot import create_snapshot, verify_snapshot, environment_inventory


@dataclass(frozen=True)
class ClusterConfig:
    partition: str
    time: str
    memory_gb: int
    python: str
    storage_root: str
    cache_root: str
    snapshot_root: str
    output_root: str
    modules: tuple[str, ...] = ()
    activation_script: str | None = None
    account: str | None = None
    qos: str | None = None
    constraint: str | None = None

    def __post_init__(self) -> None:
        for name in ("partition", "account", "qos", "constraint"):
            value = getattr(self, name)
            if name == "partition" and not value:
                raise BCError("Set an accessible partition in configs/cluster.local.json after inspecting sinfo")
            if value is not None and (not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.&|+-]+", value)):
                raise BCError(f"Invalid cluster {name}")
        if not isinstance(self.time, str) or not re.fullmatch(r"(?:\d+-)?\d{1,3}:\d{2}:\d{2}", self.time):
            raise BCError("Set an explicit site-approved time as [D-]HH:MM:SS")
        if seconds(self.time) <= 0:
            raise BCError("Set a positive bounded time; Slurm's zero/unlimited request is not allowed")
        if type(self.memory_gb) is not int or self.memory_gb < 1:
            raise BCError("Set positive memory_gb (host RAM, not GPU VRAM)")
        for name in ("python", "storage_root", "cache_root", "snapshot_root", "output_root"):
            value = getattr(self, name)
            if not isinstance(value, str) or not Path(value).is_absolute() or "\n" in value or "\x00" in value:
                raise BCError(f"Set an absolute user-writable {name} in the local cluster configuration")
        if self.activation_script is not None and not Path(self.activation_script).is_absolute():
            raise BCError("activation_script must be an absolute trusted environment activation file")
        for module in self.modules:
            if not re.fullmatch(r"[A-Za-z0-9_./+-]+", module):
                raise BCError("Invalid module name")


def load_cluster(path: Path) -> ClusterConfig:
    data = read_json(path)
    strict_keys(data, set(ClusterConfig.__dataclass_fields__),
                {"partition", "time", "memory_gb", "python", "storage_root", "cache_root", "snapshot_root", "output_root"})
    data["modules"] = tuple(data.get("modules", []))
    return ClusterConfig(**data)


def command(argv: list[str]) -> str:
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BCError(f"Cannot inspect/run {argv[0]}: {type(exc).__name__}; use the cluster online terminal") from exc
    if result.returncode:
        raise BCError(f"{argv[0]} exited {result.returncode}: {result.stderr.strip()[:1000]}")
    return result.stdout.strip()


def registry_root() -> Path:
    # Shared across all repositories, profiles, preflights, and campaigns for this user.
    # Intentionally not configurable per submission (which would defeat the guard).
    return Path.home() / ".local" / "state" / "beyond-consensus"


def active_gpu_jobs() -> dict[str, int]:
    identifiers = command(["squeue", "--noheader", "--user", getpass.getuser(), "--format=%i"]).splitlines()
    jobs = {}
    for identifier in identifiers:
        if not re.fullmatch(r"[0-9_\[\],%\-]+", identifier):
            raise BCError("Unrecognized squeue job ID; cannot establish global GPU usage")
        details = command(["scontrol", "show", "job", "--oneliner", identifier])
        records = re.split(r"(?=JobId=)", details)
        parsed = False
        for record in records:
            if not record.startswith("JobId="):
                continue
            job = re.search(r"JobId=(\S+)", record).group(1)
            req = re.search(r"\bReqTRES=(\S+)", record)
            if req is None or req.group(1) in ("(null)", "N/A"):
                raise BCError(f"Unknown GPU accounting for job {job}; ask site support to expose ReqTRES")
            tres = dict(x.split("=", 1) for x in req.group(1).split(",") if "=" in x)
            gpu_values = [v for k, v in tres.items() if k == "gres/gpu" or k.startswith("gres/gpu:")]
            if any(not v.isdecimal() for v in gpu_values):
                raise BCError(f"Unknown GPU count for job {job}")
            typed = sum(int(v) for k, v in tres.items() if k.startswith("gres/gpu:"))
            count = max(int(tres.get("gres/gpu", "0")), typed)
            if "gpu" in record.lower() and not gpu_values:
                raise BCError(f"GPU request outside understood TRES accounting for job {job}")
            if count:
                jobs[job] = count
            parsed = True
        if not parsed:
            raise BCError(f"No parseable accounting for active/pending job {identifier}")
    return jobs


def terminal_accounting(job: str) -> bool:
    output = command(["sacct", "--noheader", "--parsable2", "--jobs", job,
                      "--format=JobIDRaw,State"])
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL",
                "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED"}
    lines = [line.split("|") for line in output.splitlines() if line and "." not in line.split("|")[0]]
    return bool(lines) and all(len(parts) >= 2 and parts[1].split()[0].rstrip("+") in terminal for parts in lines)


def guard(registry: dict[str, Any], *, serialize: bool = False) -> list[str]:
    if registry.get("uncertain_submission"):
        raise BCError("A prior submission has an uncertain outcome. Reconcile squeue/sacct and registry before retrying")
    active = active_gpu_jobs()
    known = {r["job_id"] for r in registry.get("jobs", [])}
    unaccounted = [job for job in active if job.split("_")[0] not in known]
    if unaccounted:
        raise BCError(f"Other/unknown GPU jobs are active or pending: {unaccounted}. Finish them before submitting this campaign")
    pending = []
    for job in known:
        if any(j.split("_")[0] == job for j in active) or not terminal_accounting(job):
            pending.append(job)
    if pending and not serialize:
        raise BCError(f"Overlapping GPU campaign rejected: {sorted(pending)}. Wait for completion or explicitly use --serialize")
    return sorted(pending)


def seconds(value: str) -> int:
    days, clock = value.split("-", 1) if "-" in value else ("0", value)
    parts = [int(v) for v in clock.split(":")]
    if len(parts) == 2:
        parts.insert(0, 0)
    if len(parts) != 3 or parts[1] >= 60 or parts[2] >= 60:
        raise BCError(f"Cannot interpret scheduler time {value}")
    return int(days)*86400 + parts[0]*3600 + parts[1]*60 + parts[2]


def validate_site(config: ClusterConfig) -> None:
    info = command(["scontrol", "show", "partition", config.partition, "--oneliner"])
    if f"PartitionName={config.partition}" not in info:
        raise BCError("Configured partition is not documented by this scheduler")
    maximum = re.search(r"\bMaxTime=(\S+)", info)
    if maximum is None or maximum.group(1) in ("N/A", "NOT_SET"):
        raise BCError("Partition time limit is unknown; obtain site information before submission")
    if maximum.group(1) != "UNLIMITED" and seconds(config.time) > seconds(maximum.group(1)):
        raise BCError("Requested time exceeds the reported partition limit")
    memory = command(["sinfo", "--noheader", "--Node", "--partition", config.partition, "--format=%m"])
    values = memory.splitlines()
    if not values or any(not v.strip().isdecimal() for v in values):
        raise BCError("Cannot determine partition host memory; inspect sinfo and local site limits")
    if config.memory_gb*1024 > max(int(v) for v in values):
        raise BCError("Requested host RAM exceeds reported node memory in this partition")


def sbatch_arguments(config: ClusterConfig, snapshot: Path, output: Path, shards: list[int],
                     concurrency: int, *, mode: str = "run", dependencies: list[str] = (),
                     retry: bool = False) -> list[str]:
    if type(concurrency) is not int or not 1 <= concurrency <= 4:
        raise BCError("Concurrency must be 1..4 total GPUs in the campaign")
    if not shards or any(type(s) is not int or s < 0 for s in shards) or len(shards) != len(set(shards)):
        raise BCError("Invalid shard set")
    if mode == "preflight" and (concurrency != 1 or shards != [0]):
        raise BCError("Preflight requests exactly one GPU")
    ordered = sorted(shards)
    array = f"0-{ordered[-1]}" if ordered == list(range(ordered[-1]+1)) else ",".join(map(str, ordered))
    argv = ["sbatch", "--parsable", f"--partition={config.partition}", "--nodes=1", "--ntasks=1",
            "--cpus-per-task=4", "--gres=gpu:1", f"--array={array}%{concurrency}",
            f"--time={config.time}", f"--mem={config.memory_gb}G", "--job-name=bc-"+mode,
            f"--output={output / 'logs' / '%A_%a.out'}", f"--error={output / 'logs' / '%A_%a.err'}",
            "--signal=B:TERM@60", "--no-requeue", f"--chdir={snapshot}"]
    for name in ("account", "qos", "constraint"):
        if getattr(config, name):
            argv.append(f"--{name}={getattr(config, name)}")
    if dependencies:
        if any(not re.fullmatch(r"\d+", job) for job in dependencies):
            raise BCError("Invalid dependency job ID")
        argv.append("--dependency=afterany:" + ":".join(dependencies))
    argv.extend([str(snapshot / "experiments" / "run_shard.sbatch"), str(snapshot), str(output), mode,
                 "retry" if retry else "resume", config.python])
    return argv


def submit(repo: Path, config: ClusterConfig, manifest: dict[str, Any], model_lock: dict[str, Any],
           concurrency: int, *, mode: str = "run", dry_run: bool = False, serialize: bool = False,
           existing_snapshot: Path | None = None, failed_shards: list[int] | None = None) -> dict[str, Any]:
    if os.environ.get("SLURM_JOB_ID"):
        raise BCError("Batch/allocation code cannot submit additional GPU jobs")
    if type(concurrency) is not int or not 1 <= concurrency <= 4:
        raise BCError("Concurrency must be 1..4 total GPUs")
    from .manifest import validate_manifest
    run_config = validate_manifest(manifest)
    if run_config.model.backend != "transformers":
        raise BCError("GPU submissions require an explicitly resolved Transformers configuration")
    if not run_config.model.revision or not run_config.model.tokenizer_revision:
        raise BCError("Stage and resolve model revisions before GPU submission")
    if model_lock.get("revision") != run_config.model.revision:
        raise BCError("Manifest and staged model differ")
    if run_config.task_kind == "cooperbench":
        from ..runtime.sandbox import require_repository_sandbox
        require_repository_sandbox()
    if mode == "preflight" and concurrency != 1:
        raise BCError("Preflight requires concurrency=1")
    shards = failed_shards if failed_shards is not None else list(range(1 if mode == "preflight" else run_config.shards))
    output = Path(config.output_root) / (manifest["experiment_id"] + ("-preflight" if mode == "preflight" else ""))
    registry_path = registry_root()
    state_path = registry_path / "registry.json"
    def prepare_and_submit() -> dict[str, Any]:
        state = read_json(state_path) if state_path.exists() else {"jobs": []}
        dependencies = guard(state, serialize=serialize)
        finished = [job for job in state.get("jobs", []) if job["job_id"] not in dependencies]
        state["completed_jobs"] = (state.get("completed_jobs", []) + finished)[-100:]
        state["jobs"] = [job for job in state.get("jobs", []) if job["job_id"] in dependencies]
        validate_site(config)
        snapshot = existing_snapshot or Path(config.snapshot_root) / "SNAPSHOT_CREATED_AT_SUBMISSION"
        if existing_snapshot:
            marker = verify_snapshot(existing_snapshot)
            if marker["manifest_hash"] != digest(manifest) or marker["cluster_hash"] != digest(config):
                raise BCError("Retry snapshot/config provenance mismatch; start a new campaign")
        if dry_run:
            argv = sbatch_arguments(config, snapshot, output, shards, concurrency, mode=mode,
                                     dependencies=dependencies, retry=failed_shards is not None)
            return {"dry_run": True, "argv": argv, "output": str(output), "submitted": False,
                    "snapshot": "requires clean committed checkout at actual submission",
                    "registry": str(state_path)}
        for path in (config.storage_root, config.cache_root, config.snapshot_root, config.output_root):
            Path(path).mkdir(parents=True, exist_ok=True)
            if not os.access(path, os.W_OK):
                raise BCError(f"Storage path is not writable: {path}")
        if not Path(config.python).is_file():
            raise BCError("Configured environment Python does not exist; complete environment setup")
        snapshot = existing_snapshot or create_snapshot(repo, Path(config.snapshot_root), manifest, plain(config), model_lock)
        (output / "logs").mkdir(parents=True, exist_ok=True)
        atomic_json(output / "manifest.json", manifest)
        argv = sbatch_arguments(config, snapshot, output, shards, concurrency, mode=mode,
                                 dependencies=dependencies, retry=failed_shards is not None)
        # Scheduler validates actual access/account/QoS/resource requests without a job.
        command([argv[0], "--test-only", *argv[1:]])
        state["uncertain_submission"] = {"manifest_hash": digest(manifest), "snapshot": str(snapshot)}
        atomic_json(state_path, state)
        response = command(argv)
        job = response.split(";", 1)[0]
        if not re.fullmatch(r"\d+", job):
            raise BCError("sbatch returned an unknown job ID; registry stays uncertain for manual reconciliation")
        state["uncertain_submission"] = None
        state["jobs"].append({"job_id": job, "manifest_hash": digest(manifest), "snapshot": str(snapshot),
                              "output": str(output), "concurrency": concurrency, "mode": mode})
        atomic_json(state_path, state)
        return {"job_id": job, "snapshot": str(snapshot), "output": str(output), "submitted": True}
    if dry_run:
        return prepare_and_submit()
    with directory_lock(registry_path / ".submission.lock"):
        return prepare_and_submit()


def doctor(config: ClusterConfig | None = None) -> dict[str, Any]:
    found = {name: bool(shutil.which(name)) for name in ("sinfo", "squeue", "sacct", "sbatch", "scontrol", "module")}
    info: dict[str, Any] = {"commands": found, "python": sys.version.split()[0],
        "registry": str(registry_root()), "modules": "Run module avail in the online terminal; it may be a shell function",
        "model_loaded": False}
    roots = [Path.cwd()] if config is None else [Path(getattr(config, name)) for name in
             ("storage_root", "cache_root", "snapshot_root", "output_root")]
    storage = []
    for root in roots:
        ancestor = root
        while not ancestor.exists() and ancestor.parent != ancestor:
            ancestor = ancestor.parent
        usage = shutil.disk_usage(ancestor)
        storage.append({"requested_root": str(root), "exists": root.exists(),
                        "writable_existing_parent": os.access(ancestor, os.W_OK), "free_bytes": usage.free})
    info["storage"] = storage
    if found["sinfo"]:
        info["partitions"] = command(["sinfo", "--noheader", "--format=%P|%G|%m|%l|%a"])
    from ..runtime.sandbox import capabilities
    info["sandbox"] = capabilities()
    return info


def failed_shard_ids(manifest: dict[str, Any], output: Path) -> list[int]:
    from .runner import RETRYABLE
    shards = set()
    for episode in manifest["episodes"]:
        path = output / "episodes" / episode["episode_id"] / "result.json"
        if not path.exists():
            shards.add(episode["shard"])
        else:
            row = read_json(path)
            if row["provenance"]["manifest_hash"] != digest(episode):
                raise BCError("Result changed provenance; cannot resubmit")
            if row["status"] in RETRYABLE:
                shards.add(episode["shard"])
    return sorted(shards)


def batch(snapshot: Path, output: Path, mode: str, retry: bool) -> int:
    snapshot_marker = verify_snapshot(snapshot)
    from ..models.transformers_backend import require_allocation
    require_allocation()
    config = load_cluster(snapshot / "resolved" / "cluster.json")
    if config.activation_script:
        from ..util import file_hash
        if file_hash(Path(config.activation_script)) != snapshot_marker["activation_hash"]:
            raise BCError("Environment activation script changed since submission")
    expected_environment = read_json(snapshot / "resolved" / "environment.json")
    if environment_inventory(config.python) != expected_environment:
        raise BCError("Environment changed since submission; do not mutate environments used by running jobs")
    manifest = snapshot / "resolved" / "manifest.json"
    model_lock = snapshot / "resolved" / "model-lock.json"
    args = [config.python, "-I", "-B", str(snapshot / "scripts" / "bc.py")]
    if mode == "preflight":
        args += ["gpu-preflight", "--manifest", str(manifest), "--model-lock", str(model_lock),
                 "--output", str(output / "preflight.json")]
    elif mode == "run":
        shard = os.environ.get("SLURM_ARRAY_TASK_ID")
        if shard is None or not shard.isdecimal():
            raise BCError("Missing Slurm array index")
        args += ["run", "--manifest", str(manifest), "--output", str(output), "--shard", shard,
                 "--model-lock", str(model_lock)]
        if retry:
            args.append("--retry-failures")
    else:
        raise BCError("Unknown batch mode")
    env = dict(os.environ)
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HOME=config.cache_root,
               PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", TOKENIZERS_PARALLELISM="false")
    env.pop("PYTHONPATH", None)
    # Environment configuration is trusted user input. Shell contents are fixed;
    # module names/paths are positional arguments, never interpolated shell code.
    shell = ('set -euo pipefail\nactivation="$1"; shift\n'
             'count="$1"; shift\nfor ((i=0;i<count;i++)); do '
             'type module >/dev/null 2>&1 || { echo "module command unavailable; configure activation" >&2; exit 2; }; '
             'module load "$1"; shift; done\n'
             'if [[ -n "$activation" ]]; then source "$activation"; fi\nexec "$@"')
    os.execvpe("bash", ["bash", "-lc", shell, "bc-environment", config.activation_script or "",
                        str(len(config.modules)), *config.modules, *args], env)
    raise AssertionError("exec returned")
