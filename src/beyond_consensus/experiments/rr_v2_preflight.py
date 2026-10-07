"""Synthetic variable-pool allocation probe. Never authorizes task execution."""
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import time

from ..config import ModelConfig
from ..util import BCError, digest, read_json
from .manifest import source_revision

SCHEMA = "rr-v2-preflight-manifest-v1"
PROTOCOL = "rr-isolated-histories-v1"
FOOTPRINT_PROFILE = "rr-open-footprint-profile-v2"
FOOTPRINT_PROTOCOL = "rr-open-footprint-planner4096-v2"

STRESS_PROTOCOL = "rr-forced-token-full-budget-v1"


def grammar(m,role):
    contract=m.get('execution_contract','adaptive_legacy')
    if contract not in ('adaptive_legacy','plan_scoped_v1'):raise BCError('Unknown probe execution contract')
    suffix='scoped-v1' if contract=='plan_scoped_v1' else 'v2'
    return f'reporecourse-{role}-{suffix}-pool-{m["pool"]}'


def build(root, worker_lock, planner_lock, pool, *, full_budget_stress=False, plan_scoped=False, planner_output_cap=2048):
    from ..models.competence import CHECKPOINT, REVISION
    if type(planner_output_cap) is not int or planner_output_cap not in (2048, 4096):
        raise BCError("Unsupported planner output cap")
    if planner_output_cap == 4096 and (pool != 7 or not plan_scoped or full_budget_stress):
        raise BCError("Planner 4096 requires separate scoped pool-7 footprint qualification")
    if type(pool) is not int or pool not in range(2, 9):
        raise BCError("Pool must be 2..8")
    model = asdict(ModelConfig(backend="transformers", checkpoint=CHECKPOINT,
        revision=REVISION, tokenizer_revision=REVISION, dtype="bfloat16",
        context_limit=16384, max_new_tokens=2048, thinking=True, do_sample=False,
        action_constraint=f"reporecourse-json-{'scoped-v1' if plan_scoped else 'v2'}-pool-{pool}"))
    m = dict(schema=SCHEMA, protocol=STRESS_PROTOCOL if full_budget_stress else PROTOCOL, pool=pool, model=model,
        source_revision=source_revision(root), model_lock_sha256=digest(worker_lock),
        planner_lock=planner_lock, shards=1, episodes=[], planned_episodes=0,
        task_inputs_used=False, task_execution_allowed=False, rounds=2)
    if plan_scoped:m["execution_contract"]="plan_scoped_v1"
    if planner_output_cap == 4096:
        m.update(schema=FOOTPRINT_PROFILE, protocol=FOOTPRINT_PROTOCOL,
                 planner_output_cap=4096)
    m["experiment_id"] = digest(m)
    validate(m)
    check_locks(m, worker_lock)
    return m


def validate(m):
    body = {k: v for k, v in m.items() if k != "experiment_id"}
    special = m.get('schema') == FOOTPRINT_PROFILE
    version_valid = (m.get('protocol') == FOOTPRINT_PROTOCOL and
                     type(m.get('planner_output_cap')) is int and m['planner_output_cap'] == 4096 and m.get('pool') == 7 and
                     m.get('execution_contract') == 'plan_scoped_v1') if special else (
        m.get('schema') == SCHEMA and m.get('protocol') in (PROTOCOL, STRESS_PROTOCOL) and
        'planner_output_cap' not in m)
    if (not version_valid
            or digest(body) != m.get("experiment_id")
            or type(m.get("pool")) is not int or m["pool"] not in range(2, 9)
            or m.get("rounds") != 2 or m.get("episodes") != []
            or m.get("planned_episodes") != 0 or m.get("shards") != 1
            or m.get("task_inputs_used") is not False
            or m.get("task_execution_allowed") is not False):
        raise BCError("Invalid synthetic preflight manifest")
    from ..models.competence import CHECKPOINT, REVISION
    config = ModelConfig(**m["model"])
    if (config.checkpoint != CHECKPOINT or config.revision != REVISION
            or config.tokenizer_revision != REVISION or config.backend != "transformers"
            or config.dtype != "bfloat16" or not config.thinking or config.do_sample
            or config.context_limit != 16384 or config.max_new_tokens != 2048
            or config.action_constraint != grammar(m,'json')):
        raise BCError("Probe requires the frozen pool-bound 27B BF16 profile")
    # Validate the actual planner config before submission or model loading,
    # not only when the first planner case switches the shared backend's role.
    replace(config, action_constraint=grammar(m, 'plan'), max_new_tokens=output_cap(m, 'plan'))
    return SimpleNamespace(model=config, shards=1, task_kind="rr_v2_preflight")


