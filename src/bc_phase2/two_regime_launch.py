"""One prefix step or one frozen worker pair through the existing shared registry."""
from pathlib import Path
import json
import re
from types import SimpleNamespace

from . import two_regime as grid
from . import prospective_block3_launch as prior
from . import prospective_block3_worker_launch as controls
from . import prospective_pipeline as pipeline
from . import composite_math_launch as base, composite_math as worker
from . import joint_d1_local as local, d1_natural_screen as screen
from .joint_schema import require
from .model import digest

ANCHORS = {'math500':'f85c5e2b667e77b5ed5e3520d0794cebe51876540f206effcf81139d2ae1a0e4',
           'medqa':'8ce77d60a8592e0a91171a5f4e2a13da3b16556946d66af383fcff7ff61385c3'}
SCRIPT = 'experiments/run_two_regime.sbatch'


def read(path):
    return controls.read(path)


def anchor(path, dataset):
    release = read(Path(path)/'manifest.json')['release']
    scope = release['manifest']['scope']
    require(digest(scope)==release['manifest']['scope_digest']==ANCHORS[dataset], 'historical model/source binding')
    return scope


def public_rows(parent, dataset):
    package = parent['source_package']
    path = Path(package['path'])
    require(path.stat().st_size<=4*1024*1024 and local.file_hash(path)==package['sha256'],'pinned public file')
    rows = read(path)
    for r in rows:
        pipeline.adapters.faithful_identity(r)
        require(('problem' in r)==(dataset=='math500'),'dataset public allowlist')
    return {r['id']:r for r in rows}


def cell(cell_id):
    return next(slot for slot in grid.frozen()['slots'] if slot['id']==cell_id)


def cohort(slot, records):
    ds=slot['dataset']
    rows=[]
    for sid in slot['candidates']:
        exact,normalized=pipeline.adapters.faithful_identity(records[sid])
        rows.append(dict(source_id=sid,exact_hash=exact,normalized_hash=normalized,status='eligible'))
    c=dict(dataset=ds,procedure_digest=grid.frozen()['procedures'][ds],
           slot_id=slot['id'],reservation_digest=digest(grid.frozen()),blocks=[dict(slot=1,records=rows)])
    c['cohort_digest']=digest(c)
    return c


def review_card(slot, sid, public):
    from collections import Counter
    from fractions import Fraction
    def tokens(r):
        text=r.get('problem') or r['question']+' '+' '.join(r['options'].values())
        return set(re.findall(r'\d+(?:\.\d+)?|[A-Za-z]+|[^\sA-Za-z\d]',text))
    require(sid in slot['candidates'],'reserved source')
    known=grid.frozen()['historical_ids'][slot['dataset']]
    current=[s for b in grid.frozen()['slots'] if b['dataset']==slot['dataset'] for s in b['candidates']]
    target=tokens(public[sid])
    def distance(other):
        candidate=tokens(public[other])
        return -Fraction(len(candidate & target),len(candidate | target)), other
    neighbors=sorted((s for s in set(known) if s in public),key=distance)[:3]
    identity=pipeline.adapters.faithful_identity(public[sid])[1]
    norm=Counter(pipeline.adapters.faithful_identity(public[s])[1] for s in set(known+current) if s in public)
    packet=dict(cell=slot['id'],source=public[sid],historical_neighbors=[public[s] for s in neighbors],
                duplicate_identity=norm[identity]>1 or identity in grid.frozen()['known_historical_normalized_hashes'],review_scope='recorded same-pool history; cross-pool family clearance limited to known receipts',
                reviewed_public_digest=digest(public[sid]))
    return dict(packet,card_digest=digest(packet))


def check_review(slot,sid,records,review):
    card=review_card(slot,sid,records)
    require(review['card_digest']==card['card_digest'] and isinstance(review.get('reviewer'),str) and review['reviewer'].strip()
            and isinstance(review.get('rationale'),str) and review['rationale'].strip(),'source family and text review')
    require(review['decision'] in ('clear','blocked'),'review decision')
    require(review['decision']=='blocked' or not card['duplicate_identity'],'known duplicate')


