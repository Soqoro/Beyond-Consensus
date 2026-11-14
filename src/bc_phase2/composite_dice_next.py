"""One producer-boundary amendment and a five-cell prospective MATH recipe."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
from . import composite_scaling as spec, composite_scaling_runtime as runtime
from . import composite_derivation_interface as common, composite_math as worker
from . import composite_common_derivation_launch as parent
from .joint_schema import require,canonical_domain
from .joint_pipeline_runtime import Artifact,snapshot_digest
from .model import digest

VERSION='dice-single-die-boundary-v1'
PARENT_SCOPE='4a772b74e52b7c4412c47a3216a89e923e04639565337a04a142036b673387d4'
DICE='test/counting_and_probability/1003.json'
ORDER=(4,3,5,7,8)
BOUNDARY=(' Limit the derivation to a short finished argument establishing the single-die model. '
    'The probabilities field must give the symbolic single-face probability model; pairing must give '
    'the opposite-face relationships; constraints must give normalization and admissibility. '
    'Do not derive or use the two-die event equation, solve roots, or compute the requested numerical answer: '
    'those belong exclusively to the existing downstream tasks. Finish all four fields. '
    'If a required model result cannot be established, put exactly UNAVAILABLE in that result field '
    'and explain the limitation in derivation; do not invent it.')

def revised_task(c,t,mode):
    v=common.task(spec.task(c,t,mode))
    if c['source_id']==DICE and t['id']=='t2':v['responsibility']+=BOUNDARY
    return v

def component_version(c):
    return digest(dict(previous_contract=c['contract_id'],version=VERSION,
        tasks=[revised_task(c,t,c['reference_mode']) for t in c['tasks']]))

def descriptor(c,t,mode):
    v=common.descriptor(c,t,mode)
    if c['source_id']==DICE:
        v['task']=revised_task(c,t,mode)
        v['ancestor_lineage']=dict(component_version=component_version(c),changed_producer='t2',
            fresh_chain=['t2','t3','t4'],state='fresh profile prerequisites; no historical parents')
    return v

def key(c,t,mode):return digest(descriptor(c,t,mode))
def coverage(components):
    return [dict(key=key(c,t,a),historical_key=spec.key(c,t,a),source_id=c['source_id'],task_id=t['id'],
        component=c['namespace'],mode=a,descriptor=descriptor(c,t,a)) for c in components for a in c['A_modes'] for t in c['tasks']]

def domain(components,n,prices=None):
    d=spec.domain(components,n,None if prices is None else {e['historical_key']:prices[e['key']] for e in coverage(components)})
    for c in components:
        if c['source_id']==DICE:
            next(t for t in d['tasks'] if t['id']==c['namespace']+'_t2')['instruction']+=BOUNDARY
    return canonical_domain(d)

def request(c,t,mode,sources,parents):
    r=runtime.request(c,t,mode,sources,parents)
    r['payload']['required_string_fields']=revised_task(c,t,mode)['fields']
    r['payload']['responsibility']=revised_task(c,t,mode)['responsibility']
    r['payload_digest']=digest(r['payload']);return r

class Engine(runtime.Engine):
    def task_for_operation(self,op):
        t=super().task_for_operation(op);c=self.components[t['_component']]
        original=next(x for x in c['tasks'] if x['id']==t['id'])
        return dict(revised_task(c,original,t['_proof']),_component=t['_component'],_proof=t['_proof'])
    def make_request(self,t,store):
        c=self.components[t['_component']];original=next(x for x in c['tasks'] if x['id']==t['id'])
        parents={p:json.loads(store[c['namespace']+'_e'+p[1:]].value) for p in t['parents']}
        return request(c,original,t['_proof'],self.sources,parents)
    def parse_artifact(self,text,t):
        value=worker.parse_artifact(text,t)
        c=self.components[t['_component']]
        if c['source_id']==DICE and t['id']=='t2':
            obj=json.loads(value)
            require(all(obj[f].strip()!='UNAVAILABLE' for f in ('probabilities','pairing','constraints')),'explicit producer inability; no consumer dispatch')
        return value

def check_profile(receipt,entry):common.check_profile(receipt,entry)

def freeze(parent_wave):
    require(parent_wave['wave_id']==digest({k:v for k,v in parent_wave.items() if k!='wave_id'}),'parent wave hash')
    entries=deepcopy(parent_wave['components']);bundles=[];matrix=[]
    for n in ORDER:
        saved=next((b for b in parent_wave['bundles'] if b['n']==n and b['slot']==1),None)
        b=deepcopy(saved) if saved else spec.construct(entries,n,1)
        row=dict(n=n,slot=1,methods=['NEUTRAL','JOINT'],status=b['status'],execution='unrun')
        if b['status']=='supported_frozen':
            b['parent_preprice_id']=b['preprice_id']
            b['neutral_provenance']='preserved historical grouping' if saved else 'existing metadata-only builder; frozen before prices'
            b['worker_contracts']={c['source_id']:component_version(c) if c['source_id']==DICE else c['contract_id'] for c in b['components']}
            b['preprice_specification']=dict(prior=b['preprice_specification'],worker_contracts=b['worker_contracts'],interface='common-derivation-first',version=VERSION)
            b['preprice_id']=digest(b['preprice_specification']);row['preprice_id']=b['preprice_id'];bundles.append(b)
        matrix.append(row)
    components=sorted({c['source_id']:c for b in bundles for c in b['components']}.values(),key=lambda c:c['source_id'])
    dice=next(c for c in components if c['source_id']==DICE)
    cov=coverage(components)
    schedule=[dict(component=dice['namespace'],mode=dice['reference_mode'],events=[dice['namespace']+'_e'+t['id'][1:] for t in dice['tasks']],calls=3)]
    calls=3+sum(b['call_bounds']['evaluation_calls'] for b in bundles)
    w=dict(schema='dice-next-math-wave-v1',condition=VERSION,parent_wave_id=parent_wave['wave_id'],bank=parent_wave['bank'],components=components,
        bundles=bundles,matrix=matrix,profile_coverage=cov,profile_schedule=schedule,
        profile_consumers={e['key']:[b['preprice_id'] for b in bundles if e['source_id'] in b['sources']] for e in cov},
        limits={**parent_wave['limits'],'maximum_calls':calls,'token_cap':calls*16384},
        dispatch_order=list(ORDER),profile_policy='one producer attempt is its profile; descendants fresh; all compatible unchanged profiles reused',
        completed_no_rerun=[2,6],execution_allowed=False,neutral_freeze='before loading profile receipts',
        local_failure='block affected conditions; proceed in fixed order if journal and resources reliable',
        systemic_failure='halt on uncertain dispatch, usage, integrity or hard limits',
        semantic_review='after recording; no correctness or oversolving rejection/resampling',
        evaluation_sessions_ceiling=sum(2*(b['n']+1) for b in bundles))
    w['preprice_wave_digest']=digest(w)
    return w

def attach_prices(frozen,receipts):
    w=deepcopy(frozen);allowed={e['key'] for e in w['profile_coverage'] if e['source_id']!=DICE}
    require(set(receipts)==allowed,'complete compatible unchanged coverage required')
    runtime.validate_receipts(receipts,w['profile_coverage'])
    require(all(r['kind']=='historical_profile' and r.get('reuse_verified') is True for r in receipts.values()),'verified designated profiles only')
    w['reused_profiles']=deepcopy(receipts);w['wave_id']=digest(w);return w

def import_profiles(scope,envelope,price_file,profiles):
    """Semantic projection of designated profiles, never evaluation or solved diagnostic bills."""
    state=envelope['state'];require(envelope['sha256']==digest(state) and state['binding_digest']==digest(state['binding']),'ledger integrity')
    require(state['binding']['scope']==PARENT_SCOPE,'exact previous common-interface run')
    transport=state['binding']['transport'];model=scope['model']
    expected=dict(checkpoint=model['checkpoint'],revision=model['revision'],template=model['non_thinking_verification'],tokens=model['generation_tokens'],context=16384,output=3072,do_sample=False,thinking=False,
        evidence='real_composite_worker_development',inventory_digest=digest(parent.base.pilot.lock_for(scope)),decoder='task-fields-xgrammar-v1',xgrammar_version='0.1.32',decoder_cpu_seconds_per_call=30)
    require(all(transport.get(k)==v for k,v in expected.items()),'worker/model/template/generation binding')
    attempts=state['attempts'];require(all(worker.reliable_terminal(a) for a in attempts),'unresolved historical usage')
    require(len({a['id'] for a in attempts})==len(attempts),'duplicate invocation')
    byid={a['id']:a for a in attempts};receipts={}
    for c in scope['wave']['components']:
        if c['source_id']==DICE:continue
        for mode in c['A_modes']:
            slot='profile/'+c['namespace']+'/'+mode;row=profiles[slot]
            require(row['slot']==slot and row['snapshot_role']=='profile' and row['complete'] and row['accounting_complete'],'complete designated profile')
            converted=deepcopy(row);converted['store']={k:Artifact(tuple(v['contract']),v['value'],v['invocation'],v['organisation']) for k,v in row['store'].items()}
            require(snapshot_digest(converted)==row['snapshot_digest'],'profile snapshot integrity')
            ids=[]
            for t in c['tasks']:
                event=c['namespace']+'_e'+t['id'][1:];trace=next(x for x in row['trace'] if x['event']==event)
                a=byid[trace['invocation']];ids.append(a['id'])
                require(a['slot']==slot and a['event']==event and trace['committed'] is True,'profile slot/event binding')
                req=a['request'];payload=req['payload'];problem=payload['source']['problem']
                require(hashlib.sha256(problem.encode()).hexdigest()==c['statement_sha256'],'profile statement')
                parents={p:json.loads(row['store'][c['namespace']+'_e'+p[1:]]['value']) for p in t['parents']}
                require(req==request(c,t,mode,{c['source_id']:problem},parents),'source/instruction/field/parent compatibility')
                rendered=a['rendered'];require(rendered['payload_digest']==req['payload_digest'] and rendered['rendered_ids_digest']==digest(rendered['input_ids']) and len(rendered['input_ids'])==a['input_tokens'],'rendered binding')
                obs=a['observation'];require(obs['finish_reason']=='eos' and not obs.get('boundary_error'),'committed EOS')
                value=worker.parse_artifact(obs['final_text'],revised_task(c,t,mode))
                require(value==row['store'][event]['value'] and row['store'][event]['invocation']==a['id'] and trace['usage']==a['actual_tokens'],'observed artifact and bill')
                from .composite_math_decoder import schema
                require(transport['schema_hashes'][c['source_id']+':'+t['id']]==digest(schema(revised_task(c,t,mode))),'same field grammar')
                k=key(c,t,mode);r=price_file['receipts'][k]
                require(r['kind']=='new_profile' and r['key']==k and r['descriptor']==descriptor(c,t,mode) and r['invocation']==a['id'] and r['tokens']==a['actual_tokens'],'designated frozen receipt')
                prefix=deepcopy(state);last=max(attempts.index(byid[i]) for i in row['invocations']);prefix['attempts']=attempts[:last+1]
                prefix['totals']=dict(actual_tokens=sum(x['actual_tokens'] for x in prefix['attempts']),reserved_tokens=0,calls=len(prefix['attempts']))
                require(r['ledger_digest']==digest(prefix),'original profile ledger checkpoint')
                receipts[k]={**deepcopy(r),'kind':'historical_profile','original_receipt':deepcopy(r),'reuse_verified':True,
                    'source_scope':PARENT_SCOPE,'verified_ledger_digest':envelope['sha256'],'request_digest':req['payload_digest'],
                    'rendered_digest':digest(rendered),'compatibility':'exact public request, field order/schema, parent lineage, pinned worker and state policy; source release preserved'}
            require(ids==row['invocations'] and sum(byid[i]['actual_tokens'] for i in ids)==row['full_cost'],'profile complete accounting')
    return receipts
