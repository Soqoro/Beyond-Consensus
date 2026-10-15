#!/usr/bin/env bash
# CPU-only, explicit user-triggered qualification. Never self-submits.
set -euo pipefail
usage() {
    cat <<'EOF'
Usage: qualify_reporecourse.sh --sources DIR --output NEW_DIR [--model-lock FILE | --worker-lock FILE --planner-lock FILE] [--local] [--dry-run] [--track-f-controls] [--v2-controls] [--scoped-controls] [--cohort-controls] [--rich-only] [--interface-reliability] [--pool-count N] [--repo-root DIR] [--decoder-diagnostic-controls | --organization-catalog]
CPU pack/reference checks; optional pinned-tokenizer grammar qualification.
Use sbatch on the cluster. --local allows explicit workstation CPU checks.
EOF
}
repo_root=''
sources=''
output=''
model_lock=''
worker_lock=''
planner_lock=''
interface_profile=''
interface_args=()
rich_only=false
decoder_diagnostic=false
organization_catalog=false
local_run=false
dry=false
track_f=false
v2=false
scoped=false
cohort=false
pool_count=4
while (($#)); do
    case "$1" in
        --decoder-diagnostic-controls) decoder_diagnostic=true; shift ;;
        --organization-catalog) organization_catalog=true; shift ;;
        --help|-h) usage; exit 0 ;;
        --dry-run) dry=true; shift ;;
        --local) local_run=true; shift ;;
        --v2-controls) v2=true; shift ;;
        --scoped-controls) scoped=true; v2=true; shift ;;
        --cohort-controls) cohort=true; shift ;;
        --rich-only) rich_only=true; shift ;;
        --interface-reliability) interface_profile=rr-interface-reliability-v1; interface_args=(--interface-profile "$interface_profile"); shift ;;
        --pool-count) (($# >= 2)) || exit 2; pool_count="$2"; shift 2 ;;
        --track-f-controls) track_f=true; shift ;;
        --sources|--output|--model-lock|--worker-lock|--planner-lock|--repo-root)
            (($# >= 2)) || { usage >&2; exit 2; }
            case "$1" in
                --repo-root) repo_root="$2" ;;
                --sources) sources="$2" ;;
                --output) output="$2" ;;
                --model-lock) model_lock="$2" ;;
                --worker-lock) worker_lock="$2" ;;
                --planner-lock) planner_lock="$2" ;;
            esac
            shift 2 ;;
        *) usage >&2; exit 2 ;;
    esac
done
if "$decoder_diagnostic" || "$organization_catalog"; then
    if "$cohort" || "$v2" || "$scoped" || "$track_f" || "$rich_only" || [[ -n "$interface_profile$worker_lock$planner_lock" ]] || { "$decoder_diagnostic" && "$organization_catalog"; }; then
        printf 'Use decoder diagnostics or organization catalog as a separate CPU qualification.\n' >&2; exit 2
    fi
    if "$organization_catalog" && [[ -n "$model_lock" ]]; then
        printf 'Organization catalog does not use a model lock.\n' >&2; exit 2
    fi
    if "$decoder_diagnostic" && [[ -z "$model_lock" ]]; then
        printf 'Decoder diagnostic controls require --model-lock.\n' >&2; exit 2
    fi
fi
if [[ -n "$interface_profile" ]] && { ! "$cohort" || ! "$rich_only" || [[ -z "$model_lock" || -n "$worker_lock" ]]; }; then
    printf "Interface revision requires --cohort-controls --rich-only --model-lock; renew both grammars.\n" >&2; exit 2
fi
if "$rich_only" && ! "$cohort"; then printf 'Use --rich-only with --cohort-controls.\n' >&2; exit 2; fi
if [[ -n "$worker_lock$planner_lock" ]]; then
    if ! "$cohort" || [[ -z "$worker_lock" || -z "$planner_lock" || -n "$model_lock" ]]; then
        printf 'Role lock reuse requires both locks, cohort controls, and no --model-lock.\n' >&2; exit 2
    fi
