"""Explicit bounded setup only; never called by worker or batch execution."""
import csv
import io
import json
import tempfile
from pathlib import Path
from .common import Rejected, file_hash, load, encoded, write_new
from .tasks import ROOT


def github_metadata_slice(document):
    """Public operation-selected closure; never consult tasks, gold or fixtures."""
    paths = {'/repos/{owner}/{repo}/topics': ('put',),
             '/repos/{owner}/{repo}/languages': ('get',)}
    out = {'openapi': document['openapi'], 'paths': {
        path: {method: document['paths'][path][method] for method in methods}
        for path, methods in paths.items()}, 'components': {}}
    seen = set()
    def visit(value):
        if isinstance(value, list):
            for item in value: visit(item)
        elif isinstance(value, dict):
            if '$ref' in value:
                ref = value['$ref']
                parts = ref.split('/')
                if len(parts) != 4 or parts[:2] != ['#', 'components']:
                    raise Rejected('source_reference')
                if ref not in seen:
                    seen.add(ref)
                    if len(seen) > 64: raise Rejected('source_closure_bound')
                    section, name = parts[2:]
                    child = document['components'][section][name]
                    out['components'].setdefault(section, {})[name] = child
                    visit(child)
            for item in value.values(): visit(item)
    visit(out['paths'])
    return out


def extract(pack, files):
    if pack=='jaffle':
        out={k.replace('/','__'):v for k,v in files.items() if not k.endswith('.csv')}
        tables={}
        definitions={'customers':[('id','INTEGER'),('first_name','TEXT'),('last_name','TEXT')],
            'orders':[('id','INTEGER'),('user_id','INTEGER'),('order_date','TEXT'),('status','TEXT')],
            'payments':[('id','INTEGER'),('order_id','INTEGER'),('payment_method','TEXT'),('amount','INTEGER')]}
        for name,cols in definitions.items():
            rows=csv.DictReader(io.StringIO(files['seeds/raw_'+name+'.csv'].decode()))
            tables[name]={'columns':cols,'rows':[[int(r[k]) if t=='INTEGER' else r[k] for k,t in cols] for r in rows]}
        out['tables.json']=encoded(tables)
        return out
    if pack=='energy':
        cols=[('iso_code','TEXT'),('year','INTEGER'),('electricity_generation','REAL')]
        rows=[]
        for r in csv.DictReader(io.StringIO(files['owid-energy-data.csv'].decode())):
            if r['iso_code'] in ('DNK','FIN','OWID_WRL') and 2018<=int(r['year'])<=2023:
                rows.append([r['iso_code'],int(r['year']),float(r['electricity_generation']) if r['electricity_generation'] else None])
        cb=[r for r in csv.DictReader(io.StringIO(files['owid-energy-codebook.csv'].decode())) if r['column'] in [c[0] for c in cols]]
        return {'README.md':files['README.md'],'codebook.json':encoded(cb),
                'tables.json':encoded({'energy':{'columns':cols,'rows':rows}})}
    if pack=='github-metadata':
        d=json.loads(files['descriptions/api.github.com/api.github.com.json'])
        return {'README.md':files['README.md'],'LICENSE.md':files['LICENSE.md'],
                'metadata.json':encoded(github_metadata_slice(d))}
    if pack=='github':
        d=json.loads(files['descriptions/api.github.com/api.github.com.json'])
        return {'README.md':files['README.md'],'LICENSE.md':files['LICENSE.md'],
            'topics.json':encoded({'openapi':d['openapi'],'path':'/repos/{owner}/{repo}/topics',
                'put':d['paths']['/repos/{owner}/{repo}/topics']['put'],
                'topic':d['components']['schemas']['topic'],'topic_example':d['components']['examples']['topic']})}
    raise Rejected('source_pack')


def stage(root, dry_run=True, packs=None):
    registry=load(ROOT/'source_registry.json')
    if packs is not None:
        if not packs or set(packs)-{p['id'] for p in registry['packs']}:raise Rejected('source_pack')
        registry['packs']=[p for p in registry['packs'] if p['id'] in packs]
    plan={'schema':'rr-source-plan-v1','packs':registry['packs'],
        'maximum_download_bytes':sum(f['bytes'] for p in registry['packs'] for f in p['upstream']),
        'execution':'none; repositories never imported or run','network':not dry_run}
    if dry_run:return plan
    from urllib.request import urlopen
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    for pack in registry['packs']:
        target=root/pack['id']
        if target.exists():
            if all((target/f['path']).is_file() and file_hash(target/f['path'])==f['sha256'] for f in pack['retained']):continue
            raise Rejected('existing_source_changed')
        files={}
        for f in pack['upstream']:
            url=f"https://raw.githubusercontent.com/{pack['repository']}/{pack['revision']}/{f['path']}"
            with urlopen(url,timeout=60) as r:raw=r.read(f['bytes']+1)
            import hashlib
            if len(raw)!=f['bytes'] or hashlib.sha256(raw).hexdigest()!=f['sha256']:raise Rejected('source_download_integrity')
            files[f['path']]=raw
        retained=extract(pack['id'],files)
        import hashlib
        if any(hashlib.sha256(retained[f['path']]).hexdigest()!=f['sha256'] for f in pack['retained']):raise Rejected('source_extraction_integrity')
        with tempfile.TemporaryDirectory(dir=root,prefix='.stage-') as temp:
            t=Path(temp)
            for f in pack['retained']:(t/f['path']).write_bytes(retained[f['path']])
            t.rename(target)
    return {**plan,'status':'staged','root':str(root)}
