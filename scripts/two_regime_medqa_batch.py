#!/usr/bin/env python3
"""Resume a bounded MedQA or MATH planner prefix from a Jupyter terminal."""
import argparse
from datetime import datetime, timezone
import fcntl
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bc_phase2 import two_regime_launch as launch
from bc_phase2.joint_schema import require
from bc_phase2.model import digest
from beyond_consensus.util import atomic_json

CELL = "medqa-n4-extra"
FIRST = "4600e227c2b8325ee5a4fbe74357ba9f99f65ee8176dc09b5639a39bdc228470"
IDS = [f"test/row/{i}" for i in (846, 882, 165, 1237, 1080, 997, 1094, 1082)]

MATH_CELL = "math500-n4-equal"
MATH_FIRST = "c2a7c3616b520f6ea725cbb7fb81fffe5a2c2c76bf91183a9422b458d225c86e"
MATH_IDS = [
    "test/prealgebra/505.json", "test/intermediate_algebra/986.json",
    "test/algebra/2102.json", "test/number_theory/1032.json",
    "test/algebra/2043.json", "test/algebra/1184.json",
    "test/algebra/2058.json", "test/prealgebra/1922.json",
]


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    if path.exists():
        require(read(path) == value, f"existing record differs: {path}")
    else:
        atomic_json(path, value)


