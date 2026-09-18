"""Syntax-check documented Bash blocks and embedded scripts without executing them."""
from pathlib import Path
import re
import shutil
import subprocess
import sys


def check(paths):
    if not shutil.which("bash"):
        raise SystemExit("Bash is required to validate documentation/generated-script syntax")
    blocks = scripts = 0
    for path in paths:
        for index, body in enumerate(re.findall(r"^```(?:bash|sh)\n(.*?)^```", path.read_text(), re.M | re.S), 1):
            # Quoted here-documents are not parsed as scripts by the outer bash -n.
            subprocess.run(["bash", "-n"], input=body, text=True, check=True, capture_output=True)
            blocks += 1
            for match in re.finditer(r"<<['\"]?(\w+)['\"]?\n(.*?)^\1\s*$", body, re.M | re.S):
                script = match.group(2)
                if script.startswith("#!") and "bash" in script.splitlines()[0]:
                    subprocess.run(["bash", "-n"], input=script, text=True, check=True, capture_output=True)
                    scripts += 1
            if re.search(r'"\\\$BC_|\\#!/|BC\\_', body):
                raise ValueError(f"Possible pasted Markdown escaping in {path.name} block {index}")
    return blocks, scripts


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    paths = [Path(p) for p in sys.argv[1:]] or [root/"docs/RESEARCH_GATE.md", root/"docs/VALIDATION_CYCLE.md"]
    blocks, scripts = check(paths)
    print(f"Validated {blocks} documentation shell blocks and {scripts} embedded Bash scripts; no commands executed")
