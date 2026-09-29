#!/usr/bin/env python3
"""Standalone benchmark entry point; does not import beyond_consensus."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from reporecourse.v2_cli import main
if __name__=='__main__':main()
