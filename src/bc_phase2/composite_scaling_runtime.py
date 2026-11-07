"""Variable-n physical recipe using the accepted journal, artifact engine and R0 replay."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import time
from . import composite_scaling as spec, composite_math as base, composite_joint as ab
from .model import digest
from .joint_schema import require
from .joint_core import explicit_selection, compile_organisation, evaluate
from .joint_pipeline_runtime import recover, Artifact, snapshot_digest
from beyond_consensus.util import atomic_json, read_json


def catalog(components):return [dict(t,source_id=c['source_id']) for c in components for t in c['tasks']]


def request(c,t,proof,sources,parents):
    t=spec.task(c,t,proof)
    payload=dict(instruction=base.PROMPT,task_id=t['id'],responsibility=t['responsibility'],
        source=dict(id=c['source_id'],problem=sources[c['source_id']]),
        parent_artifacts=parents,required_string_fields=t['fields'])
    require(set(parents)==set(t['parents']),'exact parent payload')
    return dict(payload=payload,payload_digest=digest(payload))


class Engine(base.MathEngine):
    def __init__(self,journal,sources,out,components):
        super().__init__(journal,sources,out)
        self.components={c['namespace']:c for c in components}
    def task_for_operation(self,op):
        ns,local=op.host.split('_',1);c=self.components[ns]
        t=next(t for t in c['tasks'] if t['id']==local)
        return dict(spec.task(c,t,op.mode),_component=ns,_proof=op.mode)
    def make_request(self,t,store):
        c=self.components[t['_component']];original=next(x for x in c['tasks'] if x['id']==t['id'])
        parents={p:json.loads(store[c['namespace']+'_e'+p[1:]].value) for p in t['parents']}
        return request(c,original,t['_proof'],self.sources,parents)


def import_profiles(export,components):
    """Only the five v4 PROFILE calls; never evaluation bills or profile answer reuse."""
    from . import composite_joint_launch as old
    files=export['files'];release=files['release/approved-release.json']['content'];scope=old.verify_parent(release)
    env=files['execution/journal/ledger.json']['content'];state=env['state']
    require(env['sha256']==digest(state) and state['binding_digest']==digest(state['binding']),'historical ledger integrity')
    require(state['binding']['scope']==old.PARENT_SCOPE,'profile scope')
    transport=state['binding']['transport'];require(transport['template']==scope['model']['non_thinking_verification'],'profile template')
    for k in ('checkpoint','revision','thinking','do_sample','context','output'):
        expected={'context':16384,'output':3072}.get(k,ab.WORKER_POLICY.get(k))
        require(transport[k]==expected,'profile worker policy')
    profile=files['execution/profile.json']['content'];require(profile['snapshot_role']=='profile' and profile['complete'],'historical profile complete')
    require(profile['full_cost']==10898,'historical profile receipt')
    receipts={}
    for row in state['attempts']:
        if row['slot']!='profile':continue
        require(row['id'] in profile['invocations'] and base.reliable_terminal(row),'profile invocation/usage')
        payload=row['request']['payload'];sid=payload['source']['id']
        c=next((c for c in components if c['source_id']==sid),None)
        if c is None:continue
        t=next(t for t in c['tasks'] if t['id']==payload['task_id']);mode=c['reference_mode']
        require(digest(payload)==row['request']['payload_digest'],'historical payload digest')
        import hashlib
        require(hashlib.sha256(payload['source']['problem'].encode()).hexdigest()==c['statement_sha256'],'historical source')
        expected=request(c,t,mode,{sid:payload['source']['problem']},payload['parent_artifacts'])
        require(expected==row['request'],'profile payload incompatible')
        require(row['rendered']['input_tokens']==row['input_tokens'] and row['actual_tokens']==row['input_tokens']+row['observation']['output_tokens'],'historical metering')
        k=spec.key(c,t,mode)
        receipts[k]=dict(key=k,tokens=row['actual_tokens'],kind='historical_profile',scope=old.PARENT_SCOPE,invocation=row['id'],
            ledger_digest=env['sha256'],request_digest=row['request']['payload_digest'],rendered_digest=digest(row['rendered']),
            descriptor=spec.descriptor(c,t,mode),transport=transport,profile_expense_already_recorded=True)
    return receipts


def validate_receipts(receipts,coverage):
    allowed={r['key']:r for r in coverage}
    require(set(receipts)<=set(allowed),'unknown profile keys')
    for k,r in receipts.items():
        require(r['key']==k and r['descriptor']==allowed[k]['descriptor'] and type(r['tokens'])is int and r['tokens']>0,'incompatible profile key')
        require(r['kind'] in ('historical_profile','new_profile') and r['invocation'],'evaluation bills forbidden')


def schedule_profiles(components,receipts):
    schedule=[]
    for c in components:
        for mode in c['A_modes']:
            if any(spec.key(c,t,mode) not in receipts for t in c['tasks']):
                # Generate own prerequisites. Never insert historical profile artifacts.
                schedule.append(dict(component=c['namespace'],mode=mode,events=[c['namespace']+'_e'+t['id'][1:] for t in c['tasks']],calls=len(c['tasks'])))
    return schedule


def pending_rows(wave):
    return [dict(n=r['n'],slot=r['slot'],method=m,status='unrun',configuration_status=r['status'],replay_mean=None,
        replay_max=None,question_quality='unknown',composite_quality='unknown') for r in wave['matrix'] for m in spec.METHODS]


def execution_structure(ex, selection):
    hosts={o.id:o.host for o in ex.operations};ownership=selection['ownership']
    edges=[dict(parent=read.event,consumer=op.id,cross_owner=ownership[hosts[read.event]]!=ownership[op.host])
           for op in ex.operations for read in op.reads if read.event]
    return dict(operations=[dict(id=o.id,host=o.host,owner=ownership[o.host],mode=o.mode) for o in ex.operations],
                dependencies=edges,cross_owner_edges=sum(e['cross_owner'] for e in edges),
                communication_mode='direct_parent_artifacts',outputs=dict(ex.outputs))


def summary_method(clean,repairs,n):
    costs=[r.get('full_cost') for r in repairs];complete=len(costs)==n and all(x is not None for x in costs)
    return dict(status='complete' if clean['complete'] and complete else 'incomplete',clean=base.serial(clean),repairs=base.serial(repairs),
        clean_calls=len(clean['invocations']),repair_calls=sum(len(r['invocations']) for r in repairs),
        clean_cpu_seconds=clean['cpu_seconds'],repair_cpu_seconds=sum(r.get('cpu_seconds',0) for r in repairs),
        full_cost_coverage=complete,replay_sum=sum(costs) if complete else None,replay_mean=str(Fraction(sum(costs),n)) if complete else None,
        max_owner_mean=max(costs) if complete else None,largest_observed_incident=max(costs) if complete else None,
        question_quality='unknown',composite_quality='unknown',quality_preserving_saving=None)


def persist(out,name,value):
    """Exclusive immutable result records. Progress files are separate."""
    path=Path(out)/name
    path.parent.mkdir(parents=True,exist_ok=True)
    require(not path.exists(),'immutable result already exists')
    atomic_json(path,base.serial(value))


def run_wave(journal,sources,out,wave,solver=None):
    from .joint_solver import solve
    out=Path(out);out.mkdir(exist_ok=True);solver=solver or solve
    components=wave['components'];engine=Engine(journal,sources,out,components)
    prices=deepcopy(wave['reused_profiles']);validate_receipts(prices,wave['profile_coverage'])
    result=dict(schema='composite-scaling-result-v2',wave_id=wave['wave_id'],status='running',methods=list(spec.METHODS),
        evidence=journal.binding['transport'].get('evidence','unclassified'),model_executed=False,conditions=[],rows=pending_rows(wave),profile_records=[],totals=journal.snapshot()['totals'],quality='pending_blinded_review',later_waves_enabled=False)
    if (out/'wave-result.json').exists():
        saved=read_json(out/'wave-result.json')
        require(saved['wave_id']==wave['wave_id'],'resume scope changed')
        require(saved['status']=='completed_wave_recipe' and saved['totals']==journal.snapshot()['totals'] and not saved['totals']['reserved_tokens'],'interrupted or uncertain wave; no redispatch')
        return saved  # Read-only exact completed receipt, never another physical sweep.
    def save():
        result['totals']=journal.snapshot()['totals'];result['model_executed']=result['evidence']=='real_composite_worker_development' and result['totals']['calls']>0;atomic_json(out/'wave-result.json',base.serial(result))
    save()
    try:
        for s in wave['profile_schedule']:
            c=next(c for c in components if c['namespace']==s['component'])
            # Use a containing frozen bundle for valid owner/task counts; execute only this component.
            b=next(b for b in wave['bundles'] if c['source_id'] in b['sources']);d=spec.domain(b['components'],b['n'])
            a=deepcopy(b['neutral']['A'])
            if len(c['A_modes'])>1:a[c['namespace']+'_proof']=s['mode']
            ex=compile_organisation(d,explicit_selection(d,a,{},b['neutral']['ownership']))
            slot='profile/'+c['namespace']+'/'+s['mode'];row=engine.run(ex,slot,required=set(s['events']),phase='profile')
            result['profile_records'].append(base.serial(row));save()
            if not row['complete']:continue
            for t in c['tasks']:
                k=spec.key(c,t,s['mode'])
                if k in prices:continue # prerequisite generation does not replace earlier prices
                tr=next(tr for tr in row['trace'] if tr['event']==c['namespace']+'_e'+t['id'][1:])
                prices[k]=dict(key=k,tokens=tr['usage'],kind='new_profile',invocation=tr['invocation'],descriptor=spec.descriptor(c,t,s['mode']),wave_id=wave['wave_id'])
        persist(out,'prices.frozen.json',dict(receipts=prices,consumers=wave['profile_consumers'],physical_new_profile_tokens=sum(r['known_attempted_spend'] for r in result['profile_records']),historical_reused_profile_tokens=sum(r['tokens'] for r in wave['reused_profiles'].values())))
        for b in wave['bundles']:
            bid=b['preprice_id'];prefix='condition-'+bid
            needed={r['key'] for r in spec.coverage(b['components'])}
            cond=dict(preprice_id=bid,n=b['n'],slot=b['slot'],source_ids=b['sources'],m=b['m'],q=b['q'],K=2,methods={},status='pending',profile_keys=sorted(needed))
            if not needed<=prices.keys():
                cond.update(status='blocked_profile_coverage',missing_profile_keys=sorted(needed-prices.keys()))
                for method in spec.METHODS:cond['methods'][method]=dict(status='unrun',replay_mean=None)
            else:
                d=spec.domain(b['components'],b['n'],{k:prices[k]['tokens'] for k in needed})
                ns=explicit_selection(d,b['neutral']['A'],{},b['neutral']['ownership'])
                start=time.monotonic();cpu=time.process_time();cert=solver(d,seed=ns,seconds=30,threads=1,random_seed=0)
                chosen=ab.checked_candidate(d,cert,ns)
                en=compile_organisation(d,ns);ej=compile_organisation(d,chosen);same=en==ej
                cid=digest(dict(preprice_id=bid,neutral=b['neutral'],prices={k:prices[k]['tokens'] for k in sorted(needed)}))
                cond.update(condition_id=cid,priced_domain_id=ns['domain'],designs=dict(NEUTRAL=ns,JOINT=chosen),certificate=base.serial(cert),
                    solver_wall_seconds=time.monotonic()-start,solver_cpu_seconds=time.process_time()-cpu,shared_observations=same,predicted={m:base.serial(evaluate(ex)) for m,ex in [('NEUTRAL',en),('JOINT',ej)]},
                    scope_label='AB' if d['choices'] else 'B-effective',
                    profile_proxy_limitation='Parent artifacts and their token lengths can change on regeneration; frozen prices are development proxies.',
                    searched_axes=['A','B'] if d['choices'] else ['B'],available_axes=['A','B'] if d['choices'] else ['B'],C='fixed_direct',
                    changed=dict(A=ns['A']!=chosen['A'],B=sorted(g for _,g in en.groups)!=sorted(g for _,g in ej.groups),C=False,topology=False),
                    execution_structure={m:execution_structure(ex,sel) for m,ex,sel in [('NEUTRAL',en,ns),('JOINT',ej,chosen)]},
                    exact_call_schedule={m:len(ex.operations)+sum(len(x) for x in evaluate(ex)['recovery_sets']) for m,ex in [('NEUTRAL',en),('JOINT',ej)]})
                require(sum(cond['exact_call_schedule'].values())<=b['call_bounds']['evaluation_calls'],'component bound violated')
                persist(out,prefix+'/designs.frozen.json',cond)
                methods=['NEUTRAL'] if same else list(spec.METHODS);execs=dict(NEUTRAL=en,JOINT=ej);cleans={};repairs={m:[] for m in methods}
                for m in methods:cleans[m]=engine.run(execs[m],prefix+'/'+m+'/clean')
                for i in range(b['n']):
                    for m in methods:
                        row=recover(engine,execs[m],cleans[m],'o'+str(i),prefix+'/'+m+'/owner/o'+str(i),None)
                        row['answer_origin']={qid:'regenerated' if eid in row.get('reconstruction',[]) else 'retained' if eid in row.get('store',{}) else 'missing' for qid,eid in execs[m].outputs}
                        repairs[m].append(row);persist(out,prefix+'/'+m+'-owner-'+str(i)+'.json',row);save()
                for m in methods:cond['methods'][m]=summary_method(cleans[m],repairs[m],b['n'])
                if same:cond['methods']['JOINT']=dict(deepcopy(cond['methods']['NEUTRAL']),shared_with='NEUTRAL')
                a=cond['methods']['NEUTRAL'];z=cond['methods']['JOINT']
                cond['paired_saving']=str(1-Fraction(z['replay_sum'],a['replay_sum'])) if a['full_cost_coverage'] and z['full_cost_coverage'] and a['replay_sum']>0 else None
                cond['status']='completed_comparison' if all(r['status']=='complete' for r in cond['methods'].values()) else 'incomplete_comparison'
                # Blinded artifact judgments remain separate from method mapping.
                reviews=[];mapping={}
                for m in methods:
                    for row in [cleans[m]]+repairs[m]:
                        for qid,eid in execs[m].outputs:
                            if eid not in row.get('store',{}):continue
                            c=next(c for c in b['components'] if eid.startswith(c['namespace']+'_'))
                            rid='review-'+digest([cid,row['slot'],qid])[:20]
                            reviews.append(dict(id=rid,statement=sources[c['source_id']],output=json.loads(row['store'][eid].value),intermediate_artifacts={e:json.loads(v.value) for e,v in row['store'].items() if e.startswith(c['namespace']+'_')},validity='unknown'))
                            mapping[rid]=dict(slot=row['slot'],output=qid,source_id=c['source_id'],retained=eid not in row.get('reconstruction',[]) if row.get('snapshot_role')=='repair' else False)
                persist(out,prefix+'/QUALITY_REVIEW.blinded.json',sorted(reviews,key=lambda r:r['id']));persist(out,prefix+'/QUALITY_REVIEW.mapping.private.json',mapping)
            result['conditions'].append(cond)
            for row in result['rows']:
                if row['n']==b['n'] and row['slot']==b['slot']:
                    stats=cond['methods'][row['method']];row.update({k:stats.get(k) for k in ['status','replay_mean','max_owner_mean','largest_observed_incident']});row['condition_id']=cond.get('condition_id')
            persist(out,prefix+'/result.json',cond);save()
            # Append-only per-size report after each pair, equal-bundle estimand only.
            done=[c for c in result['conditions'] if c['n']==b['n'] and c.get('paired_saving') is not None]
            persist(out,'per-n-'+str(b['n'])+'-after-slot-'+str(b['slot'])+'.json',dict(n=b['n'],complete_pairs=len(done),planned_slots=3,frozen_slots=sum(x['n']==b['n'] for x in wave['bundles']),equal_bundle_mean=str(sum(Fraction(c['paired_saving']) for c in done)/len(done)) if done else None,independent_samples=False))
        result['status']='completed_wave_recipe';save();return result
    except BaseException:
        result['status']='halted';save();raise


def fixed_work_receipt_link(saved, requested):
    keys=('condition_id','preprice_id','priced_domain_id','designs')
    require(saved.get('status')=='completed_comparison','incomplete receipt cannot serve another view')
    require(all(k in saved and k in requested and saved[k]==requested[k] for k in keys),'full condition identity required, not work_id alone')
    return dict(kind='linked_existing_condition_not_new_observation',condition_id=saved['condition_id'],independent_observation=False)


AB_PROFILE_SCOPE='cc8e23639df5ab2749d1045e23c9e35c51882e6587e099db8d38e74e260c720f'

def import_ab_profiles(export,components):
    """Additional algebraic profile from the completed AB run, not its evaluations."""
    import hashlib
    expected_scope=AB_PROFILE_SCOPE
    files=export['files'];release=files['release/approved-release.json']['content'];scope=release['manifest']['scope']
    require(release['release_digest']==digest({k:v for k,v in release.items() if k!='release_digest'}),'AB release integrity')
    require(release['manifest']['scope_digest']==expected_scope==digest(scope),'exact completed AB scope')
    envelope=files['execution/journal/ledger.json']['content'];state=envelope['state']
    require(envelope['sha256']==digest(state) and state['binding_digest']==digest(state['binding']) and state['binding']['scope']==expected_scope,'AB ledger binding')
    profile=files['execution/profile_algebraic.json']['content']
    require(profile['snapshot_role']=='profile' and profile['complete'] and profile['slot']=='profile/algebraic','AB profile only')
    transport=state['binding']['transport']
    require(transport['template']==scope['model']['non_thinking_verification'],'AB tokenizer template')
    for k in ('checkpoint','revision','thinking','do_sample','context','output'):
        require(transport[k]=={'context':16384,'output':3072}.get(k,ab.WORKER_POLICY.get(k)),'AB model setting')
    receipts={}
    for row in state['attempts']:
        if row['slot']!='profile/algebraic':continue
        require(row['id'] in profile['invocations'] and base.reliable_terminal(row),'AB profile usage')
        p=row['request']['payload'];c=next(c for c in components if c['source_id']==p['source']['id']);t=next(t for t in c['tasks'] if t['id']==p['task_id'])
        require(hashlib.sha256(p['source']['problem'].encode()).hexdigest()==c['statement_sha256'],'AB statement')
        require(row['request']==request(c,t,'algebraic',{c['source_id']:p['source']['problem']},p['parent_artifacts']),'AB profile request mismatch')
        require(row['actual_tokens']==row['input_tokens']+row['observation']['output_tokens'],'AB usage sum')
        k=spec.key(c,t,'algebraic');receipts[k]=dict(key=k,tokens=row['actual_tokens'],kind='historical_profile',scope=expected_scope,invocation=row['id'],ledger_digest=envelope['sha256'],request_digest=row['request']['payload_digest'],rendered_digest=digest(row['rendered']),descriptor=spec.descriptor(c,t,'algebraic'),transport=transport,profile_expense_already_recorded=True)
    require(len(receipts)==2 and len(profile['invocations'])==2,'both existing algebraic profile records required')
    require(sum(x['tokens'] for x in receipts.values())==profile['full_cost'],'AB full profile cost')
    return receipts
