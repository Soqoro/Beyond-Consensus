"""Opt-in charged operation measurements through the existing manifest runner."""
from ..schemas import EpisodeResult
from ..util import digest, plain
from .budget import BudgetExceeded
from .episode import EpisodeEngine, Interrupted


class MeasurementEngine(EpisodeEngine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measurements = []
        self.pending_measurement = None
        self.calibrating = True

    def state(self, boundary):
        return {**super().state(boundary), "measurements": self.measurements, "pending_measurement": self.pending_measurement}

    def restore(self, state):
        super().restore(state)
        self.measurements = state.get("measurements", [])
        self.pending_measurement = state.get("pending_measurement")

    def run(self):
        previous = self.journal.previous(digest(self.manifest))
        if previous:
            self.restore(previous)
        status, error = "completed", None
        try:
            if self.plan is None:
                self.plan_primary()
            for unit in self.task.required_outputs:
                for label, operation, identity, prep in (
                        ("cold", "implement", "w0", None), ("index", "prepare", "w1", None),
                        ("after_index", "implement", "w2", "index"), ("outline", "prepare", "w1", None),
                        ("after_outline", "implement", "w2", "outline"), ("replication", "replicate", "w3", None)):
                    key = f"measure:{unit}:{label}"
                    if key in self.completed:
                        continue
                    prior = next((m for m in self.measurements if m["unit"] == unit and m["operation"] == prep), None)
                    if prep and (prior is None or not prior["artifact_id"] or not prior["source_grounded"]):
                        self.measurements.append({"unit": unit, "operation": label, "status": "unavailable_preparation",
                            "work": 0, "artifact_id": None, "source_grounded": False})
                    else:
                        if self.pending_measurement is None:
                            self.pending_measurement = {"key": key, "start_entry": len(self.ledger.entries)}
                        if self.pending_measurement["key"] != key:
                            raise ValueError("Measurement checkpoint does not match the ordered operation")
                        start = self.pending_measurement["start_entry"]
                        self.boundary("measurement_inflight")
                        reads = (prior["artifact_id"],) if prep else ()
                        outcome = self.worker().run(self.task, unit, identity, "calibration", self.manifest.seed,
                            operation=operation, allowed_artifacts=reads, fresh_context=True,
                            preparation_style=label if operation == "prepare" else None)
                        artifact = self.store.artifacts.get(outcome.artifact_id)
                        self.measurements.append({"unit": unit, "operation": label, "status": outcome.status,
                            "work": sum(e["work"] for e in self.ledger.entries[start:]), "artifact_id": outcome.artifact_id,
                            "start_entry": start, "end_entry": len(self.ledger.entries),
                            "source_grounded": bool(artifact and artifact.source_hashes),
                            "reused_preparation_version": reads[0] if reads else None})
                    self.pending_measurement = None
                    self.completed.append(key)
                    self.boundary("measurement_complete")
        except BudgetExceeded as exc:
            status, error = "budget_exhausted", str(exc)
        except Interrupted as exc:
            status, error = "interrupted", str(exc)
        except Exception as exc:
            status, error = "infrastructure_failed", "Operation measurement failed; inspect private journal"
            self.journal.event("failure", error=type(exc).__name__)
        from ..tasks.data_manifest import regime
        from ..planning.costs import compatibility
        from ..evaluation.metrics import observations
        obs = observations(status, None)
        obs["evaluator_status"] = "not_run_operation_measurement"
        result = EpisodeResult(self.manifest.episode_id, self.attempt_id, self.manifest.experiment_id,
            self.manifest.protocol, self.manifest.mode, status, None, self.task.id, self.task.group,
            self.manifest.policy, self.manifest.attack.family, self.manifest.seed, self.ledger.summary(),
            {"measurements": self.measurements, "observations": obs, "detected_but_unfinished": False,
             "unaffected_work_retained": 0, "integration_failure": False, "false_alarm": False, "reserve_violations": 0},
            {"manifest_hash": digest(self.manifest), "source_revision": self.manifest.source_revision,
             "model_hash": self.manifest.model_hash, "data_hash": self.manifest.data_hash,
             "data_regime": regime(self.task), "calibration_compatibility": compatibility(self.config, self.task),
             "measurement_origin": "mock-measured" if self.config.model.backend == "mock" else "development-measured",
             "backend_runtime": getattr(self.backend, "runtime", {}),
             "condition": {"profile": self.config.development_profile, "silo_interface": self.config.silo_interface,
                "diagnostic_mode": self.task.metadata.get("diagnostic_mode", "full"), "operation_measurement": True}},
            ["Operation costs only; no task-accuracy or savings claim. Indexing and outlines are separately requested preparations.",
             "Every read, full prompt, generation and replay is charged; baseline cost remains in its own immutable run."], error)
        self.journal.result(result)
        return result