def output_cap(m, role):
    if role not in ('json', 'plan'):
        raise BCError('Unknown qualification role')
    return m.get('planner_output_cap', 2048) if role == 'plan' else 2048


def check_locks(m, worker):
    from ..models.competence import require_qualification
    if digest(worker) != m["model_lock_sha256"]:
        raise BCError("Worker lock changed")
    planner = m["planner_lock"]
    for key in ("checkpoint", "revision", "tokenizer_revision", "model_path",
                "tokenizer_path", "metadata_hashes", "weight_hashes"):
        if not worker.get(key) or worker[key] != planner.get(key):
            raise BCError("Planner and workers must share identical staged weights/tokenizer")
    for role, lock in (("json", worker), ("plan", planner)):
        require_qualification(lock, lock.get("decoder_qualification", {}).get("packages", {}),
                              16384, grammar(m,role), output_cap(m, role))


def check_submission(m, worker, root, mode, concurrency):
    validate(m)
    if mode != "preflight" or concurrency != 1:
        raise BCError("Synthetic v0.2 qualification is preflight-only, concurrency one")
    if source_revision(root) != m["source_revision"]:
        raise BCError("Source changed; rebuild synthetic preflight manifest")
    check_locks(m, worker)


def history(count, identity):
    # Each identity owns a distinct inert history and an exact synthetic read.
    expected = {"tool": "read_source", "name": "probe_" + identity}
    system = ("Synthetic context-switch diagnostic. Ignore the inert numbered records. "
              "Return exactly this JSON action, no Markdown: " + json.dumps(expected))
    records = [f"record {i:05d}: {digest([identity, i])[:24]}\n" for i in range(16384)]
    def render(n):
        return [{"role": "system", "content": system}, {"role": "user", "content":
            "<inert_records>\n" + "".join(records[:n]) + "</inert_records>\nReturn the requested action."}]
    lo, hi = 0, len(records)
    if count(render(0)) > 14336:
        raise BCError("Probe instruction exceeds input allowance")
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if count(render(mid)) <= 14336: lo = mid
        else: hi = mid - 1
    messages = render(lo)
    if not 14080 <= count(messages) <= 14336:
        raise BCError("Probe did not reach the declared long-input band")
    return messages, expected


def sequence(backend, pool, switch, memory, *, full_budget_stress=False):
    """Injectable for CPU tests; production uses one backend and fresh call caches."""
    identities = [f"w{i}" for i in range(pool)] + ["planner"]
    histories = {i: history(backend.count_input, i) for i in identities}
    rows = []
    for round_index in range(2):
        for identity in identities:
            switch("plan" if identity == "planner" else "json")
            messages, expected = histories[identity]
            # No other identity's generation enters this prompt. Revisit exactly
            # the same retained history; all re-prefill tokens are charged again.
            before = digest(messages)
            tokens = 14336 if full_budget_stress else backend.count_input(messages)
            row = dict(identity=identity, round=round_index, prompt_hash=before,
                       input_tokens=tokens, output_cap=2048, passed=False)
            start = time.process_time(); wall = time.monotonic()
            memory(reset=True)
            try:
                if full_budget_stress:
                    from ..models.rr_memory_stress import generate as stress_generate
                    g = stress_generate(backend, copy.deepcopy(messages), 2048, 0)
                else:
                    g = backend.generate(copy.deepcopy(messages), 2048, 0)
                row.update(generation=asdict(g), output_tokens=g.output_tokens,
                           uncertain_tokens=0)
                try:
                    row["passed"] = (json.loads(g.text) == expected
                        and g.diagnostics.get("constraint_complete") is True
                        and g.diagnostics.get("finish_reason") == "eos")
                except (ValueError, TypeError):
                    pass
                if full_budget_stress:
                    from ..models.rr_memory_stress import verified
                    row["passed"] = verified(g.diagnostics, g.output_tokens)
            except Exception as exc:
                row.update(error_type=type(exc).__name__, output_tokens=None,
                           uncertain_tokens=tokens + 2048)
            row.update(process_cpu_seconds=time.process_time()-start,
                       wall_seconds=time.monotonic()-wall, memory=memory(reset=False))
            rows.append(row)
            if digest(messages) != before:
                raise BCError("Probe history mutated")
            if row.get("error_type"):
                return rows
    return rows


