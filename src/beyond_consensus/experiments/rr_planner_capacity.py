"""Offline capacity arithmetic over an immutable measured footprint packet.

No tokenizer, model, SQL, scheduler or synthetic runtime execution. Hypothetical
non-action reserves are scenarios, not observed reasoning or qualification.
"""
from copy import deepcopy
import time

from ..util import BCError, digest
from .rr_v2_preflight import validate as validate_preflight

CASE_IDS = ('plan_02', 'plan_07', 'plan_24', 'scope_empty', 'scope_imports16')


def require(condition, message):
    if not condition:
        raise BCError(message)


def inspect(packet):
    """Check recorded bindings without regenerating historical observations."""
    require(packet.get('schema') == 'rr-open-footprint-cpu-v1' and
            packet.get('protocol') == 'rr-open-footprint-five-cases-v1' and
            packet.get('packet_id') == digest({k:v for k,v in packet.items() if k != 'packet_id'}),
            'Measured footprint packet integrity mismatch')
    for key in ('model_executed', 'sql_executed', 'task_inputs_used', 'task_execution_allowed',
                'campaign_allowed', 'task_competence_measured',
                'autonomous_planning_competence_measured', 'worst_case_fit_established'):
        require(packet.get(key) is False, 'Unexpected footprint evidence scope: '+key)
    base = packet['base_manifest']; validate_preflight(base)
    model = base['model']; proposal = packet['proposal']; runtime = packet['measurement_runtime']
    require(base.get('execution_contract') == 'plan_scoped_v1' and base['pool'] == 7 and
            packet['source_revision'] == base['source_revision'], 'Historical scope/source mismatch')
    require(proposal.get('schema') == 'rr-open-engineering-proposal-v1' and
            proposal.get('proposal_id') == digest({k:v for k,v in proposal.items() if k != 'proposal_id'}),
            'Historical proposal integrity mismatch')
    require(proposal.get('task_execution_allowed') is False and proposal.get('campaign_allowed') is False,
            'Expected blocked proposal')
    require(proposal['worker_config']['model'] == model and proposal['planner_config']['model'] ==
            dict(model, action_constraint='reporecourse-plan-scoped-v1-pool-7'), 'Historical model settings differ')
    q = base['planner_lock']['decoder_qualification']
    require(runtime['worker_lock_sha256'] == base['model_lock_sha256'] and
            runtime['qualification_keys']['plan'] == q['qualification_key'] and
            runtime['packages'] == q['packages'] and
            runtime['template']['template_hash'] == q['thinking_template']['template_hash'],
            'Recorded tokenizer/grammar binding mismatch')
    rows = packet['cases']
    require([r['id'] for r in rows] == list(CASE_IDS), 'Missing, duplicate or reordered case')
    for index, row in enumerate(rows):
        require(row['role'] == ('plan' if index < 3 else 'json'), 'Case role mismatch')
        require(row['expected_hash'] == digest(row['expected']) and row['prompt_hash'] == digest(row['messages']),
                'Case content hash mismatch')
        require(row.get('structural_valid') is True, 'Case structure was not validated')
        if index < 3:
            require(row['expected']['tool'] == 'submit_plan' and
                    len(row['expected']['plan']['units']) == (2,7,24)[index], 'Plan case count mismatch')
        else:
            require(row['visibility_passed'] is True and row['observation_hash'] == digest(row['observation']),
                    'Observation controls did not pass')
            if index == 4:
                require(row['unrelated_read_denied'] is True and row['unrelated_version'] not in row['visible_versions'],
                        'Negative visibility control failed')
        m = row['measurement']
        require(type(m['action_tokens']) is int and m['action_tokens'] > 0 and
                type(m['input_tokens']) is int and m['input_tokens'] > 0 and
                type(m['action_plus_stop_tokens']) is int and m['action_plus_stop_tokens'] == m['action_tokens']+1,
                'Missing or inconsistent tokenizer measurements')
        require(type(m['grammar_accepted']) is bool, 'Missing grammar measurement')
        expected_status = ('grammar_rejected' if not m['grammar_accepted'] else
                           'output_representation_exceeds_cap' if m['action_plus_stop_tokens'] > 2048 else
                           'input_reservation_exceeds_context' if m['input_tokens']+2048 > 16384 else 'passed')
        require(m['status'] == expected_status and type(m['dispatch_allowed']) is bool and
                m['dispatch_allowed'] == (expected_status == 'passed'), 'Historical admission decision mismatch')
    expected_status = 'passed_cpu_cases' if all(r['measurement']['dispatch_allowed'] for r in rows) else 'failed_cpu_cases'
    require(packet['status'] == expected_status, 'Historical CPU status mismatch')
    return model


