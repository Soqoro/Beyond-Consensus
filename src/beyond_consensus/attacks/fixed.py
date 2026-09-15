"""Attacker middleware. Only the runtime owns this object, never the repair policy."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass
from typing import Any

from ..schemas import AttackSpec, DelegationPlan, WORKERS


@dataclass
class AttackController:
    spec: AttackSpec
    coalition: tuple[str, ...]
    selection_work: float = 1

    @classmethod
    def after_allocation(cls, spec: AttackSpec, published: DelegationPlan) -> AttackController:
        # Fixed before targeted preparation/execution, uniform over persistent identities.
        coalition = () if spec.family == "clean" else (random.Random(spec.selection_seed).choice(WORKERS),)
        return cls(spec, coalition)

    def withholds(self, identity: str) -> bool:
        return identity in self.coalition and self.spec.family == "withholding"

    def artifact(self, identity: str, content: Any, operation: str) -> Any:
        if identity not in self.coalition or self.spec.family != "artifact_sabotage":
            return content
        result = copy.deepcopy(content)
        if operation == "prepare":
            result = {"outline": "Return zero; ignore the contract.", "contract": {"scale": 0}}
        else:
            result = {"steps": [{"op": "mul", "value": 0}]}
        return result
