"""Exact, non-confirmatory Jaffle handoff-loss engineering scope.

No scheduler or model implementation lives here. Historical resolution is an
adapter responsibility; all three rows use the existing engine and JIT policy.
"""
from copy import deepcopy
from pathlib import Path
from .common import Rejected, digest, load
from .resources import ACCOUNTING, PROFILE

TYPE = 'reporecourse_track_f_engineering_v1'
TASK = 'jaffle-recorded-payments'
CONDITIONS = ('fresh_clean', 'loss_w0', 'loss_w1')
REVISION = 'fc05daec18b0a78c049392ed2e771dde82bdf654'
TRIGGER = 'first_assigned_publication_v1'
RESOURCE = dict(profile=PROFILE, token_cap=100000, cpu_cap=1200,
                budget_basis='uncalibrated_engineering_cap')
CONTROLS = ('fresh_clean', 'loss_w0', 'loss_w1', 'wrong_repair', 'nontrigger',
            'resume_before', 'resume_after', 'visibility', 'finish_then_repair')


def build(base, historical):
    """Copy resolved historic settings; current qualifications remain mandatory."""
    h = historical['manifest']; old = h['episodes'][0]
    m = deepcopy(base)
    for k in ('experiment_id', 'episodes', 'planned_episodes'):m.pop(k)
    m.update(experiment_type=TYPE, engineering_smoke=False, shards=3,
             historical_resolution=deepcopy(historical), model=deepcopy(h['model']),
             resource=deepcopy(h['resource']), max_actions=historical['max_actions'],
             accounting_version=ACCOUNTING, fault_rule=TRIGGER)
    exp = digest(m); rows = []
    for index, condition in enumerate(CONDITIONS):
        row = deepcopy(old)
        row.pop('episode_id')
        row.update(experiment_id=exp, condition=condition, shard=index,
                   track='clean' if index == 0 else 'F',
                   target=None if index == 0 else 'w'+str(index-1))
        row['episode_id'] = digest(row); rows.append(row)
    m.update(experiment_id=exp, episodes=rows, planned_episodes=3)
    require(m)
    return m


def require(m):
    from .experiments import validate
    validate(m)
    h = m.get('historical_resolution', {})
    old = h.get('manifest', {})
    validate(old)
    rows = old['episodes']
    if (len(rows)!=1 or not old.get('engineering_smoke') or rows[0]['track']!='clean'
        or rows[0]['target'] is not None or rows[0]['task_id']!=TASK
        or rows[0]['policy']!='delegation_jit' or rows[0]['outline']!='independent'
        or type(rows[0]['seed']) is not int):raise Rejected('track_f_historical_control')
    if h.get('manifest_hash')!=digest(old) or not h.get('snapshot_hash') or not h.get('result_hash'):
        raise Rejected('track_f_historical_provenance')
    model=old['model']
    required=dict(backend='transformers', checkpoint='Qwen/Qwen3.5-27B', revision=REVISION,
                  tokenizer_revision=REVISION, dtype='bfloat16', context_limit=16384,
                  max_new_tokens=2048, thinking=True, do_sample=False,
                  action_constraint='reporecourse-json-v1')
    if any(model.get(k)!=v for k,v in required.items()) or m['model']!=model:
        raise Rejected('track_f_model')
    if (m.get('experiment_type')!=TYPE or m['tasks']!=old['tasks'] or len(m['tasks'])!=1
        or m['tasks'][0]['id']!=TASK or m['public_hashes']!=old['public_hashes']
        or m['resource']!=RESOURCE or old['resource']!=RESOURCE
        or m.get('max_actions')!=24 or h.get('max_actions')!=24
        or m.get('accounting_version')!=ACCOUNTING or m.get('fault_rule')!=TRIGGER
        or m['shards']!=3 or m['planned_episodes']!=3 or m['engineering_smoke']
        or m['confirmatory'] or m['policy_campaign_enabled']
        or m['independent_review']!='pending' or m['lane']!='requirement_delegation'):
        raise Rejected('track_f_exact_scope')
    expected_plan=rows[0]['plan']
    if expected_plan.get('id')!='independent' or [(u['id'],u['worker'],u['outputs'],u['depends']) for u in expected_plan['units']] != [
        ('customer_summary','w0',['customer_summary'],[]),('method_summary','w1',['method_summary'],[])]:
        raise Rejected('track_f_assignments')
    for i,row in enumerate(m['episodes']):
        expected=deepcopy(rows[0]);expected.pop('episode_id')
        expected.update(experiment_id=m['experiment_id'],condition=CONDITIONS[i],shard=i,
                        track='clean' if i==0 else 'F',target=None if i==0 else 'w'+str(i-1))
        expected['episode_id']=digest(expected)
        if row!=expected:raise Rejected('track_f_exact_conditions')
    q=m.get('qualification') or {}; f=q.get('track_f_controls') or {}
    if (q.get('status')!='cpu_qualified_review_pending' or q.get('task_hash')!=digest(m['tasks'][0])
        or f.get('status')!='passed' or f.get('accounting_version')!=ACCOUNTING
        or f.get('public_hash')!=m['public_hashes'][TASK]
        or set(f.get('controls',{}))!=set(CONTROLS)
        or not all(v is True for v in f['controls'].values())):
        raise Rejected('track_f_current_cpu_controls_required')


