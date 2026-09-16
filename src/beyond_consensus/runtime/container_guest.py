"""Trusted container-only helper; standalone Python standard library.

Invoked with -I -S at a fixed readonly mount. Never run this module on the host.
Every invocation reconstructs its workspace in private /tmp; no writable host
directory is mounted. Candidate files and command output are untrusted data.
"""
import base64
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import shutil
import stat
import subprocess
import time

MAX_FILES = 20000
MAX_TREE = 268435456
MAX_FILE = 4194304
MAX_CHANGES = 8388608
FORBIDDEN = {".git", ".hg", ".svn", ".ssh", ".aws", ".env"}


def safe_name(name):
    p = PurePosixPath(name)
    if (not isinstance(name, str) or not name or name in (".", "..") or p.is_absolute() or str(p) != name or
            set(p.parts) & (FORBIDDEN | {"..", "."}) or "\\" in name or "\x00" in name):
        raise ValueError("Unsafe repository path")
    return p


def inventory(root):
    result, total = {}, 0
    for path in sorted(root.rglob("*")):
        name = str(path.relative_to(root))
        safe_name(name)
        st = path.lstat()
        if stat.S_ISDIR(st.st_mode):
            continue
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise ValueError("Links and special files are not accepted")
        total += st.st_size
        if st.st_size > MAX_FILE or total > MAX_TREE or len(result) >= MAX_FILES:
            raise ValueError("Repository size bound exceeded")
        result[name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "executable": bool(st.st_mode & 0o111)}
    return result


def probe(request):
    def readonly(path):
        try:
            Path(path).write_text("must not write")
        except OSError:
            return True
        return False
    status = Path("/proc/self/status").read_text()
    caps = [line.split()[1] for line in status.splitlines() if line.startswith(("CapEff:", "CapPrm:", "CapBnd:"))]
    routes = Path("/proc/net/route").read_text().splitlines()[1:]
    interfaces = os.listdir("/sys/class/net")
    mounts = Path("/proc/self/mountinfo").read_text().splitlines()
    tmp_mounts = [line.split(" - ", 1)[1].split()[0] for line in mounts if line.split()[4] == "/tmp"]
    env = os.environ
    checks = {
        "private_network": os.readlink("/proc/self/ns/net") != request["host_net"] and
                           not routes and set(interfaces) <= {"lo"},
        "private_pid": os.readlink("/proc/self/ns/pid") != request["host_pid"],
        "host_paths_hidden": all(not Path(p).exists() for p in request["outside"]),
        "evaluator_hidden": not Path("/bc/evaluator").exists(),
        "environment_clean": not any(k.startswith(("SLURM_", "HF_", "AWS_", "SSH_")) or
                                      k in ("CUDA_VISIBLE_DEVICES", "PYTHONPATH") for k in env),
        "no_scheduler": all(shutil.which(k) is None for k in ("sbatch", "srun", "salloc", "scancel")),
        "no_privileged_sockets": all(not Path(p).exists() for p in (
            "/var/run/docker.sock", "/run/docker.sock", "/run/containerd/containerd.sock",
            "/run/dbus/system_bus_socket", "/run/munge/munge.socket.2")),
        "no_capabilities": len(caps) == 3 and all(int(c, 16) == 0 for c in caps),
        "readonly_input": readonly("/bc/input/marker") and readonly("/bc/request.json"),
        "private_tmpfs": tmp_mounts == ["tmpfs"],
        "readonly_cgroup": bool(os.statvfs("/sys/fs/cgroup").f_flag & os.ST_RDONLY),
        "no_new_privileges": "NoNewPrivs:\t1" in status,
    }
    Path("/tmp/bc-write").write_text("ok")
    checks["work_write"] = Path("/tmp/bc-write").read_text() == "ok"
    return checks


