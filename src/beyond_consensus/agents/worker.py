"""Bounded JSON action loop with injected model, tools, budget, and attack boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from .prompts import WORKER_INSTRUCTIONS
from ..attacks.fixed import AttackController
from ..config import RunConfig
from ..models.base import Backend
from ..runtime.budget import BudgetExceeded, BudgetLedger
from ..runtime.provenance import ProvenanceStore
from ..schemas import ArtifactVersion, TaskInstance, WORKERS
from ..tasks.workflow import interpret, validate_program
from ..util import BCError, canonical, strict_keys


@dataclass(frozen=True)
class WorkerOutcome:
    status: str
    artifact_id: str | None
    actions: int


class UnknownSource(BCError):
    """Source lookup failed before reading any task or harness content."""


class WorkerLoop:
    def __init__(self, backend: Backend, config: RunConfig, ledger: BudgetLedger,
                 store: ProvenanceStore, attacker: AttackController,
                 boundary: Callable[[str], None] = lambda _: None, domain=None) -> None:
        self.backend, self.config, self.ledger = backend, config, ledger
        self.store, self.attacker, self.boundary = store, attacker, boundary
        self.domain = domain

    def run(self, task: TaskInstance, unit: str, identity: str, stage: str, seed: int,
            *, operation: str = "implement", allowed_artifacts: tuple[str, ...] = (),
            floor: float = 0, fresh_context: bool = True) -> WorkerOutcome:
        if task.kind != "workflow_fixture" and self.domain is None:
            raise BCError("Worker tools require the typed workflow adapter; repository execution is blocked")
        if fresh_context:
            self.store.reset(identity)
        ctx = self.store.contexts[identity]
        initial = [{"role": "system", "content": (self.domain.instructions if self.domain else WORKER_INSTRUCTIONS) + "\nTask: " + task.specification},
            {"role": "user", "content": canonical({"assignment": unit, "operation": operation,
                "permitted_sources": list(task.sources), "available_artifacts": list(allowed_artifacts),
                "first_action": {"tool": "read_source", "name": unit},
                **(self.domain.initial(identity, operation, allowed_artifacts) if self.domain else {})})}]
        if not any(message["role"] == "system" for message in ctx.messages):
            ctx.messages.insert(0, initial[0])
        ctx.messages.extend(initial[1:])
        self.store.save_context(identity)
        for version in allowed_artifacts:
            if self.ledger.remaining - self.config.budget.tool_charge < floor:
                raise BudgetExceeded("Artifact read would consume the protected repair reserve")
            self.ledger.charge(stage, self.config.budget.tool_charge, kind="context_reconstruction",
                               tool_calls=1, cpu_limit_seconds=1)
            value = self.store.read(identity, version)
            self._observe(identity, {"tool": "read_artifact", "version": version, "result": value})
        self.boundary("worker_start")
        if self.attacker.withholds(identity):
            if self.ledger.remaining - self.attacker.spec.timeout_seconds * self.config.budget.timeout_charge_per_second < floor:
                raise BudgetExceeded("Withholding deadline would consume the protected repair reserve")
            self.ledger.charge(stage, self.attacker.spec.timeout_seconds * self.config.budget.timeout_charge_per_second,
                               kind="withholding_timeout", timeout_seconds=self.attacker.spec.timeout_seconds,
                               tool_calls=1, cpu_limit_seconds=self.attacker.spec.timeout_seconds,
                               wall_seconds=0, simulated_deadline=True)
            # Runtime attack injection models a bounded expired deadline; no sleeping process.
            self.boundary("withholding_timeout")
            return WorkerOutcome("withheld", None, 0)
        malformed = 0
        for turn in range(self.config.max_actions):
            messages = self.store.contexts[identity].messages
            input_tokens = self.backend.count_input(messages)
            if input_tokens + self.config.model.max_new_tokens > self.config.model.context_limit:
                raise BCError("Context limit exceeded; history was not silently truncated")
            reservation = self.ledger.reserve_call(stage, input_tokens, self.config.model.max_new_tokens, floor,
                                                   generation_seed=seed + turn)
            self.boundary("model_inflight")
            try:
                generation = self.backend.generate(messages, self.config.model.max_new_tokens, seed + turn)
                self.ledger.reconcile(reservation, output_tokens=generation.output_tokens,
                                      reasoning_tokens=generation.reasoning_tokens,
                                      device_seconds=generation.device_seconds)
            except Exception:
                if reservation in self.ledger.reservations:
                    self.ledger.reconcile(reservation, output_tokens=None, reasoning_tokens=None, failed=True)
                self.boundary("model_failed")
                raise
            messages.append({"role": "assistant", "content": generation.text})
            self.boundary("model_complete")
            action_parsed = False
            try:
                action = json.loads(generation.text)
                action_parsed = True
                artifact = self._tool(task, unit, identity, action, stage, operation, allowed_artifacts, floor)
                self.boundary("tool_complete")
                if artifact:
                    return WorkerOutcome("submitted", artifact.id, turn + 1)
            except (ValueError, TypeError, KeyError, BCError) as exc:
                from ..runtime.data_domain import ActionFieldsError, SQL_COLUMN_HINT, SQL_KINDS, TaskUnavailable
                if isinstance(exc, (BudgetExceeded, TaskUnavailable)):
                    raise
                malformed += 1
                if self.domain and isinstance(exc, json.JSONDecodeError) and not action_parsed:
                    # Parser diagnostics describe only the worker's own text;
                    # never return the document or an unrelated tool exception.
                    observation = {
                        "error": "Invalid JSON syntax. No tool was executed. Resend one complete JSON object with matching braces and brackets.",
                        "error_code": "invalid_json",
                        "parser_error": exc.msg, "line": exc.lineno, "column": exc.colno,
                    }
                    if task.kind in SQL_KINDS:
                        observation["hint"] = ("For SQL actions, write permitted_artifact_versions before select_sql "
                                               "at the top level. Close both the query object and the action object. "
                                               + SQL_COLUMN_HINT)
                elif self.domain and isinstance(exc, ActionFieldsError):
                    observation = {
                        "error": "SQL tool arguments must be top-level action fields. permitted_artifact_versions is a sibling of select_sql, never inside it.",
                        "error_code": "invalid_action_fields",
                        "required_fields": list(exc.required_fields),
                    }
                elif self.domain and isinstance(exc, UnknownSource):
                    # Only repeat public assignment metadata. Do not echo the
                    # invalid name, raw exception, source contents or gold.
                    observation = {
                        "error": "read_source needs a permitted source ID. Copy next_action to read the current assignment's contract.",
                        "error_code": "unknown_source",
                        "permitted_sources": list(task.sources),
                        "next_action": {"tool": "read_source", "name": unit},
                    }
                else:
                    observation = {"error": str(exc) if not self.domain else "Action rejected by the restricted tool contract"}
                self._observe(identity, observation)
                if self.domain:
                    self.store.events.append({"type": "prohibited_or_malformed_action", "identity": identity,
                        "unit": unit, "stage": stage, "error_code": observation.get("error_code", "restricted_action_rejected")})
                self.boundary("malformed_action")
                if malformed > self.config.malformed_retries:
                    return WorkerOutcome("malformed", None, turn + 1)
        return WorkerOutcome("action_limit", None, self.config.max_actions)

    def _observe(self, identity: str, value: Any) -> None:
        text = canonical(value)
        if len(text) > self.config.observation_limit:
            raise BCError("Observation exceeds configured bound; no silent truncation")
        self.store.contexts[identity].messages.append({"role": "user", "content": text})

    def _tool(self, task: TaskInstance, unit: str, identity: str, action: Any,
              stage: str, operation: str, allowed_artifacts: tuple[str, ...], floor: float = 0) -> ArtifactVersion | None:
        if self.ledger.remaining - self.config.budget.tool_charge < floor:
            raise BudgetExceeded("Tool call would consume the protected repair reserve")
        self.ledger.charge(stage, self.config.budget.tool_charge, kind="tool", tool_calls=1,
                           cpu_limit_seconds=1, interpreter_max_steps=16)
        if not isinstance(action, dict):
            raise BCError("Action must be a JSON object")
        tool = action.get("tool")
        if self.domain and tool not in ("read_source", "message", "submit"):
            return self.domain.handle(self, unit, identity, action, stage, operation, allowed_artifacts, floor)
        if tool == "read_source":
            strict_keys(action, {"tool", "name"}, {"tool", "name"})
            name = action["name"]
            if not isinstance(name, str) or name not in task.sources:
                raise UnknownSource("Unknown source name; use a permitted source ID")
            result = task.sources[name]
            self.store.source(identity, name, result)
            observation = {**action, "result": result}
            if self.domain:
                observation.update(self.domain.contract_context(unit, name))
            self._observe(identity, observation)
        elif tool == "read_artifact":
            strict_keys(action, {"tool", "version"}, {"tool", "version"})
            if action["version"] not in allowed_artifacts:
                raise BCError("Artifact is outside this context's logged access set")
            self._observe(identity, {**action, "result": self.store.read(identity, action["version"])})
        elif tool == "message":
            strict_keys(action, {"tool", "recipient", "text"}, {"tool", "recipient", "text"})
            if action["recipient"] not in WORKERS or not isinstance(action["text"], str):
                raise BCError("Invalid message")
            if len(action["text"]) > 2000:
                raise BCError("Message exceeds bound")
            # Messages are mediated, but independent replica/preparation contexts cannot communicate.
            if operation in ("replicate", "prepare"):
                raise BCError("Independent contexts cannot exchange contributor messages")
            self.store.message(identity, action["recipient"], action["text"])
            self._observe(identity, {"message_sent": action["recipient"]})
        elif tool == "test":
            strict_keys(action, {"tool", "program", "value"}, {"tool", "program", "value"})
            if type(action["value"]) not in (int, float):
                raise BCError("Test input must be numeric")
            self._observe(identity, {"tool": "test", "result": interpret(action["program"], action["value"])})
        elif tool == "submit":
            strict_keys(action, {"tool", "content"}, {"tool", "content"})
            content = action["content"]
            if operation == "prepare":
                strict_keys(content, {"outline", "contract"}, {"outline", "contract"})
                if not isinstance(content["outline"], str) or len(canonical(content)) > 8192:
                    raise BCError("Preparation must be a bounded outline/contract object")
            else:
                if self.domain:
                    raise BCError("Use the domain-specific required-artifact submission tool")
                validate_program(content)
            content = self.attacker.artifact(identity, content, operation)
            return self.store.submit(identity, unit, content,
                                     "preparation" if operation == "prepare" else "implementation")
        else:
            raise BCError("Unknown tool; host commands and Python code are never executed")
        return None
