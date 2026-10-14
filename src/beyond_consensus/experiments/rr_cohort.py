"""Shared-registry adapter for bounded prospective stock and rich-task cohorts.

One configuration per shard: one planning sequence then its precommitted branch
schedule, on one shared model. No nested submission or clean-success filtering.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import signal
import time
from ..config import ModelConfig
from ..util import BCError, digest, file_hash, read_json, atomic_json, directory_lock
from .manifest import source_revision
from . import rr_v2_preflight as profile, rr_open_review as review
from .rr_open_clean import load_control_record, seal
from reporecourse import cohort, v2
from reporecourse.common import Rejected, load
from reporecourse.tasks import ROOT, catalog, load_task, private_task
from reporecourse.qualification import implementation_hashes, runtime_versions
from reporecourse.resources import Resources

SCHEMA='rr-cohort-manifest-v1'
UNREVIEWED_LANE='rich_development_unreviewed'
DEFERRED_LIMITATIONS=['independent_task_review_deferred_by_user',
    'source_and_provider_rights_review_pending_not_clearance','unreviewed_development_only']

def limitations(lane):
    return LIMITATIONS + (DEFERRED_LIMITATIONS if lane==UNREVIEWED_LANE else [])

RICH_TASKS=('jaffle-payment-release','energy-single-indicator-release','github-topics-client-package','github-multioperation-integration')
LIMITATIONS=['development_requests_not_population_inference','uncalibrated_engineering_caps_not_B0',
             'observed_memory_only','no_retry_no_training','persistent_availability_F_not_adaptive_adversary',
             'seed1_deterministic_not_independent_sample']

# These modules are not used to generate or execute the task-free GPU probe.
# Their changed behavior is qualified by the renewed CPU cohort/task controls.
# All worker, scope, engine, grammar, backend and resource code stays hash-exact.
FOOTPRINT_OFFLINE_MODULES={
    'src/reporecourse/sources.py','src/reporecourse/rich_tasks.py',
    'src/reporecourse/evaluator.py','src/reporecourse/cohort.py',
}


def footprint_compatibility(root, marker):
    """Compare only the task-free probe's contract, including added code files."""
    root=Path(root)
    prefixes=('src/reporecourse/','src/restricted_artifacts/','src/beyond_consensus/models/')
    fixed={'src/beyond_consensus/config.py','src/beyond_consensus/experiments/rr_v2_preflight.py',
           'src/beyond_consensus/experiments/rr_open_footprint.py'}
    paths={p for p in marker['files'] if p.startswith(prefixes)}|fixed
    for prefix in prefixes:
        paths.update(str(p.relative_to(root)) for p in (root/prefix).rglob('*.py'))
    changed=sorted(p for p in paths if not (root/p).is_file() or file_hash(root/p)!=marker['files'].get(p))
    return dict(compatible=not (set(changed)-FOOTPRINT_OFFLINE_MODULES),
        probe_contract_changes=sorted(set(changed)-FOOTPRINT_OFFLINE_MODULES),
        cpu_controlled_changes=sorted(set(changed)&FOOTPRINT_OFFLINE_MODULES))


def control_hashes(root):
    paths=['src/beyond_consensus/experiments/rr_cohort.py','src/beyond_consensus/experiments/cluster.py',
           'src/beyond_consensus/experiments/runner.py','src/beyond_consensus/experiments/manifest.py',
           'src/beyond_consensus/reporecourse_cli.py','src/beyond_consensus/evaluation/aggregate.py',
           'src/beyond_consensus/cli.py','experiments/qualify_reporecourse.sh',
           'tests/test_rr_cohort.py','tests/test_rr_rich_tasks.py','tests/test_rr_interface.py','scripts/check_rr_cohort.py',
           'tests/test_rr_response_probe.py','scripts/prepare_rr_response_probe.py',
           'tests/test_unique_keys.py','src/beyond_consensus/models/unique_keys.py',
           'src/beyond_consensus/experiments/rr_response_probe.py']
    return {p:file_hash(Path(root)/p) for p in paths}


def model_settings(interface_profile=None):
    from ..models.competence import CHECKPOINT,REVISION
    return asdict(ModelConfig(backend='transformers',checkpoint=CHECKPOINT,revision=REVISION,
        tokenizer_revision=REVISION,dtype='bfloat16',context_limit=16384,max_new_tokens=2048,
        thinking=True,do_sample=False,action_constraint='reporecourse-json-reliable-v1-pool-7' if interface_profile else 'reporecourse-json-scoped-v1-pool-7'))