def read_result(m, output, row):
    path=Path(output)/'episodes'/row['episode_id']/'result.json'
    if not path.exists():return None
    result=load(path)
    if (result.get('experiment_id')!=m['experiment_id'] or result.get('episode_id')!=row['episode_id']
        or result.get('provenance')!={'manifest_hash':digest(row)}):
        raise Rejected('track_f_result_provenance')
    return result


def classification(row):
    if row is None:return 'unlaunched'
    failures=row.get('failures',[])
    if any(f.get('category') in ('episode_closed','worker_unavailable_dispatch','fixed_state_graph_mismatch') for f in failures):
        return 'harness_state_or_dispatch_failure'
    if row['status'] in ('interrupted','infrastructure_failed','blocked_prerequisite'):
        return 'interrupted_or_infrastructure'
    r=row['resource_profile']
    if (row['status']=='resource_exhausted' or r['cpu_cap_debit']>r['cpu_cap']
        or r['actual_tokens']+r['uncertain_tokens']>r['token_cap']):return 'resource_cap_failure'
    if row.get('intervention_triggered'):
        # Success alone does not demonstrate reconstruction by an eligible worker.
        target=row.get('target'); events=row.get('events',[])
        loss=next((i for i,e in enumerate(events) if e['type']=='unavailable'),None)
        bound=row.get('state',{}).get('bound',{})
        missing=set(events[loss].get('missing_assignments',[])) if loss is not None else set()
        repaired=bool(missing) and all(any(e['type']=='publish' and e.get('worker')!=target
            and o in e.get('obligations',[]) and e.get('version')==bound.get(o)
            for e in events[loss+1:]) for o in missing)
        return 'correct_after_applied_loss_and_reconstruction' if row.get('success') and repaired else 'triggered_loss_failed_or_missing_repair'
    return 'correct_without_applied_loss' if row.get('success') else 'primary_query_or_semantic_failure'


def select(m, output, condition):
    require(m)
    if condition not in CONDITIONS:raise Rejected('track_f_select_one_condition')
    index=CONDITIONS.index(condition)
    if index:
        clean=read_result(m,output,m['episodes'][0])
        if not clean or clean.get('success') is not True or classification(clean)!='correct_without_applied_loss':
            raise Rejected('track_f_stop_clean_not_passed')
    if index==2:
        previous=read_result(m,output,m['episodes'][1])
        if not previous or classification(previous) in ('harness_state_or_dispatch_failure','interrupted_or_infrastructure','resource_cap_failure'):
            raise Rejected('track_f_stop_review_previous_loss')
    return index


def report(m, output):
    require(m); rows=[]
    for e in m['episodes']:
        r=read_result(m,output,e)
        item=dict(condition=e['condition'],episode_id=e['episode_id'],classification=classification(r),
                  status='unlaunched' if r is None else r['status'], initial_plan=e['plan'],
                  selected_target=e['target'],seed=e['seed'])
        if r:
            keys=('success','model_executed','mode','intervention_triggered','no_intervention','evaluation',
                  'public_alarm','failures','events','resource_profile','post_alarm_tokens','post_alarm_cpu',
                  'retained_versions','execution_facts','error','error_category','stack_locations')
            item.update({k:r[k] for k in keys if k in r})
            # Public event/resource evidence, never queries, sources or hidden fixtures.
            item['evaluation']={k:r.get('evaluation',{}).get(k) for k in ('status','success','obligations','evaluator_resources')}
            state=r.get('state',{})
            item['bound_versions']=state.get('bound',{})
            item['unavailable']=state.get('unavailable',[])
            item['artifact_inventory']=[{'version':v,**{k:a.get(k) for k in ('author','name','sequence')}}
                for v,a in state.get('artifacts',{}).items()]
        rows.append(item)
    return dict(schema='rr-track-f-report-v1',experiment_id=m['experiment_id'],analysis_model_executed=False,
                analysis_sql_executed=False,historical_scores_changed=False,conditions=rows,
                provenance={k:m[k] for k in ('source_revision','public_hashes','model','model_lock_sha256','resource','accounting_version')},
                runtime_hash=digest(m['qualification'].get('implementation_hashes',{})),
                resource_profile_hash=digest([m['resource'],m['accounting_version']]),
                historical_resolution_hash=digest(m['historical_resolution']),
                manifest_hash=digest(m),task_hash=digest(m['tasks']),outline_hash=digest(m['episodes'][0]['plan']),
                qualification_hash=digest(m['qualification']),confirmatory=False,
                interpretation='Three engineering episodes on one demo task; no population or policy-superiority inference.')