fi
if "$dry"; then
    printf 'CPU qualification only: reference alternatives, negatives, compiler; optional model-specific decoder. No model weights or GPU jobs.\n'
    exit 0
fi
[[ -n "$output" ]] || { usage >&2; exit 2; }
if ! "$decoder_diagnostic"; then [[ -n "$sources" ]] || { usage >&2; exit 2; }; fi
if ! "$local_run"; then
    : "${SLURM_JOB_ID:?Use a CPU batch allocation, or explicitly --local on a workstation}"
fi
: "${BC_PYTHON:?Set BC_PYTHON to the Python 3.12+ environment with pinned optional CPU dependencies}"
# Slurm copies the batch script to its spool. In an allocation use the
# configured --chdir, never the copied script's parent or submission directory.
if [[ -z "$repo_root" ]]; then
    if [[ -n "${SLURM_JOB_ID:-}" ]]; then
        repo_root="$PWD"
    else
        repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
    fi
fi
cd "$repo_root"
repo_root="$PWD"
for required in scripts/bc.py scripts/rr_v2.py src/reporecourse/engine.py; do
    [[ -f "$required" ]] || { printf 'Invalid repository root: %s (missing %s). Use --repo-root or sbatch --chdir.\n' "$repo_root" "$required" >&2; exit 2; }
done
[[ ! -e "$output" ]] || { printf 'Use a fresh output directory.\n' >&2; exit 2; }
mkdir -p -- "$output"
if "$decoder_diagnostic"; then
    "$BC_PYTHON" -I scripts/check_rr_cohort.py --output "$output/controls.json"
    for role in native guarded; do
        mode=reporecourse-json-reliable-v1-pool-7
        if [[ "$role" == guarded ]]; then mode=reporecourse-json-unique-v1-pool-7; fi
        "$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$model_lock" \
            --context-limit 16384 --output-cap 2048 --action-constraint "$mode" \
            --output "$output/$role-grammar.json" --qualified-lock "$output/$role-lock.json"
    done
    printf 'CPU decoder controls complete; no GPU execution authorized.\n'
    exit 0
fi
if "$organization_catalog"; then
    "$BC_PYTHON" -I scripts/check_rr_cohort.py --output "$output/controls.json"
    "$BC_PYTHON" -I scripts/sample_rr_organizations.py --sources "$sources" \
        --output "$output/catalog.json" --qualify
    printf 'Organization catalog prepared; inspect qualification and missing slots. No GPU execution authorized.\n'
    exit 0
fi
"$BC_PYTHON" -I scripts/bc.py rr-readiness --sources "$sources" --output "$output/readiness.json"
if "$cohort"; then
    if "$v2" || "$track_f"; then printf 'Use cohort controls as a separate qualification.\n' >&2; exit 2; fi
    "$BC_PYTHON" -I scripts/check_rr_cohort.py --output "$output/cohort-controls.json"
    "$BC_PYTHON" -I scripts/bc.py rr-rich-inventory --sources "$sources" --output "$output/rich-inventory.json"
    if ! "$rich_only"; then
        "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" --task synthetic-stock --output "$output/synthetic-stock.json"
    fi
    # Missing source packs are explicit blockers; never create surrogate staged data.
    PYTHONPATH="$repo_root/src" "$BC_PYTHON" - "$sources" "$output" <<'PYRICH'
import sys
from pathlib import Path
from reporecourse.rich_tasks import qualify
from reporecourse.common import write_new, Rejected
for task in ('jaffle-payment-release','energy-single-indicator-release','github-topics-client-package','github-multioperation-integration'):
    try:report=qualify(task,sys.argv[1])
    except (Rejected,OSError) as exc:report=dict(task=task,status='blocked_prerequisite',reason=str(exc),model_executed=False)
    write_new(Path(sys.argv[2])/(task+'.json'),report)
    if report['status']=='failed':raise SystemExit('Rich reference controls failed: '+task)
PYRICH
    if [[ -n "$worker_lock" ]]; then
        PYTHONPATH="$repo_root/src" "$BC_PYTHON" - "$worker_lock" "$planner_lock" "$output" <<'PYLOCKS'
