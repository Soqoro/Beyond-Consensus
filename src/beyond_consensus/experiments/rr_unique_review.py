"""Read-only normal-mode evidence audit; never runs historical code or a model."""
import math
from pathlib import Path
import re

from ..util import BCError, digest, file_hash
from ..models.competence import require_qualification
from . import rr_unique_preflight as probe
from .rr_open_clean import load_control_record as load
from .snapshot import verify_snapshot


def require(ok, message):
    if not ok:
        raise BCError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def check_report(manifest, report, lock):
    probe.validate(manifest)
    probe.normal_gate(manifest.get('diagnostic_evidence'), manifest.get('normal_approval'),
        dict(source_revision=manifest['source_revision'],
             model_lock_sha256=manifest['model_lock_sha256'], controls_hash=digest(manifest['controls'])))
    require(report.get('schema') == 'rr-unique-preflight-report-v1' and
        report.get('protocol') == probe.PROTOCOL and report.get('status') == 'passed_observed_cases' and
        report.get('command_failed') is False, 'Normal qualification did not pass')
    require(report.get('experiment_id') == manifest['experiment_id'] and
        report.get('manifest_hash') == digest(manifest) and
        report.get('source_revision') == manifest['source_revision'], 'Normal report provenance changed')
    require(all(report.get(k) is False for k in ('task_inputs_used', 'sql_executed',
        'task_execution_allowed', 'worst_case_fit_established', 'task_competence_measured')) and
        report.get('model_executed') is True and report.get('model_instances') == 1 and
        report.get('maximum_calls') == 3, 'Normal qualification scope changed')
    runtime = report['runtime']; q = lock['decoder_qualification']
    require(digest(lock) == manifest['model_lock_sha256'] == runtime['model_lock_hash'] and
        runtime['settings'] == manifest['model'], 'Normal worker lock or settings changed')
    require(q.get('status') == 'passed' and q.get('model_executed') is False and
        q.get('sql_executed') is False and q.get('context_limit') == 16384 and
        q.get('output_cap') == 2048 and q['contract']['mode'] == probe.MODE and
        runtime['qualification_key'] == q['qualification_key'], 'Normal CPU qualification mismatch')
    require(runtime['checkpoint_revision'] == lock['revision'] and
        runtime['tokenizer_revision'] == lock['tokenizer_revision'], 'Normal model revision changed')
    require(bool(runtime['dependencies']) and all(q['packages'].get(k) == v
        for k, v in runtime['dependencies'].items()), 'Normal runtime dependencies changed')
    require(all(q['effective_generation_tokens'][k] == runtime['generation_tokens'][k]
        for k in ('eos_token_id', 'pad_token_id')) and
        q['thinking_template']['template_hash'] == runtime['chat_template']['template_hash'],
        'Normal generation template changed')
    rows = report['calls']
    require(len(rows) == 3, 'Incomplete normal qualification')
    total = 0
    for index, (row, case) in enumerate(zip(rows, manifest['cases'])):
        g = row['generation']; d = g['diagnostics']; r = row['resources']; pre = row['pre_dispatch']
        require(row['id'] == case['id'] and row['call_order'] == index and row['passed'] is True and
            row['dispatched'] is True and row['status'] == 'passed' and row['strict_parser_valid'] is True and
            row['accelerator_status'] == 'no_exception_observed' and not row.get('error_type') and
            not row.get('failure_stage') and not row.get('accounting_error'), 'Failed normal case')
        inp = row['input_tokens']; out = g['output_tokens']
        require(type(inp) is int and inp > 0 and type(out) is int and 0 < out <= 2048 and
            inp + 2048 <= 16384 and row['output_cap'] == 2048 and d['rendered_input_tokens'] == inp,
            'Normal case token bounds changed')
        require(not case['long_context'] or 14080 <= inp <= 14336, 'Normal long-context band changed')
        require(g['reasoning_tokens'] is None or
            (type(g['reasoning_tokens']) is int and 0 <= g['reasoning_tokens'] <= out), 'Reasoning usage changed')
        require(d['finish_reason'] == 'eos' and d['constraint_complete'] is True and
            d['action_constraint'] == q['contract'] and
            d['eos_token_id'] == runtime['generation_tokens']['eos_token_id'] and
            d['last_generated_token_id'] in d['eos_token_id'] and
            number(d['constraint_cpu_seconds']) and d['constraint_cpu_seconds'] <= 30,
            'Normal decoder completion changed')
        require(isinstance(g.get('text_sha256'), str) and re.fullmatch('[0-9a-f]{64}', g['text_sha256']) and
            type(g.get('text_characters')) is int and g['text_characters'] > 0, 'Missing response observation')
        require(pre['settings'] == manifest['model'] and pre['runtime'] == runtime and
            pre['output_cap'] == 2048 and pre['seed'] == 0 and pre['role'] == 'worker' and
            pre['grammar_mode'] == probe.MODE and pre['guard_enabled'] is True and pre['call_order'] == index and
            pre['prompt_hash'] == row['prompt_hash'], 'Normal pre-dispatch binding changed')
        reservation = pre['reservation']
        require(reservation['input_tokens'] == inp and reservation['output_cap'] == 2048 and
            reservation['total_tokens'] == inp + 2048, 'Normal admission reservation changed')
        require(r['token_cap'] == 16384 and r['cpu_cap'] == 1200 and
            all(r[k] == 0 for k in ('uncertain_tokens', 'reserved_tokens', 'uncertain_cpu', 'cpu_reserved')) and
            r['actual_tokens'] == inp + out and r['remaining_tokens'] == 16384 - inp - out and
            number(r['cpu_cap_debit']) and r['cpu_cap_debit'] <= 1200, 'Normal resource accounting changed')
        events = r['events']; usage = [e for e in events if e['kind'] == 'model_usage']
        admissions = [e for e in events if e['kind'] == 'reservation']
        cpu = [e for e in events if e['kind'] == 'cpu']
        require(len(usage) == len(admissions) == len(cpu) == 1 and
            usage[0]['input_tokens'] == inp and usage[0]['output_tokens'] == out and
            usage[0]['reasoning_tokens'] == g['reasoning_tokens'] and usage[0]['released'] == 2048 - out and
            admissions[0] == dict(kind='reservation', id=reservation['id'], input=inp, output_cap=2048) and
            not any(e['kind'] in ('uncertain_interruption', 'admission_failure') for e in events),
            'Normal event ledger changed')
        require(cpu[0]['usage_uncertain'] is False and number(cpu[0]['actual_cpu_seconds']) and
            cpu[0]['cap_debit'] == cpu[0]['actual_cpu_seconds'] == r['cpu_cap_debit'] and
            cpu[0]['decoder_cpu_seconds'] == d['constraint_cpu_seconds'] and
            d['constraint_cpu_seconds'] <= r['cpu_cap_debit'], 'Normal CPU ledger changed')
        for name in ('memory_before', 'memory_after'):
            mem = row[name]
            require(0 < mem['peak_allocated_bytes'] <= mem['peak_reserved_bytes'] <=
                mem['total_bytes'] == runtime['vram_total_bytes'], 'Normal memory observation changed')
        total += inp + out
    require(report['actual_tokens'] == total and report['uncertain_tokens'] == 0,
        'Normal total usage mismatch')


