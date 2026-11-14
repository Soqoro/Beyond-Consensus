"""Bounded MedQA intake, natural planning, reviewed contracts and exact-label scoring.

No dataset discovery, network access, model loading or scheduler entry point.
Transport/journal injection uses the existing metered worker interface.
"""
from copy import deepcopy
import hashlib,json
from .model import digest,Invalid
from .joint_schema import require,decode
from . import d1_natural_screen as natural,composite_math as worker
from . import composite_scaling as spec,composite_scaling_runtime as runtime

VERSION='medqa-four-option-dev-v1'
LABELS=('A','B','C','D')
POLICY='medqa-dev-id-sha256-seed0-first12-v1'
PLAN_PROMPT=natural.PROMPT.replace('mathematical work','exam-question work').replace('mathematical output','intermediate output')+'''
The original question and all four unmarked options are public. problem_statement
means that complete public source. Do not identify an answer or supply a diagnosis
as an already solved fact in a task responsibility. Do not force parallelism or
multiple tasks. This is closed-book exam work: no retrieval or external tools.'''
WORK_PROMPT='''Perform only the declared responsibility using the original exam question,
all four unmarked options and the supplied parent artifacts. No external tools.
Return one JSON object with exactly the required string fields, in their given order.
Give concise finished reasoning. For a terminal task, put the finished justification
first and one option_label last, exactly A, B, C or D. Do not add an answer-text field.
If unable to complete the task, state the limitation; do not invent intermediate facts.'''
PLAN_LIMITS=dict(maximum_calls=12,context=16384,input_cap=13312,output_cap=3072,
    token_cap=196608,wall_seconds=3600,physical_gpus=1,cpus=4,host_memory_gb=128,minimum_vram_bytes=80000000000)

def public_record(row,identity):
    q=row.get('question');opts=row.get('options')
    require(isinstance(q,str) and q.strip(),'question')
    require(type(opts)is dict and set(opts)==set(LABELS),'exact original four-option variant')
    require(all(isinstance(opts[k],str) and opts[k].strip() for k in LABELS),'option text')
    return dict(id=identity,question=q,options={k:opts[k] for k in LABELS})

def protected_record(row,identity,public):
    # Text is only a cross-check/fallback when unique. Never choose first duplicate.
    label=row.get('answer_idx');text=row.get('answer')
    if label is None and isinstance(text,str):
        matches=[k for k in LABELS if public['options'][k]==text]
        label=matches[0] if len(matches)==1 else None
    valid=label in LABELS and (text is None or public['options'][label]==text)
    return dict(id=identity,public_digest=digest(public),correct_option=label if valid else None,
        status='known' if valid else 'unknown_ambiguous_or_inconsistent_mapping')

def intake(raw,provenance):
    require(provenance.get('read_authorized') is True,'explicit local source-read permission required')
    require(provenance.get('dataset')=='MedQA-USMLE' and provenance.get('language')=='English' and
            provenance.get('variant')=='four-option' and provenance.get('split')=='dev','verified dev variant required')
    require(all(provenance.get(k) for k in ('revision','artifact','terms_reference','source_verification')),'source/version/terms receipt required')
    require(hashlib.sha256(raw).hexdigest()==provenance['sha256'],'source bytes')
    require(len(raw)<=64*1024*1024,'bounded source')
    eligible=[];blocked=[];private={};seen=set()
    for i,line in enumerate(raw.decode('utf8').splitlines(),1):
        row=decode(line);require(type(row)is dict,'record object')
        identity=str(row['id']) if row.get('id') is not None else 'dev/row/'+str(i)
        require(identity not in seen,'duplicate authoritative identity');seen.add(identity)
        try:public=public_record(row,identity)
        except Invalid as e:blocked.append(dict(id=identity,row=i,reason=str(e)));continue
        eligible.append(public);private[identity]=protected_record(row,identity,public)
    ranked=sorted(eligible,key=lambda r:(digest([POLICY,r['id']]),r['id']))
    selected=ranked[:12]
    packet=dict(schema=VERSION,selection_rule=POLICY,source_provenance=deepcopy(provenance),
        records=selected,blocked=blocked,eligible_count=len(eligible),selected_count=len(selected),
        status='selected_pending_planner_approval' if len(selected)==12 else 'blocked_insufficient_eligible_sources',
        reserved_count=max(0,len(eligible)-12),execution_allowed=False,model_executed=False)
    packet['cohort_digest']=digest(packet)
    return packet,{r['id']:private[r['id']] for r in selected}

