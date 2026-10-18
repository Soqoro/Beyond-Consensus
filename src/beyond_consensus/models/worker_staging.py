"""Bounded official metadata retrieval; separate explicit weight staging."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import urllib.request
from ..util import BCError,digest,file_hash
from .worker_profiles import profile,PACKAGES,verify_lock


def fetch(url,limit=16*1024*1024):
    with urllib.request.urlopen(url,timeout=60) as response:
        raw=response.read(limit+1)
    if len(raw)>limit:raise BCError('Official metadata exceeds bound')
    return json.loads(raw)


def metadata(name):
    p=profile(name);m=p['model'];repo=m['checkpoint'];rev=m['revision']
    info=fetch('https://huggingface.co/api/models/'+repo+'/revision/'+rev+'?blobs=true')
    if info.get('sha')!=rev:raise BCError('Official revision differs')
    files=[]
    for f in info['siblings']:
        n=f['rfilename']
        if '/' not in n and (n.endswith(('.safetensors','.json','.jinja')) or n in ('LICENSE','README.md','merges.txt','vocab.json')):
            size=f.get('size');lfs=f.get('lfs') or {}
            if type(size) is not int or size<0:raise BCError('Exact asset bytes unavailable')
            files.append(dict(name=n,bytes=size,sha256=lfs.get('sha256')))
    if not any(x['name'].endswith('.safetensors') for x in files):raise BCError('Weight inventory missing')
    result=dict(schema='rr-worker-assets-v1',profile=p,revision=rev,files=files,
        checkpoint_bytes=sum(x['bytes'] for x in files),metadata_only=True,license=info.get('cardData',{}).get('license'),
        official_source='https://huggingface.co/'+repo+'/tree/'+rev)
    result['metadata_id']=digest(result);return result


def feasibility(assets,destination,partition=None):
    p=assets['profile'];root=Path(destination)
    existing=root
    while not existing.exists():existing=existing.parent
    free=shutil.disk_usage(existing).free
    scheduler={};errors=[]
    for name,argv in (('nodes',['sinfo','-N','-o','%N|%P|%t|%G']),('partition',['scontrol','show','partition',partition] if partition else None)):
        if argv:
            try:
                result=subprocess.run(argv,text=True,capture_output=True,timeout=30,check=True);scheduler[name]=result.stdout[:131072]
            except (OSError,subprocess.SubprocessError) as e:errors.append(name+':'+type(e).__name__)
    return dict(schema='rr-worker-feasibility-v1',assets_id=assets['metadata_id'],profile=p,staging_path=str(root),
        checkpoint_bytes=assets['checkpoint_bytes'],disk_free_bytes=free,staging_reserve_bytes=2*assets['checkpoint_bytes'],
        storage_sufficient=free>=2*assets['checkpoint_bytes'],scheduler=scheduler,scheduler_errors=errors,
        required_allocation=dict(nodes=1,tasks=1,gpus=p['physical_gpus'],host_memory_gb=p['host_memory_gb']),
        required_packages=PACKAGES,placement=p['placement'],allocation_shape_verified=False,
        gpu_memory_measured=False,interconnect=None,loading_overhead=None,model_executed=False,
        blockers=['site_co_located_allocation_and_quota_review','explicit_large_download_approval','native_and_GPU_qualification_pending'],
        note='Scheduler text is evidence for review, not a fabricated capacity or permission decision.')


def stage(assets,destination,approval=None):
    if assets.get('metadata_id')!=digest({k:v for k,v in assets.items() if k!='metadata_id'}):raise BCError('Metadata changed')
    p=assets['profile'];root=Path(destination)
    if approval is None:
        return dict(schema='rr-worker-staging-approval-v1',assets_id=assets['metadata_id'],destination=str(root),
            maximum_bytes=assets['checkpoint_bytes'],profile=p['name'],decision='pending',reviewer=None,reviewed_at=None)
    expected=stage(assets,destination)
    if set(expected)!=set(approval) or any(approval[k]!=v for k,v in expected.items() if k not in ('decision','reviewer','reviewed_at')) or approval['decision']!='approved' or not all(approval[k] for k in ('reviewer','reviewed_at')):raise BCError('Exact download approval required')
    if not os.environ.get('SLURM_JOB_ID'):raise BCError('Weight staging requires allocated CPU/host memory')
    root.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(root).free<assets['checkpoint_bytes']:raise BCError('Insufficient staging disk')
    from huggingface_hub import snapshot_download
    snapshot_download(p['model']['checkpoint'],revision=p['model']['revision'],local_dir=str(root),
        allow_patterns=[f['name'] for f in assets['files']],max_workers=2)
    weights={};meta={}
    for f in assets['files']:
        path=root/f['name']
        if path.stat().st_size!=f['bytes']:raise BCError('Asset size changed')
        h=file_hash(path)
        if f['sha256'] and h!=f['sha256']:raise BCError('Official LFS hash mismatch')
        (weights if f['name'].endswith('.safetensors') else meta)[f['name']]=h
    lock=dict(schema='rr-worker-lock-v1',**{k:p['model'][k] for k in ('checkpoint','revision','tokenizer_revision')},
        model_path=str(root),tokenizer_path=str(root),metadata_hashes=meta,weight_hashes=weights,
        assets_id=assets['metadata_id'],checkpoint_bytes=assets['checkpoint_bytes'],license=assets['license'])
    verify_lock(p,lock,weights=True);return lock