def history(slot, public, entries):
    c=cohort(slot,public)
    outcomes={}
    overhead=dict(calls=0,actual_tokens=0)
    for entry in entries:
        step=grid.select(slot,outcomes)
        sid=entry['source_id']
        require(step.get('source_id')==sid,'first unresolved rank; no intake after freeze')
        family=entry['family_review']
        check_review(slot,sid,public,family)
        if family['decision']=='blocked':
            require(set(entry)=={'source_id','family_review'},'blocked before transmission')
            outcomes[sid]=dict(status='blocked')
            continue
        run=Path(entry['run'])
        prior_release=read(run/'manifest.json')['release']
        parent=prior_release['manifest']
        scope=parent['scope']
        require(parent['scope_digest']==digest(scope) and scope['key']==key(slot,sid)
                and scope['history']==entries[:len(outcomes)]
                and prior_release['approval'].get('family_review',scope['family_review'])==family,
                'earlier physical prefix and source review')
        result=read(run/'execution/result.json')
        ledger=read(run/'execution/journal/ledger.json')
        state=ledger['state']
        require(ledger['sha256']==digest(state) and state['binding_digest']==digest(state['binding'])
                and state['binding']['scope']==parent['scope_digest'],'physical planner journal')
        require(result.get('evidence')=='real_prospective_planner' and len(result['rows'])==1,'physical prefix result')
        if not state['attempts']:
            require(result['rows'][0]==dict(source_id=sid,status='unrun_fit',review=None)
                    and result['totals']==dict(calls=0,actual_tokens=0,reserved_tokens=0)
                    and entry['decision']=='invalid','pre-dispatch fit outcome')
            outcomes[sid]=dict(status='invalid')
            continue
        require(len(state['attempts'])==1,'one terminal attempt')
        a=state['attempts'][0]
        row=result['rows'][0]
        require(worker.reliable_terminal(a) and a['request']==pipeline.adapters.planner_request(slot['dataset'],public[sid])
                and row['source_id']==sid and row['invocation']==a['id']
                and row['raw_response']==a['observation'].get('final_text'),'reviewed invocation binding')
        require(result['totals']==dict(calls=1,actual_tokens=a['actual_tokens'],reserved_tokens=0),'resolved usage')
        overhead['calls']+=1
        overhead['actual_tokens']+=a['actual_tokens']
        decision=entry['decision']
        if decision=='admitted':
            require(row['review']['status']=='wire_valid' and a['observation']['finish_reason']=='eos'
                    and not a['observation'].get('boundary_error'),'terminal response required')
            outcome=pipeline.admit(slot['dataset'],c,public[sid],row['raw_response'],entry['contract'])
            if len(outcome['component']['tasks'])<=2*slot['n']-1:
                outcome['status']='admitted'
            require(outcome['component']['A_modes']==['base'],'selected-component alternatives only')
        else:
            require(decision in ('review_unresolved','unsupported','invalid') and entry['rationale'].strip(),'review disposition')
            outcome=dict(status=decision)
        outcomes[sid]=outcome
    return grid.select(slot,outcomes),overhead


def key(slot,sid=None):
    return f"{grid.CAMPAIGN}-{slot['id']}-"+(f"plan-{slot['candidates'].index(sid)+1}" if sid else 'pair')


def identity():
    names=set(controls.identity())|{grid.CONFIG,'src/bc_phase2/two_regime.py',
        'src/bc_phase2/two_regime_launch.py','src/bc_phase2/two_regime_results.py','scripts/two_regime.py',SCRIPT}
    return {p:local.file_hash(grid.ROOT/p) for p in sorted(names)}


def derive(parent_dir,slot,entries,review,alternatives):
    parent=anchor(parent_dir,slot['dataset'])
    public=public_rows(parent,slot['dataset'])
    selected, overhead=history(slot,public,entries)
    if selected['status']=='next_candidate':
        sid=selected['source_id']
        if review is not None:
            check_review(slot,sid,public,review)
            require(review['decision']=='clear','candidate blocked')
        card=review_card(slot,sid,public)
        require(not alternatives and not card['duplicate_identity'],'known conflict or premature alternate')
        limits=dict(pipeline.LIMITS,maximum_calls=1,calls_per_source=1,token_cap=16384,wall_seconds=3600)
        return parent,dict(key=key(slot,sid),source_ids=[sid],limits=limits,planning_overhead=overhead,card_digest=card['card_digest'])
    require(selected['status']=='bundle_frozen' and review is None,'frozen supported bundle required')
    w=grid.wave(slot,selected,alternatives)
    return parent,dict(key=key(slot),source_ids=selected['sources'],wave=w,limits=w['limits'],planning_overhead=overhead)


