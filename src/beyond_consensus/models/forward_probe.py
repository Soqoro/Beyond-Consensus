"""Fixed synthetic forward observations. No generation, masking or qualification."""
from copy import deepcopy
import resource
import time
from ..util import BCError, digest
from .process_trace import process_launch_trace
from .worker_profiles import child_process_observation, child_cpu_observation

PROTOCOL='rr-coder-fixed-prefix-forward-v1'
ROWS=('cache_prefill','cached_token','full_prefix')


def contract():
    return dict(protocol=PROTOCOL,maximum_forward_calls=3,generated_tokens=0,
        fixed_suffix='{',order=list(ROWS),masking=False,token_cap=16384,cpu_cap=1200,
        shared_model=True,cache_reuse='prefill_to_cached_token_only',
        full_prefix_use_cache=False,qualification_allowed=False,
        child_cpu='observations_only_incomplete_not_qualification',
        stop_on_exception=True,continue_on_nonfinite_observation=True)


def raw_logits_summary(logits):
    """Inspect only last-position raw logits; never save logits or repair them."""
    import torch
    if logits is None or len(logits.shape)!=3 or logits.shape[0]!=1 or logits.shape[1]<1:
        raise BCError('Raw logits shape unavailable')
    values=logits[:, -1, :]
    result=dict(shape=list(logits.shape),observed_shape=list(values.shape),
                dtype=str(values.dtype),device=str(values.device),
                finite=int(torch.isfinite(values).sum().item()),
                nan=int(torch.isnan(values).sum().item()),
                positive_infinity=int(torch.isposinf(values).sum().item()),
                negative_infinity=int(torch.isneginf(values).sum().item()))
    result['all_finite']=result['finite']==values.shape[-1]
    return result


def forward_kwargs(step, ids, prefix, cache, torch):
    """Explicit pinned Qwen3Next forward contract, no generation helper defaults."""
    n=ids.shape[1];full=torch.cat((ids,prefix),dim=1)
    if step=='cache_prefill':
        seq=ids;past=None;position=torch.arange(n,device=ids.device);use=True
    elif step=='cached_token':
        if cache is None:raise BCError('Prefill did not return a cache')
        seq=prefix;past=cache;position=torch.arange(n,n+1,device=ids.device);use=True
    elif step=='full_prefix':
        seq=full;past=None;position=torch.arange(n+1,device=ids.device);use=False
    else:raise BCError('Unknown raw forward probe')
    return dict(input_ids=seq,attention_mask=torch.ones_like(ids if step=='cache_prefill' else full),
        cache_position=position,position_ids=position.unsqueeze(0),past_key_values=past,
        use_cache=use,return_dict=True,logits_to_keep=1)


def run(backend, entry, save=lambda row:None):
    from reporecourse.resources import Resources
    if backend.profile['name']!='coder':raise BCError('Raw forward diagnostic is Coder-only')
    r=Resources(16384,1200);prep_start=time.process_time()
    torch=backend.torch
    encoded=backend.encode(entry['messages'])
    ids=encoded['input_ids']
    if ids.shape[0]!=1 or ids.shape[1]!=entry['input_tokens'] or digest(ids[0].tolist())!=entry['rendered_ids_hash']:
        raise BCError('Raw forward prompt changed')
    prefix_ids=backend.tokenizer.encode('{',add_special_tokens=False)
    if prefix_ids!=entry['fixed_prefix_ids'] or len(prefix_ids)!=1:
        raise BCError('Fixed brace token changed')
    r.reconcile_cpu('raw_forward_preparation',0,time.process_time()-prep_start)
    rows=[];cache=None
    for step in ROWS:
        row=dict(id=step,status='started',dispatched=False,protocol=PROTOCOL,
                 task_execution_allowed=False,qualification_passed=False)
        rows.append(row);key=None;start=time.process_time();wall=time.monotonic()
        before=resource.getrusage(resource.RUSAGE_CHILDREN);boundary=child_process_observation()
        with process_launch_trace() as launches:
            try:
                count=ids.shape[1] if step=='cache_prefill' else 1 if step=='cached_token' else ids.shape[1]+1
                r.reserve_cpu(31);key=r.reserve(int(count),0)
                row['resources']=deepcopy(r.summary());save(dict(row))
                if step=='cache_prefill':
                    ids=ids.to(torch.device('cuda:0'))
                    prefix=torch.tensor([prefix_ids],device=ids.device,dtype=ids.dtype)
                    if hasattr(backend.model,'_cache'):backend.model._cache=None
                kwargs=forward_kwargs(step,ids,prefix,cache,torch)
                for i in range(backend.profile['physical_gpus']):torch.cuda.synchronize(i)
                row['dispatched']=True;save(dict(row))
                with torch.inference_mode():output=backend.model(**kwargs)
                for i in range(backend.profile['physical_gpus']):torch.cuda.synchronize(i)
                row['raw_logits']=raw_logits_summary(output.logits)
                if step=='cache_prefill':cache=output.past_key_values
                row['cache_returned']=getattr(output,'past_key_values',None) is not None
                del output,kwargs
                r.reconcile(key,0,0);key=None
                row['status']='observed'
            except BaseException as exc:
                if key is not None:r.reconcile(key)
                row.update(status='infrastructure_failed',error_type=type(exc).__name__,error_category=str(exc)[:160])
            finally:
                child=child_cpu_observation(before,resource.getrusage(resource.RUSAGE_CHILDREN),boundary,child_process_observation())
                child['process_launch_trace']=launches
                for allowance in list(r.cpu_pending):
                    try:r.reconcile_cpu('raw_forward_parent',allowance,time.process_time()-start)
                    except Exception as exc:
                        row.update(status='infrastructure_failed',error_type=type(exc).__name__,error_category=str(exc)[:160])
                row.update(inference_child_cpu=child,cpu_accounting_complete=False,resources=deepcopy(r.summary()),
                    wall_seconds=time.monotonic()-wall,generated_tokens=0,
                    accounting='separate cumulative teacher-forced input ledger; child CPU diagnostic only, not qualification')
                save(dict(row))
        if row['status']=='infrastructure_failed':break
    cache=None
    return rows


def forward_input_summary(args, kwargs):
    """Bounded synthetic-only input metadata; never inspect cache tensors."""
    result = {}
    for name in ('input_ids', 'attention_mask', 'position_ids', 'cache_position'):
        value = kwargs.get(name)
        if name == 'input_ids' and value is None and args:
            value = args[0]
        if value is None:
            result[name] = None
            continue
        shape = list(value.shape)
        count = 1
        for size in shape:
            count *= size
        item = dict(shape=shape, dtype=str(value.dtype), device=str(value.device))
        # No unbounded host transfer, including unusual attention masks.
        if count <= 16384:
            data = value.tolist()
            item['sha256'] = digest(data)
            if count <= 128:
                item['values'] = data
            else:
                item['values_omitted'] = True
        else:
            item['values_omitted'] = True
            item['hash_omitted'] = True
        result[name] = item
    cache = kwargs.get('past_key_values')
    result['cache'] = dict(present=cache is not None,
        type=type(cache).__name__ if cache is not None else None)
    for name in ('use_cache', 'logits_to_keep', 'return_dict'):
        value = kwargs.get(name)
        result[name] = value if type(value) in (bool, int, str) or value is None else 'non_scalar'
    return result
