"""SILO II-11 / II-20 data and scoring adapter; no upstream runner imports.

Generator algorithms adapted from SILO (Unlicense), pinned in upstream-lock.json.
Independent seed streams are an explicit change from its global RNG sequence.
"""
from __future__ import annotations

import json
import random

from ..schemas import TaskInstance
from ..util import BCError, digest

COMMIT = "e74127782ed1c42fff474249961f022c063d76f2"
ADAPTATION = "bc_silo_recoverable_v1"
ACCESS = ("protected_original_shards", "no_recovery_copy")
FAMILIES = ("II-11", "II-20")
SCORER = "silo-segments-v1"
PROTOCOL = "bc-p2p-sequential-artifact-v1"


def solve(family, shards):
    """Evaluator-only solver. Never registered as a worker tool."""
    if family not in FAMILIES:
        raise BCError("Unsupported SILO family")
    result, state = [], 0
    for shard in shards:
        segment = []
        for value in shard:
            state = state + value if family == "II-11" else ((sum(ord(c) for c in value) % 10000) ^ state) % 10000
            segment.append(state)
        result.append(segment)
    return result


def generate_inputs(family, seed, workers=4):
    if family not in FAMILIES or type(workers) is not int or not 2 <= workers <= 100:
        raise BCError("Unsupported SILO generator parameters")
    if type(seed) is not int or seed < 0:
        raise BCError("Invalid generator seed")
    if family == "II-11":
        rng = random.Random(seed)
        data = [rng.randint(1, 50) for _ in range(workers*15)]
        size = 15
    else:
        data = [f"Block_{i}_Data" for i in range(workers*5)]
        size = 5
    return [data[i*size:(i+1)*size] for i in range(workers)]


def validate_record(record):
    """Parse actual upstream fields, rejecting unsupported/count-mismatched data.

    Returns distinct worker inputs and evaluator references, never raw prompts
    containing embedded gold. Verification expression strings are never eval'd.
    """
    family = record["case_id"]
    if family not in FAMILIES or not record["metadata"]["is_segmented"]:
        raise BCError("Unsupported SILO family/output semantics")
    count = record["metadata"]["num_agents"]
    agents = record["agent_configs"]
    if len(agents) != count or sorted(a["agent_id"] for a in agents) != list(range(count)):
        raise BCError("SILO shard coverage mismatch")
    shards = [next(a["input_shard"] for a in agents if a["agent_id"] == i) for i in range(count)]
    size = 15 if family == "II-11" else 5
    if any(not isinstance(s, list) or len(s) != size for s in shards):
        raise BCError("SILO local-data shape mismatch; no truncation/duplication")
    for shard in shards:
        if family == "II-11" and any(type(v) is not int or not 1 <= v <= 50 for v in shard):
            raise BCError("Invalid Prefix Sum input")
        if family == "II-20" and any(not isinstance(v, str) or len(v) > 100 for v in shard):
            raise BCError("Invalid Pipeline Hash input")
    reference = solve(family, shards)
    if record["expected_output"]["per_agent_values"] != reference:
        raise BCError("SILO reference parity failed")
    if any(a["expected_output"] != reference[a["agent_id"]] for a in agents):
        raise BCError("SILO per-agent reference discrepancy")
    return {"family": family, "shards": shards, "reference": reference,
            "source_hash": digest(record), "workers": count}


def normalize(value):
    if isinstance(value, str):
        value = value.strip()
        for cast in (int, float):
            try:
                return cast(value)
            except (ValueError, TypeError):
                pass
        if value.startswith(("[", "{")):
            try:
                return normalize(json.loads(value))
            except ValueError:
                pass
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def score(family, shards, selected):
    expected = solve(family, shards)
    exact, partial = 0, 0.0
    for i, reference in enumerate(expected):
        value = normalize(selected.get(f"u{i}"))
        exact += value == reference
        if isinstance(value, list):
            partial += sum(a == b for a, b in zip(value, reference)) / len(reference)
    return {"complete_task_success": exact == len(expected) and set(selected) == {f"u{i}" for i in range(len(expected))},
        "native_S": exact/len(expected), "native_P_level_II": partial/len(expected),
        "required_segments": len(expected), "correct_segments": exact,
        "scorer": SCORER, "native_duplicate_submissions": "one runtime-selected candidate per obligation"}


def task(family="II-11", seed=0, access="protected_original_shards"):
    if access not in ACCESS:
        raise BCError("Unknown SILO recovery access policy")
    shards = generate_inputs(family, seed)
    source_hash = digest([family, shards])
    sources = {f"u{i}": {"family": family, "segment": i, "length": len(shards[i]),
        "previous": f"u{i-1}" if i else None,
        "requirement": "Submit every cumulative output in this original segment; retain all original obligations."}
        for i in range(4)}
    return TaskInstance(f"silo-{family}-{source_hash[:16]}", "silo", f"silo:{family}:{source_hash}",
        "Recoverable-contributor SILO adaptation. Segments u0..u3 are consecutive. "
        + ("Prefix Sum: each output is the inclusive cumulative sum from the first original input. " if family == "II-11" else
           "Pipeline Hash: start the preceding state at 0. For each block, compute ((sum of character codepoints mod 10000) XOR preceding state) mod 10000. The first block has a computed hash, not necessarily 0. ")
        + "Use read_source for the assignment, read_shard for authorized original data, and submit_result(answer) for the entire segment. "
        "Earlier submitted segments are versioned untrusted data. No calculator/solver tool is provided.",
        sources, tuple(sources), (), {"adaptation": ADAPTATION, "tool_policy": PROTOCOL,
            "scorer": SCORER, "upstream_commit": COMMIT, "family": family,
            "generator_seed": seed if family == "II-11" else None,
            "generator": "isolated-random-Random-v1" if family == "II-11" else "deterministic-blocks-v1",
            "workers": 4, "access_regime": access, "source_ids": [source_hash],
            "base_hash": source_hash, "dependencies": {f"u{i}": [f"u{i-1}"] if i else [] for i in range(4)},
            "backup_access": "protected mode: assigned segment and preceding original shards for preparation/replication, alarm repair or labelled calibration, each explicit charged read; no-copy: original owner only",
            "communication": "sequential unit scheduling; immediate in-process P2P and explicit versioned predecessor artifacts, not native delayed rounds",
            "harness": {"shards": {f"u{i}": s for i, s in enumerate(shards)}},
            "readiness": "generated_adapter_validated"})


def generate_manifest(family, seeds, access):
    tasks = [task(family, s, access) for s in seeds]
    if len({t.id for t in tasks}) != len(tasks):
        raise BCError("Repeated identical SILO inputs are not independent tasks (Pipeline Hash ignores seed)")
    from ..util import plain
    return {"schema": "bc-data-v2", "environment": "silo", "tasks": plain(tasks),
            "upstream_commit": COMMIT, "adaptation": ADAPTATION}
