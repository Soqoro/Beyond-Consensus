"""Portable source entrypoint; also the only batch import bootstrap."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
from beyond_consensus.cli import main

raise SystemExit(main())