def build(root,sources,lane,*,worker=None,planner=None,evidence=None,interface_profile=None):
    if lane not in ('stock_protocol','rich_pilot',UNREVIEWED_LANE):raise BCError('Unknown prospective cohort')
    tasks=('synthetic-stock',) if lane=='stock_protocol' else RICH_TASKS
    planners=('prompted_open',) if lane=='stock_protocol' else cohort.PLANNERS
    rows=[cohort.configuration(t,p,target_rule='all' if lane=='stock_protocol' else 'uniform',interface_profile=interface_profile) for t in tasks for p in planners]
    bindings={}
    for task in tasks:
        try:
            card,public=load_task(task,sources);private=private_task(task)
            bindings[task]=dict(card=card,public_hash=digest(public),private_hash=digest(private),source_error=None)
        except (Rejected,OSError) as exc:
            card=next((c for c in catalog(ROOT/'rich')['tasks'] if c['id']==task),None)
            blocked_card=load(ROOT/'rich'/'blocked-api-integration.json')
            if card is None and blocked_card['id']==task:card=blocked_card
            bindings[task]=dict(card=card,public_hash=None,private_hash=None,source_error=str(exc))
    base=profile.build(root,worker,planner,7,plan_scoped=True,planner_output_cap=6144,interface_profile=interface_profile) if worker and planner else None
    maximum=sum(c['maximum_branches'] for c in rows)
    m=dict(schema=SCHEMA,lane=lane,source_revision=source_revision(root),sources_root=str(Path(sources).resolve()),
        configurations=rows,task_bindings=bindings,model=model_settings(interface_profile),backend_profile=base,
        model_lock_sha256=digest(worker) if worker else None,implementation_hashes=implementation_hashes(),
        evidence=deepcopy(evidence or {}),approval=None,task_execution_allowed=False,confirmatory=False,
        limitations=limitations(lane),shards=len(rows),planned_episodes=None,
        maximum_execution_branches=maximum,maximum_model_planning_sequences=sum(c['planner']=='prompted_open' for c in rows),
        maximum_logical_tokens=maximum*100000,maximum_charged_cpu_seconds=maximum*1200,
        budget_basis='uncalibrated_engineering_cap',episodes=[dict(episode_id=c['configuration_id'],shard=i) for i,c in enumerate(rows)])
    if interface_profile:
        from reporecourse.interface import enabled, bindings
        enabled(interface_profile)
        if lane!=UNREVIEWED_LANE:raise BCError('Interface revision uses the existing unreviewed development lane')
        m['interface_profile']=interface_profile;m['interface_bindings']=bindings()
    if lane==UNREVIEWED_LANE:
        pending=task_review_templates(m)
        review.require(not m['evidence'].get('reviews') or m['evidence']['reviews']==pending,
                       'Unreviewed lane must retain pending task and rights records')
        m['evidence']['reviews']=pending
    return seal(m)


def approval_template(m):
    return dict(schema='rr-cohort-approval-v1',proposal_id=m['experiment_id'],decision='pending',reviewer=None,reviewed_at=None,
        scope_hash=digest({k:v for k,v in m.items() if k not in ('experiment_id','approval','task_execution_allowed')}),
        maximum_execution_branches=m['maximum_execution_branches'],limitations_accepted=limitations(m['lane']))


def task_review_templates(m):
    packs={p['id']:p for p in load(ROOT/'source_registry.json')['packs']}
    return {task:dict(task_hash=digest(b['card']),source_hash=digest(packs[b['card']['pack']]),
        scope='this_cohort_only',decision='pending',reviewer=None,reviewer_role=None,
        reviewed_at=None,evidence=None,independent_review='pending',rights='pending',
        rights_basis=None,rights_reviewer=None,rights_reviewer_role=None,rights_reviewed_at=None,
        **({'underlying_providers':'pending'} if b['card']['pack']=='energy' else {}))
        for task,b in m['task_bindings'].items() if b['card'] and b['card'].get('pack') in packs}


def authorize(m,receipt,root,worker):
    validate(m);verify(m,root,worker)
    review.require(m['approval'] is None,'Already approved')
    expected=approval_template(m)
    review.require(set(receipt)==set(expected) and receipt['decision']=='approved' and
        all(isinstance(receipt.get(k),str) and receipt[k].strip() for k in ('reviewer','reviewed_at')) and
        all(receipt[k]==expected[k] for k in expected.keys()-{'decision','reviewer','reviewed_at'}),'Explicit cohort-scoped approval required')
    out=deepcopy(m);out.update(approval=receipt,task_execution_allowed=True)
    return seal(out)


