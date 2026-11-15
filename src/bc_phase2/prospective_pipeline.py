"""Fixed-block integration with the accepted profile/selection/R0 engine.

No live transport is opened here. Review and source access remain explicit.
"""
from copy import deepcopy
import json
import sys
import hashlib
from pathlib import Path
from .model import digest
from .joint_schema import require, decode
from . import d1_natural_screen as natural, composite_math as worker
from . import composite_scaling as spec, composite_scaling_runtime as runtime
from . import medqa_worker_launch as roles, prospective_adapters as adapters
from .prospective_sources import select_block, SIZES
from .composite_joint import WORKER_POLICY

VERSION='source-disjoint-block-v1'
LIMITS=dict(context=16384,input_cap=13312,output_cap=3072,physical_gpus=1,cpus=4,
            host_memory_gb=128,minimum_vram_bytes=80000000000,solver_seconds=30,solver_threads=1,solver_seed=0)

def procedure(dataset):
    require(dataset in SIZES,'dataset')
    root=Path(__file__).resolve().parents[2]
    names=('prospective_sources','prospective_adapters','prospective_pipeline','d1_natural_screen',
           'composite_scaling','composite_scaling_runtime','composite_math','composite_joint',
           'medqa_development','medqa_worker_launch','joint_pipeline_runtime','joint_core')
    implementation={name:hashlib.sha256((root/'src/bc_phase2'/f'{name}.py').read_bytes()).hexdigest() for name in names}
    p=dict(version=VERSION,implementation=implementation,model_policy=WORKER_POLICY,dataset=dataset,methods=['NEUTRAL','JOINT'],n=4,K=2,
           objective='mean_first',recovery='all_owner_R0_original_snapshot',
           planner_prompt=adapters.planner_request(dataset,{'id':'synthetic','problem':'synthetic'} if dataset in ('math500','aime2025','aime2026') else
                {'id':'synthetic','question':'synthetic','options':dict(zip('ABCD',['one','two','three','four']))})['payload']['prompt'],
           response_schema=natural.response_schema(),planner_calls_per_source=1,corrections=0,
           admission='source/plan bound solution-free substantive whole components; human or explicitly labelled AI-assisted review',
           subset_order=['abs(m-6)','m','source_rank_tuple'],m_range=[5,8],max_operations_per_task=1,
           max_component_tasks=64,max_plan_bytes=natural.MAX_RESPONSE_BYTES,
           private_keys_in_workers=False,new_profiles_required=True,limits=LIMITS,
           source_order='bc-prospective-source-disjoint-v1',outcome_adaptation=False,
           worker_prompts={'intermediate':roles.INTERMEDIATE_PROMPT,'terminal':roles.TERMINAL_PROMPT,
                          'math':worker.PROMPT},AIME_terminal='justification then final_integer: trimmed ASCII [0-9]{1,3}',
           larger_plans='valid_but_outside_capacity_never_truncated')
    p['procedure_digest']=digest(p);return p