def assert_public(r):
    require(set(r)=={'id','question','options'},'public-only source boundary')
    require(public_record(r,r['id'])==r,'public record validation')

def planner_request(r):
    assert_public(r)
    p=dict(schema=natural.VERSION,prompt=PLAN_PROMPT,source=deepcopy(r),response_schema=natural.response_schema())
    return dict(payload=p,payload_digest=digest(p))

def plan_batch(journal,packet):
    require(packet['cohort_digest']==digest({k:v for k,v in packet.items() if k!='cohort_digest'}),'cohort integrity')
    require(packet['selected_count']==12,'exactly twelve frozen candidates')
    rows=[]
    for r in packet['records']:
        # Journal owns uncertainty/caps; exceptions propagate and stop the batch.
        a=journal.invoke(planner_request(r),'planning/'+r['id'],'plan')
        if a is None:
            rows.append(dict(source_id=r['id'],status='input_overflow',meaningfulness='unknown',automatic_admission=False));continue
        obs=a['observation']
        review=natural.review_response(obs.get('final_text'),r['id']) if obs.get('finish_reason')=='eos' and not obs.get('boundary_error') else dict(status='invalid_or_truncated')
        rows.append(dict(source_id=r['id'],invocation=a['id'],raw_response=obs.get('final_text'),review=review,
            meaningfulness='pending_human_review',automatic_admission=False))
    return dict(cohort_digest=packet['cohort_digest'],rows=rows,usage=journal.snapshot()['totals'],
        status='planning_complete_review_required',worker_execution_allowed=False)

def grade(raw,protected,public):
    assert_public(public)
    require(protected['id']==public['id'] and protected['public_digest']==digest(public),'grade/source binding')
    try:
        obj=decode(raw)
        require(type(obj)is dict and set(obj)=={'justification','option_label'},'terminal fields')
        require(type(obj['justification'])is str and bool(obj['justification'].strip()),'justification')
        require(type(obj['option_label'])is str and obj['option_label'] in LABELS,'exact option label; no normalization')
    except (Invalid,ValueError,TypeError):return dict(status='structurally_invalid',correct=None)
    if protected['status']!='known':return dict(status='unknown_grade',correct=None,option_label=obj['option_label'])
    return dict(status='graded',correct=obj['option_label']==protected['correct_option'],option_label=obj['option_label'],
        meaning='exam-answer agreement only; reasoning not certified')

def admit(public,plan_row,review):
    """Explicit human-reviewed contract; no automatic plan-to-executable admission."""
    assert_public(public)
    require(natural.parse_response(plan_row['raw_response'],public['id'])['status']=='wire_valid','structurally valid plan')
    require(review.get('decision')=='admitted' and review.get('reviewer') and review.get('reviewed_at'),'human responsibility review required')
    require(review.get('public_digest')==digest(public) and review.get('plan_digest')==digest(plan_row),'source/plan review binding')
    require(review.get('substantive_no_answer_leakage') is True,'solution-free responsibilities reviewed')
    tasks=deepcopy(review['tasks']);outputs=review['outputs']
    require(len(outputs)==1 and 1<=len(tasks)<=8,'one substantive terminal; bounded component')
    require([t['id'] for t in tasks]==['t'+str(i) for i in range(len(tasks))],'canonical task IDs')
    for t in tasks:
        require(set(t)=={'id','responsibility','parents','fields'},'reviewed task fields')
        require(t['fields']==(['justification','option_label'] if t['id'] in outputs else ['derivation','artifact']),'fixed wire fields')
    c=dict(source_id=public['id'],statement_sha256=digest(public),tasks=tasks,outputs=outputs,A_modes=['base'],C='direct_parent_artifacts',reference_mode='base',
        raw_plan_sha256=digest(plan_row),review=deepcopy(review),status='reviewed_development')
    c['contract_id']=digest({k:c[k] for k in ('source_id','statement_sha256','tasks','outputs','A_modes','C','reference_mode')});c['namespace']='c'+c['contract_id'][:10]
    spec.validate_component(c);return c

