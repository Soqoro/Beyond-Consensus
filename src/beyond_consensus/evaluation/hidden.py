"""Terminal fixture evaluator. Its outputs are never sent to workers or repair."""

from __future__ import annotations

import math
import random
from typing import Any

from ..schemas import TaskInstance
from ..tasks.workflow import expected, run_outputs
from ..util import BCError


def evaluate(task: TaskInstance, programs: dict[str, Any], seed: int) -> dict[str, Any]:
    rng = random.Random(seed)
    cases = [-100.0, -1.0, 0.5, 17.0] + [rng.uniform(-50, 50) for _ in range(12)]
    outputs = {u: True for u in task.required_outputs}
    try:
        for x in cases:
            actual, reference = run_outputs(task, programs, x), expected(task, x)
            for unit in task.required_outputs:
                outputs[unit] &= math.isclose(actual[unit], reference[unit], rel_tol=1e-9, abs_tol=1e-8)
    except (BCError, KeyError, ValueError, TypeError):
        outputs = {u: False for u in task.required_outputs}
    return {"complete_task_success": all(outputs.values()), "requested_outputs": outputs}