def inspect(run, snapshots, current_root):
    run = Path(run).resolve(); snapshots = Path(snapshots).resolve(); current_root = Path(current_root).resolve()
    manifest = load(run/'manifest.json'); report = load(run/'preflight.json')
    sid = report['runtime']['snapshot_id']
    require(isinstance(sid, str) and re.fullmatch('[0-9a-f]{64}', sid), 'Unsafe snapshot ID')
    snapshot = snapshots/sid
    require(not snapshot.is_symlink(), 'Snapshot symlink rejected')
    marker = verify_snapshot(snapshot)
    lock = load(snapshot/'resolved/model-lock.json')
    require(load(snapshot/'resolved/manifest.json') == manifest and
        marker['manifest_hash'] == digest(manifest) and marker['source_revision'] == manifest['source_revision'],
        'Normal snapshot manifest mismatch')
    require(marker['cluster_hash'] == digest(load(snapshot/'resolved/cluster.json')),
        'Normal snapshot cluster mismatch')
    require(report['runtime']['import_path'] == str(snapshot/'src/beyond_consensus/models/transformers_backend.py'),
        'Normal backend import path mismatch')
    check_report(manifest, report, lock)
    # Compare the complete decoder/model package plus the executed probe. Changes
    # to an offline auditor do not force a new qualification. Never execute old code.
    prefixes = ('src/beyond_consensus/models/', 'src/reporecourse/', 'src/restricted_artifacts/')
    names = {str(p.relative_to(current_root)) for prefix in prefixes
        for p in (current_root/prefix).rglob('*.py')}
    names |= {n for n in marker['files'] if n.startswith(prefixes) and n.endswith('.py')}
    names |= {'src/beyond_consensus/config.py', 'src/reporecourse/action_schema.py',
        'src/reporecourse/resources.py', 'src/beyond_consensus/experiments/rr_unique_preflight.py',
        'scripts/check_action_constraints.py'}
    changed = sorted(n for n in names if not (current_root/n).is_file() or
        n not in marker['files'] or file_hash(current_root/n) != marker['files'][n])
    compatibility_errors = []
    if changed:compatibility_errors.append('qualification_implementation_changed')
    try:
        require_qualification(lock, lock['decoder_qualification']['packages'], 16384, probe.MODE, 2048)
    except BCError as exc:
        compatibility_errors.append(str(exc))
    paths = [run/'manifest.json', run/'preflight.json', snapshot/'snapshot.json',
        snapshot/'resolved/model-lock.json', snapshot/'resolved/cluster.json']
    return dict(schema='rr-unique-normal-audit-v1', status='verified_internal_bindings_review_pending',
        experiment_id=manifest['experiment_id'], run=str(run), snapshots=str(snapshots),
        input_files={str(p):file_hash(p) for p in paths}, snapshot_inventory_verified=True,
        current_compatibility=dict(status='compatible' if not compatibility_errors else 'blocked',
            changed_files=changed, errors=compatibility_errors, checked_root=str(current_root)),
        audit_implementation_hashes={name:file_hash(current_root/name) for name in (
            'src/beyond_consensus/experiments/rr_unique_review.py', 'scripts/audit_rr_unique_normal.py')},
        observed_calls=3, actual_tokens=report['actual_tokens'], uncertain_tokens=0,
        scheduler_completion_verified=False, model_executed=False, sql_executed=False,
        historical_scores_changed=False, task_execution_allowed=False, worst_case_fit_established=False,
        limitations=['File integrity is not independent authenticity or task approval.',
            'Saved normal responses contain hashes, not text; semantic validation is the frozen runtime observation.',
            'Launch blocking is rejected by the frozen runner; no independent environment trace was saved.',
            'Observed synthetic cases do not establish task competence or worst-case fit.'])