def load_tokenizer(model):
    from transformers import AutoTokenizer
    for name,h in local.METADATA.items():
        require(local.file_hash(Path(model['local_path'])/name)==h,'snapshot metadata')
    tokenizer=AutoTokenizer.from_pretrained(model['local_path'],local_files_only=True,trust_remote_code=False)
    require(screen.verify_non_thinking(tokenizer)==model['non_thinking_verification'],'pinned template')
    return tokenizer


def preview(parent,slot,packet):
    model=parent['model']
    req=pipeline.adapters.planner_request(slot['dataset'],packet['source'])
    r=screen.render_request(load_tokenizer(model),req,model['non_thinking_verification']['template_hash'])
    return dict(checkpoint=model['checkpoint'],revision=model['revision'],input_tokens=r['input_tokens'],
                output_cap=3072,reserved_tokens=r['input_tokens']+3072,payload_digest=req['payload_digest'],
                rendered_ids_digest=r['rendered_ids_digest'],maximum_calls=1,token_cap=16384,wall_seconds=3600,
                execution_allowed=False)


def prepare(parent_dir,slot,entries,review,alternatives,directory,partition):
    parent,data=derive(parent_dir,slot,entries,review,alternatives)
    model=parent['model']
    tokenizer=load_tokenizer(model)
    pair='wave' in data
    s=dict(**data,cell=slot['id'],history=entries,family_review=review,alternatives=alternatives,
           parent=str(Path(parent_dir).resolve()),model=model,source_package=parent['source_package'],
           cluster=dict(parent['cluster'],time='04:00:00' if pair else '01:00:00',output_root=str(Path(directory).resolve()/'outputs')),
           partition_record=partition,runtime_identity=identity(),scheduler_policy=parent['scheduler_policy'],
           deployment=base.deployment())
    protocol=Stage(s)
    records=protocol.source_records(s)
    requests=[]
    if pair:
        import importlib.metadata
        import xgrammar as xgr
        from .composite_math_decoder import schema
        from importlib.util import spec_from_file_location,module_from_spec
        require(importlib.metadata.version('xgrammar')=='0.1.32','worker decoder')
        path=grid.ROOT/'scripts/check_composite_common_derivation.py'
        modspec=spec_from_file_location('two_regime_controls',path)
        mod=module_from_spec(modspec)
        modspec.loader.exec_module(mod)
        config=read(Path(model['local_path'])/'config.json')
        eos=model['generation_tokens']['eos_token_id']
        info=xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=config.get('text_config',config)['vocab_size'],stop_token_ids=eos)
        compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
        s['grammar_checks']={}
        for c in s['wave']['components']:
            for mode in c['A_modes']:
                for original in c['tasks']:
                    t=grid.mode_task(c,original,mode)
                    h=digest(schema(t))
                    if h not in s['grammar_checks']:
                        grammar=compiler.compile_json_schema(schema(t),any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
                        obs=mod.controls(lambda:xgr.GrammarMatcher(grammar),tokenizer,t['fields'],eos)
                        require(all(r['passed'] for r in obs),'worker schema CPU controls')
                        s['grammar_checks'][h]=obs
                    parents={p:{f:'Synthetic parent artifact.' for f in next(a for a in c['tasks'] if a['id']==p)['fields']} for p in t['parents']}
                    requests.append(grid.worker_request(c,t,mode,records,parents))
    else:
        requests=[pipeline.adapters.planner_request(slot['dataset'],records[s['source_ids'][0]])]
    s['verified_requests']=[]
    for req in requests:
        r=screen.render_request(tokenizer,req,model['non_thinking_verification']['template_hash'])
        s['verified_requests'].append(dict(source_id=req['payload']['source']['id'],
            **{k:r[k] for k in ('payload_digest','rendered_ids_digest','input_tokens')}))
    manifest=dict(schema=grid.CAMPAIGN,scope=s,scope_digest=digest(s),execution_allowed=False)
    protocol.validate_manifest(manifest)
    return manifest


class Stage:
    def __init__(self,s):
        self.KEY=s['key']
        self.pair='wave' in s
        self.TRANSPORT_EVIDENCE='real_composite_worker_development' if self.pair else 'real_prospective_planner'

    def source_records(self,s):
        rows=public_rows({'source_package':s['source_package']},cell(s['cell'])['dataset'])
        return {sid:rows[sid] for sid in s['source_ids']}

    def validate_manifest(self,m):
        s=m['scope']
        require(m['schema']==grid.CAMPAIGN and m['scope_digest']==digest(s) and m['execution_allowed'] is False,'disabled scope integrity')
        slot=cell(s['cell'])
        require(grid.frozen()['procedures'][slot['dataset']]==pipeline.procedure(slot['dataset'])['procedure_digest'],'frozen task interface')
        parent,data=derive(s['parent'],slot,s['history'],s['family_review'],s['alternatives'])
        require(all(s[k]==v for k,v in data.items()) and self.KEY==data['key'],'replay frozen recipe')
        require(('wave' in data)==self.pair and s['runtime_identity']==identity(),'runtime identity')
        for k in ('model','source_package','scheduler_policy'):
            require(s[k]==parent[k],'historical binding '+k)
        cluster=s['cluster']
        require(cluster==dict(parent['cluster'],output_root=cluster['output_root'],time='04:00:00' if self.pair else '01:00:00')
                and cluster['partition']=='HPCAIq' and cluster['memory_gb']==128,'scheduler policy')
        fields=dict(re.findall(r'(\w+)=([^\s]+)',s['partition_record']))
        require(fields.get('PartitionName')=='HPCAIq' and fields.get('State')=='UP','partition evidence')
        require(s['deployment']['packages']==base.EXPECTED_PACKAGES and s['deployment']['solver_importable'],'deployment')
        require(Path(cluster['python']).resolve()==Path(s['deployment']['python']),'interpreter binding')
        if not self.pair:
            row=s['verified_requests'][0]
            sid=s['source_ids'][0]
            req=pipeline.adapters.planner_request(slot['dataset'],self.source_records(s)[sid])
            require(row['source_id']==sid and row['payload_digest']==req['payload_digest']
                    and re.fullmatch('[0-9a-f]{64}',row['rendered_ids_digest']),'exact measured request')
        require(len(s['verified_requests'])==(len(s['wave']['profile_coverage']) if self.pair else 1)
                and all(0<r['input_tokens']<=13312 for r in s['verified_requests']),'request fit')
        if self.pair:
            from .composite_math_decoder import schema
            hashes={digest(schema(t)) for t in controls.transport_tasks(s)}
            require(set(s['grammar_checks'])==hashes and all([r['eos'] for r in obs]==[248046,248044]
                    and all(r['passed'] for r in obs) for obs in s['grammar_checks'].values()),'complete decoder controls')
        return s

    def approve(self,m,a):
        s=self.validate_manifest(m)
        flags=('source_worker_transmission','contract_accepted','gpu_recipe_authorized') if self.pair else ('statement_transmission_authorized','GPU_spending_authorized')
        fields={'schema','scope_digest','decision','reviewer','reviewed_at',*flags}
        if not self.pair and s['family_review'] is None:
            fields.add('family_review')
            slot=cell(s['cell'])
            public=public_rows({'source_package':s['source_package']},slot['dataset'])
            check_review(slot,s['source_ids'][0],public,a['family_review'])
            require(a['family_review']['decision']=='clear','completed source review before approval')
        require(set(a)==fields,'approval fields')
        require(a['schema']==self.KEY+'-approval' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved'
                and all(a[f] is True for f in flags)
                and a['reviewer'].strip() and a['reviewed_at'].strip(),'exact source and GPU approval')
        v=dict(schema=self.KEY+'-release',manifest=m,approval=a)
        v['release_digest']=digest(v)
        return v

    def validate_release(self,v):
        require(self.approve(v['manifest'],v['approval'])==v,'release integrity')
        return v['manifest']['scope']

    def submission_check(self,release,state):
        # The shared registry locks the scientific prefix even if an operator edits a history file.
        s=release['manifest']['scope']
        slot=cell(s['cell'])
        attempts=state.get('composite_math_attempts',{})
        require(key(slot) not in attempts,'cell already frozen and submitted')
        for entry in s['history']:
            registered=attempts.get(key(slot,entry['source_id']))
            if entry['family_review']['decision']=='blocked':
                require(registered is None,'submitted candidate cannot be skipped')
                continue
            require(registered and registered['state']=='submitted_no_retry'
                    and Path(registered['output']).resolve()==Path(entry['run']).resolve(),'registered prefix evidence')
            original=read(Path(entry['run'])/'manifest.json')['release']
            require(registered['scope_digest']==original['manifest']['scope_digest']
                    and registered['release_digest']==original['release_digest']
                    and original['release_digest']==digest({k:v for k,v in original.items() if k!='release_digest'}),
                    'original planner release')
        for sid in slot['candidates'][len(s['history']):]:
            require(key(slot,sid) not in attempts,'later or uncertain prefix already exists')

    def arguments(self,config,snapshot,output):
        argv=base.arguments(config,snapshot,output)
        argv[-4]=str(snapshot/SCRIPT)
        return argv

    def check_scoped_allocation(self,record,s):
        if self.pair:
            controls.check_scoped_allocation(record,s)
        else:
            prior.check_scoped_allocation(record,s)

    def make_transport(self,tokenizer,model,torch,s):
        if not self.pair:
            return prior.make_transport(tokenizer,model,torch,s)
        from .composite_math_decoder import TaskTransport
        # Alternatives share the same decoder fields. Selected instructions still come from Engine.
        tasks={ (t['source_id'],t['id']):t for t in controls.transport_tasks(s)}
        return TaskTransport(tokenizer,model,torch,tasks=list(tasks.values()))

    def open_transport(self,v):
        return base.open_transport(v,protocol=self)

    def report_pair(self,s,r,out):
        from .two_regime_results import summarize,table,pending
        from beyond_consensus.util import atomic_json
        record=summarize(s,r)
        atomic_json(out/'cell.json',record)
        rows=pending()
        registry=read(base.cluster.registry_root()/'registry.json').get('composite_math_attempts',{})
        for other in grid.frozen()['slots']:
            entry=registry.get(key(other))
            if entry and other['id']!=s['cell']:
                path=Path(entry['output'])/'execution/cell.json'
                if path.is_file():
                    saved=read(path)
                    require(saved['cell']==other['id'] and saved['scope_digest']==entry['scope_digest'],
                            'prior rolling result scope')
                    rows[other['id']]=dict(saved,evidence=str(path))
        rows[s['cell']]=dict(record,evidence=str(out/'cell.json'))
        atomic_json(out/'cells.json',list(rows.values()))
        (out/'RESULTS.md').write_text(table(list(rows.values())))

    def dispatch(self,v,directory):
        s=self.validate_release(v)
        slot=cell(s['cell'])
        def journal(path,transport,scope,check_source):
            return worker.Journal(path,transport,scope,check_source,condition=self.KEY,limits=s['limits'])
        def run(j,records,out):
            if self.pair:
                r=grid.run_wave(j,records,out,s['wave'])
                r['planning_overhead']=s['planning_overhead']
                return r
            sid=s['source_ids'][0]
            exact,norm=pipeline.adapters.faithful_identity(records[sid])
            c=dict(dataset=slot['dataset'],blocks=[dict(slot=1,records=[dict(source_id=sid,status='eligible',exact_hash=exact,normalized_hash=norm)])])
            rows=pipeline.plan_block(j,c,1,records,out/'planning')
            return dict(rows=rows,totals=j.snapshot()['totals'],status='prefix_review_required',evidence=self.TRANSPORT_EVIDENCE)
        self.recipe=SimpleNamespace(Journal=journal,run_recipe=run,blueprint=lambda:dict(schedule=[self.KEY]))
        probe=controls.common.placement.probe._probe_output
        token=probe.set(Path(directory))
        try:
            self.check_cuda=controls.check_cuda
            result=base.dispatch(v,directory,protocol=self)
            if self.pair:
                self.report_pair(s,result,Path(directory))
            return result
        finally:
            probe.reset(token)
