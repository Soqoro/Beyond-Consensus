"""Public observations only. This module has no attacker/evaluator dependency."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..schemas import Alarm, ArtifactVersion, RecoveryUnit, TaskInstance
from ..tasks.workflow import expected, interpret
from ..util import BCError


@dataclass(frozen=True)
class Audit:
    selected: dict[str, str]
    alarm: Alarm


def audit(task: TaskInstance, units: tuple[RecoveryUnit, ...],
          candidates: dict[str, list[ArtifactVersion]]) -> Audit:
    selected, bad, suspects, reasons = {}, [], set(), []
    for unit in units:
        passing = []
        for artifact in candidates.get(unit.id, []):
            if not artifact.valid or artifact.kind != "implementation":
                continue
            try:
                ok = True
                for x in task.public_cases:
                    reference = expected(task, x)
                    input_name = task.sources[unit.id]["input"]
                    value = x if input_name == "x" else reference[input_name]
                    ok &= math.isclose(interpret(artifact.content, value), reference[unit.id], abs_tol=1e-8)
                if ok:
                    passing.append(artifact.id)
                else:
                    suspects.add(artifact.author)
            except (BCError, ValueError, TypeError):
                suspects.add(artifact.author)
        if passing:
            selected[unit.id] = passing[0]
        else:
            bad.append(unit.id)
            suspects.add(unit.owner)
            reasons.append(f"{unit.id}: no valid candidate passes public cases")
    return Audit(selected, Alarm(tuple(bad), tuple(sorted(suspects)), tuple(reasons)))