def validate(m):
    review.require(m.get('schema')==SCHEMA and m.get('experiment_id')==digest({k:v for k,v in m.items() if k!='experiment_id'}),'Cohort manifest integrity')
    tasks=('synthetic-stock',) if m['lane']=='stock_protocol' else RICH_TASKS if m['lane'] in ('rich_pilot',UNREVIEWED_LANE) else ()
    planners=('prompted_open',) if m['lane']=='stock_protocol' else cohort.PLANNERS
    expected=[cohort.configuration(t,p,target_rule='all' if m['lane']=='stock_protocol' else 'uniform',interface_profile=m.get('interface_profile')) for t in tasks for p in planners]
    review.require(bool(tasks) and m['configurations']==expected and m['shards']==len(expected) and
        set(m['task_bindings'])==set(tasks) and m['model']==model_settings(m.get('interface_profile')) and m['limitations']==limitations(m['lane']) and
        m['maximum_execution_branches']==sum(c['maximum_branches'] for c in expected) and
        m['maximum_logical_tokens']==m['maximum_execution_branches']*100000 and
        m['maximum_charged_cpu_seconds']==m['maximum_execution_branches']*1200 and
        m['maximum_model_planning_sequences']==sum(c['planner']=='prompted_open' for c in expected) and
        m['episodes']==[dict(episode_id=c['configuration_id'],shard=i) for i,c in enumerate(expected)] and
        m['planned_episodes'] is None and m['confirmatory'] is False and m['budget_basis']=='uncalibrated_engineering_cap','Cohort scope changed')
    if m.get('interface_profile'):
        from reporecourse.interface import enabled, bindings
        enabled(m['interface_profile'])
        review.require(m['lane']==UNREVIEWED_LANE and m.get('interface_bindings')==bindings(),'Interface revision changed')
    if m['lane']==UNREVIEWED_LANE:
        review.require(m['evidence'].get('reviews')==task_review_templates(m),
                       'Pending review records changed in unreviewed lane')
    if m['backend_profile']:
        profile.validate(m['backend_profile'])
        review.require(m['backend_profile']['model']==m['model'] and m['backend_profile']['source_revision']==m['source_revision'] and
                       m['backend_profile']['model_lock_sha256']==m['model_lock_sha256'],'Role/profile mismatch')
    if m['approval'] is None:review.require(m['task_execution_allowed'] is False,'Missing approval')
    else:
        p=deepcopy(m);p.update(approval=None,task_execution_allowed=False);seal(p)
        receipt=m['approval'];e=approval_template(p)
        review.require(m['task_execution_allowed'] is True and set(receipt)==set(e) and receipt['decision']=='approved' and
            all(isinstance(receipt.get(k),str) and receipt[k].strip() for k in ('reviewer','reviewed_at')) and
            all(receipt[k]==e[k] for k in e.keys()-{'decision','reviewer','reviewed_at'}),'Approval binding changed')
    return SimpleNamespace(model=ModelConfig(**m['model']),shards=m['shards'],task_kind='rr_cohort')


