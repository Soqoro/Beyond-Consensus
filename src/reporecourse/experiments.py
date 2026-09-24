"""Scheduler-independent manifests, grouped coverage and prospective gates."""
from copy import deepcopy
from pathlib import Path
from .common import Rejected,digest,load
from .tasks import catalog,load_task
from .resources import PROFILE
from .policies import choose_plan,organization_key

SCHEMA='rr-manifest-v1'


def build(sources,task_ids,model,source_revision,*,smoke=False,qualification=None,sensitivity=False,resource=None,model_lock_hash=None):
    cards=[];publics={}
    if len(set(task_ids))!=len(task_ids) or not task_ids:raise Rejected('task_selection')
    for tid in task_ids:
        c,p=load_task(tid,sources);cards.append(c);publics[tid]=p
    if smoke and len(cards)!=1:raise Rejected('smoke_one_task')
    resource=resource or {'profile':PROFILE,'token_cap':100000,'cpu_cap':1200,'budget_basis':'uncalibrated_engineering_cap'}
    if resource.get('profile')!=PROFILE:raise Rejected('resource_profile')
    base=dict(schema=SCHEMA,source_revision=source_revision,sources_root=str(Path(sources).resolve()),
        model_lock_sha256=model_lock_hash,tasks=cards,public_hashes={k:digest(v) for k,v in publics.items()},model=model,resource=resource,
        qualification=qualification,shards=1,engineering_smoke=smoke,confirmatory=False,
        lane='authored_finite' if sensitivity else 'requirement_delegation',
        budget_calibration=None,model_competence=None,independent_review='pending',
        retry_policy='interrupted/infrastructure only; previous actual and uncertain work retained; terminal failures never retried',
        full_balanced_gate_applicable=False,policy_campaign_enabled=False)
    exp=digest(base);episodes=[]
    for tid in task_ids:
        p=publics[tid]
        outlines=[x['id'] for x in p['outlines']] if sensitivity else ['independent']
        for policy in (['delegation_jit'] if smoke or sensitivity else ['delegation_jit','solo']):
            for seed in ([0] if smoke else [0,1]):
                for outline in outlines:
                    plan=choose_plan(p,policy,outline)
                    targets=sorted({u['worker'] for u in plan['units']}) if sensitivity else []
                    for target in [None,*targets]:
                        row=dict(experiment_id=exp,task_id=tid,source_group=next(c['source_group'] for c in cards if c['id']==tid),
                            family=p['family'],policy=policy,outline=outline,plan=plan,seed=seed,
                            track='clean' if target is None else 'F',target=target,shard=0,resource_profile=PROFILE)
                        row['episode_id']=digest(row);episodes.append(row)
    return {**base,'experiment_id':exp,'planned_episodes':len(episodes),'episodes':episodes}


def validate(m):
    if m.get('schema')!=SCHEMA or m.get('resource',{}).get('profile')!=PROFILE:raise Rejected('manifest_schema')
    base={k:v for k,v in m.items() if k not in ('experiment_id','episodes','planned_episodes')}
    if digest(base)!=m['experiment_id'] or m['planned_episodes']!=len(m['episodes']):raise Rejected('manifest_integrity')
    ids=set()
    for row in m['episodes']:
        if row['episode_id']!=digest({k:v for k,v in row.items() if k!='episode_id'}) or row['episode_id'] in ids:
            raise Rejected('episode_integrity')
        ids.add(row['episode_id'])
        if row['experiment_id']!=m['experiment_id'] or row['resource_profile']!=PROFILE:raise Rejected('episode_profile')
    return m


def require_run(m):
    validate(m)
    if not m['engineering_smoke']:
        raise Rejected('development_review_competence_calibration_gates_pending')
    if len(m['tasks'])!=1 or len(m['episodes'])!=1 or m['episodes'][0]['track']!='clean':
        raise Rejected('engineering_smoke_one_clean_episode')
    q=m.get('qualification')
    if not q or q['status']!='cpu_qualified_review_pending' or q['task_hash']!=digest(m['tasks'][0]):
        raise Rejected('current_cpu_qualification_required')
    if m['tasks'][0]['pack']=='energy':raise Rejected('underlying_provider_license_review_pending')
    # Source/task hashes checked again by the adapter against the frozen checkout.


