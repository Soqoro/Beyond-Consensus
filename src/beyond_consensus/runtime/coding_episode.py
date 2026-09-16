"""One clean, integrated CooperBench E0 episode; no policy-comparison claims."""
import time
from pathlib import Path

from ..agents.coding import CodingWorker
from ..evaluation.cooperbench import evaluate
from ..schemas import EpisodeResult
from ..util import BCError, digest, plain
from .budget import BudgetExceeded, BudgetLedger
from .episode import Interrupted
from .provenance import ProvenanceStore
from .repository import CodingEnvironment, RepositorySession, inventory


def require_coding_e0(config):
    if config.protocol != "A" or config.policies != ("single",) or config.attacks != ("clean",):
        raise BCError("Coding execution currently supports clean single-agent Protocol A E0 only; "
                      "four-policy coding planning/calibration remain unimplemented")
    if config.task_count != 1 or config.shards != 1:
        raise BCError("Initial coding E0 is bounded to one task and one shard")
    if config.monitor_id != "coding-structure-v1":
        raise BCError("Coding E0 requires the explicitly labelled coding-structure-v1 monitor")
    if not config.coding_environment or not config.coding_environment_hash:
        raise BCError("Coding E0 requires a pinned reviewed coding_environment")
    return CodingEnvironment(Path(config.coding_environment), config.coding_environment_hash)


def validate_coding_task(config, environment, task):
    from ..evaluation.cooperbench import require_environment_validation
    environment.validate_task(task)
    if not config.coding_validation or not config.coding_validation_hash:
        raise BCError("Coding E0 needs measured baseline/reference evaluator validation")
    require_environment_validation(config.coding_validation, config.coding_validation_hash, environment, task)


class CodingEpisodeEngine:
    def __init__(self, task, manifest, config, backend, journal, attempt_id, stop_requested=lambda: False):
        self.task, self.manifest, self.config = task, manifest, config
        self.backend, self.journal, self.attempt_id = backend, journal, attempt_id
        self.stop_requested = stop_requested
        self.ledger = BudgetLedger(config.budget.total, config.budget)
        self.store = ProvenanceStore()
        self.phase = "primary"
        self.session = None

    def boundary(self, name):
        self.journal.checkpoint(plain({"manifest_hash": digest(self.manifest), "boundary": name,
            "coding_schema": "coding-e0-v1", "phase": self.phase, "ledger": self.ledger,
            "store": self.store.export(), "workspace": str(self.session.workspace),
            "tree_hash": digest(inventory(self.session.workspace))}))
        self.journal.event("boundary", name=name, phase=self.phase, attempt_id=self.attempt_id,
                           work=self.ledger.spent)
        if self.stop_requested():
            raise Interrupted("Coding execution interrupted at a recorded boundary")

    def run(self):
        status, success, error, final = "completed", False, None, {}
        outcome = "not_started"
        try:
            environment = require_coding_e0(self.config)
            validate_coding_task(self.config, environment, self.task)
            previous = self.journal.previous(digest(self.manifest))
            if previous:
                if previous.get("coding_schema") != "coding-e0-v1":
                    raise BCError("Incompatible coding checkpoint")
                state = previous["ledger"]
                self.ledger = BudgetLedger(state["cap"], self.config.budget, state["entries"], state["reservations"], state["historical"])
                self.ledger.uncertain_inflight()
            if previous and previous["phase"] == "evaluation":
                self.phase = "evaluation"
                self.session = RepositorySession(environment, Path(previous["workspace"]), cancelled=self.stop_requested)
                if digest(inventory(self.session.workspace)) != previous["tree_hash"]:
                    raise BCError("Frozen evaluation candidate changed")
                self.store = ProvenanceStore.restore(previous["store"])
                outcome = "submitted"
            else:
                # A tool can be interrupted between guest execution and applying
                # its response. Restart from pristine data, preserving ALL charges.
                self.session = RepositorySession(environment, self.journal.path / ("candidate-" + self.attempt_id),
                                                 cancelled=self.stop_requested)
                maximum = environment.profile.timeout_seconds * self.config.budget.timeout_charge_per_second
                key = self.ledger.reserve_work("primary", maximum, "repository_materialization")
                started = time.monotonic()
                try:
                    self.session.initialize()
                    elapsed = time.monotonic()-started
                    self.ledger.reconcile_work(key, min(maximum, elapsed*self.config.budget.timeout_charge_per_second))
                    self.ledger.entries[-1]["wall_seconds"] = elapsed
                except Exception:
                    self.ledger.reconcile_work(key, None)
                    raise
                if previous:
                    self.journal.event("coding_restart", semantics="pristine restart; all prior and uncertain work charged")
                self.boundary("coding_start")
                outcome, submitted = CodingWorker(self.backend, self.config, self.ledger, self.store,
                    self.session, self.boundary).run(self.task, self.manifest.seed)
                if submitted:
                    self.phase = "evaluation"
                    self.boundary("coding_evaluation_ready")
            if self.phase == "evaluation":
                # Once this phase is recorded there is never a return to the model,
                # even on retry after a failed/interrupted hidden evaluation.
                final = evaluate(self.task, environment, self.session.workspace, self.config.data_manifest,
                                 self.ledger, boundary=self.boundary, cancelled=self.stop_requested)
                success = final["complete_task_success"]
        except BudgetExceeded as exc:
            status, success, error = "budget_exhausted", False, str(exc)
        except Interrupted as exc:
            status, success, error = "interrupted", None, str(exc)
        except Exception as exc:
            status, success, error = "infrastructure_failed", None, f"{type(exc).__name__}: {exc}"
            self.journal.event("failure", error=error)
        result = EpisodeResult(self.manifest.episode_id, self.attempt_id, self.manifest.experiment_id,
            self.manifest.protocol, self.manifest.mode, status, success, self.task.id, self.task.group,
            self.manifest.policy, self.manifest.attack.family, self.manifest.seed, self.ledger.summary(),
            {"coding_outcome": outcome, "final_evaluation": final, "alarmed": False,
             "false_alarm": False, "detected_but_unfinished": False, "reserve_violations": 0,
             "unaffected_work_retained": 0, "integration_failure": status == "completed" and not success},
            {"manifest_hash": digest(self.manifest), "source_revision": self.manifest.source_revision,
             "model_hash": self.manifest.model_hash, "data_hash": self.manifest.data_hash,
             "coding_environment_hash": self.config.coding_environment_hash,
             "backend_runtime": getattr(self.backend, "runtime", {})},
            ["Clean coding E0 only; no recovery-policy comparison or confirmatory claims",
             "Task environment and joint test commands require separate review/validation",
             "Interrupted primary work restarts from pristine files with all prior work charged"], error)
        self.journal.result(result)
        return result