def blockers(m,root,worker=None):
    validate(m);errors=[]
    def need(ok,message):
        if not ok:errors.append(message)
    need(source_revision(root)==m['source_revision'],'source_revision_changed')
    need(m['implementation_hashes']==implementation_hashes(),'runtime_changed')
    need(m['backend_profile'] is not None,'renewed_role_locks_required')
    if m['backend_profile'] is not None:
        try:profile.check_submission(m['backend_profile'],worker,root,'preflight',1)
        except (BCError,KeyError,TypeError,OSError):errors.append('role_lock_qualification_incompatible')
    e=m['evidence'];controls=e.get('controls',{})
    need(controls.get('status')=='passed' and controls.get('schema')=='rr-cohort-controls-v1' and
         controls.get('implementation_hashes')==control_hashes(root) and controls.get('source_revision')==m['source_revision'] and
         controls.get('failures')==controls.get('errors')==controls.get('skipped')==0 and controls.get('tests',0)>=12 and
         controls.get('runtime_versions')==runtime_versions(),'current_no_skip_cohort_controls_required')
    from reporecourse.track_f_controls import PINS
    need(all(runtime_versions().get(k)==v for k,v in PINS.items()),'pinned_cpu_dependencies_required')
    for task,binding in m['task_bindings'].items():
        try:
            card,pub=load_task(task,m['sources_root']);private=private_task(task)
            need(binding==dict(card=card,public_hash=digest(pub),private_hash=digest(private),source_error=None),task+':source_or_task_changed')
            q=e.get('tasks',{}).get(task,{})
            need(q.get('status')=='cpu_qualified_review_pending' and q.get('task_hash')==digest(card) and
                 q.get('implementation_hashes')==implementation_hashes() and q.get('source_integrity') is True and
                 q.get('reset_repeat_identical') is True and q.get('model_executed') is False and q.get('runtime_versions')==runtime_versions(),task+':fresh_task_cpu_qualification_required')
            if m['lane']!=UNREVIEWED_LANE:
                r=e.get('reviews',{}).get(task,{})
                need(r.get('task_hash')==digest(card) and r.get('decision') in ('approved','engineering_exception') and
                     bool(r.get('reviewer')) and bool(r.get('reviewed_at')) and r.get('scope')=='this_cohort_only',task+':specific_task_review_required')
                if r.get('decision')=='engineering_exception':
                    need(r.get('independent_review')=='pending' and r.get('limitations_accepted')==['independent_review_pending','development_engineering_only'],task+':exception_must_preserve_pending_review')
                else:need(r.get('independent_review')=='approved',task+':independent_review_unresolved')
                need(r.get('rights')=='approved' and bool(r.get('rights_basis')),task+':rights_review_required')
                if m['lane']=='rich_pilot':
                    # Experiment consent and author self-review are separate from
                    # the independently attributed review required by this pilot.
                    need(r.get('decision')=='approved' and r.get('independent_review')=='approved' and
                         r.get('reviewer_role')=='independent_reviewer' and bool(r.get('evidence')),
                         task+':independent_review_receipt_required')
                    need(r.get('source_hash')==digest(next(p for p in load(ROOT/'source_registry.json')['packs'] if p['id']==card['pack'])) and
                         bool(r.get('rights_reviewer')) and bool(r.get('rights_reviewer_role')) and bool(r.get('rights_reviewed_at')),
                         task+':attributed_source_rights_receipt_required')
                if card['pack']=='energy':need(r.get('underlying_providers')=='approved',task+':provider_rights_pending')
            # Exact public prompt footprint measured with qualified tokenizer, not guessed from characters.
            footprint=e.get('task_footprints',{}).get(task,{})
            need(footprint.get('public_hash')==digest(pub) and footprint.get('model_lock_sha256')==m['model_lock_sha256'] and
                 footprint.get('implementation_hashes')==implementation_hashes() and footprint.get('status')=='passed' and
                 footprint.get('task_execution_allowed') is False,task+':public_prompt_footprint_required')
            if m.get('interface_profile'):
                from reporecourse.interface import mode
                from reporecourse.action_schema import schema_v2
                ids=[r['id'] for r in pub['required_outputs']];schema=schema_v2(mode('plan'),ids)
                need(footprint.get('public_grammar_binding')==dict(task_id=pub['id'],terminal_ids=ids,schema_sha256=digest(schema),cache_key=digest([mode('plan'),pub['id'],ids,schema]),accepted=True,invalid_output_rejected=True),task+':task_grammar_binding_required')
            expected=prompt_cases(pub,m.get("interface_profile"));measured=footprint.get('cases',[])
            need(len(expected)==len(measured) and all(
                a['id']==b.get('id') and a['role']==b.get('role') and digest(a['messages'])==b.get('messages_hash') and
                b.get('output_cap')==(6144 if a['role']=='plan' else 2048) and type(b.get('input_tokens')) is int and
                0<b['input_tokens']<=16384-b['output_cap'] and b.get('passed') is True
                for a,b in zip(expected,measured)),task+':prompt_measurements_incomplete_or_changed')
            if m['lane'] in ('rich_pilot',UNREVIEWED_LANE):
                actions=[a['action'] for w in private['witnesses'] for a in w['actions']]
                sizes=footprint.get('reference_action_measurements',[])
                need(len(actions)==len(sizes) and all(digest(a)==r.get('action_hash') and
                    r.get('binding_measurement')=='representative-64-hex-version-v1' and
                    type(r.get('action_plus_stop_tokens')) is int and 0<r['action_plus_stop_tokens']<=2048
                    for a,r in zip(actions,sizes)),task+':reference_output_expressibility_required')
        except (Rejected,OSError):errors.append(task+':source_or_card_unavailable')
    audit=e.get('footprint_audit')
    if not audit:errors.append('renewed_gpu_footprint_audit_required')
    else:
        try:
            fresh=review.inspect(audit['run'],audit['snapshots']);need(fresh==audit,'footprint_files_changed')
            report=read_json(Path(audit['run'])/'preflight.json');manifest=read_json(Path(audit['run'])/'manifest.json')
            snapshot=Path(audit['snapshots'])/report['runtime']['snapshot_id'];marker=read_json(snapshot/'snapshot.json')
            need(footprint_compatibility(root,marker)['compatible'],'execution_contract_changed_renew_gpu_footprint')
            need(manifest['model']==m['model'],'footprint_model_changed')
            old=read_json(snapshot/'resolved/model-lock.json')
            need(worker is not None and all(worker.get(k)==old.get(k) for k in ('revision','tokenizer_revision','metadata_hashes','weight_hashes')),'footprint_weights_changed')
        except (BCError,KeyError,OSError):errors.append('invalid_footprint_audit')
    return errors


def verify(m,root,worker):
    errors=blockers(m,root,worker)
    review.require(not errors,'Cohort blocked: '+', '.join(errors))


def submission(m,root,worker,mode,concurrency,output,shard=None):
    review.require(mode=='run' and concurrency==1,'Prospective qualification/pilot uses concurrency one')
    verify(m,root,worker)
    review.require(m['approval'] is not None and m['task_execution_allowed'],'Cohort needs explicit scoped approval')
    output=Path(output)
    review.require(not (output/'cohort-pause.json').exists(),'Cohort paused: preserve unrun configurations; no automatic continuation')
    review.require(not (output/'manifest.json').exists() or read_json(output/'manifest.json')==m,'Output manifest mismatch')
    for e in m['episodes']:
        ep=output/'episodes'/e['episode_id']
        review.require(not (ep/'started.json').exists() or (ep/'result.json').exists(),
                       'Unresolved started configuration: pause remaining cohort, retain evidence')
        if shard is not None and e['shard']!=shard:continue
        review.require(not (ep/'started.json').exists() and not (ep/'result.json').exists(),'Configuration already started: preserve interrupted/unrun evidence; no retry')
    if shard is not None:
        for e in m['episodes'][:shard]:
            path=output/'episodes'/e['episode_id']/'result.json'
            review.require(path.exists(),'Earlier configuration not terminal: fixed cohort order required')
            previous=load_control_record(path)
            review.require(previous.get('provenance',{}).get('manifest_hash')==digest(m) and
                previous.get('status') in ('completed','invalid_plan'),
                'Earlier configuration failed integrity/runtime gates; stop cohort')


