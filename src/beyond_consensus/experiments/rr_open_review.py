"""Read-only footprint-v3 file audit. No historical code, model or SQL execution."""
import json
import re
from pathlib import Path

from ..util import BCError, digest, file_hash, read_json
from .snapshot import verify_snapshot
from . import rr_open_footprint as footprint


def require(ok, message):
    if not ok:
        raise BCError(message)


def unique(items):
    out = {}
    for key, value in items:
        require(key not in out, 'Duplicate action key')
        out[key] = value
    return out


def check_report(manifest, report, worker):
    footprint.validate(manifest)
    require(manifest['schema'] == footprint.SCHEMA_V3, 'Planner-6144 v3 evidence required')
    packet = manifest['cpu_packet']; profile = packet['base_manifest']
    runtime = report['runtime']; planner = profile['planner_lock']
    require(report['schema'] == 'rr-open-footprint-report-v3' and
            report['protocol'] == footprint.PROTOCOL_V3 and
            report['status'] == 'passed_observed_cases' and report['command_failed'] is False,
            'Footprint did not pass')
    require(report['experiment_id'] == manifest['experiment_id'] and
            report['manifest_hash'] == digest(manifest) and
            report['packet_id'] == packet['packet_id'] and
            report['proposal_id'] == packet['proposal']['proposal_id'] and
            report['source_revision'] == manifest['source_revision'], 'Footprint bindings changed')
    require(all(report.get(k) is False for k in (*footprint.FLAGS, 'sql_executed', 'task_inputs_used')) and
            report['model_executed'] is True and report['model_instances'] == 1 and report['pool'] == 7,
            'Footprint scope changed')
    require(report['role_output_caps'] == {'json': 2048, 'plan': 6144}, 'Role caps changed')
    require(digest(worker) == manifest['model_lock_sha256'] == runtime['model_lock_hash'] and
            runtime['settings'] == profile['model'], 'Worker runtime binding changed')
    for key in ('checkpoint', 'revision', 'tokenizer_revision', 'metadata_hashes', 'weight_hashes', 'model_path', 'tokenizer_path'):
        require(bool(worker.get(key)) and worker[key] == planner[key], 'Role model mismatch: '+key)
    require(runtime['checkpoint_revision'] == worker['revision'] and runtime['tokenizer_revision'] == worker['tokenizer_revision'], 'Runtime revision mismatch')
    for role, lock in (('json', worker), ('plan', planner)):
        q = lock['decoder_qualification']
        require(q['status'] == 'passed' and q['model_executed'] is False and q['sql_executed'] is False and
                q['context_limit'] == 16384 and q.get('output_cap') == (2048 if role == 'json' else 6144) and q['contract']['mode'] == footprint.base.grammar(profile, role), 'Role qualification mismatch')
        require(report['qualification_keys'][role] == q['qualification_key'] == packet['measurement_runtime']['qualification_keys'][role], 'Role key mismatch')
        require(all(q['packages'].get(k) == v for k, v in runtime['dependencies'].items()), 'Package mismatch')
        require(all(q['effective_generation_tokens'][k] == runtime['generation_tokens'][k] for k in ('eos_token_id', 'pad_token_id')) and
                q['thinking_template']['template_hash'] == runtime['chat_template']['template_hash'], 'Generation template mismatch')
    require(runtime['qualification_key'] == report['qualification_keys']['json'], 'Runtime grammar mismatch')
    require(len(report['calls']) == len(packet['cases']) == 5, 'Incomplete cases')
    tokens = 0
    for row, case in zip(report['calls'], packet['cases']):
        g = row['generation']; d = g['diagnostics']; measured = case['measurement']; cap = report['role_output_caps'][case['role']]
        require(row['id'] == case['id'] and row['passed'] is True and row['dispatched'] is True and
                row['status'] == 'passed' and row['uncertain_tokens'] == 0, 'Failed case')
        require(row['input_tokens'] == measured['input_tokens'] == d['rendered_input_tokens'] and
                measured['rendered_input_ids_hash'] == d['rendered_input_ids_hash'], 'Rendered input changed')
        require(row['output_cap'] == cap and row['output_tokens'] == g['output_tokens'] and
                type(g['output_tokens']) is int and 0 < g['output_tokens'] <= cap and row['input_tokens']+cap <= 16384, 'Token accounting mismatch')
        require(d['finish_reason'] == 'eos' and d['constraint_complete'] is True and
                json.loads(g['text'], object_pairs_hook=unique) == case['expected'], 'Incomplete or different response')
        q = (worker if case['role'] == 'json' else planner)['decoder_qualification']
        require(d['action_constraint'] == q['contract'] and d['eos_token_id'] == runtime['generation_tokens']['eos_token_id'] and
                d['last_generated_token_id'] in d['eos_token_id'], 'Decoder contract mismatch')
        mem = row['memory']
        require(0 < mem['peak_allocated_bytes'] <= mem['peak_reserved_bytes'] <= mem['total_bytes'] == runtime['vram_total_bytes'], 'Invalid memory observation')
        tokens += row['input_tokens']+g['output_tokens']
    require(tokens == report['actual_tokens'] and report['uncertain_tokens'] == 0, 'Total usage mismatch')


def inspect(run, snapshots):
    run = Path(run).resolve(); snapshots = Path(snapshots).resolve()
    manifest = read_json(run/'manifest.json'); report = read_json(run/'preflight.json')
    sid = report['runtime']['snapshot_id']
    require(isinstance(sid, str) and re.fullmatch('[0-9a-f]{64}', sid), 'Unsafe snapshot ID')
    snapshot = snapshots/sid
    require(not snapshot.is_symlink(), 'Snapshot symlink rejected')
    marker = verify_snapshot(snapshot)
    worker = read_json(snapshot/'resolved/model-lock.json')
    require(read_json(snapshot/'resolved/manifest.json') == manifest and marker['manifest_hash'] == digest(manifest), 'Snapshot manifest mismatch')
    require(marker['source_revision'] == manifest['source_revision'], 'Snapshot source mismatch')
    require(report['runtime']['import_path'] == str(snapshot/'src/beyond_consensus/models/transformers_backend.py'), 'Backend import path differs from snapshot')
    require(marker['cluster_hash'] == digest(read_json(snapshot/'resolved/cluster.json')), 'Snapshot cluster mismatch')
    check_report(manifest, report, worker)
    files = [run/'manifest.json', run/'preflight.json', snapshot/'snapshot.json', snapshot/'resolved/model-lock.json', snapshot/'resolved/cluster.json']
    return dict(schema='rr-open-footprint-audit-v1', status='verified_internal_bindings_review_pending',
                run=str(run), snapshots=str(snapshots), experiment_id=manifest['experiment_id'],
                input_files={str(p): file_hash(p) for p in files}, snapshot_inventory_verified=True,
                scheduler_completion_verified=False, task_execution_allowed=False,
                model_executed=False, sql_executed=False, historical_scores_changed=False,
                limitation='File integrity is not independent authenticity or task approval.')
