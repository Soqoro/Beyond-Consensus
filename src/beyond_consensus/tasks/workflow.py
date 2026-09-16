"""A bounded numeric workflow language, not a Python execution sandbox."""

from __future__ import annotations

import math
from typing import Any

from ..schemas import TaskInstance
from ..util import BCError, canonical, strict_keys

MAX_STEPS = 16
MAX_VALUE = 1e12


def validate_program(program: Any) -> dict[str, Any]:
    if not isinstance(program, dict) or len(canonical(program)) > 8192:
        raise BCError("Workflow must be a small JSON object")
    strict_keys(program, {"steps"}, {"steps"})
    if not isinstance(program["steps"], list) or not 1 <= len(program["steps"]) <= MAX_STEPS:
        raise BCError("Workflow needs 1..16 steps")
    for step in program["steps"]:
        strict_keys(step, {"op", "value"}, {"op", "value"})
        if step["op"] not in ("add", "mul", "min", "max"):
            raise BCError("Operation is not allowlisted")
        value = step["value"]
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 10000:
            raise BCError("Operand must be finite numeric with magnitude <=10000")
    return program


def interpret(program: Any, value: float) -> float:
    validate_program(program)
    if not math.isfinite(value) or abs(value) > MAX_VALUE:
        raise BCError("Input outside interpreter limits")
    for step in program["steps"]:
        op, operand = step["op"], step["value"]
        if op == "add":
            value += operand
        elif op == "mul":
            value *= operand
        elif op == "min":
            value = min(value, operand)
        elif op == "max":
            value = max(value, operand)
        if not math.isfinite(value) or abs(value) > MAX_VALUE:
            raise BCError("Workflow exceeded numeric resource limit")
    return value


def fixtures(count: int = 1) -> list[TaskInstance]:
    if not 1 <= count <= 20:
        raise BCError("Fixture count must be 1..20")
    tasks = []
    for n in range(count):
        sources = {}
        for i in range(4):
            sources[f"u{i}"] = {"scale": 1 + (n+i) % 3, "offset": (n*3+i) % 7 - 3,
                                 "lower_bound": -10 + i,
                                 "input": "u0" if i > 1 and n % 2 else "x"}
        tasks.append(TaskInstance(
            f"fixture-{n:02d}", "workflow_fixture", f"fixture-pool-{n//2:02d}",
            "Implement all four numeric outputs. For each unit multiply its input by scale, "
            "add offset, then clamp from below at lower_bound. A named input is another unit's output. "
            "Use mul for scaling, add for offset, and max for a lower bound. "
            "Submit each assigned unit's program through the submit action. All sources are permitted.",
            sources, tuple(sources), (0.0, 1.0), {"fixture_version": "numeric-v1",
                                                "instruction_version": "json-actions-v2", "synthetic": True}))
    return tasks


def dependencies(task: TaskInstance, unit: str) -> tuple[str, ...]:
    input_name = task.sources[unit]["input"]
    return () if input_name == "x" else (input_name,)


def ordered_units(task: TaskInstance) -> tuple[str, ...]:
    pending, done = list(task.required_outputs), []
    while pending:
        eligible = [u for u in pending if set(dependencies(task, u)) <= set(done)]
        if not eligible:
            raise BCError("Task dependencies are cyclic or missing")
        for u in eligible:
            done.append(u)
            pending.remove(u)
    return tuple(done)


def expected(task: TaskInstance, x: float) -> dict[str, float]:
    values: dict[str, float] = {}
    for unit in ordered_units(task):
        src = task.sources[unit]
        value = x if src["input"] == "x" else values[src["input"]]
        values[unit] = max(value * src["scale"] + src["offset"], src["lower_bound"])
    return values


def run_outputs(task: TaskInstance, programs: dict[str, Any], x: float) -> dict[str, float]:
    values: dict[str, float] = {}
    for unit in ordered_units(task):
        if unit not in programs:
            raise BCError(f"Missing required output {unit}")
        src = task.sources[unit]
        value = x if src["input"] == "x" else values[src["input"]]
        values[unit] = interpret(programs[unit], value)
    return values