def execute_configuration(m,c,public,private,backend,switch,save):
    start=time.process_time()
    if c['planner']=='prompted_open':switch('plan')
    binding={'worker_settings':m['model'],'planner_output_cap':6144,'worker_lock':m['model_lock_sha256'],
             'planner_lock':digest(m['backend_profile']['planner_lock'])}
    frozen=cohort.plan(c,public,binding,backend,save=lambda x:save('planner-journal',x))
    resources=Resources(**deepcopy(frozen['planning_resources']))
    # Include target resolution and adapter work in the once-per-branch planning ledger.
    cohort.schedule(c,frozen)
    try:resources.parent_overhead('prospective_planning_and_resolution',start,0)
    except Rejected:frozen.update(status='invalid_plan',plan=None,error='planning_resource_exhausted')
    frozen['planning_resources']=deepcopy(vars(resources));frozen['frozen_id']=digest({k:v for k,v in frozen.items() if k!='frozen_id'})
    save('frozen-plan',frozen);schedule=cohort.schedule(c,frozen)
    def execute(branches,branch):
        from reporecourse.engine import ModelWorker
        switch('json');checkpoint=None;begin=time.process_time()
        def checkpoint_save(value):
            nonlocal checkpoint
            checkpoint=value;save('checkpoint-'+branch['branch_id'],value)
        try:
            result=v2._execute_branch(branches,branch['branch_id'],public,private,ModelWorker(backend,16384,2048),save=checkpoint_save)
            result.update(fault_fraction=branch['fault_fraction'],within_track_weight=branch['within_track_weight'])
            return result
        except (Exception,KeyboardInterrupt) as exc:
            raw=checkpoint['engine']['resources'] if checkpoint else frozen['planning_resources']
            r=Resources(**deepcopy(raw))
            for token in list(r.reservations):r.reconcile(token)
            for n in list(r.cpu_pending):
                try:r.reconcile_cpu('interrupted_cohort_branch',n,None)
                except Rejected:pass
            try:r.parent_overhead('failed_branch_adapter',begin,len(frozen['planning_resources']['events']))
            except Rejected:pass
            exhausted=isinstance(exc,Rejected) and str(exc) in ('cpu_cap','token_cap','context_limit')
            return dict(status='resource_exhausted' if exhausted else 'interrupted' if isinstance(exc,(KeyboardInterrupt,InterruptedError)) else 'infrastructure_failed',
                success=False if exhausted else None,error_type=type(exc).__name__,resource_profile=r.summary(),
                planning_logical_charged_each_branch=True,mode='real_model',checkpoint=checkpoint)
    return cohort.run_scheduled(c,schedule,execute,save)


def run(m,output,root,*,model_lock,shard=None,retry_failures=False):
    review.require(type(shard) is int and 0<=shard<m['shards'] and not retry_failures and model_lock is not None,'Explicit configuration shard, no retry')
    worker=read_json(model_lock);output=Path(output)
    submission(m,root,worker,'run',1,output,shard)
    from ..models.transformers_backend import require_allocation
    require_allocation();c=m['configurations'][shard];ep=output/'episodes'/c['configuration_id'];ep.mkdir(parents=True,exist_ok=True)
    with directory_lock(ep/'.lock'):
        submission(m,root,worker,'run',1,output,shard)
        atomic_json(output/'manifest.json',m);atomic_json(ep/'started.json',{'manifest_hash':digest(m)})
        handlers={};backend=None
        def save(name,data):atomic_json(ep/(name+'.json'),dict(manifest_hash=digest(m),content=data))
        def stop(*_):raise InterruptedError('allocation_termination')
        for sig in (signal.SIGTERM,signal.SIGINT):handlers[sig]=signal.signal(sig,stop)
        try:
            backend,switch,_=profile.qualified_backend(m['backend_profile'],model_lock,root)
            prior=read_json(Path(m['evidence']['footprint_audit']['run'])/'preflight.json')['runtime']
            for key in ('hardware','compute_capability','vram_total_bytes','torch_cuda','dependencies'):
                review.require(backend.runtime[key]==prior[key],'Allocation differs from footprint: '+key)
            _,public=load_task(c['task'],m['sources_root']);private=private_task(c['task'])
            row=execute_configuration(m,c,public,private,backend,switch,save)
        except (Exception,KeyboardInterrupt) as exc:
            row=dict(configuration_id=c['configuration_id'],status='interrupted' if isinstance(exc,(KeyboardInterrupt,InterruptedError)) else 'infrastructure_failed',
                     branches=[],planning=None,error_type=type(exc).__name__,target_status='unresolved')
            for name in ('configuration-result','schedule','frozen-plan','planner-journal'):
                path=ep/(name+'.json')
                if path.exists():row[name.replace('-','_')]=load_control_record(path)['content']
            f=row.get('frozen_plan') or row.get('planner_journal',{}).get('frozen')
            if f:row['planning']=f
            elif row.get('planner_journal',{}).get('resources'):
                resources=Resources(**deepcopy(row['planner_journal']['resources']))
                for key in list(resources.reservations):resources.reconcile(key)
                for allowance in list(resources.cpu_pending):
                    try:resources.reconcile_cpu('interrupted_prospective_planning',allowance,None)
                    except Rejected:pass
                row['planning_interrupted_usage']=resources.summary()
        finally:
            for sig,handler in handlers.items():signal.signal(sig,handler)
        row.update(experiment_id=m['experiment_id'],provenance={'manifest_hash':digest(m)},runtime=backend.runtime if backend else None,
                   evidence='real_model',confirmatory=False,retry_allowed=False)
        save('configuration-result',row);atomic_json(ep/'result.json',row)
        if row['status'] in ('paused','interrupted','infrastructure_failed'):
            atomic_json(output/'cohort-pause.json',dict(experiment_id=m['experiment_id'],configuration_id=c['configuration_id'],
                reason=row.get('pause_reason') or row['status'],remaining_configurations='unrun',retry_allowed=False))
        return [row]


