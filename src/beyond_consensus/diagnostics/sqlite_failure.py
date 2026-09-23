"""Offline CPU replay only. No model, worker feedback, or historical score writes."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

from ..util import BCError, digest, file_hash, read_json
from ..runtime.sqlite_executor import DEFAULT_LIMITS, SQLRejected, _child, capabilities


def error_category(exc):
    # Never export SQLite messages: they may contain private identifiers/values.
    if isinstance(exc, SQLRejected):
        return 'structured_policy'
    text = str(exc).lower()
    for prefix, category in (
        ('no such column:', 'unresolved_column'), ('ambiguous column name:', 'ambiguous_column'),
        ('no such table:', 'unresolved_table'), ('no such function:', 'unresolved_function'),
        ('misuse of aggregate', 'aggregate_misuse'), ('aggregate functions are not allowed', 'aggregate_misuse'),
        ('wrong number of arguments', 'function_arity'), ('near ', 'sql_syntax')):
        if text.startswith(prefix):
            return category
    return 'sqlite_execution_error'


def probe(request):
    """Same restricted child, with offline-only fixed error categories."""
    try:
        return _child(request)
    except SQLRejected as exc:
        return {'status': 'prohibited_operation', 'category': error_category(exc)}
    except sqlite3.DatabaseError as exc:
        code = getattr(exc, 'sqlite_errorcode', None)
        status = ('execution_limit' if code in (sqlite3.SQLITE_INTERRUPT, sqlite3.SQLITE_NOMEM,
                  sqlite3.SQLITE_TOOBIG, sqlite3.SQLITE_FULL) else
                  'prohibited_operation' if code == sqlite3.SQLITE_AUTH else 'semantic_error')
        return {'status': status, 'category': error_category(exc)}
    except (MemoryError, OverflowError):
        return {'status': 'execution_limit', 'category': 'memory_or_value'}
    except Exception:
        return {'status': 'infrastructure_failed', 'category': 'executor_failure'}


def execute_probe(database, tables, views, queries, limits, source_hash):
    if set(limits) != set(DEFAULT_LIMITS) or any(type(v) is not int or v < 1 for v in limits.values()):
        raise BCError('Invalid recorded executor limits')
    request = dict(database=str(database), tables=tables, views=views, queries=queries,
                   limits=limits, source_hash=source_hash)
    raw = json.dumps(request, allow_nan=False)
    if len(raw.encode()) > 2097152 or len(queries) > 32:
        raise BCError('Replay request exceeds executor bounds')
    script = Path(__file__).resolve().parents[3]/'scripts/probe_sqlite_failure.py'
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='bc-replay-') as temporary:
        env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR') if k in os.environ}
        env.update(TMPDIR=temporary, TEMP=temporary, TMP=temporary)
        child = subprocess.Popen([sys.executable, '-I', '-S', str(script)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=temporary, env=env)
        try:
            out, _ = child.communicate(raw, timeout=limits['seconds'])
        except BaseException:
            child.kill()
            child.communicate()
            if sys.exc_info()[0] is not subprocess.TimeoutExpired:
                raise
            return dict(status='execution_limit', category='deadline', wall_seconds=time.monotonic()-start)
    try:
        result = json.loads(out) if child.returncode == 0 else {'status':'execution_limit' if child.returncode < 0 else 'infrastructure_failed', 'category':'executor_terminated'}
    except ValueError:
        result = {'status':'infrastructure_failed', 'category':'invalid_executor_response'}
    result['wall_seconds'] = time.monotonic()-start
    return result


class ReplayLedger:
    def __init__(self, charge, max_calls=40):
        self.charge, self.max_calls, self.entries = charge, max_calls, []

    def call(self, task, views, queries, label):
        from ..tasks.sqlite_tasks import verify_file
        if len(self.entries) >= self.max_calls:
            raise BCError('Offline replay call bound reached')
        harness = task.metadata['harness']
        database = verify_file(harness['database'])
        limits = harness['limits']
        entry = dict(index=len(self.entries), purpose=label,
                     work=self.charge*limits['cpu_seconds'], cpu_allowance_seconds=limits['cpu_seconds'])
        self.entries.append(entry)  # Charge even failed/unknown calls.
        result = execute_probe(database, harness['tables'], views, queries, limits, harness['database']['sha256'])
        entry.update({k:result.get(k) for k in ('status', 'category', 'steps', 'wall_seconds')})
        return result


def replay_task(task, state, result, ledger):
    from ..runtime.data_domain import DataDomain
    from ..runtime.provenance import ProvenanceStore
    from ..tasks.sqlite_tasks import compare_rows
    report = dict(task=task.id, historical_success=result['success'], failed_query_replays=[], checks=[])
    store = state['store']
    # This bounded audit supports the supplied single-worker trace. Refuse to
    # guess action/turn alignment after restoration or across multiple workers.
    messages = store.get('contexts', {}).get('w0', {}).get('messages', [])
    actions = [m.get('content','') for m in messages if m.get('role') == 'assistant']
    turn, failed_turns = 0, []
    for event in store.get('events', []):
        if event['type'] == 'generation_metadata':
            turn += 1
        if event['type'] == 'sql_execution' and event.get('stage') == 'primary' and event.get('status') == 'semantic_error':
            failed_turns.append(turn)
    if len(failed_turns) > 2:
        raise BCError('This audit admits at most two failed query replays per task')
    for index in failed_turns:
        row = {'generation':index}
        if len(actions) != turn:
            row['status'] = 'history_unavailable'
        else:
            try:
                action = json.loads(actions[index-1])
            except (ValueError, IndexError):
                action = {}
            if not isinstance(action, dict) or action.get('tool') != 'run_read_query' or action.get('permitted_artifact_versions') != {}:
                row['status'] = 'unsupported_action_or_bindings'
            else:
                replay = ledger.call(task, [], [action['select_sql']], 'failed_query')
                row.update({k:replay.get(k) for k in ('status','category')})
        report['failed_query_replays'].append(row)
    selected = state.get('selected', {})
    if set(selected) != set(task.required_outputs):
        report['comparison_status'] = 'missing_obligations'
        return report
    domain = DataDomain(SimpleNamespace(task=task, store=ProvenanceStore.restore(store)))
    views, queries, units = domain.bundle(selected)
    # Exact evaluator bundle semantics. Results stay private in process memory.
    bundle = ledger.call(task, views, queries, 'selected_bundle')
    if bundle['status'] != 'ok':
        report['comparison_status'] = bundle['status']
        return report
    outputs = {unit:out['rows'] for unit,out in zip(units,bundle['outputs'])}
    for unit_index, (unit, evaluation) in enumerate(task.metadata['evaluation'].items()):
        if not 1 <= len(evaluation['checks']) <= 8:
            raise BCError('This audit admits one to eight reviewed checks per obligation')
        for index, check in enumerate(evaluation['checks']):
            actual = ({'status':'ok','outputs':[{'rows':outputs[unit]}]} if check.get('submitted_report') else
                      ledger.call(task, views, [check['select']], 'candidate_check'))
            reference = ledger.call(task, [], [check['reference']], 'reference_check')
            row = dict(obligation_index=unit_index, check_index=index,
                       candidate_status=actual['status'], reference_status=reference['status'],
                       exact_match=None, native_comparison_match=None)
            if actual['status'] == reference['status'] == 'ok':
                a, b = actual['outputs'][0]['rows'], reference['outputs'][0]['rows']
                ordered = check.get('order', evaluation['conditions'].get('order', False))
                row.update(exact_match=compare_rows(a,b,ordered),
                           native_comparison_match=compare_rows(a,b,ordered,native=True))
            report['checks'].append(row)
    report['comparison_status'] = 'replayed_offline_not_rescored'
    return report



def candidate_content(task, state, artifact_id):
    """Admit only an explicitly named, unbound, historically executed query."""
    store = state['store']
    artifact = store.get('artifacts', {}).get(artifact_id)
    if (task.id != 'solar_2' or task.required_outputs != ('solar_2',) or
            not artifact or artifact.get('id') != artifact_id or
            artifact.get('unit') != 'solar_2' or artifact.get('author') != 'w0' or
            artifact.get('kind') != 'data_artifact' or
            not artifact.get('complete_provenance') or state.get('selected')):
        raise BCError('Candidate must be an unselected solar_2 query with complete recorded provenance')
    content = artifact['content']
    if (content.get('kind') != 'query' or content.get('bindings') != {} or
            not isinstance(content.get('select'), dict) or not isinstance(content.get('rows'), list) or
            content.get('execution_binding_hash') != digest([[], content['select']])):
        raise BCError('Candidate query execution binding mismatch or unsupported dependencies')
    events = store.get('events', [])
    if not any(e.get('type') == 'submit' and e.get('version') == artifact_id and
               e.get('unit') == 'solar_2' and e.get('author') == 'w0' for e in events):
        raise BCError('Candidate creation event missing')
    if not any(e.get('type') == 'sql_execution' and e.get('status') == 'ok' and
               e.get('stage') == 'primary' and e.get('views') == digest([]) and
               e.get('queries') == digest([content['select']]) for e in events):
        raise BCError('Matching historical successful execution missing')
    evaluation = task.metadata['evaluation']['solar_2']
    if not 1 <= len(evaluation['checks']) <= 8 or not all(
            c.get('submitted_report') is True for c in evaluation['checks']):
        raise BCError('Candidate audit requires reviewed submitted-report checks')
    return artifact, content, evaluation


def replay_candidate(task, state, result, ledger, artifact_id):
    from ..tasks.sqlite_tasks import compare_rows
    artifact, content, evaluation = candidate_content(task, state, artifact_id)
    actual = ledger.call(task, [], [content['select']], 'unsubmitted_candidate')
    report = dict(task=task.id, artifact_id=artifact_id, content_hash=digest(content),
        historical_success=result['success'], historical_artifact_valid=artifact['valid'],
        candidate_promoted=False, comparison_status='offline_unsubmitted_candidate', checks=[],
        candidate_status=actual['status'], recorded_rows_match=None)
    if actual['status'] != 'ok':
        return report
    rows = actual['outputs'][0]['rows']
    report['recorded_rows_match'] = rows == content['rows']
    if not report['recorded_rows_match']:
        report['comparison_status'] = 'historical_rows_mismatch'
        return report
    for index, check in enumerate(evaluation['checks']):
        reference = ledger.call(task, [], [check['reference']], 'candidate_reference_check')
        row = dict(check_index=index, reference_status=reference['status'],
                   exact_match=None, native_comparison_match=None)
        if reference['status'] == 'ok':
            expected = reference['outputs'][0]['rows']
            ordered = check.get('order', evaluation['conditions'].get('order', False))
            row.update(exact_match=compare_rows(rows, expected, ordered),
                       native_comparison_match=compare_rows(rows, expected, ordered, native=True))
        report['checks'].append(row)
    return report


def audit(run, candidate_artifact=None):
    if not os.environ.get('SLURM_JOB_ID'):
        raise BCError('Native failure replay requires a CPU sbatch allocation')
    from ..experiments.manifest import validate_manifest, task_from, source_revision
    from ..experiments.snapshot import verify_snapshot
    from ..tasks.sqlite_tasks import verify_file
    import resource
    started, wall = time.process_time(), time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    manifest = read_json(run/'manifest.json')
    config = validate_manifest(manifest)
    if (config.development_profile != 'qwen35-27b-native-context16k-actions24' or
            {t['id'] for t in manifest['tasks']} != {'solar_2','solar_M_3'} or len(manifest['episodes']) != 2):
        raise BCError('Replay is limited to the two completed native 24-action solar episodes')
    root = Path(__file__).resolve().parents[3]
    files = ('src/beyond_consensus/runtime/sqlite_executor.py', 'src/beyond_consensus/runtime/data_domain.py',
             'src/beyond_consensus/tasks/sqlite_tasks.py')
    inputs, hashes = [], {}
    # Validate all prerequisites before running any SQL.
    for episode in manifest['episodes']:
        directory = run/'episodes'/episode['episode_id']
        paths = (directory/'result.json', directory/'checkpoint.json')
        result, state = map(read_json, paths)
        if (result['status'] != 'completed' or result['episode_id'] != episode['episode_id'] or
                result['provenance']['manifest_hash'] != digest(episode) or state['manifest_hash'] != digest(episode)):
            raise BCError('Completed episode/checkpoint binding mismatch')
        snapshot = Path(result['provenance']['import_path']).parents[3]
        marker = verify_snapshot(snapshot)
        if marker['source_revision'] != manifest['source_revision'] or any(file_hash(snapshot/f) != file_hash(root/f) for f in files):
            raise BCError('Historical executor/scorer implementation differs; do not reinterpret the run')
        task = task_from(next(t for t in manifest['tasks'] if t['id'] == episode['task_id']))
        if capabilities() != task.metadata['executor_runtime']:
            raise BCError('Historical SQLite runtime differs')
        verify_file(task.metadata['harness']['database'])
        for evaluation in task.metadata['evaluation'].values():
            if not 1 <= len(evaluation['checks']) <= 8:
                raise BCError('Reviewed check count exceeds audit bound')
        hashes[episode['episode_id']] = [file_hash(p) for p in paths]
        inputs.append((task,state,result,paths))
    if candidate_artifact is not None:
        for task, state, _, _ in inputs:
            if task.id == "solar_2":
                candidate_content(task, state, candidate_artifact)
    ledger = ReplayLedger(config.budget.tool_charge)
    reports = []
    for task,state,result,_ in inputs:
        try:
            if candidate_artifact is not None:
                if task.id == "solar_2":
                    reports.append(replay_candidate(task,state,result,ledger,candidate_artifact))
            else:
                reports.append(replay_task(task,state,result,ledger))
        except (BCError, ValueError, KeyError, TypeError):
            # Preserve spent replay work without exporting private exception text.
            reports.append(dict(task=task.id, historical_success=result['success'],
                                comparison_status='replay_unavailable_preserve_ledger'))
    for task,state,result,paths in inputs:
        if [file_hash(p) for p in paths] != hashes[result['episode_id']]:
            raise BCError('Historical output changed during audit')
        verify_file(task.metadata['harness']['database'])
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return dict(schema='bc-native-failure-replay-v1', experiment_id=manifest['experiment_id'],
        model_executed=False, sql_executed=bool(ledger.entries), historical_scores_changed=False,
        candidate_artifact=candidate_artifact,
        worker_feedback=False, tasks=reports, replay_ledger=ledger.entries,
        replay_work=sum(e['work'] for e in ledger.entries), accounting='Separate offline analysis; never added to or substituted for historical episode work',
        analysis_cpu_seconds=time.process_time()-started, child_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        wall_seconds=time.monotonic()-wall, source_revision=source_revision(root),
        manifest_hash=digest(manifest), input_hashes=hashes,
        audit_implementation_hashes={f:file_hash(root/f) for f in ('src/beyond_consensus/diagnostics/sqlite_failure.py', 'scripts/probe_sqlite_failure.py')},
        implementation_hashes={f:file_hash(root/f) for f in files})
