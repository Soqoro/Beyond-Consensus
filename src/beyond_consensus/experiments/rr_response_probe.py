"""Three selected reconstructed-input calls; no tools, evaluator, or retry."""
from copy import deepcopy
from pathlib import Path
import json
import time

from ..util import BCError, digest, read_json, atomic_json
from . import rr_v2_preflight as base
from .manifest import source_revision

SCHEMA='rr-response-probe-v1'
HISTORICAL='dd7f957805ef6c9e78dbe30739e890ed74e6d8fb38bd70d9fe4850cc1b72df4f'
TASK='github-multioperation-integration'
SELECTION=(('requirement_level','F'),('prompted_open','clean'),('prompted_open','F'))


def require(ok,message):
    if not ok:raise BCError(message)


def select(export):
    """Extract observations only, never evaluator labels or private artifacts."""
    require(export.get('experiment_id')==HISTORICAL,'Unexpected historical experiment')
    inputs={x['configuration_id']:x for x in export['public_planner_inputs']}
    found={}
    for entry in export['future_outcome_labels']:
        public=inputs[entry['configuration_id']]
        if public['task']!=TASK:continue
        for branch in entry['result']['branches']:
            key=(public['planner'],branch['track'])
            if key not in SELECTION:continue
            require(key not in found,'Duplicate selected branch')
            for index,row in enumerate(branch.get('trajectories',[])):
                result=row.get('tool_result')
                if not isinstance(result,dict) or result.get('error')!='malformed_json':continue
                assignment=row['observation'].get('assignment') or {}
                if 'repository_summary' not in assignment.get('outputs',[]):continue
                usage=[e for e in row['costs'] if e.get('kind')=='model_usage']
                if len(usage)!=1 or usage[0].get('finish_reason')!='eos':continue
                observation=deepcopy(row['observation'])
                history=deepcopy(observation.pop('worker_history'))
                seed=branch['checkpoint']['engine']['v2_config']['seeds']['execution']
                found[key]=dict(id=public['planner']+'-'+branch['track'],branch_id=branch['branch_id'],
                    trajectory_index=index,actor=row['actor'],stage=row['stage'],unit=row['unit'],
                    observation=observation,history=history,seed=seed,
                    historical_input_tokens=usage[0]['input_tokens'],historical_output_tokens=usage[0]['output_tokens'],
                    selected_trace_hash=digest(row))
                break
    require(set(found)==set(SELECTION),'Expected exactly three selected EOS mapping failures')
    return [found[k] for k in SELECTION]


def build(root,export,worker,planner,preflight,snapshots,controls):
    profile=base.build(root,worker,planner,7,plan_scoped=True,planner_output_cap=6144,
                       interface_profile='rr-interface-reliability-v1')
    check_controls(root,controls)
    evidence=preflight_evidence(root,preflight,snapshots,worker,planner)
    m=dict(schema=SCHEMA,source_revision=source_revision(root),base_manifest=profile,
        model=profile['model'],model_lock_sha256=digest(worker),shards=1,episodes=[],planned_episodes=0,
        historical_experiment=HISTORICAL,export_hash=digest(export),cases=select(export),preflight_evidence=evidence,controls=controls,
        maximum_calls=3,maximum_logical_tokens=49152,declared_cpu_caps_total=3600,output_cap=2048,context_limit=16384,task_inputs_used=True,
        task_execution_allowed=False,sql_executed=False,historical_scores_changed=False,
        interpretation='Selected reconstructed worker observations; original rendered bytes unavailable. Not exact replay, competence, or an independent sample.')
    m['experiment_id']=digest(m);validate(m);return m


def check_controls(root,controls):
    from .rr_cohort import control_hashes
    require(controls.get('status')=='passed' and all(controls.get(k)==0 for k in ('skipped','failures','errors')),
            'Fresh no-skip CPU controls required')
    require(controls.get('source_revision')==source_revision(root) and
            controls.get('implementation_hashes')==control_hashes(root) and
            'test_rr_response_probe.py' in controls.get('patterns',[]),'Diagnostic controls changed or missing')


def preflight_evidence(root,run,snapshots,worker,planner):
    from .rr_open_review import inspect
    from .rr_cohort import footprint_compatibility
    audit=inspect(run,snapshots)
    report=read_json(Path(run)/'preflight.json')
    marker=read_json(Path(snapshots)/report['runtime']['snapshot_id']/'snapshot.json')
    require(footprint_compatibility(root,marker)['compatible'],'Preflight runtime changed')
    profile=read_json(Path(run)/'manifest.json')['cpu_packet']['base_manifest']
    require(profile['model_lock_sha256']==digest(worker) and profile['planner_lock']==planner,'Preflight locks differ')
    return audit