def aggregate(m,output):
    validate(m);records={}
    for c in m['configurations']:
        ep=Path(output)/'episodes'/c['configuration_id'];path=ep/'result.json'
        if path.exists():
            r=load_control_record(path)
            review.require(r.get('experiment_id')==m['experiment_id'] and r.get('configuration_id')==c['configuration_id'] and r.get('provenance',{}).get('manifest_hash')==digest(m),'Cohort result provenance')
            records[c['configuration_id']]=r
        elif (ep/'started.json').exists() and not (ep/'schedule.json').exists():
            r=dict(configuration_id=c['configuration_id'],status='interrupted',planning=None,branches=[],target_status='unresolved')
            journal=ep/'planner-journal.json'
            if journal.exists():
                saved=load_control_record(journal)
                review.require(saved.get('manifest_hash')==digest(m),'Interrupted planner provenance changed')
                content=saved['content']
                if content.get('frozen'):r['planning']=content['frozen']
                elif content.get('resources'):
                    resources=Resources(**deepcopy(content['resources']))
                    for key in list(resources.reservations):resources.reconcile(key)
                    for allowance in list(resources.cpu_pending):
                        try:resources.reconcile_cpu('interrupted_planning_observation',allowance,None)
                        except Rejected:pass
                    r['planning_interrupted_usage']=resources.summary()
            records[c['configuration_id']]=r
        # Recover coverage from durable records after an allocation was killed.
        # This is read-only analysis, never a resume or a generation retry.
        schedule_path=ep/'schedule.json'
        if schedule_path.exists() and (c['configuration_id'] not in records or not records[c['configuration_id']].get('branches')):
            saved=load_control_record(schedule_path)
            review.require(saved.get('manifest_hash')==digest(m),'Schedule provenance changed')
            schedule=saved['content'];cohort.check_schedule(c,schedule)
            branches=[]
            for branch in (schedule['branches']['rows'] if schedule['branches'] else []):
                p=ep/('branch-'+branch['branch_id']+'.json')
                if p.exists():
                    saved_branch=load_control_record(p)
                    review.require(saved_branch.get('manifest_hash')==digest(m),'Branch provenance changed')
                    result=saved_branch['content']
                    review.require(all(result.get(k)==branch[k] for k in ('branch_id','track','target')),'Branch identity mismatch')
                else:
                    started=(ep/('branch-start-'+branch['branch_id']+'.json')).exists()
                    result=dict(branch_id=branch['branch_id'],track=branch['track'],target=branch['target'],
                                status='interrupted' if started else 'unrun',success=None)
                    checkpoint=ep/('checkpoint-'+branch['branch_id']+'.json')
                    if checkpoint.exists():
                        data=load_control_record(checkpoint)
                        review.require(data.get('manifest_hash')==digest(m),'Checkpoint provenance changed')
                        raw=data['content'];review.require(raw.get('branch_id')==branch['branch_id'] and raw.get('manifest_id')==schedule['branches']['manifest_id'],'Checkpoint binding changed')
                        resources=Resources(**deepcopy(raw['engine']['resources']))
                        for key in list(resources.reservations):resources.reconcile(key)
                        for allowance in list(resources.cpu_pending):
                            try:resources.reconcile_cpu('interrupted_branch_observation',allowance,None)
                            except Rejected:pass
                        result['resource_profile']=resources.summary()
                branches.append(result)
            records[c['configuration_id']]=dict(configuration_id=c['configuration_id'],planning=schedule['frozen'],
                status='interrupted' if schedule['branches'] else schedule['planning_status'],target_status=schedule['target_status'],branches=branches,
                read_only_reconstruction=True)
        if c['configuration_id'] in records and records[c['configuration_id']].get('branches'):
            r=records[c['configuration_id']]
            review.require(schedule_path.exists(),'Branch results without a prospectively saved schedule')
            saved=load_control_record(schedule_path)
            review.require(saved.get('manifest_hash')==digest(m),'Schedule provenance changed')
            schedule=saved['content'];cohort.check_schedule(c,schedule)
            review.require(r.get('planning')==schedule['frozen'],'Result planning changed')
            expected=schedule['branches']['rows'] if schedule['branches'] else []
            review.require(len(expected)==len(r['branches']) and all(
                all(a[k]==b.get(k) for k in ('branch_id','track','target')) for a,b in zip(expected,r['branches'])),
                'Result branch coverage changed')
    summary=cohort.summarize(m['configurations'],records)
    for row in summary['configurations']:
        card=m['task_bindings'][row['task']]['card'] or {}
        row.update(task_version=card.get('task_version'),grounding=card.get('grounding'),source_group=card.get('source_group'),
                   independent_review=card.get('independent_review'))
        public_path=(ROOT/'rich' if row['task'] in RICH_TASKS else ROOT)/'public'/(row['task']+'.json')
        row['required_outputs']=len(load(public_path)['required_outputs']) if public_path.exists() else None
        row['task_review_receipt']=deepcopy(m['evidence'].get('reviews',{}).get(row['task']))
    source_summary={}
    for row in summary['configurations']:
        source_summary.setdefault(row['source_group'],{}).setdefault(row['planner'],[]).append(row)
    summary['per_source']={source:{planner:cohort.track_summary(rows) for planner,rows in planners.items()}
                           for source,planners in source_summary.items()}
    return dict(summary,experiment_id=m['experiment_id'],lane=m['lane'],
                review_status='deferred_by_user' if m['lane']==UNREVIEWED_LANE else 'see_task_review_receipts',
                limitations=deepcopy(m['limitations']),
                source_groups={t:b['card']['source_group'] if b['card'] else None for t,b in m['task_bindings'].items()},
                evidence='real_model_results_or_unrun',confirmatory=False,maximum_execution_branches=m['maximum_execution_branches'])


