"""Portable LF checks; use bash -n when Bash is installed (Git Bash/WSL on Windows)."""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
files = sorted([*root.glob("experiments/*.sh"), *root.glob("experiments/*.sbatch"), *root.glob("scripts/*.sh")])
for path in files:
    raw = path.read_bytes()
    if b"\r" in raw or not raw.endswith(b"\n"):
        raise SystemExit(f"Shell file needs LF endings and final newline: {path}")
    if b"set -euo pipefail" not in raw or b"--dry-run" not in raw or b"Usage:" not in raw:
        raise SystemExit(f"Missing usage, dry-run, or strict handling: {path}")
    if shutil.which("bash"):
        subprocess.run(["bash", "-n", str(path)], check=True)
print(f"Validated {len(files)} shell files: LF/usage/dry-run/strict handling" +
      (" and bash -n" if shutil.which("bash") else "; bash -n skipped: Bash is not installed"))
