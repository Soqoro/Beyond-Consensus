"""Explicit serializable research records. Truth is deliberately absent from Alarm."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .util import BCError, digest, positive

PolicyName = Literal["single", "ordinary", "jit", "replication", "recovery"]
Protocol = Literal["A", "B"]
WORKERS = ("w0", "w1", "w2", "w3")


@dataclass(frozen=True)
class WorkerIdentity:
    id: str
    backbone: str = "shared-frozen"

    def __post_init__(self) -> None:
        if self.id not in WORKERS:
            raise BCError(f"Unknown worker identity {self.id}")


@dataclass(frozen=True)
class TaskInstance:
    id: str
    kind: Literal["workflow_fixture", "cooperbench"]
    group: str
    specification: str
    sources: dict[str, Any]
    required_outputs: tuple[str, ...]
    public_cases: tuple[float, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.group or not self.required_outputs:
            raise BCError("Task needs an ID, split group, and required outputs")
        if len(set(self.required_outputs)) != len(self.required_outputs):
            raise BCError("Duplicate task outputs")
        if self.kind not in ("workflow_fixture", "cooperbench"):
            raise BCError("Unknown task adapter")

    @property
    def source_hash(self) -> str:
        return digest(self)


@dataclass
class ArtifactVersion:
    id: str
    unit: str
    author: str
    content: Any
    parents: tuple[str, ...]
    contributors: tuple[str, ...]
    source_hashes: tuple[str, ...]
    kind: str = "implementation"
    valid: bool = True
    complete_provenance: bool = True


@dataclass(frozen=True)
class RecoveryUnit:
    id: str
    required_functionality: str
    owner: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    boundary: str

    def __post_init__(self) -> None:
        if self.owner not in WORKERS or not self.outputs or not self.boundary:
            raise BCError("Invalid recovery-unit owner, outputs, or replaceable boundary")


@dataclass
class RecoveryRoute:
    id: str
    prerequisites: tuple[str, ...]
    produces: tuple[str, ...]
    executor: str
    preparation: tuple[str, ...]
    contributors: tuple[str, ...]
    predicted_cost: float
    operation: str = "cold"
    measured_outcome: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        positive(self.predicted_cost, "route cost", allow_zero=True)
        if self.executor not in WORKERS or not self.produces:
            raise BCError("A route needs an eligible identity and produced units")


@dataclass(frozen=True)
class PreparationItem:
    id: str
    unit: str
    author: str
    artifact_version: str
    operation: str
    measured_cost: float


@dataclass
class DelegationPlan:
    id: str
    units: tuple[RecoveryUnit, ...]
    preparation: tuple[tuple[str, str], ...] = ()
    replicas: tuple[tuple[str, str], ...] = ()
    reserve: float = 0
    allocation_status: str = "uncalibrated"
    predicted_cost: float | None = None
    search_states: int = 0


@dataclass(frozen=True)
class Alarm:
    units: tuple[str, ...]
    suspicious_authors: tuple[str, ...]
    reasons: tuple[str, ...]
    diagnostic_oracle: bool = False


@dataclass(frozen=True)
class AttackSpec:
    family: Literal["clean", "withholding", "artifact_sabotage"] = "clean"
    coalition_size: int = 1
    timeout_seconds: float = 1.0
    selection_seed: int = 0

    def __post_init__(self) -> None:
        if self.family not in ("clean", "withholding", "artifact_sabotage"):
            raise BCError("Unsupported attack family")
        if self.coalition_size != 1:
            raise BCError("E1 implements one fixed compromised identity")
        positive(self.timeout_seconds, "withholding timeout")


@dataclass(frozen=True)
class EpisodeManifest:
    episode_id: str
    experiment_id: str
    source_revision: str
    config_hash: str
    data_hash: str
    model_hash: str
    task_id: str
    group: str
    policy: PolicyName
    attack: AttackSpec
    seed: int
    evaluation_seed: int
    protocol: Protocol
    mode: str
    shard: int
    fixed_state_hash: str | None = None


@dataclass
class EpisodeResult:
    episode_id: str
    attempt_id: str
    experiment_id: str
    protocol: Protocol
    mode: str
    status: str
    success: bool | None
    task_id: str
    group: str
    policy: PolicyName
    attack: str
    seed: int
    costs: dict[str, Any]
    metrics: dict[str, Any]
    provenance: dict[str, Any]
    limitations: list[str] = field(default_factory=list)
    error: str | None = None