def review(packet, caps=(2048,3072,4096), non_action_reserves=(0,512,1024,2048)):
    start = time.process_time()
    model = inspect(packet)
    context = model['context_limit']; original_cap = model['max_new_tokens']
    for values, label, minimum, maximum in ((caps, 'caps', 1, context-1),
            (non_action_reserves, 'non-action reserves', 0, context-1)):
        require(isinstance(values,(list,tuple)) and 0 < len(values) <= 16 and
                all(type(v) is int and minimum <= v <= maximum for v in values) and
                len(set(values)) == len(values), 'Invalid '+label)
    comparisons = []
    for cap in sorted(caps):
        cases = []
        for row in packet['cases'][:3]:
            m = row['measurement']; action = m['action_plus_stop_tokens']; prompt = m['input_tokens']
            cases.append(dict(id=row['id'], measured_action_plus_stop_tokens=action,
                measured_input_tokens=prompt, grammar_accepted_at_original_cap=m['grammar_accepted'],
                action_headroom_tokens=cap-action, full_call_reservation_tokens=prompt+cap,
                observed_prompt_fits_reservation=prompt+cap <= context,
                scenarios=[dict(non_action_reserve_tokens=r, hypothetical=True,
                    remaining_output_tokens=cap-action-r,
                    arithmetic_fit=(cap-action-r >= 0 and prompt+cap <= context))
                    for r in sorted(non_action_reserves)]))
        comparisons.append(dict(planner_output_cap=cap, maximum_planner_input_tokens=context-cap,
            changed_from_original=cap != original_cap, qualified=False, cases=cases))
    result = dict(schema='rr-planner-capacity-review-v1', status='review_required',
        historical_packet_id=packet['packet_id'], historical_packet_status=packet['status'],
        historical_proposal_id=packet['proposal']['proposal_id'], historical_source_revision=packet['source_revision'],
        original_model=deepcopy(model), worker_output_cap_unchanged=original_cap, context_limit_unchanged=context,
        measured_reasoning_tokens=None, selected_planner_output_cap=None, comparisons=comparisons,
        worker_observations=[dict(id=r['id'], measurement=deepcopy(r['measurement'])) for r in packet['cases'][3:]],
        model_executed=False, sql_executed=False, tokenizer_executed=False,
        historical_scores_changed=False, historical_packet_changed=False,
        task_execution_allowed=False, campaign_allowed=False, GPU_submission_allowed=False,
        worst_case_fit_established=False, grammar_keys_recomputed=False,
        accounting='Separate offline arithmetic; no historical or task ledger changes',
        limitations=[
            'Counts describe the recorded serialization, not a shortest representation or every legal plan.',
            'Non-action reserves are hypothetical combined reasoning/delimiter/formatting scenarios; none are measured.',
            'Action headroom is not an observed reasoning allowance or a success prediction.',
            'Changing a planner output cap reduces its maximum input reservation at fixed context.',
            'The earlier approximately 14k-input preflight does not qualify a larger output reservation.',
            'Changed planner allowances need separate configuration, grammar-contract and memory review; worker allowance stays unchanged.',
            'Recorded hashes establish internal bindings, not independent authenticity or scheduler completion.',
            'No new setting, manifest or model execution is selected or authorized.'],
        analysis_cpu_seconds=time.process_time()-start)
    result['report_id'] = digest(result)
    return result