import sys, shutil
from pathlib import Path
from beyond_consensus.models.competence import require_qualification, versions
from beyond_consensus.experiments import rr_v2_preflight as profile
from reporecourse.common import load, write_new, digest
worker,planner=map(load,sys.argv[1:3]);root=Path.cwd();output=Path(sys.argv[3])
m=profile.build(root,worker,planner,7,plan_scoped=True,planner_output_cap=6144)
profile.check_locks(m,worker)
for role,lock,cap in [('json',worker,2048),('plan',planner,6144)]:
    require_qualification(lock,versions(),16384,'reporecourse-'+role+'-scoped-v1-pool-7',cap)
for name,path in [('worker',sys.argv[1]),('planner',sys.argv[2])]:shutil.copyfile(path,output/(name+'-lock.json'))
write_new(output/'role-lock-reuse.json',dict(status='compatible',worker=digest(worker),planner=digest(planner),model_executed=False))
PYLOCKS
    fi
    if [[ -n "$model_lock" ]]; then
        for role in worker planner; do
            mode=json; cap=2048; grammar_suffix=scoped-v1
            if [[ -n "$interface_profile" ]]; then grammar_suffix=reliable-v1; fi
            if [[ "$role" == planner ]]; then mode=plan; cap=6144; fi
            "$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$model_lock" \
                --context-limit 16384 --output-cap "$cap" --action-constraint "reporecourse-$mode-$grammar_suffix-pool-7" \
                --output "$output/$role-grammar.json" --qualified-lock "$output/$role-lock.json"
        done
    fi
    if [[ -n "$model_lock$worker_lock" ]]; then
        for task in synthetic-stock jaffle-payment-release energy-single-indicator-release github-topics-client-package github-multioperation-integration; do
            if [[ "$task" == synthetic-stock ]] && "$rich_only"; then continue; fi
            if "$BC_PYTHON" -c 'import json,sys; sys.exit(json.load(open(sys.argv[1])).get("status")!="cpu_qualified_review_pending")' "$output/$task.json"; then
                "$BC_PYTHON" -I scripts/bc.py rr-cohort-footprint --task "$task" --sources "$sources" \
                    --model-lock "$output/worker-lock.json" --output "$output/$task-footprint.json" "${interface_args[@]}"
            fi
        done
    fi
    if [[ -n "$interface_profile" ]]; then
        # A written report is not necessarily a passing qualification. Fail
        # before preparing a GPU job if any actual task prompt failed its gate.
        "$BC_PYTHON" - "$output" <<'PYINTERFACE'
import json, sys
from pathlib import Path
root=Path(sys.argv[1])
for task in ('jaffle-payment-release','energy-single-indicator-release','github-topics-client-package','github-multioperation-integration'):
    for suffix,expected in (('', 'cpu_qualified_review_pending'),('-footprint', 'passed')):
        path=root/(task+suffix+'.json')
        if not path.is_file() or json.loads(path.read_text()).get('status')!=expected:
            raise SystemExit('Interface qualification blocked: '+str(path))
PYINTERFACE
        "$BC_PYTHON" -I scripts/prepare_rr_open_footprint.py \
            --interface-profile "$interface_profile" --planner-output-cap 6144 --measure \
            --model-lock "$output/worker-lock.json" --planner-lock "$output/planner-lock.json" \
            --output "$output/interface-footprint.json"
        "$BC_PYTHON" -I scripts/bc.py rr-open-footprint-manifest \
            --packet "$output/interface-footprint.json" --model-lock "$output/worker-lock.json" \
            --output "$output/interface-preflight-manifest.json"
    fi
    printf 'Prospective CPU preparation complete. Source/review/rights/GPU footprint and explicit cohort approval remain separate gates.\n'
    exit 0
fi
if "$v2"; then
    if "$track_f"; then printf 'Choose v2 controls or legacy Track F, not both.\n' >&2; exit 2; fi
    [[ "$pool_count" =~ ^[2-8]$ ]] || { printf 'Pool must be 2..8.\n' >&2; exit 2; }
    PYTHONPATH="$repo_root/src" "$BC_PYTHON" - <<'PYV2'
