"""Finite worker selection. Separate approved Q/A/B/C blocks, never auto-chain."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import json
import os
import signal
import time
from ..util import BCError, digest, file_hash, atomic_json
from ..models import worker_profiles as profiles
from .manifest import source_revision
from .rr_open_clean import load_control_record as load, seal
from .worker_presentation import PRESENTATIONS, PresentedBackend, render, audit
from reporecourse import worker_cases as design
from reporecourse.common import Rejected
from reporecourse.resources import Resources, success_at_budget
from reporecourse.engine import ModelWorker, worker_messages
from reporecourse.qualification import implementation_hashes, runtime_versions

SCHEMA='rr-worker-selection-v1'
MODELS=('control','coder')
LIMITATIONS=['synthetic_selection_not_population_inference','development_workflows_unreviewed',
    'engineering_caps_not_B0','observed_fit_only','no_retry_no_training','provider_templates_differ',
    'worker_backed_execution_and_repair_stack','single_process_CPU_no_distributed_ranks']


def require(ok,message):
    if not ok:raise BCError(message)


def hashes():
    root=Path(__file__).resolve().parents[3]
    return {**implementation_hashes(),**profiles.implementation(),**{p:file_hash(root/p) for p in (
        'src/beyond_consensus/experiments/worker_selection.py','src/beyond_consensus/experiments/worker_presentation.py',
        'src/beyond_consensus/experiments/cluster.py','src/beyond_consensus/experiments/runner.py',
        'src/beyond_consensus/experiments/rr_cohort.py','src/beyond_consensus/experiments/manifest.py',
        'src/beyond_consensus/models/worker_staging.py','scripts/worker_selection.py')}}


def observation(env):
    value=env.observation('w0');value.pop('cpu_remaining',None)
    value['diagnostic_caps']={'tokens':16384,'cpu_seconds':1200}
    value['synthetic_sources']=deepcopy(env.public['sources'])
    if 'allowed_inputs' in env.public:value['allowed_inputs']=deepcopy(env.public['allowed_inputs'])
    value['diagnostic_instruction']='All source facts are supplied. Return exactly one publish action for report. No read calls, repair or retry.'
    return value


def messages(case):
    env=design.environment(case,Resources(16384,1200))
    try:return worker_messages(observation(env),[])
    finally:env.close()


def controls():
    rows=[]
    for c in design.cases():
        for negative in (False,True):
            env=None;r=Resources(16384,1200)
            row=dict(case=c['id'],negative=negative,status='failed')
            try:
                env=design.environment(c,r);env.action('w0',design.action(c,negative))
                monitor=env.check_public()['report'];result=design.evaluate(c,env)
                row.update(public_monitor_passed=monitor,evaluation=result,
                    status='passed' if result['correct'] is (not negative) and all(x['execution_status']=='ok' for x in result['checks']) else 'failed')
            except Exception as exc:row.update(error_type=type(exc).__name__,error_category=str(exc)[:160])
            finally:
                if env is not None:env.close()
            row['resources']=r.summary();rows.append(row)
    return dict(schema='rr-worker-case-controls-v1',case_set_id=design.inventory()['case_set_id'],implementation=hashes(),
        runtime_versions=runtime_versions(),status='passed' if all(x['status']=='passed' for x in rows) else 'failed',cases=rows,
        model_executed=False,evidence='CPU_reference_and_mutants_not_model_competence',task_execution_allowed=False)


def grid(stage,presentation=None,configurations=None):
    if stage=='Q':return [dict(id=x,kind='qualification') for x in ('sql','schema','mapping','long')]
    if stage in ('A','B'):
        selected=[c for c in design.cases() if c['split']==('screen' if stage=='A' else 'confirm')]
        if stage=='B':require(presentation in PRESENTATIONS,'Common presentation required')
        result=[]
        # Alternate starting presentation by case; fixed within model-loaded blocks.
        for model in MODELS:
            for i,c in enumerate(selected):
                ps=PRESENTATIONS[::1 if i%2==0 else -1] if stage=='A' else (presentation,)
                for p in ps:result.append(dict(id=digest([stage,model,c['id'],p]),model=model,case=c['id'],domain=c['domain'],presentation=p))
        return result
    require(stage=='C' and len(configurations or [])==6,'Six authored organizations required')
    return [dict(id=digest(['C',m,c['configuration_id'],t]),model=m,configuration_id=c['configuration_id'],track=t,presentation=presentation)
        for m in MODELS for c in configurations for t in ('clean','F')]


def study(root):
    return dict(schema='rr-worker-study-v1',source_revision=source_revision(root),implementation=hashes(),
        case_set_id=design.inventory()['case_set_id'],profiles={n:profiles.profile(n) for n in MODELS},
        presentations={p:digest([render(messages(c),p) for c in design.cases()]) for p in PRESENTATIONS},
        screen_grid=grid('A'),confirmation_case_ids=[c['id'] for c in design.cases() if c['split']=='confirm'],
        stage_counts={'A':48,'B':24,'C':24},selection_rule='total_semantic_then_minimum_model_domain_then_current',
        adequacy=dict(overall=10,sql=5,api=5),output_cap=4096,context_limit=16384,limitations=LIMITATIONS)


def probes():
    values=[dict(tool='publish',name='demo',format='sql',content='SELECT 1 AS id',bindings={},obligations=[]),
        dict(tool='publish',name='demo',format='schema',content={'type':'object','properties':{'x':{'type':'string'}}},bindings={},obligations=[]),
        dict(tool='publish',name='demo',format='mapping',content={'fields':{'a"b':{'path':['x'],'missing':'error'}},'output_schema':{'type':'object'}},bindings={},obligations=[]),
        dict(tool='list_sources')]
    return dict(zip(('sql','schema','mapping','long'),values))


def probe_prompt(case,tokenizer,p):
    value=probes()[case];base=[{'role':'system','content':'Return exactly the requested single JSON action, no Markdown.'},
        {'role':'user','content':json.dumps(value)}]
    if case=='long':
        # Synthetic numbered records, not task material. Measure actual tokenizer admission.
        lo,hi=0,8000
        while lo<hi:
            n=(lo+hi+1)//2
            candidate=deepcopy(base);candidate[-1]['content']='\n'.join('Record %d: neutral datum.'%i for i in range(n))+'\nRequired action: '+json.dumps(value)
            count=len(tokenizer.apply_chat_template(candidate,tokenize=True,add_generation_prompt=True,**profiles.template_options(p)))
            if count<=12288:lo=n
            else:hi=n-1
        base[-1]['content']='\n'.join('Record %d: neutral datum.'%i for i in range(lo))+'\nRequired action: '+json.dumps(value)
    return base


def footprint(p,lock,stage,rows,configs=(),publics=None):
    require(os.environ.get('SLURM_JOB_ID'),'Footprint measurement requires CPU allocation')
    profiles.require_qualified(p,lock)
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True,trust_remote_code=False)
    prompts=[];outputs=[]
    if stage=='Q':prompts=[(r['id'],probe_prompt(r['id'],tokenizer,p)) for r in rows]
    elif stage in ('A','B'):
        by={c['id']:c for c in design.cases()}
        prompts=[(r['id'],render(messages(by[r['case']]),r['presentation'])) for r in rows if r['model']==p['name']]
        for c in by.values():
            count=len(tokenizer.encode(json.dumps(design.action(c),separators=(',',':')),add_special_tokens=False))+1
            outputs.append(dict(id=c['id'],action_plus_stop_tokens=count,passed=count<=4096))
    else:
        from .rr_sampled_run import prompt_cases
        for c in configs:
            for x in prompt_cases(c,publics[c['task']]):
                prompts.append((c['configuration_id']+'/'+x['id'],render(x['messages'],rows[0]['presentation'])))
        from reporecourse.organization_sampler import reference_witness
        from reporecourse.tasks import private_task
        # Bound the selected authored artifact serializations too; no solution enters prompts.
        for c in configs:
            from reporecourse.organization_sampler import sample
            candidate=next(x for x in sample(c['task'],publics[c['task']])['candidates'] if x['plan']==c['plan'])
            for i,item in enumerate(reference_witness(candidate,private_task(c['task']))['actions']):
                a=deepcopy(item['action'])
                if 'bindings' in a:a['bindings']={k:digest(['version',k]) for k in a['bindings']}
                count=len(tokenizer.encode(json.dumps(a,separators=(',',':')),add_special_tokens=False))+1
                outputs.append(dict(id=c['configuration_id']+'/'+str(i),action_plus_stop_tokens=count,passed=count<=4096))
    result=[]
    for identity,prompt in prompts:
        ids=tokenizer.apply_chat_template(prompt,tokenize=True,add_generation_prompt=True,**profiles.template_options(p))
        result.append(dict(id=identity,messages_hash=digest(prompt),input_tokens=len(ids),rendered_ids_hash=digest(ids),
            prompt_bytes=len(json.dumps(prompt).encode()),passed=0<len(ids)<=12288,**({'messages':prompt} if stage=='Q' else {})))
    return dict(schema='rr-worker-footprint-v1',stage=stage,profile=p['name'],lock_hash=digest(lock),implementation=hashes(),
        cases=result,reference_outputs=outputs,status='passed' if result and all(x['passed'] for x in result+outputs) else 'failed',
        worst_case_fit_established=False,model_executed=False)


def build(root,name,lock,stage,controls_record=None,qualification=None,prior=None,catalog=None,sources=None):
    require(stage in ('Q','A','B','C'),'Unknown stage');p=profiles.profile(name);profiles.require_qualified(p,lock)
    st=study(root);configs=[];bindings={};publics=None;presentation=None
    if stage!='Q':
        require(controls_record and controls_record.get('status')=='passed' and controls_record.get('implementation')==hashes() and
            controls_record.get('case_set_id')==st['case_set_id'] and controls_record.get('runtime_versions')==runtime_versions() and
            [(r.get('case'),r.get('negative')) for r in controls_record.get('cases',[])]==[(c['id'],n) for c in design.cases() for n in (False,True)] and
            all(r.get('status')=='passed' and r.get('evaluation',{}).get('correct') is (not r['negative']) for r in controls_record['cases']),'Fresh 24 reference + 24 mutant production controls required')
        require(qualification and qualification.get('stage')=='Q' and qualification.get('status')=='completed' and
            qualification.get('profile')==p and qualification.get('lock_hash')==digest(lock) and qualification.get('implementation')==hashes() and
            len(qualification.get('rows',[]))==4 and all(r.get('passed') is True for r in qualification['rows']), 'Fresh four-call normal qualification required')
    if stage in ('B','C'):
        require(prior and prior.get('status')=='complete' and prior.get('study')==st,'Complete prior-stage evidence required')
        require(prior.get('stage')==('A' if stage=='B' else 'B'),'Wrong stage gate')
        require(prior.get('report_id')==digest({k:v for k,v in prior.items() if k!='report_id'}),'Prior report changed')
        presentation=prior['selected_presentation']
        require(prior.get('lock_hashes',{}).get(name)==digest(lock),'Worker changed after screening')
        if stage=='C':require(any(v['adequate'] for v in prior['models'].values()),'Neither worker meets progression heuristic; review bounded alternative')
    if stage=='C':
        from .rr_sampled_run import catalog_bindings
        publics,bindings,configs=catalog_bindings(catalog,sources)
    rows=grid(stage,presentation,configs)
    measured=footprint(p,lock,stage,rows,configs,publics)
    require(measured['status']=='passed','Rendered footprint failed')
    targets={}
    if stage=='C':
        from reporecourse.sampled_cohort import schedule
        for c in configs:
            a=schedule(c,publics[c['task']]);targets[c['configuration_id']]=[dict(track=b['track'],target=b['target'],eligible=b['eligible']) for b in a['branches']['rows']]
    m=dict(schema=SCHEMA,study=st,stage=stage,profile=p,model=p['model'],model_lock_sha256=digest(lock),
        source_revision=source_revision(root),implementation=hashes(),rows=rows,shards=1,episodes=[],planned_episodes=0,
        controls=controls_record,qualification=qualification,prior=prior,footprint=measured,configurations=configs,
        sources=str(sources) if sources else None,bindings=bindings,targets=targets,
        presentation=presentation,approval=None,task_execution_allowed=False,physical_gpus=p['physical_gpus'])
    seal(m);validate(m);return m


def approval_template(m):
    return dict(schema='rr-worker-selection-approval-v1',proposal_id=m['experiment_id'],stage=m['stage'],profile=m['profile']['name'],
        maximum_calls=4 if m['stage']=='Q' else 24 if m['stage']=='A' else 12 if m['stage']=='B' else None,
        maximum_branches=12 if m['stage']=='C' else 0,physical_gpus=m['physical_gpus'],
        limitations_accepted=LIMITATIONS,decision='pending',reviewer=None,reviewed_at=None)


def validate(m):
    require(m.get('schema')==SCHEMA and m.get('experiment_id')==digest({k:v for k,v in m.items() if k!='experiment_id'}),'Manifest identity changed')
    p=profiles.profile(m['profile']['name']);require(m['profile']==p and m['model']==p['model'] and m['physical_gpus']==p['physical_gpus'],'Profile changed')
    require(m['rows']==grid(m['stage'],m['presentation'],m['configurations']) and m['shards']==1 and m['episodes']==[],'Finite grid changed')
    f=m['footprint'];expected_ids=[r['id'] for r in m['rows'] if m['stage']=='Q' or r['model']==p['name']]
    require(f.get('stage')==m['stage'] and f.get('profile')==p['name'] and f.get('lock_hash')==m['model_lock_sha256'] and
        f.get('status')=='passed' and f.get('implementation')==m['implementation'] and
        all(x.get('passed') is True and type(x.get('input_tokens')) is int and 0<x['input_tokens']<=12288 for x in f.get('cases',[])), 'Footprint contract changed')
    if m['stage']!='C':require([x['id'] for x in f['cases']]==expected_ids,'Footprint case scope changed')
    if m['approval']:
        original=deepcopy(m);original.update(approval=None,task_execution_allowed=False);seal(original)
        expected=approval_template(original);a=m['approval']
        require(set(a)==set(expected) and all(a[k]==v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')) and
            a['decision']=='approved' and all(isinstance(a[k],str) and a[k].strip() for k in ('reviewer','reviewed_at')) and
            m['task_execution_allowed']==(m['stage']!='Q'),'Exact scope approval required')
    else:require(m['task_execution_allowed'] is False,'Unapproved execution')
    return SimpleNamespace(model=SimpleNamespace(**p['model']),shards=1,task_kind='worker_selection')


def verify(m,root,lock):
    validate(m);profiles.require_qualified(m['profile'],lock)
    require(m['source_revision']==source_revision(root) and m['implementation']==hashes() and m['study']==study(root),'Frozen code/cases/renderer changed')
    require(m['model_lock_sha256']==digest(lock) and m['footprint']['lock_hash']==digest(lock) and m['footprint']['status']=='passed','Lock/footprint changed')
    if m['stage']!='Q':
        c=m['controls'];q=m['qualification']
        require(c['status']=='passed' and c['implementation']==hashes() and c['runtime_versions']==runtime_versions(), 'Case controls changed')
        require(q['status']=='completed' and q['stage']=='Q' and q['lock_hash']==digest(lock) and q['implementation']==hashes() and q['profile']==m['profile'] and
            [r['id'] for r in q['rows']]==list(probes()) and all(r.get('passed') is True for r in q['rows']), 'Qualification changed')
    if m['stage']=='C':
        from reporecourse.tasks import load_task,private_task
        from reporecourse.organization_sampler import sample
        from reporecourse.sampled_cohort import configuration,TASKS
        require(set(m['bindings'])==set(TASKS),'Workflow task scope changed')
        expected_configs=[]
        for task in TASKS:
            b=m['bindings'][task]
            card,public=load_task(task,m['sources'])
            require(b==dict(card=card,public_hash=digest(public),private_hash=digest(private_task(task))),'Source/evaluator integrity changed')
            catalog=sample(task,public)
            expected_configs.extend(configuration(task,next(c['plan'] for c in catalog['candidates'] if c['candidate_id']==cid)) for cid in catalog['selected'])
        require(m['configurations']==expected_configs,'Authored organization scope changed')


def authorize(m,a,root,lock):
    verify(m,root,lock);require(m['approval'] is None,'Already approved')
    result=deepcopy(m);result.update(approval=a,task_execution_allowed=m['stage']!='Q');seal(result);validate(result);return result


def submission(m,root,lock,mode,concurrency,output):
    verify(m,root,lock)
    require(m['approval'] is not None and concurrency==1 and mode==('preflight' if m['stage']=='Q' else 'run'),'Exact approved block, concurrency one')
    require(not (Path(output)/'worker-started.json').exists(),'Attempt already started; status/export only, no retry')


def attempt(backend,case,presentation,save,expected=None):
    r=Resources(16384,1200);e=Resources(1,1200);env=None
    wall_started=time.monotonic();task_end=None;eval_start=None
    row=dict(id=case['id'],status='started',dispatched=False,semantic_correct=None,public_monitor_passed=None,complete_in_budget=False)
    def checkpoint():
        row.update(resources=deepcopy(r.summary()),evaluator_resources=deepcopy(e.summary()));save(deepcopy(row))
    def record(g):
        row['generation']=dict(output_tokens=g.output_tokens,reasoning_tokens=g.reasoning_tokens,diagnostics=g.diagnostics,response_hash=digest(g.text))
    presented=PresentedBackend(backend,presentation,record)
    class Recorded:
        def count_input(self,m):
            count=presented.count_input(m)
            if expected is not None:
                require(expected['messages_hash']==digest(render(m,presentation)) and expected['input_tokens']==count,'Runtime prompt/footprint changed')
            return count
        def generate(self,m,cap,seed):row['dispatched']=True;checkpoint();return presented.generate(m,cap,seed)
    try:
        start=time.process_time();idx=len(r.events)
        try:env=design.environment(case,r);obs=observation(env)
        finally:r.parent_overhead('case_setup',start,idx)
        start=time.process_time();idx=len(r.events)
        try:a=ModelWorker(Recorded(),16384,4096).next_action(env.public,env.assignment['w0'],obs,[],r,0,checkpoint)
        finally:r.parent_overhead('response',start,idx)
        d=row['generation']['diagnostics']
        require(d.get('finish_reason')=='eos' and d.get('constraint_complete') is True,'incomplete_response')
        if not (isinstance(a,dict) and set(a)=={'tool','name','format','content','bindings','obligations'} and a['tool']=='publish' and
            a['name']=='report' and a['format']==case['public']['required_outputs'][0]['format'] and a['bindings']=={} and a['obligations']==['report']):raise Rejected('unexpected_action')
        start=time.process_time();idx=len(r.events)
        try:env.action('w0',a);row['public_monitor_passed']=env.check_public()['report']
        finally:r.parent_overhead('publication_monitor',start,idx)
        task_end=time.monotonic();eval_start=task_end
        env.resources=e;start=time.process_time();idx=len(e.events)
        try:result=design.evaluate(case,env)
        finally:e.parent_overhead('terminal_projection',start,idx)
        row.update(evaluation=result,semantic_correct=result['correct'],status='completed')
        row['complete_in_budget']=success_at_budget('completed',result['correct'],r)
    except Rejected as exc:row.update(status='rejected',error_category=str(exc),response_diagnostic=getattr(exc,'response_diagnostic',None))
    except BCError as exc:
        row.update(status='rejected' if str(exc)=='incomplete_response' else 'infrastructure_failed',error_category=str(exc)[:160])
    except BaseException as exc:
        row.update(status='infrastructure_failed',error_type=type(exc).__name__)
        if not isinstance(exc,Exception):checkpoint();raise
    finally:
        if env is not None:
            try:env.close()
            except Exception as exc:row.update(status='infrastructure_failed',cleanup_error_type=type(exc).__name__)
        if r.uncertain_tokens or r.uncertain_cpu:row['status']='infrastructure_failed'
        if row.get('error_category')=='blocked_prerequisite':row['status']='infrastructure_failed'
        row['task_wall_seconds']=(task_end or time.monotonic())-wall_started
        devices=getattr(backend,'profile',{}).get('physical_gpus')
        row['allocated_task_gpu_seconds']=row['task_wall_seconds']*devices if devices else None
        row['evaluator_wall_seconds']=time.monotonic()-eval_start if eval_start else None
        checkpoint()
    return row


def qualification_call(backend,entry,save=lambda r:None):
    from ..models.action_schema import validate_action
    r=Resources(16384,1200);row=dict(id=entry['id'],passed=False,dispatched=False,status='started')
    start=time.process_time();key=None
    try:
        count=backend.count_input(entry['messages']);require(count==entry['input_tokens'],'Qualification prompt changed')
        r.reserve_cpu(31);key=r.reserve(count,4096);row['dispatched']=True
        row['resources']=deepcopy(r.summary());save(deepcopy(row))
        g=backend.generate(entry['messages'],4096,0)
        r.reconcile(key,g.output_tokens,g.reasoning_tokens);key=None
        r.reconcile_cpu('model_host',31,time.process_time()-start)
        value=validate_action(g.text,profiles.MODE)
        # validate_action returns a validated object in the common parser.
        require(value==probes()[entry['id']],'Qualification action mismatch')
        require(g.diagnostics.get('constraint_complete') is True and g.diagnostics.get('finish_reason')=='eos','Incomplete probe')
        row.update(passed=True,status='completed',generation=dict(output_tokens=g.output_tokens,reasoning_tokens=g.reasoning_tokens,diagnostics=g.diagnostics))
    except BaseException as exc:
        if key is not None:r.reconcile(key)
        for n in list(r.cpu_pending):
            try:r.reconcile_cpu('interrupted_host',n,time.process_time()-start)
            except Rejected:pass
        row.update(status='infrastructure_failed',error_type=type(exc).__name__,error_category=str(exc)[:160])
    row['resources']=r.summary();return row


def run(m,output,root,*,model_lock,shard=None,retry_failures=False):
    require(shard in (None,0) and not retry_failures,'One block; no retry')
    output=Path(output);lock=load(model_lock);submission(m,root,lock,'preflight' if m['stage']=='Q' else 'run',1,output)
    require(os.environ.get('CUDA_LAUNCH_BLOCKING','0') in ('0',''),'Normal mode only')
    output.mkdir(parents=True,exist_ok=True)
    if (output/'manifest.json').exists():require(digest(load(output/'manifest.json'))==digest(m),'Output manifest changed')
    else:atomic_json(output/'manifest.json',m)
    with (output/'worker-started.json').open('x') as f:f.write(m['experiment_id'])
    report=dict(schema='rr-worker-result-v1',experiment_id=m['experiment_id'],manifest_hash=digest(m),stage=m['stage'],
        study=m['study'],profile=m['profile'],lock_hash=digest(lock),implementation=hashes(),rows=[],status='started',model_executed=False,
        task_execution_allowed=m['task_execution_allowed'],worst_case_fit_established=False,
        physical_planner_calls=0,whole_allocation_gpu_seconds=None,whole_allocation_accounting='pending_scheduler_export',runtime=None)
    wall=time.monotonic();cpu=time.process_time();handlers={}
    def save():
        report.update(process_wall_seconds=time.monotonic()-wall,process_cpu_seconds=time.process_time()-cpu)
        atomic_json(output/'worker-report.json',report)
    def stop(*_):raise InterruptedError('allocation_termination')
    for sig in (signal.SIGTERM,signal.SIGINT):handlers[sig]=signal.signal(sig,stop)
    save()
    try:
        backend=profiles.WorkerBackend(m['profile'],model_lock);report['runtime']=backend.runtime
        if m['stage']!='Q':
            require(backend.runtime['hardware']==m['qualification']['runtime']['hardware'] or
                [(h['name'],h['total_bytes'],h['capability']) for h in backend.runtime['hardware']]==
                [(h['name'],h['total_bytes'],h['capability']) for h in m['qualification']['runtime']['hardware']],'Hardware differs from qualification')
        report['model_executed']=True
        execution_started=time.monotonic()
        report['initialization_wall_seconds']=execution_started-wall
        if m['stage']=='Q':
            for item in m['footprint']['cases']:
                require(item['messages']==probe_prompt(item['id'],backend.tokenizer,m['profile']),'Synthetic probe messages changed')
                report['rows'].append(dict(id=item['id'],status='started'))
                def checkpoint_q(r):report['rows'][-1]=r;save()
                row=qualification_call(backend,item,checkpoint_q);report['rows'][-1]=row;save()
                if not row['passed']:break
        elif m['stage'] in ('A','B'):
            by={c['id']:c for c in design.cases()}
            for item in m['rows']:
                if item['model']!=m['profile']['name']:continue
                report['rows'].append(dict(item))
                def checkpoint(r):report['rows'][-1]={**r,**item};save()
                expected=next(x for x in m['footprint']['cases'] if x['id']==item['id'])
                row=attempt(backend,by[item['case']],item['presentation'],checkpoint,expected)
                if row['status']=='infrastructure_failed':break
        else:
            from reporecourse import sampled_cohort,cohort,v2
            from reporecourse.tasks import load_task,private_task
            from .rr_cohort import execute_schedule
            for c in m['configurations']:
                _,public=load_task(c['task'],m['sources']);private=private_task(c['task'])
                s=sampled_cohort.schedule(c,public,dict(profile=m['profile'],lock_hash=digest(lock)))
                # Shared seeded selection does not depend on model binding or clean outcome.
                require([dict(track=b['track'],target=b['target'],eligible=b['eligible']) for b in s['branches']['rows']]==m['targets'][c['configuration_id']],'Target changed across workers')
                def persist(name,value):atomic_json(output/(c['configuration_id']+'-'+name+'.json'),value)
                calls=[]
                def record_generation(g):
                    calls.append(dict(output_tokens=g.output_tokens,reasoning_tokens=g.reasoning_tokens,diagnostics=g.diagnostics))
                    persist('generation-costs',calls)
                row=execute_schedule(c,s,public,private,PresentedBackend(backend,m['presentation'],record_generation),lambda _:None,persist,output_cap=4096)
                row['generation_costs']=calls
                report['rows'].append(dict(configuration_id=c['configuration_id'],task=c['task'],model=m['profile']['name'],result=row));save()
                if row['status'] in ('paused','interrupted','infrastructure_failed'):break
        expected=4 if m['stage']=='Q' else 24 if m['stage']=='A' else 12 if m['stage']=='B' else 6
        report['status']='completed' if len(report['rows'])==expected and all(r.get('status',r.get('result',{}).get('status')) not in ('infrastructure_failed','paused','interrupted','started') for r in report['rows']) else 'incomplete'
    except BaseException as exc:
        report.update(status='infrastructure_failed',error_type=type(exc).__name__);save();raise
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
        teardown=time.monotonic()
        report['execution_wall_seconds_including_terminal_evaluation']=teardown-execution_started if 'execution_started' in locals() else None
        report['execution_allocated_gpu_seconds']=(teardown-execution_started)*m['physical_gpus'] if 'execution_started' in locals() else None
        if 'backend' in locals():
            del backend
        report['teardown_wall_seconds']=time.monotonic()-teardown
        report['process_allocated_gpu_seconds']=(time.monotonic()-wall)*m['physical_gpus']
        save()
    return [report]


def aggregate(m,output):
    validate(m);path=Path(output)/'worker-report.json'
    if not path.exists():return dict(status='missing',experiment_id=m['experiment_id'],manifest_hash=digest(m),planned=m['rows'],rows=[],model_executed=False)
    r=load(path);require(r['manifest_hash']==digest(m) and r['experiment_id']==m['experiment_id'],'Result provenance changed')
    if m['stage']=='C':
        from reporecourse.cohort import branch_metrics
        r=deepcopy(r)
        for row in r['rows']:
            value=row['result'];row['branch_metrics']=[branch_metrics(b) for b in value.get('branches',[])]
            row['result']={k:value.get(k) for k in ('status','target_status','pause_reason','generation_costs')}
    return r


def compare(manifests,reports):
    require(len(manifests)==len(reports)==2,'Exactly two model blocks required')
    st=manifests[0]['study'];stage=manifests[0]['stage'];require(stage in ('A','B','C'),'Not a task stage')
    require({m['profile']['name'] for m in manifests}==set(MODELS),'Missing/duplicate model arm')
    rows=[]
    for m,r in zip(manifests,reports):
        validate(m);require(m['study']==st and m['stage']==stage and r['manifest_hash']==digest(m),'Unmatched study blocks')
        rows+=deepcopy(r['rows'])
    result=dict(schema='rr-worker-comparison-v1',stage=stage,study=st,status='incomplete',rows=rows,
        blocks=[{k:r.get(k) for k in ('experiment_id','status','profile','runtime','error_type','model_executed','initialization_wall_seconds',
            'execution_wall_seconds_including_terminal_evaluation','execution_allocated_gpu_seconds','teardown_wall_seconds',
            'process_wall_seconds','process_cpu_seconds','process_allocated_gpu_seconds','whole_allocation_gpu_seconds')} for r in reports],
        evidence='prospective_model_attempts_not_population_inference',models={},lock_hashes={m['profile']['name']:m.get('model_lock_sha256') for m in manifests},selected_presentation=manifests[0]['presentation'])
    if stage in ('A','B'):
        planned=grid(stage,manifests[0]['presentation']);by={r['id']:r for r in rows}
        require(len(by)==len(rows) and set(by)<=set(x['id'] for x in planned),'Unexpected/duplicate rows')
        result['rows']=[by.get(x['id'],dict(x,status='missing',semantic_correct=None,complete_in_budget=False,resources=None)) for x in planned]
        result['status']='complete' if all(r.get('status') in ('completed','rejected') for r in result['rows']) else 'incomplete'
        if stage=='A':
            scores={}
            for p in PRESENTATIONS:
                cells=[sum(r.get('semantic_correct') is True for r in rows if r['presentation']==p and r['model']==m and r['domain']==d) for m in MODELS for d in ('sql','api')]
                scores[p]=dict(total=sum(cells),minimum_model_domain=min(cells),cells=cells)
            result['presentation_scores']=scores
            result['selected_presentation']=max(PRESENTATIONS,key=lambda p:(scores[p]['total'],scores[p]['minimum_model_domain'],p=='P_current')) if result['status']=='complete' else None
        else:
            require(manifests[0]['prior']==manifests[1]['prior'],'Different common presentation decisions')
            for name in MODELS:
                subset=[r for r in result['rows'] if r['model']==name]
                domains={d:sum(r.get('semantic_correct') is True and r.get('complete_in_budget') is True for r in subset if r['domain']==d) for d in ('sql','api')}
                result['models'][name]=dict(domains,correct=sum(domains.values()),adequate=sum(domains.values())>=10 and min(domains.values())>=5,
                    total_tokens=sum(r['resources']['actual_tokens'] for r in subset) if all(r.get('resources') for r in subset) else None,
                    total_cpu=sum(r['resources'].get('cpu_cap_debit',0) for r in subset) if all(r.get('resources') for r in subset) else None,
                    uncertain_tokens=sum(r['resources'].get('uncertain_tokens',0) for r in subset) if all(r.get('resources') for r in subset) else None,
                    task_gpu_seconds=sum(r['allocated_task_gpu_seconds'] for r in subset) if all(r.get('allocated_task_gpu_seconds') is not None for r in subset) else None,
                    failure_counts={s:sum(r.get('status')==s for r in subset) for s in ('completed','rejected','missing','infrastructure_failed')})
            pairs=[]
            for c in st['confirmation_case_ids']:
                pair=[next(r for r in result['rows'] if r['case']==c and r['model']==n) for n in MODELS]
                a,b=[r.get('complete_in_budget') is True for r in pair]
                pairs.append(dict(case=c,outcome='tie_success' if a and b else 'tie_failure' if not a and not b else 'control' if a else 'coder'))
            result['pairs']=pairs
            result['decision']='review_required_cheaper_adequate_or_inconclusive';result['whole_allocation_cost_complete']=False
    else:
        from reporecourse.cohort import branch_metrics
        result['branches']=[dict(model=r['model'],configuration_id=r['configuration_id'],**b) for r in rows for b in r.get('branch_metrics',[])]
        planned=grid('C',manifests[0]['presentation'],manifests[0]['configurations'])
        require(manifests[0]['configurations']==manifests[1]['configurations'] and manifests[0]['targets']==manifests[1]['targets'],'Workflow pairs differ')
        actual={(b['model'],b['configuration_id'],b['track']):b for b in result['branches']}
        require(len(actual)==len(result['branches']),'Duplicate workflow branch')
        result['branches']=[actual.get((x['model'],x['configuration_id'],x['track']),dict(x,status='missing',correct=None,total_tokens=None,total_cpu=None)) for x in planned]
        result['status']='complete' if len(actual)==24 and all(b.get('status') in ('completed','resource_exhausted','no_intervention') for b in result['branches']) else 'incomplete'
        result['physical_planner_calls']=0
    result['report_id']=digest(result);return result


def allocation(m,receipt,run):
    """Read scheduler parent allocation only: never sum .batch + allocation CPU."""
    import subprocess
    import re
    validate(m);require(Path(receipt['output']).resolve()==Path(run).resolve(),'Receipt output mismatch')
    job=str(receipt['job_id']).split(';')[0];require(re.fullmatch(r'\d+',job) is not None,'Bad receipt job')
    result=subprocess.run(['sacct','-n','-P','-j',job,'--format=JobID,State,ExitCode,ElapsedRaw,AllocTRES,TotalCPU'],
        capture_output=True,text=True,timeout=60,check=True)
    rows=[]
    for line in result.stdout.splitlines():
        parts=line.split('|')
        if len(parts)<6 or '.' in parts[0]:continue
        jid,state,exitcode,elapsed,tres,totalcpu=parts[:6]
        if not re.fullmatch(job+r'(?:_0)?',jid):continue
        counts=[int(n) for n in re.findall(r'(?:^|,)gres/gpu(?:[:][^=,]+)?=(\d+)',tres)]
        gpu=max(counts) if counts else None
        rows.append(dict(job_id=jid,state=state,exit_code=exitcode,elapsed_seconds=int(elapsed),physical_gpus=gpu,
            allocated_gpu_seconds=int(elapsed)*gpu if gpu is not None else None,scheduler_total_cpu=totalcpu))
    ok=len(rows)==1 and rows[0]['physical_gpus']==m['physical_gpus'] and rows[0]['state'] in ('COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY')
    return dict(schema='rr-worker-allocation-v1',experiment_id=m['experiment_id'],receipt_hash=digest(receipt),rows=rows,
        status='complete' if ok else 'incomplete',whole_allocation_gpu_seconds=rows[0]['allocated_gpu_seconds'] if ok else None,
        semantics='device occupancy, not FLOPs/energy; scheduler CPU includes setup and must not be added to task CPU',
        task_cpu_scope='single inference process threads plus separately measured trusted children',model_executed=False)
