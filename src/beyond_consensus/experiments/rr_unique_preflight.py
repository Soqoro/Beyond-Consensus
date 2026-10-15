"""Three task-free unique-key generation probes; no tools, scoring or retries."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import time
import traceback
from types import SimpleNamespace
import sys

from ..models.decoder_trace import Trace, exception_record, safe_message

from ..config import ModelConfig
from ..models.competence import CHECKPOINT, REVISION, require_qualification
from ..models.unique_keys import MODE, synthetic_controls
from ..models.action_schema import validate_action
from ..util import BCError, digest, read_json, atomic_json
from .manifest import source_revision

SCHEMA = 'rr-unique-preflight-manifest-v1'
PROTOCOL = 'rr-unique-three-synthetic-calls-v1'


def require(value, message):
    if not value:raise BCError(message)


def error_details(exc, stage):
    """Bounded synthetic-only diagnostics; no frame locals or device queries."""
    frames = list(traceback.walk_tb(exc.__traceback__))[-12:]
    return dict(error_type=type(exc).__name__, failure_stage=stage,
        error_message=safe_message(exc,4096), error_message_truncated=len(str(exc)) > 4096,
        exception_chain=exception_record(exc),
        error_frames=[dict(file=frame.f_code.co_filename[-512:], line=line,
            function=frame.f_code.co_name[:128]) for frame, line in frames])


def model():
    return ModelConfig(backend='transformers', checkpoint=CHECKPOINT, revision=REVISION,
        tokenizer_revision=REVISION, dtype='bfloat16', context_limit=16384,
        max_new_tokens=2048, thinking=True, do_sample=False, action_constraint=MODE)


def cases():
    good, _ = synthetic_controls()
    return [dict(id='nested_mapping', text=good[1], long_context=False),
            dict(id='escaped_keys', text=good[4], long_context=False),
            dict(id='long_context_mapping', text=good[1], long_context=True)]


def check_controls(root, controls):
    from .rr_response_probe import check_controls as common
    common(root, controls)
    require('test_rr_unique_preflight.py' in controls.get('patterns', []), 'Unique preflight adapter controls missing')


def normal_gate(evidence, approval, scope=None):
    from .rr_decoder_diagnostic import review_template
    require(isinstance(evidence,dict) and set(evidence)=={'manifest','report','review'},'Reviewed matched diagnostic required before normal qualification')
    template=review_template(evidence['manifest'],evidence['report']);review=evidence['review']
    require(all(review.get(k)==v for k,v in template.items() if k not in ('decision','reviewer','reviewed_at','normal_qualification_allowed')) and
        template['observed_both_arms_completed'] and review.get('decision')=='approved' and review.get('normal_qualification_allowed') is True and
        bool(review.get('reviewer')) and bool(review.get('reviewed_at')),'Diagnostic review unresolved; normal qualification blocked')
    expected=dict(schema='rr-unique-normal-approval-v1',evidence_hash=digest(evidence),maximum_calls=3,
        **(scope or {}),
        task_execution_allowed=False,launch_blocking=False,decision='pending',reviewer=None,reviewed_at=None)
    require(isinstance(approval,dict) and all(approval.get(k)==v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')) and
        approval.get('decision')=='approved' and bool(approval.get('reviewer')) and bool(approval.get('reviewed_at')),'Separate exact normal-mode qualification approval required')


def build(root, lock, controls, diagnostic_evidence=None, approval=None):
    normal_gate(diagnostic_evidence,approval,dict(source_revision=source_revision(root),model_lock_sha256=digest(lock),controls_hash=digest(controls)))
    check_controls(root, controls)
    m = dict(schema=SCHEMA, protocol=PROTOCOL, model=asdict(model()),
        diagnostic_evidence=diagnostic_evidence, normal_approval=approval,
        model_lock_sha256=digest(lock), source_revision=source_revision(root), controls=controls,
        cases=cases(), maximum_calls=3, maximum_logical_tokens=49152,
        cpu_cap_per_call=1200, shards=1, episodes=[], planned_episodes=0,
        task_inputs_used=False, task_execution_allowed=False, worst_case_fit_established=False)
    m['experiment_id'] = digest(m)
    check(m, root, lock)
    return m


def validate(m):
    require(m.get('schema') == SCHEMA and m.get('protocol') == PROTOCOL and
            m.get('experiment_id') == digest({k:v for k,v in m.items() if k != 'experiment_id'}), 'Unique preflight identity changed')
    for key, expected in dict(model=asdict(model()), cases=cases(), maximum_calls=3,
        maximum_logical_tokens=49152, cpu_cap_per_call=1200, shards=1, episodes=[],
        planned_episodes=0, task_inputs_used=False, task_execution_allowed=False,
        worst_case_fit_established=False).items():
        require(type(m.get(key)) is type(expected) and m[key] == expected, 'Unique preflight scope changed: '+key)
    return SimpleNamespace(model=model(), shards=1, task_kind='rr_unique_preflight')


def check(m, root, lock):
    validate(m)
    normal_gate(m.get('diagnostic_evidence'),m.get('normal_approval'),dict(source_revision=m['source_revision'],model_lock_sha256=m['model_lock_sha256'],controls_hash=digest(m['controls'])))
    require(m['source_revision'] == source_revision(root), 'Unique preflight source changed')
    check_controls(root, m['controls'])
    require(m['model_lock_sha256'] == digest(lock), 'Unique worker lock changed')
    require_qualification(lock, lock.get('decoder_qualification', {}).get('packages', {}), 16384, MODE, 2048)
    q = lock['decoder_qualification'].get('unique_key_controls', {})
    good, bad = synthetic_controls()
    stops = lock['decoder_qualification'].get('effective_generation_tokens', {}).get('eos_token_id', [])
    rows = q.get('cases', [])
    expected = {(i, stop, reasoning) for i in range(len(good)+len(bad)) for stop in stops for reasoning in (False,True)}
    require(q.get('schema') == 'rr-unique-key-controls-v1' and q.get('status') == 'passed' and
            q.get('controls_hash') == digest([good,bad]) and len(expected) == 44 and len(rows) == 44 and
            {(r.get('case'),r.get('stop_token_id'),r.get('reasoning')) for r in rows} == expected and
            all(type(r.get('reasoning')) is bool and r.get('accepted') is (r['case'] < len(good)) and
                r.get('expected') is (r['case'] < len(good)) for r in rows), 'Native unique-key controls missing')


def submission(m, root, lock, mode, concurrency, output):
    check(m, root, lock)
    require(mode == 'preflight' and concurrency == 1, 'Unique preflight requires preflight mode and concurrency one')
    require(not (Path(output)/'unique-preflight-started.json').exists(), 'Unique preflight already started; no retry')


def messages(case, count):
    system = 'Synthetic decoder probe only. Return exactly this JSON action, no Markdown: ' + case['text']
    def render(n):
        return [{'role':'system', 'content':system}, {'role':'user', 'content':
            '<inert_records>\n' + ''.join(f'record {i:05d}: inert synthetic data\n' for i in range(n)) +
            '</inert_records>\nReturn the requested action.'}]
    if not case['long_context']:return render(0)
    require(count(render(0)) <= 14336, 'Synthetic instruction exceeds input allowance')
    lo, hi = 0, 16384
    while lo < hi:
        mid = (lo+hi+1)//2
        if count(render(mid)) <= 14336:lo=mid
        else:hi=mid-1
    result = render(lo)
    require(14080 <= count(result) <= 14336, 'Long-input band not reached')
    return result


def sequence(backend, memory, save, *, selected_cases=None, mode=MODE, diagnostic=False):
    from reporecourse.resources import Resources
    selected_cases=cases() if selected_cases is None else selected_cases
    rows=[dict(id=c['id'],status='not_attempted',passed=False,dispatched=False,output_cap=2048,
        resources=Resources(16384,1200).summary()) for c in selected_cases]
    for order,(case,row) in enumerate(zip(selected_cases,rows)):
        resource=Resources(16384,1200);trace=Trace()
        if diagnostic:backend.diagnostic_trace=trace
        row.update(status='started',call_order=order)
        def checkpoint():
            row['resources']=resource.summary()
            row['trace']=trace.snapshot()
            row['flush_status']='persisted_atomic_checkpoint'
            save(rows)
        checkpoint()
        pending=None;cpu_pending=False;start=time.process_time();stage='input_preparation'
        try:
            resource.reserve_cpu(31);cpu_pending=True
            prompt=messages(case,backend.count_input);size=backend.count_input(prompt)
            require(size+2048<=16384,'Context limit exceeded')
            token_record=backend.diagnostic_inputs(prompt) if diagnostic else {}
            if diagnostic:require(token_record.get('rendered_input_tokens')==size,'Rendered input count changed before dispatch')
            stage='memory_before'
            row.update(input_tokens=size,prompt_hash=digest(prompt),memory_before=memory(True),
                pre_dispatch=dict(prompt_hash=digest(prompt),**token_record,
                    settings=asdict(backend.config) if hasattr(backend,'config') else None,
                    seed=0,output_cap=2048,role='worker',grammar_mode=mode,
                    guard_enabled=mode==MODE,call_order=order,
                    cache_policy='fresh_generate_call_use_cache_true_no_cross_call_cache',
                    context_policy='fresh_messages_per_call_no_assignment_history',
                    runtime=deepcopy(getattr(backend,'runtime',{}))))
            stage='token_admission';pending=resource.reserve(size,2048)
            row['pre_dispatch']['reservation']=dict(id=pending,input_tokens=size,output_cap=2048,total_tokens=size+2048)
            checkpoint();row['dispatched']=True;checkpoint()
            stage='generation';trace.begin(stage)
            generation=backend.generate(deepcopy(prompt),2048,0)
            trace.end(stage)
            # Generated text is local to strict validation, never unrestricted report text.
            row['generation']={k:v for k,v in asdict(generation).items() if k!='text'}
            row['generation'].update(text_sha256=digest(generation.text),text_characters=len(generation.text))
            row['generation_completion']=generation.diagnostics.get('finish_reason')
            row['rendered_generation_input_matches']=None if not diagnostic else token_record['rendered_input_ids_hash']==generation.diagnostics.get('rendered_input_ids_hash')
            row['native_completion']=trace.snapshot()['native_completion']
            row['accelerator_status']='no_exception_observed'
            stage='usage_reconciliation'
            resource.reconcile(pending,generation.output_tokens,generation.reasoning_tokens,
                finish_reason=generation.diagnostics.get('finish_reason'));pending=None
            cpu_pending=False
            resource.reconcile_cpu('synthetic_model_host_including_decoder',31,time.process_time()-start,
                decoder_cpu_seconds=generation.diagnostics.get('constraint_cpu_seconds'))
            stage='memory_after';row['memory_after']=memory(False)
            stage='response_validation';trace.begin(stage)
            try:
                validate_action(generation.text,mode)
                row['strict_parser_valid']=True
            except BCError:
                row['strict_parser_valid']=False
                if not diagnostic:raise
            row['passed']=(row['strict_parser_valid'] and (not diagnostic or row['rendered_generation_input_matches']) and json.loads(generation.text)==json.loads(case['text']) and
                generation.diagnostics.get('finish_reason')=='eos' and
                generation.diagnostics.get('constraint_complete') is True and
                isinstance(generation.diagnostics.get('constraint_cpu_seconds'),(int,float)) and
                0<=generation.diagnostics['constraint_cpu_seconds']<=30)
            row['status']='passed' if row['passed'] else 'failed_response'
            trace.end(stage,strict_parser_valid=row['strict_parser_valid'])
        except BaseException as exc:
            # Host-only bookkeeping after any failure: no memory query, synchronize,
            # decode, or CUDA cleanup which could replace the original exception.
            details=error_details(exc,stage)
            if pending is not None:resource.reconcile(pending)
            if cpu_pending:
                try:resource.reconcile_cpu('synthetic_model_host_including_decoder',31,time.process_time()-start)
                except Exception as accounting_error:row['accounting_error']=error_details(accounting_error,'error_accounting')
            row.update(status='error',**details)
            row['accelerator_status']='exception' if any(c['type'] in ('AcceleratorError','OutOfMemoryError') for c in details['exception_chain']) else 'unknown' if stage=='generation' else row.get('accelerator_status','not_dispatched')
            try:checkpoint()
            except Exception:
                row['flush_status']='checkpoint_failed'
                print(json.dumps(dict(error_type=type(exc).__name__,failure_stage=stage,flush_status='checkpoint_failed')),file=sys.stderr,flush=True)
            if not isinstance(exc,Exception):raise
            break
        else:checkpoint()
    return rows


def run(m, lock_path, root, output):
    import os
    require(os.environ.get('CUDA_LAUNCH_BLOCKING','0') in ('','0'),'Normal qualification requires launch blocking disabled')
    output = Path(output)
    submission(m, root, read_json(lock_path), 'preflight', 1, output.parent)
    require(not output.exists(), 'Use a fresh preflight output')
    output.parent.mkdir(parents=True, exist_ok=True)
    with (output.parent/'unique-preflight-started.json').open('x') as handle:
        json.dump({'experiment_id':m['experiment_id']}, handle)
    start = time.process_time(); wall = time.monotonic()
    report = dict(schema='rr-unique-preflight-report-v1', protocol=PROTOCOL,
        experiment_id=m['experiment_id'], manifest_hash=digest(m), source_revision=m['source_revision'], status='started', command_failed=True,
        model_executed=False, model_instances=0, task_inputs_used=False, sql_executed=False,
        task_execution_allowed=False, worst_case_fit_established=False, task_competence_measured=False,
        maximum_calls=3, calls=[], accounting='Separate synthetic qualification; no historical/task ledger changes')
    def save(rows):
        report.update(calls=deepcopy(rows), model_executed=any(r.get('dispatched') for r in rows),
            actual_tokens=sum(r['resources']['actual_tokens'] for r in rows),
            uncertain_tokens=sum(r['resources']['uncertain_tokens'] for r in rows),
            total_process_cpu_seconds=time.process_time()-start, total_wall_seconds=time.monotonic()-wall)
        atomic_json(output, report)
    save([])
    stage = 'model_load'
    try:
        from ..models.transformers_backend import TransformersBackend
        backend = TransformersBackend(model(), lock_path)
        report.update(runtime=backend.runtime, model_instances=1)
        def memory(reset):
            cuda=backend.torch.cuda
            cuda.synchronize()
            if reset:cuda.reset_peak_memory_stats(0)
            free,total=cuda.mem_get_info(0)
            return dict(peak_allocated_bytes=cuda.max_memory_allocated(0),
                peak_reserved_bytes=cuda.max_memory_reserved(0), free_bytes=free,total_bytes=total)
        stage = 'sequence'
        rows = sequence(backend, memory, save)
        passed = len(rows)==3 and all(r['passed'] for r in rows)
        report.update(status='passed_observed_cases' if passed else 'failed', command_failed=not passed)
        save(rows)
    except BaseException as exc:
        report.update(status='error', **error_details(exc, stage));save(report['calls'])
        raise
    return report


def aggregate(m, output):
    validate(m)
    path = Path(output)/'preflight.json'
    if not path.is_file():return dict(experiment_id=m['experiment_id'], status='missing', model_executed=False)
    report = read_json(path)
    require(report.get('experiment_id') == m['experiment_id'] and report.get('manifest_hash') == digest(m),
            'Unique preflight report provenance changed')
    return report
