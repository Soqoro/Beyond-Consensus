"""Standalone, stdlib command boundary for v0.2. GPU execution stays gated."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from .common import load,write_new,Rejected
from . import v2
from .tasks import load_task,private_task,catalog
from .resources import Resources


def main(argv=None):
    p=argparse.ArgumentParser(description='RepoRecourse v0.2 local preparation and reference controls; no automatic GPU jobs')
    p.add_argument('command',choices=('request','plans','freeze','resolve','demo','qualify','aggregate','export','readiness','compare','b0','slurm-dry-run','select','validate','evidence','prompted-plan'))
    p.add_argument('--sources',type=Path,default=Path('/nonexistent-sources'))
    p.add_argument('--task',default='synthetic-stock');p.add_argument('--pool',type=int,default=4)
    p.add_argument('--lane',choices=('open','shared_catalog','fixed_plan'),default='open')
    p.add_argument('--count-mode',choices=('adaptive_size','matched_primary_count'),default='adaptive_size')
    p.add_argument('--primary-count',type=int);p.add_argument('--outline',default='independent',choices=('independent','shared','grouped','branch_rejoin'))
    p.add_argument('--target-rule',choices=('uniform','all'),default='uniform');p.add_argument('--threat',choices=('F','S','R'),default='F')
    p.add_argument('--planner',default='external_supplied',help='Recorded adapter identifier; never a worker prompt')
    p.add_argument('--selector',choices=('first','nominal','recovery'),default='first')
    p.add_argument('--calibration',type=Path)
    p.add_argument('--backend-config',type=Path);p.add_argument('--model-lock',type=Path)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--token-cap',type=int,default=100000);p.add_argument('--cpu-cap',type=float,default=1200)
    p.add_argument('--input',type=Path);p.add_argument('--plan',type=Path);p.add_argument('--results',type=Path)
    p.add_argument('--incident',type=Path)
    p.add_argument('--splits',type=Path);p.add_argument('--split',choices=('train','dev','test'),default='dev')
    p.add_argument('--export-kind',choices=('plan_outcomes','event_trajectories'),default='plan_outcomes')
    p.add_argument('--output',type=Path,required=True);p.add_argument('--dry-run',action='store_true')
    a=p.parse_args(argv)
    try:result=dispatch(a);write_new(a.output,result)
    except (Rejected,ValueError,KeyError,StopIteration,OSError) as exc:
        p.exit(2,f'rr-v2: {exc}\n')
    print(json.dumps({'report':str(a.output),'status':result.get('status','written'),'model_executed':result.get('mode')=='real_model'},indent=2))


def dispatch(a):
    if a.command=='validate':
        record=load(a.input)
        keys={'rr-planning-request-v2':'request_id','rr-frozen-planning-v2':'frozen_id','rr-branches-v2':'manifest_id'}
        v2.verify_record(record,keys[record['schema']])
        return {'status':'passed','scope':'record hash integrity only; not execution qualification','schema_checked':record['schema']}
    if a.command=='evidence':return v2.sanitized_evidence(load(a.input),load(a.results))
    if a.command=='readiness':
        from .qualification import inventory
        return inventory(a.sources)
    if a.command=='aggregate':return v2.aggregate_v2(load(a.input),load(a.results))
    if a.command=='compare':return v2.paired_comparison(load(a.input))
    if a.command=='b0':
        data=load(a.input)
        return v2.estimate_b0(data['observations'],minimum=data['minimum'],statistic=data['statistic'],family=data['family'],worker_binding=data['worker_binding'])
    if a.command=='resolve':return v2.resolve_branches(load(a.input),load(a.incident) if a.incident else None)
    if a.command=='export':return v2.training_export(load(a.input),load(a.results),catalog()['tasks'],load(a.splits),a.split,a.export_kind)
    if a.command=='slurm-dry-run':
        m=load(a.input);v2.verify_record(m,'manifest_id')
        return {'status':'blocked_prerequisite','blockers':m['blockers'],
            'scheduler':'existing scripts/bc.py submit; no new scheduler',
            'logical_pools':m['frozen']['request']['config']['pool_size'],'physical_gpu_per_shard':1,
            'max_campaign_gpus':4,'qualification_concurrency':1,'submitted':False,
            'reason':'v0.2 has no approved model campaign; legacy exact-trio gate remains separate'}
    if a.command=='qualify':return qualify_matrix(a)
    card,public=load_task(a.task,a.sources)
    c=v2.configuration(a.pool,a.count_mode,a.primary_count,a.lane,a.token_cap,a.cpu_cap,a.seed,a.threat,a.target_rule,planner=a.planner)
    binding=None
    if a.backend_config or a.model_lock:
        if not a.backend_config or not a.model_lock:raise Rejected('backend_config_and_lock_required')
        from beyond_consensus.models.reporecourse_planner import binding as bind_backend
        binding=bind_backend(a.backend_config,a.model_lock,a.pool)
    req=v2.request(public,c,binding)
    if a.command=='prompted-plan':
        if not binding:raise Rejected('explicit_backend_config_and_lock_required')
        from beyond_consensus.models.reporecourse_planner import generate
        return generate(load(a.input),public,a.backend_config,a.model_lock)
    if a.command=='request':return req
    plans=[v2.fixture_rejoin(public,c)[0] if a.outline=='branch_rejoin' else v2.authored_plan(public,c,a.outline)]
    if a.command=='plans':return {'plans':plans,'descriptors':[v2.descriptors(x) for x in plans],'catalog_source':'authored','qualified':False}
    if a.command=='select':
        req=load(a.input);cap=req['config']['resource']
        return v2.shared_catalog(req,public,load(a.plan)['plans'],Resources(cap['token_cap'],cap['cpu_cap']),selector=a.selector,calibration=load(a.calibration) if a.calibration else None)
    if a.command=='freeze':
        # Explicit supplied plan: no fictional generation charges or model claim.
        req=load(a.input);cap=req['config']['resource']
        return v2.freeze(req,public,load(a.plan),Resources(cap['token_cap'],cap['cpu_cap']),[], 'supplied_unmeasured')
    if a.command=='demo':
        if card['grounding']!='synthetic_diagnostic':raise Rejected('new_source_task_reference_review_required_use_existing_rr_qualify')
        f=v2.freeze(req,public,plans[0],Resources(token_cap=a.token_cap,cpu_cap=a.cpu_cap),[],'scripted_reference')
        m=v2.resolve_branches(f)
        if a.dry_run:return m
        from .engine import ScriptedWorker
        private=private_task(a.task);w=v2.fixture_witness(public,private,c,a.outline)
        rows=[v2.run_branch(m,b['branch_id'],public,private,ScriptedWorker(w)) for b in m['rows']]
        return {'manifest':m,'results':rows,'aggregate':v2.aggregate_v2([m],rows),'status':'reference_controls_completed',
            'evidence':'private reference driver, not planner or worker model competence'}
    raise Rejected('command')


def qualify_matrix(a):
    conditions=[]
    for task in ('synthetic-stock','synthetic-nullable'):
        _,public=load_task(task,a.sources)
        for pool in range(2,9):
            for outline in ('independent','shared','grouped','branch_rejoin'):
                c=v2.configuration(pool,lane='fixed_plan',target_rule='all')
                plan=v2.fixture_rejoin(public,c)[0] if outline=='branch_rejoin' else v2.authored_plan(public,c,outline)
                conditions.append({'task':task,'pool':pool,'outline':outline,'branches':1+len({u['worker'] for u in plan['units']})})
    if a.dry_run:return {'status':'planned','conditions':conditions,'planned_episodes':sum(r['branches'] for r in conditions),
        'cost_estimate':'unmeasured reference CPU; no model tokens','gpu_submitted':False}
    from .qualification import runtime_versions
    from .track_f_controls import PINS
    actual=runtime_versions()
    if any(actual.get(k)!=v for k,v in PINS.items()):return {'status':'blocked_prerequisite','required':PINS,'actual':actual,'conditions':conditions}
    reports=[]
    for row in conditions:
        aa=deepcopy(a);aa.command='demo';aa.task=row['task'];aa.pool=row['pool'];aa.outline=row['outline'];aa.lane='fixed_plan';aa.target_rule='all';aa.count_mode='adaptive_size';aa.primary_count=None;aa.threat='F';aa.seed=0;aa.token_cap=100000;aa.cpu_cap=1200
        report=dispatch(aa)
        reports.append({**row,'successes':sum(r['success'] for r in report['results']),
            'statuses':[r['status'] for r in report['results']], 'results':report['results']})
    from .qualification import implementation_hashes
    return {'status':'passed' if all(r['successes']==r['branches'] for r in reports) else 'failed',
        'evidence':'scripted_reference_only','reports':reports,'implementation_hashes':implementation_hashes(),
        'model_executed':False,'independent_review':'pending','GPU_qualified':False}


if __name__=='__main__':main()
