"""Offline, sanitized competence audit. Never changes scores or worker feedback."""
from collections import Counter
from copy import deepcopy
import json
import math
import time
from pathlib import Path
from ..util import BCError, digest, file_hash, read_json

INTERFACE_FILES = ('src/beyond_consensus/agents/worker.py',
    'src/beyond_consensus/models/action_schema.py', 'src/beyond_consensus/models/constrained.py',
    'src/beyond_consensus/runtime/data_domain.py', 'src/beyond_consensus/runtime/sqlite_executor.py',
    'src/beyond_consensus/tasks/sqlite_compatibility.py')
ALLOWED_MODEL = ('checkpoint', 'revision', 'tokenizer_revision')


def fingerprints(root):
    return {name: file_hash(root/name) for name in INTERFACE_FILES}


def compatibility(candidate, control=None, control_root=None):
    from ..experiments.manifest import validate_manifest
    validate_manifest(candidate)
    report = {'schema': 'bc-competence-compatibility-v1', 'candidate': candidate['experiment_id'],
        'status': 'unmatched_competence_screen', 'control_raw_available': control is not None,
        'allowed_model_differences': list(ALLOWED_MODEL),
        'interpretation': 'Practical checkpoint comparison, not causal parameter-size evidence; surrogate is not FLOPs.',
        'differences': [], 'invariants': {k: {'candidate':digest(candidate.get(k)), 'control':None, 'equal':None}
            for k in ('tasks','action_constraint','data_regime','config','competence_interface_hashes')}}
    if control is None:
        report['differences'] = ['Resolved historical 4B manifest unavailable; seed 0 is the explicit new condition, not inferred history']
        return report
    validate_manifest(control)
    report['control'] = control['experiment_id']
    for key in ('tasks', 'action_constraint', 'data_regime'):
        a, b = digest(candidate.get(key)), digest(control.get(key))
        report['invariants'][key] = {'candidate': a, 'control': b, 'equal': a == b}
    report['invariants'].pop('config',None)
    report['invariants'].pop('competence_interface_hashes',None)
    configs = []
    for manifest in (candidate, control):
        c = deepcopy(manifest['config'])
        for key in ('name', 'development_profile'): c.pop(key, None)
        for key in ALLOWED_MODEL: c['model'].pop(key, None)
        configs.append(c)
    report['invariants']['execution_config'] = {'candidate': digest(configs[0]), 'control': digest(configs[1]),
                                              'equal': configs[0] == configs[1]}
    a = candidate.get('competence_interface_hashes')
    b = control.get('competence_interface_hashes')
    if control_root:
        from ..experiments.snapshot import verify_snapshot
        marker = verify_snapshot(control_root)
        if marker['source_revision'] != control['source_revision']:
            raise BCError('Historical snapshot does not bind the supplied control manifest')
        b = fingerprints(control_root)
    report['invariants']['interface_files'] = {'candidate': a, 'control': b, 'equal': bool(a and b and a == b)}
    report['differences'] = [k for k,v in report['invariants'].items() if not v['equal']]
    report['source_revision_equal'] = candidate['source_revision'] == control['source_revision']
    # New backend instrumentation must not be silently described as model-only.
    report['status'] = ('matched_recorded_fields_source_review_required' if not report['differences']
                        else 'unmatched_competence_screen')
    report['backend_review_required'] = not report['source_revision_equal']
    return report


def output_diagnostics(probe, content):
    from ..tasks.sqlite_compatibility import expected
    columns, rows = expected(probe)
    if not content:
        return {'values_multiset_match': None, 'ordered_values_match': None, 'column_contract_match': None}
    actual_rows = content.get('rows')
    actual_columns = [c.get('as', c.get('expr', {}).get('column'))
                      for c in content.get('select', {}).get('columns', [])]
    return {'values_multiset_match': None if actual_rows is None else
            Counter(map(digest, actual_rows)) == Counter(map(digest, rows)),
            'ordered_values_match': None if actual_rows is None else actual_rows == rows,
            'column_contract_match': actual_columns == columns,
            'basis': 'stored rows and declared projection; absent view rows unknown; no SQL rerun'}


