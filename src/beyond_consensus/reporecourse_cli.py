"""Additive stdlib-only CLI for RepoRecourse; no implicit model or network calls."""
from pathlib import Path
import json
from dataclasses import asdict
from .util import BCError


def add_parsers(sub):
    for command,helptext in [('rr-source-plan','Inspect pinned allowlist sizes; no download'),('rr-stage','Explicit bounded source staging'),
        ('rr-readiness','Source/task/split readiness; no model'),('rr-qualify','CPU references, mutants, reset and source checks'),
        ('rr-visibility','Audit public interface and separate evaluator binding'),('rr-plans','Inspect executable outlines and effective variation'),
        ('rr-demo','Scripted CPU episode, never empirical performance'),('rr-manifest','Freeze prospective model plans; no submission'),
        ('rr-export','Sanitized results export; no task contents or hidden checks'),('rr-calibration-plan','Prespecified calibration design; executes nothing')]:
        p=sub.add_parser(command,help=helptext)
        if command not in ('rr-export','rr-calibration-plan'):p.add_argument('--sources',type=Path,default=Path('data/reporecourse-sources'))
        if command in ('rr-qualify','rr-visibility','rr-plans','rr-demo'):p.add_argument('--task',required=True)
        if command in ('rr-source-plan','rr-stage'):
            p.add_argument('--dry-run',action='store_true')
            p.add_argument('--packs',nargs='+',choices=('jaffle','energy','github'))
        if command in ('rr-qualify','rr-demo','rr-manifest','rr-export'):p.add_argument('--output',type=Path,required=True)
        else:p.add_argument('--output',type=Path)
        if command=='rr-demo':
            p.add_argument('--policy',choices=('solo','delegation_jit','restart','replication'),default='delegation_jit')
            p.add_argument('--outline',choices=('independent','shared'),default='independent')
            p.add_argument('--track',choices=('clean','F','S'),default='clean');p.add_argument('--target',choices=('w0','w1','w2','w3'))
        if command=='rr-qualify':p.add_argument('--track-f-controls',action='store_true')
        if command=='rr-manifest':
            p.add_argument('--tasks',nargs='+',required=True);p.add_argument('--model-lock',type=Path)
            p.add_argument('--qualification',type=Path);p.add_argument('--engineering-smoke',action='store_true')
            p.add_argument('--sensitivity',action='store_true')
            p.add_argument('--track-f-engineering',action='store_true')
            p.add_argument('--baseline-run',type=Path)
            p.add_argument('--baseline-snapshot',type=Path)
        if command=='rr-export':
            p.add_argument('--run',type=Path,required=True)
            p.add_argument('--manifest',type=Path)


def dispatch(args):
    from reporecourse.common import load,write_new,digest,Rejected
    from reporecourse.tasks import load_task,private_task
    from reporecourse.qualification import qualify,inventory,run_reference
    from reporecourse.experiments import build,calibration_plan,aggregate
    command=args.command
    if command in ('rr-source-plan','rr-stage'):
        from reporecourse.sources import stage
        result=stage(args.sources,dry_run=command=='rr-source-plan' or args.dry_run,packs=args.packs)
    elif command=='rr-readiness':result=inventory(args.sources)
    elif command=='rr-qualify':
        result=qualify(args.task,args.sources)
        if args.track_f_controls:
            if args.task!='jaffle-recorded-payments':raise BCError('Track F controls require Jaffle')
            from reporecourse.track_f_controls import qualify_controls
            result['track_f_controls']=qualify_controls(args.sources)
            if result['track_f_controls']['status']!='passed':result['status']='blocked_prerequisite'
    elif command in ('rr-visibility','rr-plans'):
        c,p=load_task(args.task,args.sources)
        if command=='rr-plans':
            from reporecourse.policies import variation
            result={'outlines':p['outlines'],**variation(p['outlines'],p),'implementations_exposed':False}
        else:
            from reporecourse.runtime import Environment
            env=Environment(p)
            probes={}
            for name in ('private','../private','/etc/passwd','witnesses','expected_rows'):
                try:env.action('w0',{'tool':'read_source','name':name});probes[name]=False
                except Rejected:probes[name]=True
            env.close()
            result={'task':args.task,'public_view_hash':digest(p),'source_ids':sorted(p['sources']),
                'forbidden_reads_denied':probes,'task_card_not_serialized_to_workers':True,
                'scope':'tool interface, not an OS sandbox','status':'passed' if all(probes.values()) else 'failed'}
    elif command=='rr-demo':
        _,p=load_task(args.task,args.sources);result=run_reference(p,private_task(args.task),args.outline,args.policy,args.track,args.target)
    elif command=='rr-calibration-plan':result=calibration_plan()
    elif command=='rr-manifest':
        from .models.competence import REVISION
        from .experiments.manifest import source_revision
        from .cli import ROOT
        model=dict(backend='transformers',checkpoint='Qwen/Qwen3.5-27B',revision=REVISION,tokenizer_revision=REVISION,
            dtype='bfloat16',context_limit=16384,max_new_tokens=2048,thinking=True,do_sample=False,
            temperature=0.7,top_p=0.8,top_k=20,action_constraint='reporecourse-json-v1')
        if args.model_lock:
            lock=load(args.model_lock)
            if any(lock.get(k)!=model[k] for k in ('checkpoint','revision','tokenizer_revision')):raise BCError('Model lock does not match the frozen 27B profile')
        if args.engineering_smoke and (not args.model_lock or not args.qualification):raise BCError('Smoke requires staged model lock and CPU qualification')
        result=build(args.sources,args.tasks,model,source_revision(ROOT),smoke=args.engineering_smoke,
            qualification=load(args.qualification) if args.qualification else None,sensitivity=args.sensitivity,
            model_lock_hash=digest(load(args.model_lock)) if args.model_lock else None)
        if args.track_f_engineering:
            if args.engineering_smoke or args.sensitivity or args.tasks!=['jaffle-recorded-payments'] or not all((args.baseline_run,args.baseline_snapshot,args.qualification,args.model_lock)):
                raise BCError('Exact Track F scope requires historical run/snapshot, qualification and lock')
            from .experiments.reporecourse_history import resolve
            from reporecourse.track_f import build as build_trio
            result=build_trio(result,resolve(args.baseline_run,args.baseline_snapshot))
            from .experiments.reporecourse import verify_inputs
            verify_inputs(result,ROOT)
    elif command=='rr-export':
        m=load(args.manifest or args.run/'manifest.json');result={'aggregate':aggregate(m,args.run),'episodes':[]}
        if m.get('experiment_type')=='reporecourse_track_f_engineering_v1':
            from reporecourse.track_f import report
            result['engineering_trace']=report(m,args.run)
        for e in m['episodes']:
            path=args.run/'episodes'/e['episode_id']/'result.json'
            if path.exists():
                r=load(path);result['episodes'].append({k:r[k] for k in ('episode_id','status','success','resource_profile','track','model_executed') if k in r})
    else:raise BCError('Unknown RepoRecourse command')
    if args.output:write_new(args.output,result)
    if command in ('rr-demo','rr-qualify','rr-manifest','rr-export'):
        return {'report':str(args.output),'status':result.get('status','written'),
            'command_failed':command=='rr-qualify' and result.get('status')!='cpu_qualified_review_pending','model_executed':False if command!='rr-export' else result['aggregate']['model_executed'],
            **({k:result[k] for k in ('experiment_id','planned_episodes') if k in result})}
    return result