import unittest
from reporecourse.track_f_controls import PINS
from reporecourse.qualification import runtime_versions
actual=runtime_versions()
if any(actual.get(k)!=v for k,v in PINS.items()):raise SystemExit('Pinned CPU dependencies required')
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests',pattern='test_reporecourse_v2.py'))
if not r.wasSuccessful() or r.skipped:raise SystemExit('v2 controls must pass without skips')
PYV2
    extra=()
    grammar_version=v2
    if "$scoped"; then
        PYTHONPATH="$repo_root/src" "$BC_PYTHON" - <<'PYSCOPED'
import unittest
suite=unittest.TestSuite()
for pattern in ('test_reporecourse_scoped.py', 'test_reporecourse.py', 'test_reporecourse_track_f.py', 'test_sql_text.py'):
    suite.addTests(unittest.defaultTestLoader.discover('tests',pattern=pattern))
r=unittest.TextTestRunner(verbosity=2).run(suite)
if not r.wasSuccessful() or r.skipped:raise SystemExit('Scoped controls must pass without skips')
PYSCOPED
        extra=(--execution-contract plan_scoped_v1)
        grammar_version=scoped-v1
    fi
    "$BC_PYTHON" -I scripts/rr_v2.py qualify --sources "$sources" --output "$output/v2-fixtures.json" "${extra[@]}"
    "$BC_PYTHON" - "$output/v2-fixtures.json" <<'PYCHECK'
import json,sys
if json.load(open(sys.argv[1]))['status']!='passed':raise SystemExit('v2 fixture qualification failed')
PYCHECK
    if [[ -n "$model_lock" ]]; then
        for role in json plan; do
            "$BC_PYTHON" -I scripts/check_action_constraints.py --model-lock "$model_lock" --context-limit 16384 \
                --action-constraint "reporecourse-$role-$grammar_version-pool-$pool_count" \
                --output "$output/grammar-$role-pool-$pool_count.json" \
                --qualified-lock "$output/model-lock-$role-pool-$pool_count.json"
        done
    fi
    printf 'v2 CPU controls only; task review, B0, model competence and memory qualification remain pending.\n'
    exit 0
fi
if "$track_f"; then
    # Fail on relevant skips; a previous revision's approvals are insufficient.
    "$BC_PYTHON" - <<'PYTEST'
import sys, unittest
sys.path.insert(0, 'src')
from reporecourse.track_f_controls import PINS
from reporecourse.qualification import runtime_versions
actual = runtime_versions()
if any(actual.get(k) != v for k, v in PINS.items()):
    raise SystemExit(f"Pinned CPU qualification blocked: required={PINS}, actual={actual}")
suite = unittest.TestSuite()
for pattern in ('test_reporecourse.py', 'test_reporecourse_track_f.py', 'test_sql_text.py'):
    suite.addTests(unittest.defaultTestLoader.discover('tests', pattern=pattern))
result = unittest.TextTestRunner(verbosity=2).run(suite)
if not result.wasSuccessful() or result.skipped:
    raise SystemExit('Track F CPU qualification requires every relevant test to run and pass')
PYTEST
    "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" \
        --task jaffle-recorded-payments --track-f-controls --output "$output/jaffle-recorded-payments.json"
else
    for task in synthetic-stock synthetic-nullable jaffle-recorded-payments energy-generation-coverage github-topics-consumer; do
        "$BC_PYTHON" -I scripts/bc.py rr-qualify --sources "$sources" --task "$task" --output "$output/$task.json"
    done
fi
"$BC_PYTHON" -I scripts/check_sql_frontend.py --output "$output/compiler.json"
if [[ -n "$model_lock" ]]; then
    "$BC_PYTHON" -I scripts/check_action_constraints.py \
        --model-lock "$model_lock" --context-limit 16384 \
        --action-constraint reporecourse-json-v1 \
        --output "$output/grammar.json" --qualified-lock "$output/model-lock.json"
fi
printf 'CPU qualification reports: %s\n' "$output"
