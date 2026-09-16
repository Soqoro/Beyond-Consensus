"""Capability discovery does not authorize untrusted host execution."""

from __future__ import annotations

import shutil
from typing import Any

from ..util import BCError

BLOCKER = ("No approved repository sandbox configuration is active. CooperBench execution is blocked. "
           "The site must provide and validate isolation that denies network, home/credentials, "
           "Slurm commands and privileged sockets; restricts mounts/resources; separates worker "
           "and evaluator mounts; and removes hidden tests/reference patches including Git history. "
           "Docker/Apptainer command availability alone does not meet this contract. "
           "Use workflow_fixture for labelled engineering checks only.")


def capabilities() -> dict[str, Any]:
    return {"supported": ["typed_workflow_interpreter"], "repository_execution": False,
            "optional_repository_adapter": "apptainer-cgroup-v1 (explicit qualification and approval required)",
            "detected_commands": {name: bool(shutil.which(name)) for name in ("docker", "apptainer", "bwrap")},
            "reason": BLOCKER}


def require_repository_sandbox(config=None, *, submission=False, tasks=()) -> None:
    if config is None or not config.coding_environment:
        raise BCError(BLOCKER)
    from .coding_episode import require_coding_e0, validate_coding_task
    environment = require_coding_e0(config)
    for task in tasks:
        validate_coding_task(config, environment, task)
    if submission:
        # Login validation checks the immutable environment and approval shape.
        # The actual compute node must independently match an approved report.
        from ..util import read_json
        from .apptainer import CHECKS, SCHEMA
        approval = read_json(environment.approval)
        if (approval.get("schema") != SCHEMA or not approval.get("reviewer") or
                approval.get("image_reviewed") is not True or not approval.get("reports") or
                any(any(r.get("checks", {}).get(k) is not True for k in CHECKS) for r in approval["reports"])):
            raise BCError("No complete reviewed sandbox qualification")
    else:
        environment.sandbox().require_approval()
