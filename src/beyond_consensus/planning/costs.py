"""Development calibration with explicit compatibility and prediction errors."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import RunConfig
from ..models.base import Backend
from ..schemas import TaskInstance
from ..util import BCError, digest, positive, read_json, strict_keys


@dataclass(frozen=True)
class CostEstimates:
    cold: float
    prepare: float
    prepared: float
    status: str
    calibration_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("cold", "prepare", "prepared"):
            positive(getattr(self, name), name)


def compatibility(config: RunConfig) -> str:
    return digest({"model": config.model, "budget_rules": {
        name: getattr(config.budget, name) for name in ("input_weight", "output_weight", "tool_charge")},
        "monitor": config.monitor_id, "split": config.split_id, "task_kind": config.task_kind})


def estimates(config: RunConfig, backend: Backend, task: TaskInstance) -> CostEstimates:
    if config.calibration_file:
        data = read_json(config.calibration_file)
        strict_keys(data, {"id", "compatibility", "groups", "costs", "origin", "sample_count"},
                    {"id", "compatibility", "groups", "costs", "origin", "sample_count"})
        expected_origin = "mock-measured" if config.model.backend == "mock" else "development-measured"
        if data["origin"] != expected_origin or data["sample_count"] < 1:
            raise BCError("Real calibration must contain measured development operations")
        if data["compatibility"] != compatibility(config):
            raise BCError("Calibration model/budget/monitor/split mismatch; create a new run")
        if task.group in data["groups"]:
            raise BCError("Calibration and evaluation base-feature pools overlap")
        return CostEstimates(**data["costs"], status="development-calibrated", calibration_id=data["id"])
    # A disclosed allowance estimate derived from actual input counting and configured caps.
    # It is NOT a cost table asserting preparation saves work.
    prompt = backend.count_input([{"role": "user", "content": task.specification + str(task.sources)}])
    allowance = 2 * (prompt * config.budget.input_weight +
                     config.model.max_new_tokens * config.budget.output_weight + config.budget.tool_charge)
    return CostEstimates(allowance, allowance, allowance, "uncalibrated_allowance_surrogate")