def prompt_cases(public,interface_profile=None):
    """Fixed public-only admission scenarios, not a universal history fit proof."""
    import json
    from reporecourse.engine import worker_messages
    from reporecourse.runtime import Environment
    c=cohort.configuration(public['id'],'prompted_open',interface_profile=interface_profile)['config']
    req=v2.request(public,c)
    cases=[dict(id='planner_initial',role='plan',messages=v2.planner_messages(req))]
    for name,value in sorted(public['sources'].items()):
        cases.append(dict(id='planner_source_'+name,role='plan',messages=v2.planner_messages(req)+[
            {'role':'assistant','content':json.dumps({'tool':'read_source','name':name})},
            {'role':'user','content':json.dumps(value)}]))
    # Construct actual mediated initial worker observations with no SQL execution.
    p=v2.requirement_plan(public,c)
    env=Environment(public,resources=Resources(100000,1200),workers=c['workers'],plan=p,execution_contract='plan_scoped_v1',interface_profile=interface_profile)
    try:
        for unit in p['units']:
            env.scopes.begin(unit,unit['worker'],'primary');env.assignment[unit['worker']]=unit
            obs=env.observation(unit['worker'])
            # Fixed qualification scenario, never a reset of runtime resources.
            # Materialization CPU varies across hosts; it is not prompt content
            # that can be hash-bound across independent footprint verification.
            obs.update(remaining_tokens=100000,cpu_remaining=1200)
            cases.append(dict(id='worker_initial_'+unit['id'],role='json',messages=worker_messages(obs,[])))
            for name,value in sorted(public['sources'].items()):
                history=[{'role':'assistant','content':json.dumps({'tool':'read_source','name':name})},
                         {'role':'user','content':json.dumps(value)}]
                cases.append(dict(id='worker_source_'+unit['id']+'_'+name,role='json',messages=worker_messages(obs,history)))
    finally:env.close()
    if interface_profile:
        from reporecourse.interface import feedback, finding, plan_feedback, example_plan
        bad=example_plan();bad['units'][0]['outputs']=['invented_rows']
        cases.append(dict(id='planner_validation_feedback',role='plan',messages=v2.planner_messages(req)+[{'role':'user','content':json.dumps(plan_feedback(bad,public,'output'))}]))
        error=feedback([finding('content_type','content','{}','object','Emit an object, not JSON text.')])
        cases.append(dict(id='worker_validation_feedback',role='json',messages=worker_messages(obs,[{'role':'user','content':json.dumps(error)}])))
    return cases


