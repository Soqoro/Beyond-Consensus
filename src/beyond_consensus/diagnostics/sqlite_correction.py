"""Read-only paired correction audit, no model/SQL execution or rescoring."""
from collections import Counter
from copy import deepcopy
import time

from ..experiments.manifest import validate_manifest
from ..evaluation.aggregate import aggregate
from ..util import BCError, read_json
from .competence import audit


def compare(generic_run, feedback_run):
    started = time.process_time()
    manifests = [read_json(root/'manifest.json') for root in (generic_run, feedback_run)]
    configs = [validate_manifest(m) for m in manifests]
    for cfg, mode in zip(configs, ('generic', 'sqlite-errors-v1')):
        if cfg.sqlite_fixture_suite != 'tool_correction_v1' or cfg.sqlite_error_feedback != mode:
            raise BCError('Expected generic and categorized correction runs in that order')
    normalized = []
    for m in manifests:
        c = deepcopy(m['config'])
        for key in ('name', 'development_profile', 'sqlite_error_feedback'):
            c.pop(key, None)
        normalized.append(c)
    if normalized[0] != normalized[1]:
        raise BCError('Correction configs differ beyond feedback and labels')
    for key in ('tasks', 'source_revision', 'data_regime', 'action_constraint', 'competence_interface_hashes'):
        if manifests[0].get(key) != manifests[1].get(key):
            raise BCError('Correction runs have unmatched ' + key)
    reports = []
    for root, manifest in zip((generic_run, feedback_run), manifests):
        summary = aggregate(manifest, root)  # Validate result provenance before reading diagnostics.
        details = audit(root)
        rows = []
        for row, episode in zip(details['tasks'], manifest['episodes']):
            state_path = root/'episodes'/episode['episode_id']/'checkpoint.json'
            state = read_json(state_path) if state_path.exists() else {}
            events = state.get('store', {}).get('events', [])
            seeds = [e for e in events if e['type'] == 'diagnostic_seed_action']
            rejected = [e for e in events if e['type'] == 'prohibited_or_malformed_action']
            categories = Counter(e.get('error_code', 'restricted_action_rejected') for e in rejected)
            seed_rejected = sum(e.get('diagnostic_seed') is True for e in rejected)
            rows.append({k: row.get(k) for k in ('task', 'status', 'success', 'model_calls',
                'ledger_total', 'ledger_residual', 'tool_rejections')} | {
                'supplied_draft_executions': len(seeds), 'supplied_draft_rejections': seed_rejected,
                'seed_action_hashes': [e['action_hash'] for e in seeds],
                'seed_matches_manifest': len(seeds)==1 and seeds[0]['action_hash']==next(
                    t['metadata']['initial_action_hash'] for t in manifest['tasks'] if t['id']==episode['task_id']),
                'rejection_categories': dict(categories),
                'model_action_rejections': len(rejected)-seed_rejected,
                'feedback_path_observed': any(e.get('diagnostic_seed') and
                    e.get('error_code') in ('function_arity', 'unresolved_column') for e in rejected)})
        reports.append({'experiment_id': manifest['experiment_id'],
            'feedback': manifest['config']['sqlite_error_feedback'], 'aggregate': summary, 'tasks': rows})
    paired = [{'task': a['task'], 'generic_success': a['success'], 'categorized_success': b['success'],
               'generic_work': a['ledger_total'], 'categorized_work': b['ledger_total'],
               'same_seed_action': bool(a['seed_action_hashes'] and a['seed_action_hashes']==b['seed_action_hashes'])}
              for a, b in zip(reports[0]['tasks'], reports[1]['tasks'])]
    complete = all(t['status']=='completed' and t['supplied_draft_executions']==1 and
                   t['supplied_draft_rejections']==1 and t['seed_matches_manifest'] for r in reports for t in r['tasks'])
    return {'schema': 'bc-sqlite-correction-comparison-v1', 'model_executed': False,
        'sql_executed': False, 'historical_scores_changed': False, 'matched_inputs': True,
        'complete_diagnostic': complete, 'conditions': reports, 'paired_tasks': paired,
        'analysis_cpu_seconds': time.process_time()-started,
        'interpretation': 'Two supplied-draft corrections, one synthetic source group; no native competence or recovery claim.'}
