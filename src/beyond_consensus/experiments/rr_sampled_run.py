"""Twelve-condition sampled organization adapter using the shared cohort runner.

No generated planner, reference driver, new scheduler, retry or outcome selection.
"""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import time

from ..config import ModelConfig
from ..util import BCError, digest, file_hash
from ..models.competence import require_qualification, versions
from .manifest import source_revision
from .rr_open_clean import load_control_record as load, seal
from . import rr_cohort as shared, rr_unique_review as normal
from reporecourse import sampled_cohort as sampled, cohort, v2
from reporecourse.qualification import implementation_hashes, runtime_versions
from reporecourse.resources import Resources
from reporecourse.tasks import load_task, private_task, ROOT as TASK_ROOT
from reporecourse.common import load as task_load

SCHEMA = 'rr-sampled-run-manifest-v1'
CONTROL_FILES = (
    'src/beyond_consensus/experiments/rr_sampled_run.py',
    'src/beyond_consensus/experiments/rr_unique_review.py',
    'scripts/prepare_rr_sampled_run.py', 'scripts/check_rr_sampled_run.py',
    'tests/test_rr_sampled_run.py', 'tests/test_rr_unique_review.py',
    'scripts/audit_rr_unique_normal.py',
)


def require(ok, message):
    if not ok:raise BCError(message)


def control_hashes(root):
    return {**shared.control_hashes(root), **{p:file_hash(Path(root)/p) for p in CONTROL_FILES}}


def catalog_bindings(catalog, sources):
    """Recheck all source-backed CPU certificates without executing witnesses."""
    v2.verify_record(catalog, 'catalog_id')
    require(catalog.get('schema') == 'rr-organization-catalog-v1', 'Sampled catalog schema')
    entries = catalog['tasks']
    require(len(entries) == 2 and {e['task'] for e in entries} == set(sampled.TASKS), 'Exact two-task catalog required')
    publics = {}; bindings = {}; configs = []
    for task in sampled.TASKS:
        entry = next(e for e in entries if e['task'] == task)
        card, public = load_task(task, sources); publics[task] = public
        bindings[task] = dict(card=card, public_hash=digest(public), private_hash=digest(private_task(task)))
        selected = entry['selected']; candidates = entry['candidates']
        require(len(selected) == len(set(selected)) == 3 and
            len({c['candidate_id'] for c in candidates}) == len(candidates), 'Three unique selected organizations required')
        keys = set()
        for cid in selected:
            candidate = next((c for c in candidates if c['candidate_id'] == cid), None)
            require(candidate is not None and sampled.qualified_candidate(candidate, task, public, entry, catalog),
                'Sampled reference/source qualification changed: '+task)
            require(candidate['canonical_key'] not in keys, 'Equivalent sampled organizations')
            keys.add(candidate['canonical_key']); configs.append(sampled.configuration(task, candidate['plan']))
    return publics, bindings, configs


def build(root, sources, catalog, worker, audit, controls, footprint):
    publics, bindings, configs = catalog_bindings(catalog, sources)
    prepared = sampled.proposal(catalog, publics, worker_lock=worker, normal_qualification=audit)
    require(not prepared['missing_slots'] and len(prepared['configurations']) == 6, 'Incomplete sampled scope')
    m = dict(schema=SCHEMA, source_revision=source_revision(root), sources_root=str(Path(sources).resolve()),
        lane='rich_development_unreviewed', study='controlled_organization_characterization',
        prepared=prepared, configurations=configs, task_bindings=bindings,
        source_registry_hash=digest(task_load(TASK_ROOT/'source_registry.json')),
        implementation_hashes=implementation_hashes(), model=sampled.model_settings(),
        model_lock_sha256=digest(worker), evidence=dict(normal_audit=audit, controls=controls, footprint=footprint),
        shards=6, planned_episodes=6, planned_conditions=12, maximum_execution_branches=12,
        maximum_model_planner_calls=0, branch_caps=dict(token_cap=100000, cpu_cap=1200), reserve_rule='none',
        target_rule='seed1_uniform_meaningful_owner_before_outcomes', limitations=deepcopy(sampled.LIMITATIONS),
        confirmatory=False, campaign_allowed=False, task_execution_allowed=False, approval=None)
    m['episodes'] = [dict(episode_id=c['configuration_id'], shard=i) for i,c in enumerate(configs)]
    seal(m); verify(m,root,worker)
    return m


