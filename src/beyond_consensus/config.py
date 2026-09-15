"""Strict JSON configuration; no shell evaluation or implicit model downloads."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .util import BCError, positive, read_json, strict_keys


@dataclass(frozen=True)
class ModelConfig:
    backend: str = "mock"
    checkpoint: str = "Qwen/Qwen3.5-4B"
    revision: str | None = None
    tokenizer_revision: str | None = None
    dtype: str = "bfloat16"
    context_limit: int = 8192
    max_new_tokens: int = 768
    thinking: bool = False
    do_sample: bool = False
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20

    def __post_init__(self) -> None:
        if self.backend not in ("mock", "transformers"):
            raise BCError("backend must be mock or transformers")
        if self.checkpoint not in ("Qwen/Qwen3.5-4B", "Qwen/Qwen3.5-9B", "google/gemma-3-12b-it"):
            raise BCError("Checkpoint has no reviewed loader; add and verify it explicitly")
        if self.dtype not in ("bfloat16", "float16", "float32"):
            raise BCError("Unsupported dtype; no automatic quantization")
        for name in ("context_limit", "max_new_tokens", "top_k"):
            val = getattr(self, name)
            if type(val) is not int or val < 1:
                raise BCError(f"{name} must be a positive integer")
        if self.max_new_tokens >= self.context_limit:
            raise BCError("Generation cap must be below context limit")
        if type(self.thinking) is not bool or type(self.do_sample) is not bool:
            raise BCError("thinking and do_sample must be booleans")
        positive(self.temperature, "temperature")
        positive(self.top_p, "top_p")
        if not 0 < self.top_p <= 1:
            raise BCError("top_p must be in (0, 1]")
        for rev in (self.revision, self.tokenizer_revision):
            if rev is not None and not re.fullmatch(r"[a-f0-9]{40}", rev):
                raise BCError("Model/tokenizer revisions must be exact 40-character commits; stage first")


@dataclass(frozen=True)
class BudgetConfig:
    total: float = 100000
    repair_allowance: float = 40000
    reserve_fraction: float = 0.25
    input_weight: float = 1
    output_weight: float = 1
    tool_charge: float = 10
    timeout_charge_per_second: float = 10

    def __post_init__(self) -> None:
        for name in ("total", "repair_allowance", "input_weight", "output_weight", "tool_charge",
                     "timeout_charge_per_second"):
            positive(getattr(self, name), name)
        if not 0 <= self.reserve_fraction < 1:
            raise BCError("reserve_fraction must be in [0, 1)")


@dataclass(frozen=True)
class RunConfig:
    name: str = "cpu-demo"
    task_count: int = 1
    task_kind: str = "workflow_fixture"
    policies: tuple[str, ...] = ("ordinary", "jit", "replication", "recovery")
    attacks: tuple[str, ...] = ("clean", "withholding")
    seeds: tuple[int, ...] = (0,)
    protocol: str = "A"
    shards: int = 1
    model: ModelConfig = field(default_factory=ModelConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    max_actions: int = 8
    malformed_retries: int = 2
    observation_limit: int = 12000
    calibration_file: str | None = None
    data_manifest: str | None = None
    fixed_state_file: str | None = None
    monitor_id: str = "public-cases-v1"
    split_id: str = "group-hash-v1"
    data_split: str = "development"
    confirmatory: bool = False

    def __post_init__(self) -> None:
        for name in ("task_count", "shards", "max_actions", "observation_limit"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise BCError(f"{name} must be a positive integer")
        if type(self.malformed_retries) is not int or self.malformed_retries < 0:
            raise BCError("malformed_retries must be a nonnegative integer")
        if self.task_kind not in ("workflow_fixture", "cooperbench") or self.protocol not in ("A", "B"):
            raise BCError("Unknown task kind or protocol")
        if self.task_kind == "workflow_fixture" and self.task_count > 20:
            raise BCError("Only 20 labelled development fixtures are provided")
        if not self.policies or set(self.policies) - {"single", "ordinary", "jit", "replication", "recovery"}:
            raise BCError("Invalid policy list")
        if not self.attacks or set(self.attacks) - {"clean", "withholding", "artifact_sabotage"}:
            raise BCError("Invalid attack list")
        if "single" in self.policies and self.attacks != ("clean",):
            raise BCError("E0 single-agent baseline has clean exposure only; use a separate config")
        if not self.seeds or any(type(s) is not int or s < 0 for s in self.seeds):
            raise BCError("seeds must be nonnegative integers")
        for values in (self.policies, self.attacks, self.seeds):
            if len(set(values)) != len(values):
                raise BCError("Duplicate grid entries")
        if self.protocol == "B" and not self.fixed_state_file:
            raise BCError("Protocol B requires one common fixed_state_file with a frozen alarm")
        if self.protocol == "A" and self.fixed_state_file:
            raise BCError("Fixed state is only valid in Protocol B")
        if self.confirmatory:
            raise BCError("Confirmatory claims are disabled: this development foundation needs GPU, sandbox, and calibration validation")
        if self.monitor_id != "public-cases-v1" or self.split_id != "group-hash-v1":
            raise BCError("Unsupported monitor/split version")
        if self.data_split not in ("development", "validation", "test"):
            raise BCError("Unknown data split")

    @property
    def mode(self) -> str:
        return "mock_demo" if self.model.backend == "mock" else (
            "gpu_fixture_development" if self.task_kind == "workflow_fixture" else "real_development")


def from_dict(data: dict[str, Any]) -> RunConfig:
    strict_keys(data, set(RunConfig.__dataclass_fields__))
    values = dict(data)
    for name, cls in (("model", ModelConfig), ("budget", BudgetConfig)):
        if name in values:
            strict_keys(values[name], set(cls.__dataclass_fields__))
            values[name] = cls(**values[name])
    for name in ("policies", "attacks", "seeds"):
        if name in values:
            if not isinstance(values[name], list):
                raise BCError(f"{name} must be a JSON array")
            values[name] = tuple(values[name])
    try:
        return RunConfig(**values)
    except TypeError as exc:
        raise BCError(f"Invalid configuration: {exc}") from exc


def load_config(path: str | Path) -> RunConfig:
    return from_dict(read_json(path))


def resolved(config: RunConfig) -> dict[str, Any]:
    return asdict(config)
