#!/usr/bin/env python3
"""Read-only reconciliation of job 1115702; never authorizes a replacement."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from bc_phase2.model import digest
from bc_phase2.joint_schema import require
from beyond_consensus.experiments.snapshot import verify_snapshot

SCOPE = 'ec01b31b5b2f2beb379571cf4e641d57fd905c1cdf5cbac5dbc8693801d96364'
JOB = '1115702'
KEY = 'composite-neutral-joint-v3-ab'


def failed_accounting(text):
    rows = [line.split('|') for line in text.splitlines() if line.strip()]
    top = [r for r in rows if r[0] == JOB + '_0']
    require(len(top) == 1 and top[0][1:3] == ['FAILED', '1:0'],
            'exact terminal array-task failure missing')
    require(all(r[0] == JOB + '_0' or r[0].startswith(JOB + '_0.') for r in rows),
            'unexpected accounting job')


def inspect(output, registry, accounting):
    files = {}

    def read(path, as_json=True):
        require(not path.is_symlink(), 'symlink evidence forbidden')
        raw = path.read_bytes()
        files[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw) if as_json else raw.decode('utf8')

    state = read(registry)
    require(not state.get('uncertain_submission'), 'uncertain submission')
    record = state.get('composite_math_attempts', {}).get(KEY, {})
    require(record.get('job_id') == JOB and record.get('scope_digest') == SCOPE
            and record.get('state') == 'submitted_no_retry', 'original attempt binding')
    require(Path(record['output']).resolve() == output.resolve(), 'output binding')
    snapshot = Path(record['snapshot'])
    marker = verify_snapshot(snapshot)
    manifest = read(output / 'manifest.json')
    require(manifest == read(snapshot / 'resolved/manifest.json')
            and marker['manifest_hash'] == digest(manifest), 'snapshot manifest binding')
    release = manifest['release']
    require(release['release_digest'] == record['release_digest']
            == digest({k: v for k, v in release.items() if k != 'release_digest'}),
            'release integrity')
    require(release['manifest']['scope_digest'] == SCOPE
            == digest(release['manifest']['scope']), 'scope integrity')
    execution = output / 'execution'
    require(not execution.is_symlink() and
            {p.name for p in execution.iterdir()} ==
            {'startup.json', 'failure.json', 'recipe-state.json'},
            'unexpected execution evidence; inference cannot be excluded')
    startup = read(execution / 'startup.json')
    require(startup == dict(scope_digest=SCOPE, state='started_no_retry'), 'startup binding')
    failure = read(execution / 'failure.json')
    require(failure['error_type'] == 'AcceleratorError' and
            'CUDA-capable device(s) is/are busy or unavailable' in failure['error'] and
            failure['totals'] is None and failure['retry_allowed'] is False, 'failure mismatch')
    slots = read(execution / 'recipe-state.json')
    schedule = release['manifest']['scope']['blueprint']['schedule']
    require(slots['status'] == 'halted' and set(slots['slots']) == set(schedule)
            and all(v == 'unrun' for v in slots['slots'].values()), 'attempted or missing slots')
    stderr = read(output / 'logs' / (JOB + '_0.err'), False)
    require("model.to(torch.device('cuda:0'))" in stderr and
            'CUDA-capable device(s) is/are busy or unavailable' in stderr,
            'expected placement traceback absent')
    code = read(snapshot / 'src/bc_phase2/composite_math_launch.py', False)
    require('sources=p.source_records(s);transport=p.open_transport(v)' in code and
            code.index('sources=p.source_records(s);transport=p.open_transport(v)') <
            code.index('journal=implementation.Journal('), 'journal order changed')
    blockers = []
    try:
        require(accounting['returncode'] == 0, 'accounting unavailable')
        failed_accounting(accounting['stdout'])
    except Exception as exc:
        blockers.append(str(exc))
    require(hashlib.sha256(registry.read_bytes()).hexdigest() == files[str(registry)],
            'registry changed during inspection')
    return dict(schema='composite-joint-placement-reconciliation-v1',
                status='blocked' if blockers else 'verified_for_replacement_review',
                scope_digest=SCOPE, failed_attempt=record, input_hashes=files,
                snapshot_inventory_verified=True, no_request_journal=True,
                inference_dispatch_observed=False, startup_resources={k: failure[k] for k in
                ('cpu_seconds', 'wall_seconds')}, scheduler=accounting, blockers=blockers,
                registry_changed=False, replacement_authorized=False,
                replacement_submitted=False, execution_allowed=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True, type=Path)
    p.add_argument('--registry', type=Path, default=Path.home() / '.local/state/beyond-consensus/registry.json')
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    require(not a.output.exists(), 'preserve existing report')
    try:
        c = subprocess.run(['sacct', '--noheader', '--parsable2', '-j', JOB,
                            '--format=JobID,State,ExitCode,Elapsed,NodeList,ReqTRES,AllocTRES'],
                           capture_output=True, text=True, timeout=30)
        accounting = dict(returncode=c.returncode, stdout=c.stdout, stderr=c.stderr)
    except (OSError, subprocess.TimeoutExpired) as exc:
        accounting = dict(returncode=None, stdout='', stderr=str(exc))
    result = inspect(a.run, a.registry, accounting)
    with a.output.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