def operation_counts(value):
    result = Counter()
    def visit(v):
        if isinstance(v, dict):
            for key, item in v.items():
                if key == 'call' and isinstance(item, dict): result['call:'+str(item.get('name'))] += 1
                if key == 'binary' and isinstance(item, list) and item: result['binary:'+str(item[0])] += 1
                if key == 'joins' and isinstance(item, list): result['joins'] += len(item)
                visit(item)
        elif isinstance(v, list):
            for item in v: visit(item)
    visit(value)
    return dict(result)


def audit(run, control_run=None):
    started = time.process_time()
    manifest = read_json(run/'manifest.json')
    tasks = {t['id']: t for t in manifest['tasks']}
    rows = []
    for episode in manifest['episodes']:
        path = run/'episodes'/episode['episode_id']
        if not (path/'result.json').exists():
            rows.append({'task': episode['task_id'], 'status': 'missing', 'success': None}); continue
        r = read_json(path/'result.json')
        state = read_json(path/'checkpoint.json') if (path/'checkpoint.json').exists() else {}
        entries = r['costs']['entries']
        total = sum(e['work'] for e in entries)
        if abs(total-r['costs']['spent']) > 1e-8:
            raise BCError('Ledger total does not reconcile; preserve run for investigation')
        decoder_reconciliation = []
        charge = manifest['config']['budget']['tool_charge']
        for entry in entries:
            if entry['kind'] != 'constrained_decoding': continue
            seconds = entry.get('cpu_seconds')
            expected = math.ceil(seconds)*charge if seconds is not None else None
            reserved, released = entry.get('reserved_work'), entry.get('released_work')
            if expected is not None and expected != entry['work']:
                raise BCError('Measured decoder CPU charge does not reconcile')
            if reserved is not None and released is not None and reserved-released != entry['work']:
                raise BCError('Decoder reservation/release does not reconcile')
            decoder_reconciliation.append({'expected_measured_work': expected, 'actual_work': entry['work'],
                'reserved_work': reserved, 'released_work': released,
                'retained_unknown_work': entry['work'] if entry.get('uncertain') else 0})
        events = state.get('store', {}).get('events', [])
        generations = [e for e in events if e['type'] == 'generation_metadata']
        calls = []
        for e in generations:
            d = e.get('details', {})
            calls.append({k: e.get(k) for k in ('input_tokens', 'output_tokens', 'reasoning_tokens')} | {
                k: d.get(k) for k in ('constraint_complete', 'constraint_mask_calls', 'constraint_cpu_seconds',
                    'finish_reason', 'rendered_input_tokens', 'generation_wall_seconds', 'prefill_seconds',
                    'peak_allocated_bytes', 'peak_reserved_bytes', 'observed_cache_sequence_length')})
        actions = []
        for context in state.get('store', {}).get('contexts', {}).values():
            for message in context.get('messages', []):
                if message.get('role') != 'assistant': continue
                text = message.get('content', '')
                try:
                    action = json.loads(text)
                    tree = action.get('select_sql', {}) if isinstance(action, dict) else {}
                    joins = tree.get('joins', []) if isinstance(tree, dict) else []
                    aliases = [j.get('source', {}).get('as') for j in joins if isinstance(j, dict)]
                    aliases = [a for a in aliases if isinstance(a, str)]
                    actions.append({'json_parsed': True, 'operations': operation_counts(tree),
                                    'duplicate_join_aliases': len(aliases)-len(set(aliases))})
                except (ValueError, TypeError):
                    actions.append({'json_parsed': False, 'text_hash': digest(text),
                                    'characters': len(text), 'retained_in_history': True})
        selected = state.get('selected', {})
        artifacts = state.get('store', {}).get('artifacts', {})
        contents = [artifacts[v]['content'] for v in selected.values() if v in artifacts]
        task = tasks[episode['task_id']]
        diagnostics = (output_diagnostics(task['metadata']['probe'], contents[0] if contents else None)
                       if task['metadata'].get('probe') else {'status': 'native private diagnostics not exported'})
        runtime = r.get('provenance', {}).get('backend_runtime', {})
        rows.append({'task': r['task_id'], 'status': r['status'], 'success': r['success'],
            'public_integration': r['metrics'].get('joint_public_integration'),
            'required_artifacts': len(task['required_outputs']), 'selected_artifacts': len(selected),
            'tool_rejections': r['metrics'].get('tool_rejections'),
            'action_observations': actions, 'assistant_action_attempts': len(actions),
            'rejection_categories': {'restricted_contract_unspecified': sum(e['type'] == 'prohibited_or_malformed_action' for e in events)},
            'offline_diagnostics': diagnostics, 'submitted_operations': [operation_counts(c) for c in contents],
            'generation_calls': calls, 'model_calls': sum(e.get('model_calls', 0) for e in entries),
            'ledger_total': total, 'ledger_residual': total-r['costs']['spent'],
            'decoder_reconciliation': decoder_reconciliation,
            'ledger_rows': [{k: e.get(k) for k in ('entry_id', 'stage', 'kind', 'work', 'reserved_work',
                'released_work', 'uncertain', 'input_tokens', 'output_tokens', 'reasoning_tokens',
                'device_seconds', 'cpu_seconds', 'failed', 'reserved_output_tokens')} for e in entries],
            'static_decoder_setup_cpu_seconds': runtime.get('action_constraint', {}).get('static_setup_cpu_seconds'),
            'input_tokens': sum(e.get('input_tokens',0) for e in entries if e['kind']=='model'),
            'output_tokens': None if any(e.get('output_tokens') is None for e in entries if e['kind']=='model') else sum(e.get('output_tokens',0) for e in entries if e['kind']=='model'),
            'history_semantics': 'Unclosed capped text remains assistant history; no delimiter insertion or truncation',
            'retry_count': sum(e['type']=='prohibited_or_malformed_action' for e in events),
            'prefill_seconds': None})
    passed = sum(r.get('success') is True for r in rows)
    comparison = []
    if control_run:
        old = audit(control_run)
        lookup = {r['task']:r for r in old['tasks']}
        compatible = compatibility(manifest, read_json(control_run/'manifest.json'))
        comparison = [{'task': r['task'], 'compatibility_status': compatible['status'], 'candidate_success': r.get('success'),
                       'control_success': lookup.get(r['task'], {}).get('success')} for r in rows]
    if not control_run:
        reported = {'sqlite-tools-aggregate':False, 'sqlite-tools-join':False, 'sqlite-tools-view':True, 'sqlite-tools-case':False}
        comparison = [{'task':r['task'], 'candidate_success':r.get('success'),
            'reported_4b_success':reported.get(r['task']), 'control_raw_available':False,
            'compatibility_status':'unmatched_competence_screen'} for r in rows]
    return {'schema': 'bc-competence-audit-v1', 'model_executed': False, 'sql_executed': False,
        'experiment_id': manifest['experiment_id'], 'planned': manifest['planned_episodes'], 'successes': passed,
        'tasks': rows, 'raw_control_comparison': comparison,
        'historical_4b_evidence': 'User-reported aggregate false, join false, view true, case false; raw evidence required for matching',
        'decision': ('native_feasibility_review_no_automatic_expansion' if manifest['config']['task_kind']=='sqlite_native' else
                     'eligible_for_user_review_and_reference_renewal' if passed==4 and len(rows)==4 else
                     'inspect_remaining_failure' if passed==3 and len(rows)==4 else 'stop_expansion_review_errors'),
        'analysis_cpu_seconds': time.process_time()-started,
        'static_setup_accounting': 'Separate once-per-backend setup; not added to episode tokens or charged twice',
        'native_comparison': 'Old 4B solar interface is unmatched; native results are feasibility only'}
