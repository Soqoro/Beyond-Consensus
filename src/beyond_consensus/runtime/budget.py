"""Reserve before generation; reconcile actual usage, preserving uncertain work."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..config import BudgetConfig
from ..util import BCError, positive


class BudgetExceeded(BCError):
    pass


@dataclass
class BudgetLedger:
    cap: float
    rules: BudgetConfig = field(default_factory=BudgetConfig)
    entries: list[dict[str, Any]] = field(default_factory=list)
    reservations: dict[str, dict[str, Any]] = field(default_factory=dict)
    historical: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        positive(self.cap, "budget cap")

    @property
    def spent(self) -> float:
        return sum(e["work"] for e in self.entries)

    @property
    def remaining(self) -> float:
        return self.cap - self.spent - sum(r["work"] for r in self.reservations.values())

    def charge(self, stage: str, work: float, *, kind: str, **usage: Any) -> None:
        positive(work, "charge", allow_zero=True)
        if work > self.remaining + 1e-9:
            raise BudgetExceeded(f"{stage}/{kind} needs {work:g}; remaining {self.remaining:g}")
        self.entries.append({"stage": stage, "kind": kind, "work": work, **usage})

    def reserve_call(self, stage: str, input_tokens: int, max_output: int, floor: float = 0,
                     generation_seed: int | None = None) -> str:
        work = input_tokens * self.rules.input_weight + max_output * self.rules.output_weight
        if input_tokens < 0 or max_output < 1 or self.remaining - work < floor:
            raise BudgetExceeded(f"Cannot reserve model call ({work:g}) plus reserve ({floor:g}); remaining {self.remaining:g}")
        key = f"call-{len(self.entries)}-{len(self.reservations)}"
        self.reservations[key] = {"stage": stage, "work": work, "input_tokens": input_tokens,
                                  "max_output": max_output, "generation_seed": generation_seed}
        return key

    def reserve_work(self, stage: str, work: float, kind: str) -> str:
        positive(work, "operation allowance")
        if work > self.remaining:
            raise BudgetExceeded("Cannot reserve task-specific operation allowance")
        key = f"operation-{len(self.entries)}-{len(self.reservations)}"
        self.reservations[key] = {"stage": stage, "work": work, "kind": kind}
        return key

    def reconcile_work(self, key: str, measured: float | None) -> None:
        item = self.reservations[key]
        if measured is not None and not 0 <= measured <= item["work"]:
            raise BCError("Operation exceeded reserved allowance")
        self.reservations.pop(key)
        self.charge(item["stage"], item["work"] if measured is None else measured,
                    kind=item["kind"], uncertain=measured is None)

    def reconcile(self, key: str, *, output_tokens: int | None, reasoning_tokens: int | None = 0,
                  device_seconds: float | None = None, failed: bool = False) -> None:
        r = self.reservations[key]
        if output_tokens is not None and not 0 <= output_tokens <= r["max_output"]:
            raise BCError("Backend exceeded its reserved generation cap")
        if reasoning_tokens is not None and output_tokens is not None and not 0 <= reasoning_tokens <= output_tokens:
            raise BCError("Reasoning tokens must be a subset of generated tokens")
        self.reservations.pop(key)
        work = r["work"] if output_tokens is None else (
            r["input_tokens"] * self.rules.input_weight + output_tokens * self.rules.output_weight)
        self.charge(r["stage"], work, kind="model", input_tokens=r["input_tokens"],
                    output_tokens=output_tokens, reasoning_tokens=reasoning_tokens,
                    model_calls=1, device_seconds=device_seconds, failed=failed,
                    uncertain=output_tokens is None,
                    generation_seed=r.get("generation_seed"),
                    reserved_output_tokens=r["max_output"])

    def uncertain_inflight(self) -> None:
        for key in list(self.reservations):
            if "max_output" in self.reservations[key]:
                self.reconcile(key, output_tokens=None, reasoning_tokens=None, failed=True)
            else:
                self.reconcile_work(key, None)

    def start_repair_diagnostic(self, allowance: float) -> None:
        if self.reservations:
            raise BCError("Protocol B boundary cannot contain in-flight calls")
        self.historical.extend(self.entries)
        self.entries = []
        self.cap = allowance

    def summary(self) -> dict[str, Any]:
        stages: dict[str, float] = {}
        for entry in self.entries:
            stages[entry["stage"]] = stages.get(entry["stage"], 0) + entry["work"]
        return {"cap": self.cap, "spent": self.spent, "remaining": self.remaining,
                "stages": stages, "historical_work": sum(e["work"] for e in self.historical),
                "work_unit": "token_tool_surrogate_v1", "entries": self.entries,
                "historical_entries": self.historical,
                "uncertain_work": any(e.get("uncertain", False) for e in self.entries)}
