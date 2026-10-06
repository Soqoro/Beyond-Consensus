"""Read-only historical preflight integrity checks; no GPU, SQL or old code execution."""
import json
import re
import time
from pathlib import Path

from ..util import BCError, digest, file_hash, read_json
from .rr_v2_preflight import PROTOCOL, STRESS_PROTOCOL, grammar, validate
from .snapshot import verify_snapshot


def require(condition, message):
    if not condition:
        raise BCError(message)


def inspect(run, snapshots, protocol):
    run, snapshots = Path(run), Path(snapshots)
    manifest = read_json(run / 'manifest.json')
    report = read_json(run / 'preflight.json')
    validate(manifest)
    require(manifest['protocol'] == protocol, 'Wrong probe protocol')
    runtime = report['runtime']
    snapshot_id = runtime['snapshot_id']
    require(isinstance(snapshot_id, str) and re.fullmatch(r'[0-9a-f]{64}', snapshot_id), 'Missing/unsafe snapshot ID')
    snapshot = snapshots / snapshot_id
    require(not snapshot.is_symlink(), 'Snapshot root must not be a symlink')
    marker = verify_snapshot(snapshot)
    resolved = snapshot / 'resolved'
    require(read_json(resolved / 'manifest.json') == manifest, 'Run/snapshot manifests differ')
    require(marker['manifest_hash'] == digest(manifest), 'Snapshot manifest hash mismatch')
    require(marker['source_revision'] == manifest['source_revision'] == report['source_revision'], 'Source binding mismatch')
    require(report['experiment_id'] == manifest['experiment_id'] and report['manifest_hash'] == digest(manifest), 'Report manifest binding mismatch')
    worker = read_json(resolved / 'model-lock.json')
    planner = manifest['planner_lock']
    require(digest(worker) == manifest['model_lock_sha256'] == runtime['model_lock_hash'], 'Worker lock binding mismatch')
    require(runtime['settings'] == manifest['model'], 'Runtime/model settings mismatch')
    for k in ('checkpoint', 'revision', 'tokenizer_revision', 'model_path', 'tokenizer_path', 'metadata_hashes', 'weight_hashes'):
        require(bool(worker.get(k)) and worker[k] == planner.get(k), 'Planner/worker model binding mismatch: '+k)
    require(worker['revision'] == runtime['checkpoint_revision'] == manifest['model']['revision'], 'Checkpoint revision mismatch')
    require(worker['tokenizer_revision'] == runtime['tokenizer_revision'] == manifest['model']['tokenizer_revision'], 'Tokenizer revision mismatch')
    for role, lock in (('json', worker), ('plan', planner)):
        q = lock['decoder_qualification']
        require(q['status'] == 'passed' and q['model_executed'] is False and q['sql_executed'] is False, 'Invalid historical grammar report')
        require(q['context_limit'] == 16384 and q['contract']['mode'] == grammar(manifest, role), 'Grammar scope mismatch')
        require(q['qualification_key'] == report['qualification_keys'][role], 'Grammar key mismatch')
        for name, version in runtime['dependencies'].items():
            require(q['packages'].get(name) == version, 'Runtime/grammar dependency mismatch: '+name)
    require(runtime['qualification_key'] == report['qualification_keys']['json'], 'Runtime grammar mismatch')
    require(runtime['generation_tokens']['eos_token_id'] == worker['decoder_qualification']['effective_generation_tokens']['eos_token_id'], 'EOS binding mismatch')
    require(runtime['generation_tokens']['pad_token_id'] == worker['decoder_qualification']['effective_generation_tokens']['pad_token_id'], 'Padding binding mismatch')
    require(runtime['chat_template']['template_hash'] == worker['decoder_qualification']['thinking_template']['template_hash'], 'Template binding mismatch')
    require(report['pool'] == manifest['pool'] and report['model_instances'] == 1, 'Pool/model count mismatch')
    require(report['model_executed'] is True and report['sql_executed'] is False
            and report['task_inputs_used'] is False and report['task_execution_allowed'] is False
            and report['worst_case_fit_established'] is False, 'Probe scope mismatch')
    stress = protocol == STRESS_PROTOCOL
    require(report['command_failed'] is False and report['status'] == ('passed_full_budget_geometry' if stress else 'passed_observed_sequence'), 'Probe did not pass')
    if stress:
        require(report['full_budget_geometry_passed'] is True and report['normal_decoding'] is False, 'Stress intervention missing')
    identities = [f'w{i}' for i in range(manifest['pool'])] + ['planner']
    require(len(report['calls']) == 2*len(identities), 'Incomplete call coverage')
    tokens = 0
    for index, row in enumerate(report['calls']):
        identity = identities[index % len(identities)]
        require(row['identity'] == identity and row['round'] == index // len(identities), 'Call sequence/identity mismatch')
        require(row['passed'] is True and not row.get('error_type') and row['uncertain_tokens'] == 0, 'Failed/uncertain call')
        g = row['generation']; d = g['diagnostics']
        require(row['output_tokens'] == g['output_tokens'] and row['input_tokens'] == d['rendered_input_tokens'], 'Per-call token mismatch')
        require(row['output_cap'] == 2048 and 0 < g['output_tokens'] <= 2048, 'Output cap mismatch')
        require(re.fullmatch(r'[0-9a-f]{64}', row['prompt_hash']) is not None, 'Missing prompt hash')
        if index >= len(identities):
            prior = report['calls'][index-len(identities)]
            require(prior['prompt_hash'] == row['prompt_hash'], 'Revisited history changed')
            require(prior['generation']['diagnostics']['rendered_input_ids_hash'] == d['rendered_input_ids_hash'], 'Revisited tokenized history changed')
        if stress:
            from ..models.rr_memory_stress import verified
            require(verified(d, g['output_tokens']) and d['stress_protocol'] == STRESS_PROTOCOL
                    and d['normal_decoder_applied'] is False, 'Full-budget geometry evidence mismatch')
        else:
            require(14080 <= row['input_tokens'] <= 14336, 'Long-input band mismatch')
            require(json.loads(g['text']) == {'tool': 'read_source', 'name': 'probe_'+identity}
                    and d['constraint_complete'] is True and d['finish_reason'] == 'eos', 'Normal response mismatch')
        memory = row['memory']
        require(0 < memory['peak_allocated_bytes'] <= memory['peak_reserved_bytes'] <= memory['total_bytes'], 'Invalid memory evidence')
        tokens += row['input_tokens'] + g['output_tokens']
    require(len({r["prompt_hash"] for r in report["calls"][:len(identities)]}) == len(identities), "Identity histories are not distinct")
    require(report['actual_tokens'] == tokens and report['uncertain_tokens'] == 0, 'Total accounting mismatch')
    files = [run/'manifest.json', run/'preflight.json', snapshot/'snapshot.json', resolved/'model-lock.json']
    fingerprints = {name: value for name, value in marker['files'].items()
                    if name.startswith(('src/', 'scripts/'))}
    return dict(experiment_id=manifest['experiment_id'], protocol=protocol,
        snapshot_id=snapshot_id, source_revision=manifest['source_revision'],
        actual_tokens=tokens, calls=len(report['calls']), hardware=runtime['hardware'],
        slurm_job_id=runtime.get('slurm_job_id'), slurm_array_task_id=runtime.get('slurm_array_task_id'),
        input_files={str(p): file_hash(p) for p in files}, snapshot_inventory_verified=True,
        # No hidden task or generated program data are exported.
        comparison_binding=dict(pool=manifest['pool'], model=manifest['model'],
            model_metadata=worker['metadata_hashes'], model_weights=worker['weight_hashes'],
            qualification_keys=report['qualification_keys'], dependencies=runtime['dependencies'],
            generation_tokens=runtime['generation_tokens'], hardware=runtime['hardware'],
            compute_capability=runtime['compute_capability'], torch_cuda=runtime['torch_cuda'],
            vram_total_bytes=runtime['vram_total_bytes']), implementation=fingerprints)


def audit(normal_run, stress_run, snapshots):
    start = time.process_time()
    evidence = []; errors = []
    for label, run, protocol in (('normal', normal_run, PROTOCOL), ('stress', stress_run, STRESS_PROTOCOL)):
        try:
            evidence.append(dict(role=label, **inspect(run, snapshots, protocol)))
        except (BCError, OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
            errors.append({'role': label, 'error': str(exc)})
    differences = []; changed_source_files = []
    if len(evidence) == 2:
        a, b = evidence
        differences = [key for key in a['comparison_binding'] if a['comparison_binding'][key] != b['comparison_binding'][key]]
        changed_source_files = sorted(k for k in a['implementation'].keys() | b['implementation'].keys()
                                     if a['implementation'].get(k) != b['implementation'].get(k))
    for row in evidence:
        row.pop('implementation')
    return dict(schema='rr-v2-preflight-provenance-audit-v1',
        status='failed' if errors else 'binding_mismatch' if differences else 'verified_internal_bindings_review_pending',
        model_executed=False, sql_executed=False, historical_scores_changed=False,
        task_execution_allowed=False, evidence=evidence, errors=errors,
        cross_run_binding_differences=differences, changed_source_files=changed_source_files,
        scheduler_completion_verified=False, historical_grammar_key_recomputed=False,
        limitations=['File integrity is not independent authenticity.',
            'Historical grammar keys are linked to frozen locks; not regenerated with current source or Python.',
            'Scheduler completion and changed source files require review.',
            'No task competence, B0 or campaign approval is conferred.'],
        analysis_cpu_seconds=time.process_time()-start)


def audit_normal(normal_run, snapshots):
    """Inspect one observed sequence; never substitute for paired stress evidence."""
    start = time.process_time()
    evidence = []; errors = []
    try:
        row = dict(role='normal', **inspect(normal_run, snapshots, PROTOCOL))
        row.pop('implementation')
        evidence.append(row)
    except (BCError, OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        errors.append({'role': 'normal', 'error': str(exc)})
    return dict(schema='rr-v2-preflight-single-audit-v1',
        status='failed' if errors else 'verified_internal_bindings_review_pending',
        model_executed=False, sql_executed=False, historical_scores_changed=False,
        task_execution_allowed=False, worst_case_fit_established=False,
        stress_evidence_verified=False, evidence=evidence, errors=errors,
        scheduler_completion_verified=False, historical_grammar_key_recomputed=False,
        limitations=['Observed normal sequence only; no paired full-budget stress evidence.',
            'File integrity is not independent authenticity.',
            'Historical grammar keys are linked to frozen locks, not regenerated.',
            'Scheduler completion requires separate review.',
            'No task competence, B0 or campaign approval is conferred.'],
        analysis_cpu_seconds=time.process_time()-start)