def descriptor(c,t,mode):
    v=spec.descriptor(c,t,mode);v['prompt']=WORK_PROMPT;v['adapter']=VERSION;return v
def key(c,t,mode):return digest(descriptor(c,t,mode))
def coverage(cs):return [dict(key=key(c,t,'base'),historical_key=spec.key(c,t,'base'),component=c['namespace'],source_id=c['source_id'],task=t['id'],mode='base',descriptor=descriptor(c,t,'base')) for c in cs for t in c['tasks']]
def domain(cs,n,prices=None):return spec.domain(cs,n,None if prices is None else {e['historical_key']:prices[e['key']] for e in coverage(cs)})
def check_profile(r,e):
    from .composite_derivation_interface import check_profile as check
    check(r,e)

def worker_request(c,t,sources,parents):
    r=sources[c['source_id']];assert_public(r);require(digest(r)==c['statement_sha256'],'source integrity')
    require(set(parents)==set(t['parents']),'exact current-fork parents')
    p=dict(instruction=WORK_PROMPT,task_id=t['id'],responsibility=t['responsibility'],source=deepcopy(r),parent_artifacts=parents,required_string_fields=t['fields'])
    return dict(payload=p,payload_digest=digest(p))
class Engine(runtime.Engine):
    def make_request(self,t,store):
        c=self.components[t['_component']]
        parents={p:json.loads(store[c['namespace']+'_e'+p[1:]].value) for p in t['parents']}
        return worker_request(c,t,self.sources,parents)

def freeze_bundles(components):
    require(len(components)<=12 and len({c['source_id'] for c in components})==len(components),'one reviewed batch only')
    bundles=[];matrix=[]
    for slot in range(1,4):
        b=spec.construct(components,4,slot,[x['sources'] for x in bundles])
        if b['status']=='supported_frozen' and b['sources'] not in [x['sources'] for x in bundles]:bundles.append(b)
        else:b['status']='PENDING_STRUCTURAL_YIELD'
        matrix.append(dict(n=4,slot=slot,status=b['status']))
    cs=sorted({c['source_id']:c for b in bundles for c in b['components']}.values(),key=lambda c:c['source_id'])
    profile=sum(len(c['tasks']) for c in cs);evaluation=sum(b['call_bounds']['evaluation_calls'] for b in bundles)
    require(profile<=24 and evaluation<=240,'bounded three-composite pilot')
    w=dict(schema=VERSION+'-worker-wave',condition=VERSION,bank={'kind':'reviewed_medqa_dev'},components=cs,bundles=bundles,matrix=matrix,profile_coverage=coverage(cs),
        profile_schedule=runtime.schedule_profiles(cs,{}),profile_consumers={},reused_profiles={},
        limits={**PLAN_LIMITS,'maximum_calls':profile+evaluation,'token_cap':(profile+evaluation)*16384,'wall_seconds':14400,'solver_seconds':30,'solver_threads':1,'solver_seed':0},
        planning_calls_ceiling=12,profile_calls=profile,evaluation_calls=evaluation,evaluation_sessions=10*len(bundles),
        source_overlap={str(b['slot']):sorted(set(b['sources']) & {s for other in bundles if other['slot']<b['slot'] for s in other['sources']}) for b in bundles},
        execution_allowed=False,grade_policy='exact option_label only; private evaluator after execution',human_review_required=True)
    w['wave_id']=digest(w);return w