def bounded_command(argv, timeout, output_limit):
    if not isinstance(argv, list) or not argv or any(not isinstance(s, str) or "\x00" in s for s in argv):
        raise ValueError("Command must be an argv array")
    # Cgroup memory bounds capture even for a process that floods output; the host
    # independently bounds the wire output and kills the whole invocation cgroup.
    try:
        result = subprocess.run(argv, cwd="/tmp/work", env={"PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": "/tmp/home", "LANG": "C.UTF-8", "TMPDIR": "/tmp"},
            capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timeout": True, "stdout": "", "stderr": "command deadline exceeded"}
    return {"returncode": result.returncode,
            "stdout": result.stdout[:output_limit].decode("utf-8", "replace"),
            "stderr": result.stderr[:output_limit].decode("utf-8", "replace"),
            "output_truncated": len(result.stdout) > output_limit or len(result.stderr) > output_limit}


def main():
    if not Path("/bc/request.json").is_file() or not Path("/bc/input").is_dir():
        raise RuntimeError("Container-only helper requires its fixed mounts")
    # Set no-new-privileges before any candidate process, without optional imports.
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
        raise OSError("Cannot set no_new_privs")
    if ctypes.CDLL(None, use_errno=True).prctl(4, 0, 0, 0, 0) != 0:
        raise OSError("Cannot protect supervisor process inspection")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_TREE, MAX_TREE))
    request = json.loads(Path("/bc/request.json").read_text())
    operation = request["operation"]
    if operation == "probe":
        print(json.dumps(probe(request)))
        return
    if operation == "probe_evaluator":
        print(json.dumps({"evaluator_visible": Path("/bc/evaluator/marker").read_text() == "evaluator-only probe canary"}))
        return
    if operation == "linger":
        if os.fork() == 0:
            os.setsid()
            print("child-ready", flush=True)
            time.sleep(600)
            os._exit(0)
        time.sleep(600)
        return
    if operation not in ("list", "read", "write", "delete", "command", "evaluate", "submit"):
        raise ValueError("Unknown coding operation")
    before = inventory(Path("/bc/input"))
    shutil.copytree("/bc/input", "/tmp/work")
    Path("/tmp/home").mkdir()
    root = Path("/tmp/work")
    observation = {}
    if operation == "list":
        names = list(before)
        offset = request.get("offset", 0)
        if type(offset) is not int or offset < 0:
            raise ValueError("Invalid list offset")
        observation = {"files": names[offset:offset+100], "total": len(names), "offset": offset}
    elif operation == "read":
        name = str(safe_name(request["path"]))
        if name not in before:
            raise ValueError("No such regular file")
        offset = request.get("offset", 0)
        if type(offset) is not int or offset < 0:
            raise ValueError("Invalid read offset")
        data = (root / name).read_text()
        observation = {"path": name, "text": data[offset:offset+4000], "total_chars": len(data), "offset": offset}
    elif operation in ("write", "delete"):
        path = root / safe_name(request["path"])
        if operation == "write":
            text = request["text"]
            if not isinstance(text, str) or len(text.encode()) > MAX_FILE:
                raise ValueError("File exceeds text limit")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        else:
            path.unlink()
        observation = {"operation": operation, "path": request["path"]}
    elif operation == "command":
        observation = bounded_command(request["argv"], request["seconds"], 4000)
    elif operation == "evaluate":
        # Only evaluator mounts contain these patches. Apply tests, never feature
        # reference patches; execute the reviewed joint command once after both.
        for name in request.get("reference_patches", []) + request["patches"]:
            patch = Path("/bc/evaluator") / safe_name(name)
            applied = bounded_command(["git", "-c", "core.hooksPath=/dev/null", "apply",
                                       "--no-index", "--", str(patch)], request["seconds"], 4000)
            if applied["returncode"] != 0:
                print(json.dumps({"evaluation_error": "test_patch_application_failed", "detail": applied}))
                return
        suites = {feature: bounded_command(argv, request["seconds"], 4000)
                  for feature, argv in request["suites"].items()}
        print(json.dumps({"evaluation": suites}))
        return
    elif operation == "submit":
        observation = {"submitted": True}
    after = inventory(root)
    changes, changed_bytes = {}, 0
    for name in before.keys() | after.keys():
        if before.get(name) == after.get(name):
            continue
        if name not in after:
            changes[name] = None
        else:
            raw = (root / name).read_bytes()
            changed_bytes += len(raw)
            if changed_bytes > MAX_CHANGES:
                raise ValueError("Changes exceed transport limit")
            changes[name] = {"data": base64.b64encode(raw).decode("ascii"), "executable": after[name]["executable"]}
    print(json.dumps({"observation": observation, "changes": changes}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        # A rejected action is a bounded worker observation. Bootstrap/kernel
        # failures still exit nonzero and are classified as infrastructure errors.
        print(json.dumps({"tool_error": str(exc)[:1000], "changes_discarded": True}))