def qualified_backend(m, lock_path, root):
    worker = read_json(lock_path)
    check_submission(m, worker, root, "preflight", 1)
    from ..models.competence import require_qualification, versions
    for role, lock in (("json", worker), ("plan", m["planner_lock"])):
        require_qualification(lock, versions(), 16384, grammar(m,role), output_cap(m, role))
    from ..models.transformers_backend import TransformersBackend
    from ..models.constrained import ActionConstraint
    config = validate(m).model
    role_configs = {role: replace(config, action_constraint=grammar(m, role),
                                  max_new_tokens=output_cap(m, role)) for role in ('json', 'plan')}
    backend = TransformersBackend(role_configs['json'], lock_path)
    constraints = {"json": backend.constraint}
    constraints["plan"] = ActionConstraint(backend.tokenizer,
        backend.model.get_output_embeddings().weight.shape[0],
        backend.generation_tokens["eos_token_id"], grammar(m,'plan'))
    def switch(role):
        backend.config = role_configs[role]
        backend.constraint = constraints[role]
    def memory(*, reset):
        cuda = backend.torch.cuda
        cuda.synchronize()
        if reset: cuda.reset_peak_memory_stats(0)
        free, total = cuda.mem_get_info(0)
        return dict(allocated_bytes=cuda.memory_allocated(0), reserved_bytes=cuda.memory_reserved(0),
                    peak_allocated_bytes=cuda.max_memory_allocated(0),
                    peak_reserved_bytes=cuda.max_memory_reserved(0), free_bytes=free, total_bytes=total)
    return backend, switch, memory


def run(m, lock_path, root):
    if m.get('schema') != SCHEMA:
        raise BCError('Separate footprint profiles require the footprint runner')
    probe_cpu_start = time.process_time()
    probe_wall_start = time.monotonic()
    worker = read_json(lock_path)
    backend, switch, memory = qualified_backend(m, lock_path, root)
    stress = m["protocol"] == STRESS_PROTOCOL
    rows = sequence(backend, m["pool"], switch, memory, full_budget_stress=stress)
    passed = len(rows) == 2*(m["pool"]+1) and all(r["passed"] for r in rows)
    return dict(schema="rr-v2-context-preflight-v1", experiment_id=m["experiment_id"],
        status=("passed_full_budget_geometry" if stress else "passed_observed_sequence") if passed else "failed", command_failed=not passed,
        model_executed=True, sql_executed=False, task_inputs_used=False,
        probe_protocol=m["protocol"], full_budget_geometry_passed=passed if stress else None,
        normal_decoding=not stress, task_competence_measured=False,
        task_execution_allowed=False, worst_case_fit_established=False,
        memory_protocol="one-model-sequential-reprefill-no-cross-worker-cache-v2",
        pool=m["pool"], model_instances=1, runtime=backend.runtime, calls=rows,
        manifest_hash=digest(m), source_revision=m["source_revision"],
        qualification_keys={role: lock["decoder_qualification"]["qualification_key"]
                            for role, lock in (("json", worker), ("plan", m["planner_lock"]))},
        total_process_cpu_seconds=time.process_time()-probe_cpu_start,
        total_wall_seconds=time.monotonic()-probe_wall_start,
        actual_tokens=sum(r["input_tokens"]+r["output_tokens"] for r in rows if r["output_tokens"] is not None),
        uncertain_tokens=sum(r["uncertain_tokens"] for r in rows),
        accounting="Separate synthetic qualification; no historical/task ledger changes",
        limitation=("Synthetic forced-token tensor geometry only; normal grammar/semantic behavior and universal worst-case fit not established"
                    if stress else "Observed long-input early-EOS sequence only; no full-output-cap or task competence approval"))
