"""Fixed offline diagnostic child; never a worker command or arbitrary code runner."""
from pathlib import Path
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from beyond_consensus.diagnostics.sqlite_failure import probe
print(json.dumps(probe(json.loads(sys.stdin.read(2097153))), allow_nan=False))