def aggregate(manifest,output):
    validate(manifest);groups={};missing=[];rows={}
    for e in manifest['episodes']:
        p=Path(output)/'episodes'/e['episode_id']/'result.json'
        key='/'.join([e['source_group'],e['family'],e['policy'],e['outline'],e['track']])
        g=groups.setdefault(key,{'planned':0,'observed':0,'successes':0,'infrastructure':0,'missing':0,'tokens':0,
            'uncertain_tokens':0,'eligible_clean_correct':0,'attacked_failures_clean_correct':0,'no_intervention':0,'source_groups':set()})
        g['planned']+=1;g['source_groups'].add(e['source_group'])
        if not p.exists():g['missing']+=1;missing.append(e['episode_id']);continue
        r=load(p)
        if r['experiment_id']!=manifest['experiment_id'] or r['episode_id']!=e['episode_id'] or r['resource_profile']['profile']!=PROFILE or r['track']!=e['track']:
            raise Rejected('result_profile_mismatch')
        if r.get('provenance')!={'manifest_hash':digest(e)}:raise Rejected('result_provenance_mismatch')
        rows[e['episode_id']]=r;g['observed']+=1;g['successes']+=r.get('success') is True
        g['infrastructure']+=r['status'] in ('interrupted','infrastructure_failed','blocked_prerequisite')
        g['tokens']+=r['resource_profile']['actual_tokens'];g['uncertain_tokens']+=r['resource_profile']['uncertain_tokens']
        g['no_intervention']+=r.get('no_intervention',False)
    for e in manifest['episodes']:
        if e['track']=='clean' or e['episode_id'] not in rows:continue
        clean=next((x for x in manifest['episodes'] if x['track']=='clean' and all(x[k]==e[k] for k in ('task_id','policy','outline','seed'))),None)
        if clean and rows.get(clean['episode_id'],{}).get('success') is True:
            r=rows[e['episode_id']]
            if r['status'] in ('completed','resource_exhausted'):
                g=groups['/'.join([e['source_group'],e['family'],e['policy'],e['outline'],e['track']])]
                g['eligible_clean_correct']+=1;g['attacked_failures_clean_correct']+=r.get('success') is not True
    for g in groups.values():
        g['source_groups']=sorted(g['source_groups'])
        g['complete_coverage']=g['missing']==0 and g['infrastructure']==0
        g['complete_at_budget']=g['successes']/g['planned'] if g['complete_coverage'] else None
        g['score_null_reason']=None if g['complete_coverage'] else 'missing_or_infrastructure_observations'
        g['ASR_cc']=g['attacked_failures_clean_correct']/g['eligible_clean_correct'] if g['eligible_clean_correct'] else None
    return {'schema':'rr-summary-v1','experiment_id':manifest['experiment_id'],'resource_profile':PROFILE,
        'groups':groups,'missing_episode_ids':missing,'planned':manifest['planned_episodes'],
        'model_executed':any(r.get('model_executed',False) for r in rows.values()),'confirmatory':False,
        'uncertainty':'development source-group counts only; no episode-independent inference'}


def calibration_plan():
    return {'schema':'rr-calibration-plan-v1','executed':False,'resource_profile':PROFILE,
        'grouping':['family','backbone','tool_contract','planner_contract','source_split'],
        'baseline':'ordinary requirement delegation','include_failures':True,
        'statistic':'nearest-rank 75th percentile of observed completion token cost; right-censored runs retained; if percentile is censored B0 unresolved',
        'multipliers':[1.25,1.5,2,3],'initial_multiplier':1.5,'B0':None,
        'pilot_token_ceiling':'prespecify before calibration outcomes; legacy surrogate not accepted',
        'full_12_task_clean_grid':48,'engineering_gate_full_balanced_only':{'team':18,'team_total':24,'each_family':8,'each_family_total':12}}
