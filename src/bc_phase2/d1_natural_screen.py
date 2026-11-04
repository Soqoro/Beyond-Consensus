"""Separate natural-task screening: simple wire contract, one-shot mock ledger.

No joint-domain compilation, worker execution or live release is registered.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from collections.abc import Mapping

from .model import Invalid, digest
from .joint_schema import decode, require
from .planner_ledger import MockPlannerSession, _encoded, MAX_LEDGER_BYTES
from .planner_qwen import CHECKPOINT, REVISION, _ids
from .joint_d1_readiness import SMOKE

VERSION='d1-natural-decomposition-v1'
CONTEXT=16384
OUTPUT=3072
CALLS=3
MAX_RESPONSE_BYTES=65536
PROMPT='''Describe the natural complementary mathematical work needed to solve this question.
Do not solve it or supply the final answer. Describe responsibilities and expected
artifacts, not their values. One, two, three, or more substantive tasks are valid
findings. Sequential work is valid; parallelism is not required. Do not pad with
formatting, cosmetic checks, or duplicate whole-question solutions. Each task
needs a distinct substantive responsibility, a specific mathematical output,
implementable inputs, and a genuine contribution to answering the question.
Return one concise JSON object, without Markdown, matching the response schema.
Use task IDs T1, T2, ... (unique). required_inputs contains problem_statement or
IDs of earlier tasks whose artifacts are genuinely needed; no invented dependencies.
In final_assembly cite terminal artifacts as [T1], [T2], etc. Every task must
contribute directly or through genuine dependencies to those cited artifacts.
The citations permit a structural check; they do not prove meaningfulness.
Use single_task for exactly one substantive task, decomposed for two or more,
or unsupported with no tasks and a short reason. No ownership, costs,
communication choices, solved examples, checking quota or target task count.
One response only: no correction, retry or second sample.'''


def response_schema():
    text={'type':'string','minLength':1}
    task={'type':'object','additionalProperties':False,
          'required':['id','responsibility','required_inputs','produces'],
          'properties':{'id':{'type':'string','pattern':'^T[1-9][0-9]*$'},
                        'responsibility':text,'produces':text,
                        'required_inputs':{'type':'array','minItems':1,'uniqueItems':True,
                                           'items':{'type':'string','pattern':'^(problem_statement|T[1-9][0-9]*)$'}}}}
    branches=[]
    for status in ('single_task','decomposed','unsupported'):
        props={'schema':{'const':VERSION},'source_id':text,'status':{'const':status},
               'tasks':{'type':'array','items':task,'minItems':0 if status=='unsupported' else 1 if status=='single_task' else 2}}
        if status in ('single_task','unsupported'):props['tasks']['maxItems']=1 if status=='single_task' else 0
        props['reason' if status=='unsupported' else 'final_assembly']=text
        branches.append({'type':'object','additionalProperties':False,'required':list(props),'properties':props})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':VERSION,'oneOf':branches}


def request(record):
    require(type(record) is dict and set(record)=={'id','problem'},'statement-only id/problem required')
    require(type(record['id']) is str and bool(record['id'].strip()),'source ID')
    require(type(record['problem']) is str and bool(record['problem'].strip()),'problem statement')
    payload={'schema':VERSION,'prompt':PROMPT,'source':{k:record[k] for k in ('id','problem')},
             'response_schema':response_schema()}
    return {'payload':payload,'payload_digest':digest(payload)}


def parse_response(raw,source_id):
    require(type(raw) is str and len(raw.encode('utf8'))<=MAX_RESPONSE_BYTES,'response byte bound')
    row=decode(raw)
    require(type(row) is dict,'response object')
    status=row.get('status')
    require(status in ('single_task','decomposed','unsupported'),'screen status')
    required={'schema','source_id','status','tasks','reason' if status=='unsupported' else 'final_assembly'}
    require(set(row)==required,'response fields')
    require(row['schema']==VERSION and row['source_id']==source_id,'schema/source binding')
    require(type(row['tasks']) is list,'task list')
    if status=='unsupported':
        require(row['tasks']==[] and type(row['reason']) is str and bool(row['reason'].strip()),'unsupported reason/no tasks')
        return {'status':'unsupported','proposed_task_count':0,'meaningful_task_count':None,'semantic_review':'pending'}
    tasks=row['tasks']
    require(len(tasks)==1 if status=='single_task' else len(tasks)>=2,'status/count mismatch')
    require(type(row['final_assembly']) is str and bool(row['final_assembly'].strip()),'assembly description')
    seen=set();parents={}
    for task in tasks:
        require(type(task) is dict and set(task)=={'id','responsibility','required_inputs','produces'},'task fields')
        identity=task['id']
        require(type(identity) is str and re.fullmatch(r'T[1-9][0-9]*',identity) is not None and identity not in seen,'unique task ID')
        require(all(type(task[k]) is str and bool(task[k].strip()) for k in ('responsibility','produces')),'substantive text fields')
        inputs=task['required_inputs']
        require(type(inputs) is list and inputs and all(type(x) is str for x in inputs),'input list')
        require(len(set(inputs))==len(inputs) and set(inputs)<=(seen|{'problem_statement'}),'earlier inputs only; no cycle/dangling reference')
        parents[identity]=set(inputs)-{'problem_statement'};seen.add(identity)
    cited=set(re.findall(r'\[(T[0-9]+)\]',row['final_assembly']))
    require(cited and cited<=seen,'assembly must cite known terminal artifacts as [Tn]')
    reaches=set(cited);todo=list(cited)
    while todo:
        for parent in parents[todo.pop()]:
            if parent not in reaches:reaches.add(parent);todo.append(parent)
    require(reaches==seen,'unused task output; every task must contribute to assembly')
    return {'status':'wire_valid','declared_status':status,'proposed_task_count':len(tasks),
            'meaningful_task_count':None,'semantic_review':'pending','execution_qualified':False}


def review_response(raw,source_id):
    try:return parse_response(raw,source_id)
    except (Invalid,ValueError,TypeError,UnicodeError) as exc:
        return {'status':'invalid','error':str(exc),'proposed_task_count':None,'meaningful_task_count':None}


def verify_non_thinking(tokenizer):
    from beyond_consensus.models.transformers_backend import verify_thinking_template
    support=verify_thinking_template(tokenizer,True) # verifies actual on/off difference
    messages=[{'role':'user','content':'Synthetic non-thinking template probe.'}]
    off=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    require(type(off) is str and off.rfind('<think>')<=off.rfind('</think>') and not off.rstrip().endswith('<think>'),
            'non-thinking template must not leave an open thinking segment')
    return {'template_hash':digest(tokenizer.chat_template),'off_probe_hash':digest(off),
            'on_off_switch':support,'enable_thinking':False,'generation_verified':False}


def render_request(tokenizer,req,template_hash):
    require(digest(tokenizer.chat_template)==template_hash,'template changed')
    messages=[{'role':'user','content':json.dumps(req['payload'],sort_keys=True,ensure_ascii=False)}]
    kw={'add_generation_prompt':True,'enable_thinking':False}
    text=tokenizer.apply_chat_template(messages,tokenize=False,**kw)
    require(type(text) is str and text.rfind('<think>')<=text.rfind('</think>') and not text.rstrip().endswith('<think>'),
            'non-thinking prefix unsupported')
    encoded=tokenizer.apply_chat_template(messages,tokenize=True,return_dict=True,return_tensors=None,**kw)
    ids=_ids(encoded.get('input_ids') if isinstance(encoded,Mapping) else encoded)
    require(ids==tokenizer.encode(text,add_special_tokens=False),'text/token mismatch')
    require(len(ids)+OUTPUT<=CONTEXT,'input overflow; never truncate')
    return {'messages':messages,'rendered_text':text,'input_ids':ids,'input_tokens':len(ids),
            'payload_digest':req['payload_digest'],'rendered_ids_digest':digest(ids)}


class NaturalTransport:
    """Injected model/tokenizer plumbing; shares RepoRecourse helpers, never loads weights."""
    def __init__(self,tokenizer,model,torch):
        from beyond_consensus.models.transformers_backend import generation_tokens
        self.tokenizer,self.model,self.torch=tokenizer,model,torch
        self.template=verify_non_thinking(tokenizer)
        self.tokens=generation_tokens(tokenizer,model.generation_config)
        self.binding={'checkpoint':CHECKPOINT,'revision':REVISION,'template':self.template,
                      'tokens':self.tokens,'context':CONTEXT,'output':OUTPUT,'do_sample':False,
                      'thinking':False,'evidence':'injected_offline_double','inventory_digest':None}

    def render(self,req):return render_request(self.tokenizer,req,self.template['template_hash'])

    def generate(self,rendered):
        t=self.torch;ids=rendered['input_ids'];inputs=t.tensor([ids],dtype=t.long,device='cuda:0')
        start=time.monotonic()
        with t.inference_mode():
            result=self.model.generate(input_ids=inputs,attention_mask=t.ones_like(inputs),max_new_tokens=OUTPUT,
                do_sample=False,use_cache=True,num_beams=1,num_return_sequences=1,return_dict_in_generate=True,**self.tokens)
        t.cuda.synchronize();sequence=_ids(result.sequences)
        require(sequence[:len(ids)]==ids,'generation prefix mismatch; usage unresolved')
        generated=sequence[len(ids):];eos=self.tokens['eos_token_id']
        finish='eos' if generated and generated[-1] in eos else 'length_limit' if len(generated)>=OUTPUT else 'unknown'
        raw=self.tokenizer.decode(generated,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        final=generated[:-1] if finish=='eos' else generated
        text=self.tokenizer.decode(final,skip_special_tokens=False,clean_up_tokenization_spaces=False)
        boundary=None
        if any(x in eos for x in generated[:-1]):boundary='interior_eos'
        if '<think>' in raw or '</think>' in raw:boundary='unexpected_generated_thinking'
        if len(generated)>OUTPUT:boundary='output_overrun'
        return dict(input_tokens=len(ids),output_tokens=len(generated),generated_ids=generated,raw_decoded=raw,
                    final_text=text,finish_reason=finish,boundary_error=boundary,wall_seconds=time.monotonic()-start)


def reliable_terminal(attempt):
    """Outcome quality does not determine continuation; reliable accounting does."""
    if attempt.get('state') not in ('completed','invalid_response','response_boundary_error'):return False
    observed=attempt.get('observation') or {}
    inp=observed.get('input_tokens');out=observed.get('output_tokens')
    return (type(inp) is int and 0<inp<=CONTEXT-OUTPUT and inp==attempt.get('input_tokens')
            and type(out) is int and 0<=out<=OUTPUT
            and type(attempt.get('actual_tokens')) is int and attempt['actual_tokens']==inp+out
            and attempt.get('reservation_tokens')==inp+OUTPUT
            and observed.get('finish_reason') in ('eos','length_limit')
            and (observed.get('finish_reason')!='length_limit' or out==OUTPUT))


class NaturalMockSession(MockPlannerSession):
    """Reuse atomic locking/fsync/integrity primitives; one response is terminal."""
    def __init__(self,directory,records,transport):
        require(type(transport) is NaturalTransport,'offline natural transport required')
        require(type(records) is list and len(records)==CALLS,'three ordered synthetic records')
        requests=[request(r) for r in records]
        require(all(r['id'].startswith('mock:') for r in records),'mock IDs only; source access not granted')
        require(len({r['id'] for r in records})==CALLS,'unique sources')
        self.transport=transport
        self.binding={'version':VERSION,'requests':requests,'transport':deepcopy(transport.binding),
                      'implementation':implementation(),'scope':'mock_only','model_executed':False}
        require(len(_encoded(self.binding))<MAX_LEDGER_BYTES//2,'binding too large')
        self.root=Path(directory);self.root.mkdir(parents=True,exist_ok=True)
        with self._locked():
            if self.path.exists():self._read()
            else:self._save(dict(binding=self.binding,binding_digest=digest(self.binding),attempts=[],
                                 started_at=time.time(),model_executed=False,execution_allowed=False))

    def advance(self,source_id):
        require(self.transport.binding==self.binding['transport'],'transport changed')
        with self._locked():
            state=self._read();attempts=state['attempts']
            require(all(reliable_terminal(a) for a in attempts),'unreliable dispatch/usage or resource breach; stop, no replay')
            require(len(attempts)<CALLS and self.binding['requests'][len(attempts)]['payload']['source']['id']==source_id,
                    'one response per source in frozen order')
            require(0<=time.time()-state['started_at']<3600,'wall ceiling')
            req=self.binding['requests'][len(attempts)];rendered=self.transport.render(req)
            count=rendered['input_tokens'];require(type(count) is int and 0<count<=CONTEXT-OUTPUT,'input cap')
            reservation=count+OUTPUT
            require(sum(a['actual_tokens'] or 0 for a in attempts)+reservation<=CALLS*CONTEXT,'aggregate token cap')
            attempt={'source_id':source_id,'state':'reserved','input_tokens':count,'reservation_tokens':reservation,
                     'actual_tokens':None,'outbound_payload':req['payload'],'payload_digest':req['payload_digest'],
                     'rendered':rendered,'reserved_at':datetime.now(timezone.utc).isoformat()}
            attempts.append(attempt);self._save(state)
            start=time.monotonic();cpu=time.process_time()
            observed=self.transport.generate(rendered) # crash leaves full reservation, no auto replay
            attempt.update(observation=deepcopy(observed),cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start)
            usage=observed.get('output_tokens')
            if type(usage) is not int or usage<0 or type(observed.get('input_tokens')) is not int or observed['input_tokens']!=count:
                attempt['state']='uncertain'
            else:
                attempt['actual_tokens']=count+usage
                attempt['state']='completed' if usage<=OUTPUT else 'usage_violation'
            attempt['raw_response']=observed.get('final_text') # unchanged, no extraction/repair
            if observed.get('finish_reason')!='eos' or observed.get('boundary_error'):
                if attempt['state']=='completed':attempt['state']='response_boundary_error'
            attempt['review']=review_response(attempt['raw_response'],source_id)
            if attempt['review']['status']=='invalid' and attempt['state']=='completed':attempt['state']='invalid_response'
            if time.time()-state['started_at']>=3600:attempt['state']='wall_limit_exceeded'
            self._save(state)
            return deepcopy(attempt)


def implementation():
    root=Path(__file__).resolve().parents[2]
    files=['src/bc_phase2/d1_natural_screen.py','src/bc_phase2/planner_ledger.py','src/bc_phase2/planner_qwen.py',
           'src/bc_phase2/joint_schema.py','src/bc_phase2/model.py','src/beyond_consensus/models/transformers_backend.py']
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files}


def disabled_manifest():
    from .joint_d1_local import STATEMENTS_HASH,STATEMENT_HASHES,METADATA,DATASET_HASH
    scope={'condition':VERSION,'approval_kind':'D1-natural-screen-v1','source_ids':list(SMOKE),
           'source_package':{'path':'/dataset/suaq0001/beyond-consensus/diagnostics/d1-input-binding.Vu18JB',
             'statements_file_sha256':STATEMENTS_HASH,'statement_hashes':STATEMENT_HASHES,'dataset_sha256':DATASET_HASH,
             'hash_evidence':'previous_repository_receipt_not_reverified','read_and_transmit_permission':None},
           'model':{'checkpoint':CHECKPOINT,'revision':REVISION,'dtype':'bfloat16','attention':'sdpa',
             'do_sample':False,'num_beams':1,'thinking':False,'context_limit':CONTEXT,'max_new_tokens':OUTPUT,
             'expected_metadata_hashes':METADATA,'current_inventory':None,'non_thinking_verification':None},
           'prompt_hash':digest(PROMPT),'schema_hash':digest(response_schema()),'implementation':implementation(),
           'initial_token_counts':None,'rendered_request_hashes':None,
           'resources':{'maximum_calls':3,'calls_per_source':1,'input_token_cap':13312,'output_token_cap':3072,
             'aggregate_token_cap':49152,'campaign_wall_seconds':3600,'physical_gpus':1,'concurrency':1,
             'minimum_vram_bytes':80000000000,'host_memory_gb':128,'cpus':4,'partition':None,
             'monetary_ceiling':None,'currency':None,'fee_status':'unverified_local_backend',
             'units':{'tokens':'input plus all generated tokens including EOS','cpu':'process seconds','wall':'seconds'}},
           'retry_policy':'one_response_per_source_no_correction_no_retry_no_resume_ambiguous',
           'stop_policy':'continue_after_reliably_accounted_terminal_outcome_no_retry_stop_on_uncertain_dispatch_usage_source_integrity_or_resource_breach',
           'cache_policy':'no_response_cache_reuse','tools':[],'D2_D6_enabled':False}
    return {'schema':'d1-natural-screen-disabled-v1','scope':scope,'scope_digest':digest(scope),
            'scope_complete':False,'approval':None,'execution_allowed':False,'D1_APPROVED_TO_RUN':False}


def preflight(manifest):
    require(manifest==disabled_manifest(),'disabled proposal changed; exact preparation required')
    return {'status':'disabled_missing_exact_scope_approval','scope_digest':manifest['scope_digest'],
            'blockers':['new_source_package_read_and_transmit_permission','current_local_model_inventory',
                        'pinned_non_thinking_template_verification','actual_initial_token_fit_and_request_hashes',
                        'scheduler_partition_and_resource_binding','exact_D1-natural-screen-v1_approval',
                        'live_scope_bridge_not_registered'],
            'rows':[{'source_id':s,'status':'unrun','proposed_task_count':None,'meaningful_task_count':None,
                     'actual_tokens':0,'reserved_tokens':0} for s in SMOKE],
            'model_calls':0,'model_executed':False,'execution_allowed':False,'D1_APPROVED_TO_RUN':False,
            'live_stages':{f'D{i}':'disabled' for i in range(1,7)}}


def open_live(*args,**kwargs):
    raise Invalid('D1-natural-screen-v1 live scope not approved or registered; no model loading')