def validate(m):
    require(m.get('schema')==SCHEMA and m.get('experiment_id')==digest({k:v for k,v in m.items() if k!='experiment_id'}),'Diagnostic manifest hash mismatch')
    require(m.get('maximum_logical_tokens')==49152 and m.get('declared_cpu_caps_total')==3600 and m.get('maximum_calls')==3 and m.get('output_cap')==2048 and m.get('context_limit')==16384,
            'Diagnostic call or token caps changed')
    require(m.get('historical_experiment')==HISTORICAL and m.get('task_inputs_used') is True and
            m.get('task_execution_allowed') is False and m.get('sql_executed') is False and
            m.get('historical_scores_changed') is False and m.get('episodes')==[] and m.get('planned_episodes')==0 and m.get('shards')==1,'Diagnostic scope changed')
    require([c['id'] for c in m['cases']]==[p+'-'+t for p,t in SELECTION],'Diagnostic selection changed')
    profile=m['base_manifest'];config=base.validate(profile)
    require(m['source_revision']==profile['source_revision'] and m['model']==profile['model'] and
            m['model_lock_sha256']==profile['model_lock_sha256'],'Diagnostic profile mismatch')
    return config


def submission(m,worker,root,mode,concurrency,output):
    validate(m)
    require(mode=='run' and concurrency==1,'Response diagnostic is run-only, concurrency one')
    check_controls(root,m['controls'])
    base.check_submission(m['base_manifest'],worker,root,'preflight',1)
    audit=m['preflight_evidence']
    require(preflight_evidence(root,audit['run'],audit['snapshots'],worker,m['base_manifest']['planner_lock'])==audit,'Preflight evidence changed')
    require(not (Path(output)/'response-probe-started.json').exists(),'Diagnostic already started; no retry')


def sequence(m,backend,save):
    from reporecourse.engine import ModelWorker
    from reporecourse.resources import Resources
    from reporecourse.common import Rejected
    rows=[]
    for case in m['cases']:
        r=Resources(16384,1200);row=dict(id=case['id'],status='started',parse_accepted=False,dispatched=False)
        rows.append(row)
        def checkpoint():
            row['resources']=r.summary();save(rows)
        checkpoint()
        class RecordedBackend:
            def count_input(self,messages):return backend.count_input(messages)
            def generate(self,messages,cap,seed):
                row.update(dispatched=True,prompt_hash=digest(messages),generation_seed=seed)
                checkpoint()
                generation=backend.generate(messages,cap,seed)
                row['generation_metadata']={k:generation.diagnostics.get(k) for k in
                    ('rendered_input_ids_hash','rendered_input_tokens','finish_reason','constraint_complete')}
                return generation
        try:
            worker=ModelWorker(RecordedBackend(),16384,2048)
            action=worker.next_action({}, {},deepcopy(case['observation']),deepcopy(case['history']),r,case['seed'],checkpoint)
            row.update(status='parsed',parse_accepted=True,parsed_value_hash=digest(action))
        except Rejected as exc:
            row.update(status='rejected',error_category=str(exc))
            if hasattr(exc,'response_diagnostic'):row['response_diagnostic']=exc.response_diagnostic
        except Exception as exc:
            row.update(status='error',error_type=type(exc).__name__)
            row['resources']=r.summary();save(rows);break
        finally:
            row['resources']=r.summary()
        save(rows)
    return rows


def run(m,output,root,*,model_lock,shard=None,retry_failures=False):
    require(shard in (None,0) and not retry_failures,'No extra shard or retry')
    output=Path(output);worker=read_json(model_lock)
    submission(m,worker,root,'run',1,output)
    output.mkdir(parents=True,exist_ok=True)
    with (output/'response-probe-started.json').open('x') as f:json.dump({'experiment_id':m['experiment_id']},f)
    start=time.process_time();wall=time.monotonic()
    report=dict(schema='rr-response-probe-report-v1',experiment_id=m['experiment_id'],manifest_hash=digest(m),status='started',
        historical_experiment=HISTORICAL,task_inputs_used=True,task_execution_allowed=False,
        sql_executed=False,historical_scores_changed=False,worker_feedback=False,
        accounting='Separate diagnostic ledger; never substituted for historical work.',
        interpretation=m['interpretation'],calls=[])
    def save(rows):
        report.update(calls=deepcopy(rows),model_executed=any(r.get('dispatched') for r in rows),actual_tokens=sum(r.get('resources',{}).get('actual_tokens',0) for r in rows),
                      uncertain_tokens=sum(r.get('resources',{}).get('uncertain_tokens',0) for r in rows),
                      process_cpu_seconds=time.process_time()-start,
                      wall_seconds=time.monotonic()-wall)
        atomic_json(output/'response-diagnostic.json',report)
    save([])
    try:
        backend,_,_=base.qualified_backend(m['base_manifest'],model_lock,root)
        report['runtime']=backend.runtime
        rows=sequence(m,backend,save)
        report.update(status='completed' if len(rows)==3 and all(r['status']!='error' for r in rows) else 'incomplete',
                      maximum_calls=3)
        save(rows)
    except Exception as exc:
        report.update(status='error',error_type=type(exc).__name__);save(report['calls']);raise
    return [report]


def aggregate(m,output):
    validate(m)
    path=Path(output)/'response-diagnostic.json'
    if not path.is_file():return dict(experiment_id=m['experiment_id'],status='missing',model_executed=False)
    report=read_json(path)
    require(report.get('experiment_id')==m['experiment_id'] and report.get('manifest_hash')==digest(m),'Diagnostic result provenance mismatch')
    return report