def cli(*args):
    subprocess.run([sys.executable, "-I", "-B", ROOT / "scripts/two_regime.py", *args], check=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def family_review(card):
    print(json.dumps(card, indent=2))
    print("Consider missing images, duplicate families and text sufficiency before clearing.")
    decision, _, rationale = input("Enter clear or blocked, followed by a space and your rationale: ").strip().partition(" ")
    return dict(card_digest=card["card_digest"], decision=decision, rationale=rationale,
                reviewer=getpass.getuser())


def contract_review(packet, final_field="option_label"):
    entry = dict(packet["entry_for_review"])
    template = entry.pop("contract")
    row = packet["row"]
    if (row.get("review") or {}).get("status") == "invalid":
        return dict(entry, decision="invalid", rationale=row["review"].get("error") or "Invalid planner response")
    if row["status"] == "unrun_fit":
        return dict(entry, decision="invalid", rationale="Request did not fit at dispatch")
    print(json.dumps(packet["source"], indent=2))
    print(row.get("raw_response"))
    review = row.get("review") or {}
    if review.get("status") == "unsupported":
        return dict(entry, decision="unsupported", rationale=json.loads(row["raw_response"])["reason"])
    if review.get("status") != "wire_valid":
        return dict(entry, decision="invalid", rationale=f"Unusable planner response: {review.get('status', row['status'])}")
    plan = json.loads(row["raw_response"])
    tasks = plan["tasks"]
    names = {t["id"]: f"t{i}" for i, t in enumerate(tasks)}
    draft = []
    for t in tasks:
        draft.append(dict(id=names[t["id"]], responsibility=t["responsibility"],
                          parents=[names[k] for k in t["required_inputs"] if k != "problem_statement"],
                          fields=["derivation", "artifact"]))
    consumed = {parent for t in draft for parent in t["parents"]}
    terminals = [t for t in draft if t["id"] not in consumed]
    if len(terminals) == 1:
        terminals[0]["fields"] = ["justification", final_field]
    print("Proposed task mapping:", json.dumps(draft, indent=2))
    print("Admit only if the displayed responsibilities and dependencies are substantive, "
          "answer-free and sufficient for the sole final answer field.")
    decision, _, rationale = input(
        "Enter admitted, unsupported or review_unresolved, followed by a space and your rationale: "
    ).strip().partition(" ")
    require(decision in ("admitted", "unsupported", "review_unresolved"), "unknown review disposition")
    require(rationale.strip(), "review rationale required")
    if decision == "admitted":
        require(len(terminals) == 1, "one final obligation must cover every proposed task")
        terminal = terminals[0]["id"]
        entry["contract"] = dict(template, decision=decision, tasks=draft, outputs=[terminal],
                                 reviewer=getpass.getuser(), reviewer_kind="human", reviewed_at=now(),
                                 substantive_no_answer_leakage=True)
    return dict(entry, decision=decision, rationale=rationale)


def wait_for_result(receipt, scope):
    job = receipt["job_id"]
    require(receipt["submitted"] is True and receipt["scope_digest"] == digest(scope)
            and str(job).isdigit(), "unexpected submission receipt")
    run = Path(receipt["output"])
    require(run == Path(scope["cluster"]["output_root"]) / ("composite-" + digest(scope)), "unexpected run directory")
    print(f"Waiting for job {job}. Ctrl-C and rerun to resume.", flush=True)
    while True:
        queued = subprocess.check_output(["squeue", "-h", "--array", "-u", getpass.getuser(), "-o", "%F"], text=True)
        if str(job) not in queued.split():
            records = subprocess.check_output(["sacct", "-n", "-P", "-j", str(job), "--format=JobID,State,ExitCode"], text=True)
            rows = [line.strip().split("|") for line in records.splitlines()]
            task = [r for r in rows if r[0] == f"{job}_0"]
            require(len(task) == 1 and task[0][1:3] == ["COMPLETED", "0:0"],
                    f"job {job}: completion unconfirmed; inspect sacct and the execution directory")
            require((run / "execution/result.json").is_file(), "completed job lacks result")
            return run
        time.sleep(20)


def check_stage(scope, index, entries, family, cell=CELL, ids=IDS):
    limits = scope["limits"]
    require(scope["cell"] == cell and scope["source_ids"] == [ids[index]]
            and scope["history"] == entries and "wave" not in scope
            and limits["maximum_calls"] == limits["calls_per_source"] == 1
            and limits["token_cap"] <= 16384 and limits["output_cap"] <= 3072
            and limits["physical_gpus"] == 1 and limits["wall_seconds"] <= 3600
            and (not index or scope["family_review"] == family), "outside approved planner prefix")


def drive(campaign, math_equal=False):
    require(not os.environ.get("SLURM_JOB_ID"), "start from a login terminal")
    cell, ids, first_scope = (MATH_CELL, MATH_IDS, MATH_FIRST) if math_equal else (CELL, IDS, FIRST)
    dataset = "math500" if math_equal else "medqa"
    slot = launch.cell(cell)
    require(slot["candidates"] == ids, "frozen candidate order changed")
    first = read(campaign / "plan-1/manifest.disabled.json")
    require(first["scope_digest"] == digest(first["scope"]) == first_scope, "different first-stage anchor")
    parent = Path(first["scope"]["parent"])
    public = launch.public_rows(launch.anchor(parent, dataset), dataset)
    consent = dict(decision="approved", source_transmission_authorized=True, gpu_spending_authorized=True,
                   cell=cell, first_scope=first_scope, concurrent_jobs=1,
                   worker_authorized=False, reviewer=getpass.getuser())
    if math_equal:
        consent.update(source_ids=ids, maximum_calls=8, token_cap=131072, maximum_allocated_wall_seconds=28800)
    else:
        consent.update(additional_ids=ids[1:], maximum_additional_calls=7,
                       maximum_additional_tokens=114688, maximum_additional_wall_seconds=25200)
    save(campaign / "planner-batch-consent.json", consent)
    entries = []
    for index in range(len(ids) + 1):
        selected, usage = launch.history(slot, public, entries)
        history = campaign / f"batch-history-{index}.json"
        save(history, entries)
        if selected["status"] != "next_candidate":
            save(campaign / "planner-batch-result.json", dict(selection=selected, usage=usage, history=str(history)))
            print(selected["status"], usage, "Saved", campaign / "planner-batch-result.json")
            return
        sid = selected["source_id"]
        require(index < len(ids) and sid == ids[index], "unexpected candidate")
        step = campaign / f"plan-{index + 1}"
        entry_path = campaign / f"batch-entry-{index + 1}.json"
        if entry_path.exists():
            entries.append(read(entry_path))
            continue
        family_path = campaign / f"batch-source-{index + 1}.json"
        if index:
            card = launch.review_card(slot, sid, public)
            card_path = campaign / f"batch-card-{index + 1}.json"
            save(card_path, card)
            print("Source review packet:", card_path, flush=True)
            family = read(family_path) if family_path.exists() else family_review(card)
            launch.check_review(slot, sid, public, family)
            save(family_path, family)
            if family["decision"] == "blocked":
                entry = dict(source_id=sid, family_review=family)
                launch.history(slot, public, entries + [entry])
                save(entry_path, entry)
                entries.append(entry)
                continue
            if not step.exists():
                cli("prepare", "--cell", cell, "--parent", parent, "--history", history,
                    "--review", family_path, "--output", step)
        manifest = read(step / "manifest.disabled.json")
        scope = manifest["scope"]
        check_stage(scope, index, entries, family if index else None, cell, ids)
        receipt_path = step / "submission.json"
        if not receipt_path.exists():
            approval = read(step / "approval.pending.json")
            approval.update(decision="approved", reviewer=getpass.getuser(), reviewed_at=now(),
                            statement_transmission_authorized=True, GPU_spending_authorized=True)
            if index == 0:
                if math_equal:
                    require(approval["family_review"]["card_digest"] ==
                            "850705ab536c25ea741635d8201495be998a7291a5e7c32136b6449988ec9a31",
                            "different MATH source review")
                    rationale = (
                        "The full linear equation is in the text. The supplied historical neighbors "
                        "use a complex modulus, a variable denominator, or a logarithmic product.")
                else:
                    rationale = ("The public record supplies the cartilage-healing question and all four options. "
                                 "The identity check found no duplicate. The supplied knee-related neighbor "
                                 "asks about a cellular defect associated with bleeding.")
                approval["family_review"].update(decision="clear", reviewer="Codex (AI-assisted source review)",
                                                 rationale=rationale)
            approval_file = step / "batch-approval.json"
            if approval_file.exists():
                approval["reviewed_at"] = read(approval_file)["reviewed_at"]
            save(approval_file, approval)
            stage = launch.Stage(scope)
            release = stage.approve(manifest, approval)
            save(step / "batch-release.json", release)
            launch.base.submit(ROOT, release, dry_run=True, protocol=stage)
            save(receipt_path, launch.base.submit(ROOT, release, dry_run=False, protocol=stage))
        run = wait_for_result(read(receipt_path), scope)
        packet = step / "contract-review.json"
        if not packet.exists():
            cli("review-plan", "--run", run, "--output", packet)
        print("Contract review packet:", packet, flush=True)
        value = read(packet)
        require(value["scope_digest"] == manifest["scope_digest"] and value["previous_prefix"] == entries
                and value["entry_for_review"]["run"] == str(run.resolve()), "unexpected review packet")
        entry = contract_review(value, "final_answer" if math_equal else "option_label")
        launch.history(slot, public, entries + [entry])
        save(entry_path, entry)
        entries.append(entry)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("--approve-math-equal", action="store_true",
                        help="authorize the frozen eight-candidate MATH equal-task planner prefix")
    args = parser.parse_args()
    with (args.campaign / ".planner-batch.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        drive(args.campaign.resolve(), args.approve_math_equal)
