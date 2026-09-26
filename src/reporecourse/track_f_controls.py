"""CPU engineering controls through the production engine and artifact executor.

Private witness scripts are labelled test drivers, never worker model context.
Missing pinned children block qualification rather than yield a passing stub.
"""
from copy import deepcopy
from pathlib import Path
from .common import digest, file_hash, Rejected
from .tasks import ROOT, load_task, private_task
from .engine import Engine, ScriptedWorker
from .resources import Resources, ACCOUNTING
from .evaluator import evaluate
from .track_f import TASK, CONTROLS
from .qualification import runtime_versions

PINS={'sqlglot':'27.28.1','jsonschema':'4.25.1','referencing':'0.36.2'}


def control_fingerprints():
    base=ROOT.parents[1]
    files=['src/beyond_consensus/experiments/reporecourse.py',
           'src/beyond_consensus/experiments/reporecourse_history.py',
           'src/beyond_consensus/experiments/cluster.py',
           'experiments/qualify_reporecourse.sh', 'tests/test_reporecourse_track_f.py']
    return {name:file_hash(base/name) for name in files}


class ControlWorker(ScriptedWorker):
    """Scripted actions with synthetic ledger charges, not model measurements."""
    mode='scripted_track_f_cpu_control'
    def __init__(self,witness,variant=None):super().__init__(witness);self.variant=variant;self.finished_units=set()
    def next_action(self,public,unit,observation,history,resources,seed,save):
        token=resources.reserve(2,3);resources.reconcile(token,1,0)
        if self.variant=='nontrigger':return {'tool':'finish'}
        if self.variant=='finish_then_repair' and unit['id'] not in self.finished_units:
            self.finished_units.add(unit['id'])
            return {'tool':'finish'}
        action=super().next_action(public,unit,observation,history,resources,seed,save)
        if self.variant=='wrong_repair' and observation['unavailable'] and unit['id']=='customer_summary' and action['tool']=='publish':
            action['content']='SELECT -999 AS customer_id, 0 AS recorded_dollars, 0 AS payment_records'
        return action


def exercise(public, private):
    witness=next(w for w in private['witnesses'] if w['organization']=='independent')
    controls={name:False for name in CONTROLS};evidence={}
    for condition,target in [('fresh_clean',None),('loss_w0','w0'),('loss_w1','w1')]:
        saved=[];engine=Engine(public,ControlWorker(witness),track='F' if target else 'clean',target=target,
            resources=Resources(100000,1200),save=lambda s:saved.append(deepcopy(s)))
        try:
            row=engine.run();score=evaluate(public,private,row['state']);events=row['events']
            loss=[e for e in events if e['type']=='unavailable']
            controls[condition]=score.get('success') is True and row['status']=='completed' and len(loss)==bool(target)
            if target:
                at=next(i for i,e in enumerate(events) if e['type']=='unavailable')
                missing=loss[0]['missing_assignments']
                controls[condition] &= (target in row['state']['unavailable'] and all(
                    not (e['type'] in ('assignment_start','publish','source_read') and e.get('worker')==target)
                    for e in events[at+1:]) and all(o in row['state']['bound'] for o in missing)
                    and any(e['type']=='unit_end' and e.get('stage')=='repair' and e['worker']!=target and e['new_versions'] for e in events))
                if target=='w1':controls[condition] &= set(loss[0]['retained_versions']) <= set(row['state']['artifacts']) and bool(loss[0]['retained_versions'])
                for label,state in [('resume_before',next(s for s in reversed(saved) if not s['environment']['triggered'])),
                                    ('resume_after',next(s for s in saved if s['environment']['triggered']))]:
                    resumed=Engine(public,ControlWorker(witness),track='F',target=target,resources=Resources(100000,1200))
                    try:
                        resumed.restore(state);rr=resumed.run();ss=evaluate(public,private,rr['state'])
                        passed=(ss.get('success') is True and rr['resource_profile']['actual_tokens']==row['resource_profile']['actual_tokens']
                                and sum(e['type']=='unavailable' for e in rr['events'])==1
                                and set(rr['state']['artifacts'])==set(row['state']['artifacts']))
                        controls[label]=passed if target=='w0' else controls[label] and passed
                    finally:resumed.env.close()
                # Only committed versions are in worker observations; original
                # source access is identical for every surviving identity.
                view=engine.env.observation('w2')
                visible={a['version'] for a in view['artifacts']}
                good=visible==set(row['state']['artifacts']) and all('witnesses' not in engine.env.public and 'oracle' not in engine.env.public for _ in [0])
                announcement=loss[0]['announcement']
                good &= set(announcement)=={'worker','unavailable','assignment'} and view['source_ids']==sorted(public['sources'])
                controls['visibility']=good if target=='w0' else controls['visibility'] and good
            evidence[condition]={'success':score.get('success'),'triggered':row['intervention_triggered'],
                'unavailable':row['state']['unavailable'],'bound_versions':row['state']['bound'],
                'scripted_tokens':row['resource_profile']['actual_tokens'],
                'repair_executors':[e['worker'] for e in events if e['type']=='unit_end' and e['stage']=='repair']}
        finally:engine.env.close()
    for variant in ('wrong_repair','nontrigger','finish_then_repair'):
        engine=Engine(public,ControlWorker(witness,variant),track='F' if variant!='finish_then_repair' else 'clean',
                      target='w0' if variant!='finish_then_repair' else None,resources=Resources(100000,1200))
        try:
            row=engine.run();score=evaluate(public,private,row['state'])
            if variant=='wrong_repair':controls[variant]=row['intervention_triggered'] and score.get('success') is False
            elif variant=='nontrigger':controls[variant]=row['no_intervention'] and score.get('success') is False
            else:controls[variant]=score.get('success') is True and any(e['type']=='unit_end' and e['stage']=='repair' for e in row['events']) and not any(f['category']=='episode_closed' for f in row['failures'])
        finally:engine.env.close()
    return controls,evidence


def qualify_controls(sources):
    versions=runtime_versions()
    if any(versions.get(k)!=v for k,v in PINS.items()):
        return dict(status='blocked_prerequisite',required=PINS,actual=versions,model_executed=False)
    _,public=load_task(TASK,sources)
    controls,evidence=exercise(public,private_task(TASK))
    return dict(schema='rr-track-f-cpu-controls-v1',status='passed' if all(controls.values()) else 'failed',
                controls=controls,evidence=evidence,accounting_version=ACCOUNTING,
                public_hash=digest(public),fingerprints=control_fingerprints(),runtime_versions=versions,
                model_executed=False,sql_executed=True,
                scope='Scripted production-engine controls; synthetic token charges; not GPU recovery evidence')