def admit(dataset, cohort, public, raw_plan, review):
    require(cohort['procedure_digest']==procedure(dataset)['procedure_digest'], 'frozen procedure')
    source=next(r for b in cohort['blocks'] for r in b['records'] if r['source_id']==public['id'])
    require(source['status']=='eligible','source review unresolved')
    from .prospective_sources import faithful_identity
    require(faithful_identity(public)==(source['exact_hash'],source['normalized_hash']), 'source content')
    parsed=natural.parse_response(raw_plan,public['id'])
    require(parsed['status']=='wire_valid', 'wire-valid plan, not automatic admission')
    require(review.get('decision')=='admitted' and review.get('reviewer') and review.get('reviewed_at')
            and review.get('reviewer_kind') in ('human','AI-assisted'), 'explicit labelled contract review')
    require(review.get('public_digest')==digest(public) and review.get('plan_digest')==digest(raw_plan)
            and review.get('substantive_no_answer_leakage') is True,'review binding/no solution leakage')
    ts=deepcopy(review['tasks']);outputs=review['outputs']
    require(1<=len(ts)<=64 and [t['id'] for t in ts]==[f't{i}' for i in range(len(ts))], 'finite canonical tasks')
    require(len(outputs)==1, 'one authoritative final per whole question')
    final=['justification','option_label'] if dataset in ('medqa','gpqa') else ['justification','final_integer'] if dataset.startswith('aime') else ['justification','final_answer']
    for t in ts:
        require(set(t)=={'id','responsibility','parents','fields'},'contract fields')
        require(type(t['fields']) is list and t['fields'],'nonempty field list')
        require(t['fields']==final if t['id'] in outputs else t['fields'][0]=='derivation','derivation first / authoritative terminal')
        if dataset in ('medqa','gpqa') and t['id'] not in outputs:
            require(t['fields']==['derivation','artifact'],'qualified intermediate role boundary')
        require(len(t['fields'])<=16 and all(type(f) is str and f.isidentifier() for f in t['fields']), 'bounded named fields')
    c=dict(source_id=public['id'],statement_sha256=digest(public),tasks=ts,outputs=outputs,
           A_modes=review.get('A_modes',['base']),C='direct_parent_artifacts',reference_mode=review.get('reference_mode','base'),
           raw_plan_sha256=digest(raw_plan),review=deepcopy(review),status='reviewed_prospective',dataset=dataset,
           prospective_cohort=cohort['cohort_digest'])
    if c['A_modes']!=['base']:
        require(review.get('mode_semantics_reviewed') is True and dataset=='math500','existing mathematical alternatives only with review')
    c['contract_id']=digest({k:c[k] for k in ('source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode')})
    c['namespace']='c'+c['contract_id'][:10];spec.validate_component(c)
    return dict(status='admitted' if len(ts)<=8 else 'outside_capacity',component=c)

def prompt(c,t):
    if c['dataset'] in ('medqa','gpqa'):
        return roles.role_prompt(t)
    result=worker.PROMPT
    if c['dataset'].startswith('aime') and t['id'] in c['outputs']:
        result+='\nReturn finished justification first, then final_integer as exactly one ASCII integer string from 0 to 999. No prose or multiple candidates in final_integer.'
    return result

def worker_request(c,t,sources,parents):
    source=sources[c['source_id']]
    require(digest(source)==c['statement_sha256'], 'source integrity')
    require(set(parents)==set(t['parents']), 'exact current-fork parents')
    # t is the actually selected task, including admitted mode instructions.
    expected=[spec.task(c,x,mode) for mode in c['A_modes'] for x in c['tasks'] if x['id']==t['id']]
    public_task={k:t[k] for k in ('id','responsibility','parents','fields')}
    require(public_task in expected, 'selected task contract mismatch')
    payload=dict(instruction=prompt(c,t),task_id=t['id'],responsibility=t['responsibility'],
                 source=deepcopy(source),parent_artifacts=deepcopy(parents),required_string_fields=t['fields'])
    return dict(payload=payload,payload_digest=digest(payload))

def descriptor(c,t,mode):
    v=spec.descriptor(c,t,mode);v.update(prompt=prompt(c,spec.task(c,t,mode)),adapter=VERSION,dataset=c['dataset']);return v
def key(c,t,mode):return digest(descriptor(c,t,mode))
def coverage(cs):
    return [dict(key=key(c,t,a),historical_key=spec.key(c,t,a),component=c['namespace'],source_id=c['source_id'],
                 task=t['id'],mode=a,descriptor=descriptor(c,t,a)) for c in cs for a in c['A_modes'] for t in c['tasks']]
def domain(cs,n,prices=None):
    return spec.domain(cs,n,None if prices is None else {e['historical_key']:prices[e['key']] for e in coverage(cs)})
from .composite_derivation_interface import check_profile
class Engine(runtime.Engine):
    def make_request(self,t,store):
        c=self.components[t['_component']]
        parents={p:json.loads(store[c['namespace']+'_e'+p[1:]].value) for p in t['parents']}
        return worker_request(c,t,self.sources,parents)
    def parse_artifact(self,text,task):
        value=super().parse_artifact(text,task);v=decode(value)
        if 'option_label' in task['fields']:require(v['option_label'] in adapters.LABELS,'exact option label')
        if 'final_integer' in task['fields']:adapters.integer(v['final_integer'])
        return value