def measure_prompts(task,sources,worker,interface_profile=None):
    from transformers import AutoTokenizer
    from ..models.transformers_backend import verify_thinking_template
    from ..models.competence import require_qualification,versions
    require_qualification(worker,versions(),16384,model_settings(interface_profile)['action_constraint'],2048)
    _,public=load_task(task,sources)
    tokenizer=AutoTokenizer.from_pretrained(worker['tokenizer_path'],local_files_only=True,trust_remote_code=False)
    template=verify_thinking_template(tokenizer,True)
    rows=[]
    for case in prompt_cases(public,interface_profile):
        ids=tokenizer.apply_chat_template(case['messages'],tokenize=True,add_generation_prompt=True,enable_thinking=True,return_dict=True)['input_ids']
        cap=6144 if case['role']=='plan' else 2048
        rows.append(dict(id=case['id'],role=case['role'],messages_hash=digest(case['messages']),
            rendered_input_ids_hash=digest(ids),input_tokens=len(ids),output_cap=cap,passed=len(ids)+cap<=16384))
    import json
    grammar_binding=None
    if interface_profile:
        from ..models.constrained import ActionConstraint
        from reporecourse.interface import mode
        from reporecourse.action_schema import schema_v2
        from .rr_open_footprint import parse
        metadata=read_json(Path(worker['model_path'])/'config.json');vocab=metadata.get('text_config',metadata)['vocab_size']
        terminals=[r['id'] for r in public['required_outputs']]
        constraint=ActionConstraint(tokenizer,vocab,worker['decoder_qualification']['effective_generation_tokens']['eos_token_id'],mode('plan'),public_task=public['id'],terminal_ids=terminals)
        sample=v2.requirement_plan(public,cohort.configuration(public['id'],'prompted_open',interface_profile=interface_profile)['config'])
        for u in sample['units']:
            u['interfaces']={k:'Public terminal artifact.' for k in u['produces']};u['terminal_bindings']={k:k for k in u['outputs']}
        ids=tokenizer.encode(json.dumps({'tool':'submit_plan','plan':sample},separators=(',',':')),add_special_tokens=False)
        matcher=constraint.xgr.GrammarMatcher(constraint.compiled)
        accepted=all(matcher.accept_token(t) for t in [*ids,worker['decoder_qualification']['effective_generation_tokens']['eos_token_id'][0]])
        bad=deepcopy(sample);bad['units'][0]['outputs']=['not_a_terminal']
        bad_ids=tokenizer.encode(json.dumps({'tool':'submit_plan','plan':bad},separators=(',',':')),add_special_tokens=False)
        negative=constraint.xgr.GrammarMatcher(constraint.compiled)
        rejected=not all(negative.accept_token(t) for t in [*bad_ids,worker['decoder_qualification']['effective_generation_tokens']['eos_token_id'][0]])
        grammar_binding=dict(constraint.runtime['public_grammar_binding'],accepted=accepted,invalid_output_rejected=rejected)
    sizes=[]
    for w in private_task(task)['witnesses']:
        for item in w['actions']:
            action=item['action']
            measured=deepcopy(action)
            if 'bindings' in measured:
                measured['bindings']={k:digest(['footprint-version',k]) for k in measured['bindings']}
            tokens=len(tokenizer.encode(json.dumps(measured,separators=(',',':')),add_special_tokens=False))+1
            sizes.append(dict(action_hash=digest(action),action_plus_stop_tokens=tokens,
                              binding_measurement='representative-64-hex-version-v1'))
    return dict(schema='rr-cohort-public-footprint-v1',task=task,public_hash=digest(public),model_lock_sha256=digest(worker),
        implementation_hashes=implementation_hashes(),template=template,cases=rows,public_grammar_binding=grammar_binding,
        status='passed' if (grammar_binding is None or (grammar_binding['accepted'] and grammar_binding['invalid_output_rejected'])) and all(r['passed'] for r in rows) and all(r['action_plus_stop_tokens']<=2048 for r in sizes) else 'failed',
        reference_action_measurements=sizes,reference_measurement_scope='Evaluator-side serialization only; no solution text exported; representative version IDs; reasoning and worst-case tokenization unmeasured; not a shortest solution.',
        model_executed=False,task_sql_executed=False,
        sql_executed=public['family']=='data_product',qualification_budget_display={'remaining_tokens':100000,'cpu_remaining':1200},
        task_execution_allowed=False,worst_case_fit_established=False,
        limitation='Initial assignment and one-source observations only; later history can still exhaust context.')


def export(run):
    run=Path(run);m=load_control_record(run/'manifest.json');summary=aggregate(m,run)
    inputs=[];labels=[]
    for c in m['configurations']:
        ep=run/'episodes'/c['configuration_id'];path=ep/'result.json'
        r=load_control_record(path) if path.exists() else None
        f=r.get('planning') if r else None
        inputs.append(dict(configuration_id=c['configuration_id'],task=c['task'],planner=c['planner'],
                           planner_input=f['request']['planner_input'] if f else None))
        labels.append(dict(configuration_id=c['configuration_id'],future_label=True,result=r,
            audit_records={p.stem:load_control_record(p) for p in sorted(ep.glob('*.json')) if p.name!='result.json'}))
    return dict(schema='rr-cohort-export-v1',experiment_id=m['experiment_id'],public_planner_inputs=inputs,
        future_outcome_labels=labels,summary=summary,manifest_hash=digest(m),model_executed=False,sql_executed=False,
        historical_scores_changed=False,evidence='read_only_real_run_export_including_failed_and_unrun',training_authorized=False)


def public_export(run):
    """No journals, source bodies, execution state or hidden evaluation records."""
    private=export(run)
    summary=deepcopy(private['summary'])
    for row in summary['configurations']:
        row.pop('branches',None)
        row.pop('task_review_receipt',None)
        for b in row.get('branch_metrics',[]):
            d=b.get('offline_diagnostics',{})
            d.pop('raw_per_output_checks',None);d.pop('bundle_consistency_checks',None)
        for key in ('planning_resources','interrupted_planning_usage'):
            resources=row.get(key)
            if resources:resources.pop('events',None)
    return dict(schema='rr-cohort-public-export-v1',experiment_id=private['experiment_id'],
        public_planner_inputs=private['public_planner_inputs'],summary=summary,
        future_labels=True,training_authorized=False,model_executed=False,sql_executed=False,
        historical_scores_changed=False)
