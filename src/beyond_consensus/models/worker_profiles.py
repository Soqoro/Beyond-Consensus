"""Opt-in worker-selection deployments. Legacy backend/qualification unchanged."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import importlib.metadata
import json
import os
import time
from ..util import BCError, digest, file_hash, read_json
from .process_trace import process_launch_trace
from .transformers_backend import TransformersBackend, generation_tokens, verify_thinking_template, require_allocation

MODE='reporecourse-json-unique-v1-pool-7'
CONTROL='fc05daec18b0a78c049392ed2e771dde82bdf654'
CODER='a7fbcb5c0e12d62a448eaa0e260346bf5dcc0feb'
PACKAGES={'transformers':'5.3.0','accelerate':'1.12.0','xgrammar':'0.1.32'}


def profile(name):
    if name not in ('control','coder'):raise BCError('Unknown worker profile')
    coder=name=='coder';rev=CODER if coder else CONTROL
    return dict(schema='rr-worker-profile-v1',name=name,
        model=dict(backend='transformers',checkpoint='Qwen/Qwen3-Coder-Next' if coder else 'Qwen/Qwen3.5-27B',
            revision=rev,tokenizer_revision=rev,dtype='bfloat16',context_limit=16384,max_new_tokens=4096,
            thinking=not coder,do_sample=False,temperature=0.7,top_p=0.8,top_k=20,action_constraint=MODE),
        architecture='Qwen3NextForCausalLM' if coder else 'Qwen3_5ForConditionalGeneration',
        physical_gpus=4 if coder else 1,placement='explicit_single_process_layer_sharding' if coder else 'single_cuda',
        minimum_total_bytes=75*1024**3,minimum_free_bytes=70*1024**3,
        host_memory_gb=256 if coder else 128,packages=deepcopy(PACKAGES),
        cpu_accounting='single_process_inference_threads_plus_separately_charged_trusted_children',
        reasoning='known_zero' if coder else 'generated_think_close_partition',
        status='requires_fresh_qualification_not_measured_fit')


def implementation():
    root=Path(__file__).resolve().parents[3]
    names=['src/beyond_consensus/models/'+s+'.py' for s in ('worker_profiles','process_trace','decoder_trace','constrained','unique_keys','action_schema','transformers_backend')]
    names+=['src/reporecourse/action_schema.py']
    return {n:file_hash(root/n) for n in names}


def versions():
    return {n:importlib.metadata.version(n) for n in ('torch','transformers','accelerate','tokenizers','huggingface-hub','safetensors','xgrammar')}


def verify_lock(p,lock,weights=False):
    if p!=profile(p['name']):raise BCError('Worker profile changed')
    for k in ('checkpoint','revision','tokenizer_revision'):
        if lock.get(k)!=p['model'][k]:raise BCError('Worker lock identity changed: '+k)
    if lock.get('model_path')!=lock.get('tokenizer_path') or not lock.get('weight_hashes'):raise BCError('Co-revision inventory required')
    root=Path(lock['model_path'])
    required={'config.json','generation_config.json','tokenizer.json','tokenizer_config.json','model.safetensors.index.json'}
    if not required<=set(lock.get('metadata_hashes',{})):raise BCError('Required metadata hashes missing')
    for name in set(lock['metadata_hashes'])|set(lock['weight_hashes']):
        if Path(name).is_absolute() or '..' in Path(name).parts:raise BCError('Lock path escapes staging root')
    for name,h in lock['metadata_hashes'].items():
        if file_hash(root/name)!=h:raise BCError('Changed model metadata')
    config=read_json(root/'config.json')
    if config.get('architectures')!=[p['architecture']] or config.get('quantization_config'):raise BCError('Architecture/precision mismatch')
    if set(read_json(root/'model.safetensors.index.json')['weight_map'].values())!=set(lock['weight_hashes']):raise BCError('Weight inventory mismatch')
    if weights:
        for name,h in lock['weight_hashes'].items():
            if file_hash(root/name)!=h:raise BCError('Weight checksum mismatch')


def template_options(p):
    return {'enable_thinking':True} if p['model']['thinking'] else {}


def qualify(p,lock):
    """Allocated CPU/native controls; no weights/model loaded."""
    if not os.environ.get('SLURM_JOB_ID'):raise BCError('Native qualification requires CPU allocation')
    verify_lock(p,lock); packages=versions()
    if any(packages[k]!=v for k,v in PACKAGES.items()):raise BCError('Use isolated exact dependency proposal')
    import torch
    from transformers import AutoTokenizer
    from .constrained import ActionConstraint
    from .unique_keys import qualify_unique_keys
    from .action_schema import validate_action
    from reporecourse.action_schema import controls_v2
    tokenizer=AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True,trust_remote_code=False)
    template=verify_thinking_template(tokenizer,p['model']['thinking'])
    gen=read_json(Path(lock['model_path'])/'generation_config.json')
    stops=generation_tokens(tokenizer,SimpleNamespace(eos_token_id=gen.get('eos_token_id'),pad_token_id=gen.get('pad_token_id')))
    cfg=read_json(Path(lock['model_path'])/'config.json');vocab=cfg.get('text_config',cfg)['vocab_size']
    constraint=ActionConstraint(tokenizer,vocab,stops['eos_token_id'],MODE)
    sample=tokenizer.apply_chat_template([{'role':'user','content':'Return one JSON action.'}],tokenize=False,add_generation_prompt=True,**template_options(p))
    if p['name']=='coder' and ('<think>' in sample or '</think>' in sample):raise BCError('Non-thinking template unexpectedly opens reasoning')
    closing=tokenizer.convert_tokens_to_ids('</think>')
    if type(closing) is not int or closing<0 or closing>=vocab:closing=stops['pad_token_id']
    good,bad=controls_v2(MODE)
    for action in good:
        text=json.dumps(action,separators=(',',':'));validate_action(text,MODE)
        ids=tokenizer.encode(text,add_special_tokens=False);prefix=[stops['pad_token_id']]
        processor=constraint.processor(1,None)
        for token in ids+[stops['eos_token_id'][0]]:
            scores=processor(torch.tensor([prefix]),torch.zeros((1,vocab)))
            if not torch.isfinite(scores[0,token]):raise BCError('Native action token masked')
            prefix.append(token)
    for text in bad:
        matcher=constraint.xgr.GrammarMatcher(constraint.compiled)
        if matcher.accept_string(text) and matcher.accept_token(stops['eos_token_id'][0]):raise BCError('Invalid native control accepted')
    unique=qualify_unique_keys(constraint,tokenizer,torch,closing,stops['eos_token_id'],vocab)
    result=dict(schema='rr-worker-native-v1',profile=p,lock_hash=digest({k:v for k,v in lock.items() if k!='worker_qualification'}),
        packages=packages,implementation=implementation(),template=template,generation_tokens=stops,vocab_size=vocab,
        status='passed',unique_key_controls=unique,positive_controls=len(good),negative_controls=len(bad),model_executed=False)
    return result


def require_qualified(p,lock):
    verify_lock(p,lock)
    q=lock.get('worker_qualification',{})
    if (q.get('profile')!=p or q.get('status')!='passed' or q.get('model_executed') is not False or
        q.get('implementation')!=implementation() or q.get('packages')!=versions() or
        q.get('lock_hash')!=digest({k:v for k,v in lock.items() if k!='worker_qualification'})):
        raise BCError('Fresh model-specific 4096 native qualification required')
    return q


def device_map(p,layers):
    if p['name']=='control':return {'':0}
    if layers!=48:raise BCError('Reviewed Coder layer count changed')
    # Deliberate contiguous layer sharding; never auto, CPU, disk or multi-node.
    # The pinned Qwen3NextModel also owns rotary buffers outside its layers.
    return {'model.embed_tokens':0,'model.rotary_emb':0,'model.norm':3,'lm_head':3,
            **{'model.layers.'+str(i):i//12 for i in range(48)}}


def check_placement(model,p):
    if getattr(model,'is_quantized',False):raise BCError('Quantization forbidden')
    found=set();counts={}
    for _,v in list(model.named_parameters())+list(model.named_buffers()):
        d=str(v.device);found.add(d)
        if d not in {'cuda:'+str(i) for i in range(p['physical_gpus'])}:raise BCError('CPU/disk/meta/off-device parameter or buffer')
        if v.is_floating_point() and str(v.dtype) not in ('torch.bfloat16','torch.float32'):raise BCError('Precision fallback')
        counts[d]=counts.get(d,0)+v.numel()
    if found!={'cuda:'+str(i) for i in range(p['physical_gpus'])}:raise BCError('Deployment did not use all requested devices')
    return dict(devices=sorted(found),elements_by_device=counts,device_map=getattr(model,'hf_device_map',None))


def inference_processes():
    """Linux/Slurm single-process route; distributed or untracked children fail closed."""
    if any(os.environ.get(k, '1') != '1' for k in ('WORLD_SIZE','SLURM_NTASKS','SLURM_NNODES','SLURM_JOB_NUM_NODES')):
        raise BCError('Distributed inference CPU scope is unsupported')
    root=Path('/proc/self/task')
    if not root.is_dir():raise BCError('Cannot establish inference process tree')
    children=set()
    for task in root.iterdir():
        try:children.update((task/'children').read_text().split())
        except FileNotFoundError:continue
    if children:raise BCError('Unaccounted inference child process; equal-CPU comparison blocked')
    return dict(processes=1,threads=len(list(root.iterdir())),cpu_scope='process_time_all_threads',
                trusted_tool_children='separately measured outside model generation')


def child_process_observation():
    """Best-effort boundary snapshot, not continuous process attribution.

    Never collect command lines or environments. Short-lived/reaped children may
    be absent; RUSAGE_CHILDREN remains a separate cumulative CPU observation.
    """
    result=dict(children=[],errors=[],complete=True)
    try:
        tids=list(Path('/proc/self/task').iterdir())
        children=set()
        for task in tids:
            try:children.update((task/'children').read_text().split())
            except FileNotFoundError:continue
        for pid in sorted(children, key=int)[:64]:
            row=dict(pid=int(pid))
            try:row['comm']=(Path('/proc')/pid/'comm').read_text().strip()[:128]
            except OSError as exc:row['read_error']=type(exc).__name__
            result['children'].append(row)
        result['truncated']=len(children)>64
        result['complete']=not result['truncated']
    except (OSError,ValueError) as exc:
        result['errors'].append(type(exc).__name__);result['complete']=False
    return result


def child_cpu_observation(before,after,start,end):
    return dict(schema='rr-inference-child-cpu-observation-v1',
        before=dict(user_seconds=before.ru_utime,system_seconds=before.ru_stime),
        after=dict(user_seconds=after.ru_utime,system_seconds=after.ru_stime),
        reaped_child_cpu_delta_seconds=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime),
        boundary_before=start,boundary_after=end,
        attribution='unresolved_boundary_snapshots_not_continuous_trace',
        accounting='diagnostic_only_not_added_to_task_cpu',cpu_accounting_complete=False)


class WorkerBackend(TransformersBackend):
    """Same generate/mask/parser path, explicit placement and model-correct template."""
    def __init__(self,p,lock_path):
        require_allocation();inference_processes();lock=read_json(lock_path);q=require_qualified(p,lock);verify_lock(p,lock,weights=True)
        import torch
        import transformers
        if torch.cuda.device_count()!=p['physical_gpus']:raise BCError('Physical allocation differs from profile')
        hw=[]
        for i in range(p['physical_gpus']):
            free,total=torch.cuda.mem_get_info(i);name=torch.cuda.get_device_name(i)
            if total<p['minimum_total_bytes'] or free<p['minimum_free_bytes'] or 'MIG' in name:raise BCError('Full 80GB-class devices with loading headroom required')
            hw.append(dict(name=name,total_bytes=total,free_bytes=free,capability=list(torch.cuda.get_device_capability(i))))
        if not torch.cuda.is_bf16_supported():raise BCError('BF16 unsupported')
        os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
        self.profile=p;self.config=SimpleNamespace(**p['model']);self.torch=torch
        self.tokenizer=transformers.AutoTokenizer.from_pretrained(lock['tokenizer_path'],local_files_only=True,trust_remote_code=False)
        start=time.monotonic()
        cfg=read_json(Path(lock['model_path'])/'config.json');layers=cfg.get('text_config',cfg)['num_hidden_layers']
        self.model=getattr(transformers,p['architecture']).from_pretrained(lock['model_path'],dtype=torch.bfloat16,
            device_map=device_map(p,layers),local_files_only=True,trust_remote_code=False,attn_implementation='sdpa')
        self.model.eval();self.model.requires_grad_(False)
        placed=check_placement(self.model,p)
        self.generation_tokens=generation_tokens(self.tokenizer,self.model.generation_config)
        if self.generation_tokens!=q['generation_tokens'] or digest(self.tokenizer.chat_template)!=q['template']['template_hash']:raise BCError('Loaded tokens/template differ from qualification')
        from .constrained import ActionConstraint
        vocab=self.model.get_output_embeddings().weight.shape[0]
        if vocab!=q['vocab_size']:raise BCError('Loaded vocabulary changed')
        self.constraint=ActionConstraint(self.tokenizer,vocab,self.generation_tokens['eos_token_id'],MODE)
        self.runtime=dict(profile=p,packages=versions(),hardware=hw,placement=placed,requested_gpus=p['physical_gpus'],actual_gpus=torch.cuda.device_count(),
            load_wall_seconds=time.monotonic()-start,model_instances=1,worker_lock_hash=digest(lock),
            cpu_processes=1,cpu_threads=torch.get_num_threads(),node=os.environ.get('SLURMD_NODENAME'),
            torch_cuda=torch.version.cuda,cache_policy='fresh generate local cache each call',whole_allocation_gpu_seconds=None)
    def encode(self,messages):
        return self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_tensors='pt',return_dict=True,**template_options(self.profile))
    def generate(self,messages,max_new_tokens,seed):
        scope=inference_processes()
        import resource
        children_before=resource.getrusage(resource.RUSAGE_CHILDREN)
        model=getattr(self,'model',None)
        if hasattr(model,'_cache'):model._cache=None
        for i in range(self.profile['physical_gpus']):self.torch.cuda.synchronize(i)
        start=time.monotonic()
        boundary_before=child_process_observation()
        with process_launch_trace() as launch_trace:
            try:
                g=super().generate(messages,max_new_tokens,seed)
                for i in range(self.profile['physical_gpus']):self.torch.cuda.synchronize(i)
                elapsed=time.monotonic()-start
                children_after=resource.getrusage(resource.RUSAGE_CHILDREN)
                evidence=child_cpu_observation(children_before,children_after,boundary_before,child_process_observation())
                try:
                    inference_processes()
                    if evidence['reaped_child_cpu_delta_seconds']>1e-9:
                        raise BCError('Untracked inference child CPU; comparison blocked')
                except BCError as exc:
                    evidence['process_launch_trace']=launch_trace
                    exc.inference_child_cpu=evidence
                    raise
            except BaseException as exc:
                if not hasattr(exc,'inference_child_cpu'):
                    exc.inference_child_cpu=child_cpu_observation(children_before,
                        resource.getrusage(resource.RUSAGE_CHILDREN),boundary_before,child_process_observation())
                exc.inference_child_cpu['process_launch_trace']=launch_trace
                raise
        g.diagnostics.update(inference_cpu_scope=scope,process_launch_trace=launch_trace,
            peak_reserved_bytes_by_device=[self.torch.cuda.max_memory_reserved(i) for i in range(self.profile['physical_gpus'])],allocated_task_gpu_seconds=elapsed*self.profile['physical_gpus'],actual_gpus=self.profile['physical_gpus'],
            all_device_wall_seconds=elapsed,occupancy_not_flops=True)
        # A single-device CUDA event is not aggregate sharded-device work.
        if self.profile['physical_gpus']>1:g=replace(g,device_seconds=None)
        return g