def wave(cohort,slot,dispositions):
    selected=select_block(cohort,slot,dispositions)
    if selected['bundle'] is None:return selected
    b=selected['bundle'];cs=b['components'];entries=coverage(cs);schedule=runtime.schedule_profiles(cs,{})
    profile=sum(s['calls'] for s in schedule);evaluation=b['call_bounds']['evaluation_calls']
    require(profile<=16 and evaluation<=80,'one-call task/mode bound')
    limits=dict(LIMITS,maximum_calls=profile+evaluation,token_cap=(profile+evaluation)*16384,wall_seconds=14400)
    w=dict(condition=VERSION,cohort_digest=cohort['cohort_digest'],components=cs,bundles=[b],
           planned_slots=len(cohort['blocks']),matrix=[dict(n=4,slot=slot,status='supported_frozen')],profile_coverage=entries,profile_schedule=schedule,
           profile_consumers={e['key']:[b['preprice_id']] for e in entries},reused_profiles={},limits=limits,
           dispositions=selected['dispositions'],execution_allowed=False)
    w['wave_id']=digest(w);return w

def plan_block(journal,cohort,slot,sources,out):
    """Injected durable journal, one call per eligible source. Persist each outcome."""
    from pathlib import Path
    from beyond_consensus.util import atomic_json
    block=next(b for b in cohort['blocks'] if b['slot']==slot);out=Path(out);out.mkdir(exist_ok=False)
    rows=[]
    for r in block['records']:
        sid=r['source_id']
        if r['status']!='eligible':row=dict(source_id=sid,status='blocked',review=None)
        else:
            from .prospective_sources import faithful_identity
            require(faithful_identity(sources[sid])==(r['exact_hash'],r['normalized_hash']), 'source content changed')
            a=journal.invoke(adapters.planner_request(cohort['dataset'],sources[sid]),'planning/'+sid,'plan')
            if a is None:row=dict(source_id=sid,status='unrun_fit',review=None)
            else:
                require(worker.reliable_terminal(a),'uncertain usage/dispatch stops block')
                obs=a['observation'];raw=obs.get('final_text')
                review=natural.review_response(raw,sid) if obs.get('finish_reason')=='eos' and not obs.get('boundary_error') else {'status':'invalid_or_truncated'}
                row=dict(source_id=sid,status='completed',raw_response=raw,review=review,invocation=a['id'])
        rows.append(row);atomic_json(out/'planning.json',{'rows':rows,'totals':journal.snapshot()['totals'],
            'unrun_ids':[x['source_id'] for x in block['records'][len(rows):]],'worker_execution_allowed':False})
    return rows

def run_wave(journal,sources,out,w):
    require(w['wave_id']==digest({k:v for k,v in w.items() if k!='wave_id'}), 'wave integrity')
    return runtime.run_wave(journal,sources,out,w,interface=sys.modules[__name__])


def planning_packet(cohort,slot,sources):
    require(cohort['cohort_digest']==digest({k:v for k,v in cohort.items() if k!='cohort_digest'}),'cohort integrity')
    require(cohort['procedure_digest']==procedure(cohort['dataset'])['procedure_digest'],'procedure unchanged')
    from .prospective_sources import faithful_identity
    block=next(b for b in cohort['blocks'] if b['slot']==slot)
    requests=[]
    for record in block['records']:
        if record['status']!='eligible':continue
        pub=sources[record['source_id']]
        require(faithful_identity(pub)==(record['exact_hash'],record['normalized_hash']),'exact public source')
        requests.append(adapters.planner_request(cohort['dataset'],pub))
    limits=dict(LIMITS,maximum_calls=len(requests),calls_per_source=1,token_cap=len(requests)*16384,wall_seconds=3600)
    out=dict(schema=VERSION+'-planning-preparation',cohort_digest=cohort['cohort_digest'],slot=slot,
             requests=requests,limits=limits,model_policy=WORKER_POLICY,execution_allowed=False,
             blocked_ids=[r['source_id'] for r in block['records'] if r['status']!='eligible'],
             remaining=['pinned tokenizer full-request measurements','source usage and scheduler binding',
                        'block-specific shared-registry planner launcher binding','exact source-transmission and GPU approval'])
    out['preparation_digest']=digest(out);return out
