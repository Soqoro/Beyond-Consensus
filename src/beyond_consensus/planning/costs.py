"""Development calibration with explicit compatibility and prediction errors."""

from __future__ import annotations

from dataclasses import dataclass

from ..agents.prompts import WORKER_INSTRUCTIONS
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


def compatibility(config: RunConfig, task: TaskInstance | None = None) -> str:
    instructions = WORKER_INSTRUCTIONS
    if config.task_kind in ("sqlite_fixture", "sqlite_native", "sqlite_pair", "silo"):
        from ..runtime.data_domain import SQL_INSTRUCTIONS, SILO_INSTRUCTIONS
        instructions = SILO_INSTRUCTIONS if config.task_kind == "silo" else SQL_INSTRUCTIONS
    data = {"model": config.model, "budget_rules": {
        name: getattr(config.budget, name) for name in ("input_weight", "output_weight", "tool_charge")},
        "monitor": config.monitor_id, "split": config.split_id, "task_kind": config.task_kind,
        "worker_instructions": instructions, "silo_interface": config.silo_interface,
        "operation_measurement": config.operation_measurement}
    if config.model.action_constraint == "sqlite-sql-text-v1":
        from ..runtime.sql_text import contract as compiler_contract
        data["sql_frontend"] = compiler_contract()
    if config.sqlite_error_feedback != "generic":
        data["sqlite_error_feedback"] = config.sqlite_error_feedback
    if config.model.backend == "transformers":
        from ..models.transformers_backend import GENERATION_POLICY
        data["generation_policy"] = GENERATION_POLICY
    if config.model.action_constraint != "none":
        from ..models.action_schema import contract
        data["action_constraint"] = contract(config.model.action_constraint)
    if config.organization != "legacy":
        data["organization_catalogue"] = "boundary-jit-v1"
    if task is not None and task.kind in ("sqlite_fixture", "sqlite_native", "sqlite_pair", "silo"):
        from ..tasks.data_manifest import regime
        data["data_regime"] = regime(task)
        data["execution_limits"] = task.metadata.get("execution_limits", task.metadata.get("harness", {}).get("limits"))
        if task.kind != "silo":
            from ..runtime.sqlite_executor import capabilities
            data["executor_runtime"] = capabilities()
    return digest(data)


def estimates(config: RunConfig, backend: Backend, task: TaskInstance) -> CostEstimates:
    if config.calibration_file:
        data = read_json(config.calibration_file)
        strict_keys(data, {"id", "compatibility", "groups", "costs", "origin", "sample_count"},
                    {"id", "compatibility", "groups", "costs", "origin", "sample_count"})
        expected_origin = "mock-measured" if config.model.backend == "mock" else "development-measured"
        if data["origin"] != expected_origin or data["sample_count"] < 1:
            raise BCError("Real calibration must contain measured development operations")
        if data["compatibility"] != compatibility(config, task):
            raise BCError("Calibration model/budget/monitor/split/prompt mismatch; create a new run")
        if task.group in data["groups"]:
            raise BCError("Calibration and evaluation base-feature pools overlap")
        return CostEstimates(**data["costs"], status="development-calibrated", calibration_id=data["id"])
    # A disclosed allowance estimate derived from actual input counting and configured caps.
    # It is NOT a cost table asserting preparation saves work.
    prompt = backend.count_input([{"role": "user", "content": task.specification + str(task.sources)}])
    allowance = 2 * (prompt * config.budget.input_weight +
                     config.model.max_new_tokens * config.budget.output_weight + config.budget.tool_charge)
    return CostEstimates(allowance, allowance, allowance, "uncalibrated_allowance_surrogate")
