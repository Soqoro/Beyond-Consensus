"""Capability discovery does not authorize untrusted host execution."""

from __future__ import annotations

import shutil
from typing import Any

from ..util import BCError

BLOCKER = ("No approved repository sandbox adapter is installed. CooperBench execution is blocked. "
           "The site must provide and validate isolation that denies network, home/credentials, "
           "Slurm commands and privileged sockets; restricts mounts/resources; separates worker "
           "and evaluator mounts; and removes hidden tests/reference patches including Git history. "
           "Docker/Apptainer command availability alone does not meet this contract. "
           "Use workflow_fixture for labelled engineering checks only.")


def capabilities() -> dict[str, Any]:
    return {"supported": ["typed_workflow_interpreter"], "repository_execution": False,
            "detected_commands": {name: bool(shutil.which(name)) for name in ("docker", "apptainer", "bwrap")},
            "reason": BLOCKER}


def require_repository_sandbox() -> None:
    raise BCError(BLOCKER)