def approval_template(m):
    return dict(schema='rr-sampled-run-approval-v1', proposal_id=m['experiment_id'],
        scope_hash=digest({k:m[k] for k in ('configurations','model','branch_caps','target_rule','reserve_rule','evidence')}),
        maximum_execution_branches=12, maximum_model_planner_calls=0,
        limitations_accepted=deepcopy(sampled.LIMITATIONS), decision='pending', reviewer=None, reviewed_at=None)


def validate(m):
    require(m.get('schema') == SCHEMA and m.get('experiment_id') == digest({k:v for k,v in m.items() if k!='experiment_id'}),
        'Sampled manifest identity changed')
    fixed = dict(lane='rich_development_unreviewed', study='controlled_organization_characterization',
        shards=6, planned_episodes=6, planned_conditions=12, maximum_execution_branches=12,
        maximum_model_planner_calls=0, branch_caps=dict(token_cap=100000,cpu_cap=1200), reserve_rule='none',
        target_rule='seed1_uniform_meaningful_owner_before_outcomes', limitations=sampled.LIMITATIONS,
        model=sampled.model_settings(), confirmatory=False, campaign_allowed=False)
    require(all(type(m.get(k)) is type(v) and m[k] == v for k,v in fixed.items()), 'Sampled scope changed')
    p = m['prepared']; v2.verify_record(p,'proposal_id')
    require(p['schema'] == sampled.SCHEMA and p['planned_conditions'] == 12 and not p['missing_slots'] and
        p['catalog_id'] == p['catalog']['catalog_id'] and p['worker_lock_hash'] == m['model_lock_sha256'] and
        p['normal_qualification_evidence'] == m['evidence']['normal_audit'], 'Prepared sampled bindings changed')
    v2.verify_record(p['catalog'],'catalog_id')
    configs = m['configurations']
    require(len(configs) == len({c['configuration_id'] for c in configs}) == 6 and
        configs == [x['configuration'] for x in p['configurations']], 'Sampled plan selection changed')
    require([c['task'] for c in configs] == [t for t in sampled.TASKS for _ in range(3)], 'Sampled task order changed')
    for c, item in zip(configs, p['configurations']):
        sampled.check_configuration(c); require(c['seed_index'] == 1, 'Sampled seed changed')
        cohort.check_schedule(c, item['schedule'])
        require(item['schedule']['frozen']['plan'] == c['plan'] and
            item['schedule']['frozen']['physical_generation_count'] == 0, 'Sampled authored plan changed')
    require(m['episodes'] == [dict(episode_id=c['configuration_id'],shard=i) for i,c in enumerate(configs)], 'Sampled shards changed')
    if m['approval'] is None:require(m['task_execution_allowed'] is False, 'Missing sampled approval')
    else:
        p = deepcopy(m); p.update(approval=None, task_execution_allowed=False); seal(p)
        expected = approval_template(p); receipt = m['approval']
        require(m['task_execution_allowed'] is True and set(receipt) == set(expected) and
            receipt['decision'] == 'approved' and all(isinstance(receipt[k],str) and receipt[k].strip() for k in ('reviewer','reviewed_at')) and
            all(receipt[k] == v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')), 'Sampled approval scope changed')
    return SimpleNamespace(model=ModelConfig(**m['model']), shards=6, task_kind='rr_sampled_run')


def verify(m, root, worker):
    validate(m)
    require(source_revision(root) == m['source_revision'], 'Sampled source revision changed')
    require(m['implementation_hashes'] == implementation_hashes(), 'Sampled core changed')
    require(digest(worker) == m['model_lock_sha256'], 'Sampled worker lock changed')
    require_qualification(worker, versions(), 16384, sampled.MODE, 2048)
    publics, bindings, configs = catalog_bindings(m['prepared']['catalog'], m['sources_root'])
    require(bindings == m['task_bindings'] and configs == m['configurations'] and
        m['source_registry_hash'] == digest(task_load(TASK_ROOT/'source_registry.json')), 'Sampled task/source binding changed')
    for c,item in zip(configs,m['prepared']['configurations']):
        require(item['schedule']['frozen']['request'] == v2.request(publics[c['task']],c['config'],worker),
            'Prepared request model/public binding changed')
    controls = m['evidence']['controls']
    require(controls.get('schema') == 'rr-sampled-run-controls-v1' and controls.get('status') == 'passed' and
        controls.get('implementation_hashes') == control_hashes(root) and controls.get('source_revision') == m['source_revision'] and
        controls.get('runtime_versions') == runtime_versions() and controls.get('tests',0) >= 12 and
        all(controls.get(k) == 0 for k in ('errors','failures','skipped')) and
        controls.get('model_executed') is False and
        {'test_rr_sampled_run.py','test_rr_unique_review.py','test_rr_cohort.py','test_reporecourse_scoped.py'}.issubset(controls.get('patterns',[])), 'Renewed no-skip sampled controls required')
    audit = m['evidence']['normal_audit']
    fresh = normal.inspect(audit['run'],audit['snapshots'],root)
    # The checkout path differs inside a submission snapshot, but all checked
    # implementations, input-file hashes and audit semantics must still match.
    saved = deepcopy(audit); saved['current_compatibility']['checked_root'] = fresh['current_compatibility']['checked_root']
    require(fresh == saved and fresh['current_compatibility']['status'] == 'compatible', 'Normal qualification changed or incompatible')
    normal_manifest = load(Path(audit['run'])/'manifest.json')
    require(normal_manifest['model_lock_sha256'] == digest(worker) and normal_manifest['model'] == m['model'], 'Normal model binding differs')
    check_footprint(m, publics, worker)


def authorize(m, receipt, root, worker):
    verify(m, root, worker); require(m['approval'] is None, 'Already approved')
    result = deepcopy(m); result.update(approval=deepcopy(receipt), task_execution_allowed=True); seal(result); validate(result)
    return result


def submission(m, root, worker, mode, concurrency, output, shard=None):
    require(mode == 'run' and concurrency == 1, 'Sampled study requires run mode and concurrency one')
    verify(m, root, worker)
    require(m['task_execution_allowed'] and m['approval'] is not None, 'Exact twelve-condition approval required')
    shared.attempt_checks(m,output,shard)


def load_backend(m, lock_path):
    import os
    require(os.environ.get('CUDA_LAUNCH_BLOCKING','0') in ('','0'), 'Sampled study requires normal asynchronous mode')
    from ..models.transformers_backend import TransformersBackend
    backend = TransformersBackend(ModelConfig(**m['model']),lock_path)
    def switch(role):require(role == 'json', 'Sampled adapter cannot call planner')
    return backend, switch, load(Path(m['evidence']['normal_audit']['run'])/'preflight.json')['runtime']


def check_runtime_schedule(m, c, schedule, public=None):
    cohort.check_schedule(c,schedule)
    original = next(x['schedule'] for x in m['prepared']['configurations'] if x['configuration']['configuration_id']==c['configuration_id'])
    frozen = schedule['frozen']; expected = original['frozen']
    require(frozen['request'] == expected['request'] and frozen['plan'] == c['plan'] and
        frozen['submitted_plan'] == c['plan'] and frozen['mode'] == 'authored_catalog' and
        frozen['planning_events'] == [] and frozen['physical_generation_count'] == 0, 'Runtime sampled plan changed')
    require([(b['track'],b['target'],b['eligible']) for b in schedule['branches']['rows']] ==
        [(b['track'],b['target'],b['eligible']) for b in original['branches']['rows']], 'Prospective sampled targets changed')
    r = Resources(**deepcopy(frozen['planning_resources']))
    require(r.actual_tokens == r.uncertain_tokens == 0 and all(e['kind']=='cpu' for e in r.events), 'Unexpected sampled planner work')
    if public is not None:require(frozen['request']['public_hash'] == digest(public), 'Runtime public task changed')


def execute_configuration(m,c,public,private,backend,switch,save):
    started = time.process_time()
    original = next(x['schedule'] for x in m['prepared']['configurations'] if x['configuration']['configuration_id']==c['configuration_id'])
    schedule = sampled.schedule(c, public, original['frozen']['request']['model_binding'])
    check_runtime_schedule(m,c,schedule,public)
    frozen = schedule['frozen']; r = Resources(**deepcopy(frozen['planning_resources']))
    r.parent_overhead('sampled_receipt_and_resolution',started,0)
    frozen['planning_resources'] = deepcopy(vars(r)); frozen['frozen_id'] = digest({k:v for k,v in frozen.items() if k!='frozen_id'})
    schedule = cohort.schedule(c,frozen); check_runtime_schedule(m,c,schedule,public)
    save('frozen-plan',frozen)
    return shared.execute_schedule(c,schedule,public,private,backend,switch,save)


def aggregate(m, output):
    validate(m); records = shared.read_records(m,output)
    view = deepcopy(m['prepared'])
    for item in view['configurations']:
        c=item['configuration']; ep=Path(output)/'episodes'/c['configuration_id']
        if (ep/'schedule.json').exists():
            saved=load(ep/'schedule.json'); require(saved['manifest_hash']==digest(m),'Sampled schedule provenance')
            check_runtime_schedule(m,c,saved['content']); item['schedule']=saved['content']
        record=records.get(c['configuration_id'])
        if record and record.get('branches'):
            require(record.get('schedule_id') == item['schedule']['schedule_id'],'Sampled result schedule changed')
        elif record:
            # Retain failed admission/loading separately; no invented branch outcomes.
            records[c['configuration_id']] = dict(record, schedule_id=item['schedule']['schedule_id'])
    view['proposal_id']=digest({k:v for k,v in view.items() if k!='proposal_id'})
    result=sampled.analyze(view,records)
    return dict(result, experiment_id=m['experiment_id'], prepared_proposal_id=m['prepared']['proposal_id'],
        executed_schedule_analysis_id=view['proposal_id'], configuration_records=records,
        missing_configurations=sum(c['configuration_id'] not in records for c in m['configurations']),
        offline_costs=m['prepared']['offline_costs'], limitations=m['limitations'], confirmatory=False,
        review_status='development_reviews_deferred_not_clearance')


def export(run):
    run=Path(run);m=load(run/'manifest.json')
    return dict(evidence='read_only_real_run_export_including_failed_and_unrun',
        experiment_id=m['experiment_id'], aggregate=aggregate(m,run), manifest=m,
        model_executed=False, sql_executed=False, historical_scores_changed=False)


def prompt_cases(c,public):
    """Actual assigned public observations, never reference solution bodies."""
    import json
    from reporecourse.engine import worker_messages
    from reporecourse.runtime import Environment
    env=Environment(public,resources=Resources(100000,1200),workers=c['config']['workers'],
        plan=c['plan'],execution_contract='plan_scoped_v1',interface_profile=c['config']['interface_profile'])
    rows=[]
    try:
        for unit in c['plan']['units']:
            env.scopes.begin(unit,unit['worker'],'primary');env.assignment[unit['worker']]=unit
            obs=env.observation(unit['worker']);obs.update(remaining_tokens=100000,cpu_remaining=1200)
            rows.append(dict(id=unit['id']+'/initial',messages=worker_messages(obs,[])))
            for name,value in sorted(public['sources'].items()):
                history=[{'role':'assistant','content':json.dumps({'tool':'read_source','name':name})},
                    {'role':'user','content':json.dumps(value)}]
                rows.append(dict(id=unit['id']+'/source/'+name,messages=worker_messages(obs,history)))
    finally:env.close()
    return rows


def measure_footprint(catalog,sources,worker):
    import json
    from transformers import AutoTokenizer
    from ..models.transformers_backend import verify_thinking_template
    from reporecourse.organization_sampler import reference_witness
    require_qualification(worker,versions(),16384,sampled.MODE,2048)
    publics,_,configs=catalog_bindings(catalog,sources)
    tokenizer=AutoTokenizer.from_pretrained(worker['tokenizer_path'],local_files_only=True,trust_remote_code=False)
    template=verify_thinking_template(tokenizer,True);rows=[];outputs=[];start=time.process_time()
    for c in configs:
        for case in prompt_cases(c,publics[c['task']]):
            ids=tokenizer.apply_chat_template(case['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=True,return_dict=True)['input_ids']
            rows.append(dict(configuration_id=c['configuration_id'],id=case['id'],messages_hash=digest(case['messages']),
                input_tokens=len(ids),rendered_input_ids_hash=digest(ids),passed=0<len(ids)<=14336))
    for entry in catalog['tasks']:
        for cid in entry['selected']:
            candidate=next(c for c in entry['candidates'] if c['candidate_id']==cid)
            witness=reference_witness(candidate,private_task(entry['task']))
            for i,item in enumerate(witness['actions']):
                a=deepcopy(item['action'])
                if 'bindings' in a:a['bindings']={k:digest(['footprint-version',k]) for k in a['bindings']}
                size=len(tokenizer.encode(json.dumps(a,separators=(',',':')),add_special_tokens=False))+1
                outputs.append(dict(candidate_id=cid,index=i,action_hash=digest(item['action']),action_plus_stop_tokens=size,passed=0<size<=2048))
    return dict(schema='rr-sampled-worker-footprint-v1',catalog_id=catalog['catalog_id'],worker_lock_hash=digest(worker),
        implementation_hashes=implementation_hashes(),adapter_hash=file_hash(Path(__file__)),template=template,cases=rows,reference_outputs=outputs,
        status='passed' if all(x['passed'] for x in rows+outputs) and rows and outputs else 'failed',
        model_executed=False,task_execution_allowed=False,analysis_cpu_seconds=time.process_time()-start,
        limitation='Initial and one-source observations; later histories can exhaust context. Reference serialization excludes reasoning and is not a shortest solution.')


def check_footprint(m,publics,worker):
    from reporecourse.organization_sampler import reference_witness
    f=m['evidence']['footprint']
    require(f.get('schema')=='rr-sampled-worker-footprint-v1' and f.get('status')=='passed' and
        f.get('catalog_id')==m['prepared']['catalog_id'] and f.get('worker_lock_hash')==digest(worker) and
        f.get('implementation_hashes')==implementation_hashes() and f.get('adapter_hash')==file_hash(Path(__file__)) and
        f.get('model_executed') is False and f.get('task_execution_allowed') is False, 'Sampled worker footprint missing or changed')
    expected=[(c['configuration_id'],case['id'],digest(case['messages'])) for c in m['configurations'] for case in prompt_cases(c,publics[c['task']])]
    require(expected==[(r['configuration_id'],r['id'],r['messages_hash']) for r in f['cases']] and
        all(r['passed'] is True and type(r['input_tokens']) is int and 0<r['input_tokens']<=14336 for r in f['cases']), 'Sampled prompt measurements changed')
    expected_outputs=[]
    for entry in m['prepared']['catalog']['tasks']:
        for cid in entry['selected']:
            candidate=next(c for c in entry['candidates'] if c['candidate_id']==cid)
            witness=reference_witness(candidate,private_task(entry['task']))
            expected_outputs.extend((cid,i,digest(x['action'])) for i,x in enumerate(witness['actions']))
    require(expected_outputs==[(r['candidate_id'],r['index'],r['action_hash']) for r in f['reference_outputs']] and
        all(r['passed'] is True and type(r['action_plus_stop_tokens']) is int and 0<r['action_plus_stop_tokens']<=2048 for r in f['reference_outputs']), 'Sampled reference expressibility changed')
