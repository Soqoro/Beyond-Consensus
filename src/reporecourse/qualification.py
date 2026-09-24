"""CPU reference qualification: no model, no policy-performance claims."""
from copy import deepcopy
import time
from .common import Rejected, digest, file_hash
from .tasks import ROOT,catalog,load_task,private_task,split_check
from .engine import Engine,ScriptedWorker
from .evaluator import evaluate
from .policies import variation


def run_reference(public,private,organization='independent',policy='delegation_jit',track='clean',target=None):
    witness=next(w for w in private['witnesses'] if w['organization']==organization)
    engine=Engine(public,ScriptedWorker(witness),policy=policy,outline=organization,track=track,target=target)
    try:
        report=engine.run()
        score=evaluate(public,private,report['state'])
        report['evaluation']=score;report['success']=score.get('success')
        return report
    finally:engine.env.close()


def qualify(task_id,sources,root=ROOT):
    start=time.process_time();card,public=load_task(task_id,sources,root);private=private_task(task_id,root)
    before={part:file_hash(root/part/(task_id+'.json')) for part in ('public','private')}
    witnesses=[];negatives=[];basis=None
    for witness in private['witnesses']:
        r=run_reference(public,private,witness['organization'])
        score=r['evaluation']
        if score['status']=='blocked_prerequisite' or r['status']=='blocked_prerequisite':
            return {'task':task_id,'status':'blocked_prerequisite','model_executed':False}
        witnesses.append({'organization':witness['organization'],'success':score['success'],
            'bound_bundle_hash':score['bound_bundle_hash'],'runtime_cpu_resources':r['resource_profile'],
            'evaluator_resources':score['evaluator_resources']})
        basis=r if basis is None else basis
    # Missing each original requirement cannot be rescued by selecting any other
    # artifact. Semantically wrong but syntactically safe bound outputs must fail.
    for req in public['required_outputs']:
        key=req['id'];state=deepcopy(basis['state'])
        state['bound'].pop(key,None)
        negatives.append({'control':'missing','obligation':key,'detected':evaluate(public,private,state)['success'] is False})
        state=deepcopy(basis['state']);v=state['bound'].get(key)
        if v is None:negatives.append({'control':'semantic_mutation','obligation':key,'detected':False});continue
        a=state['artifacts'][v]
        if a['format']=='select':
            # Preserve names/shape; wrong constant values, not merely invalid SQL.
            a['content']['columns'][0]['expr']={'literal':-999}
        elif a['format']=='schema':a['content']=True  # Overbroad acceptance must be caught by negatives.
        else:
            field=next(iter(a['content']['fields']))
            a['content']['fields'][field]['path']=['absent_test_field'];a['content']['fields'][field]['missing']='null'
        negatives.append({'control':'semantic_mutation','obligation':key,'detected':evaluate(public,private,state)['success'] is False})
        variants=('wrong_alias','wrong_type') if a['format']=='select' else ('reject_all',) if a['format']=='schema' else ('dropped_field',)
        for control in variants:
            changed=deepcopy(basis['state']);artifact=changed['artifacts'][v]
            if control=='wrong_alias':artifact['content']['columns'][0]['as']='unexpected_output'
            elif control=='wrong_type':
                artifact['content']['columns'][0]['expr']={'literal':7 if req['types'][0]=='string' else 'not_a_number'}
            elif control=='reject_all':artifact['content']=False
            else:artifact['content']['fields'].pop(next(iter(artifact['content']['fields'])))
            negatives.append({'control':control,'obligation':key,'detected':evaluate(public,private,changed)['success'] is False})
    repeat=evaluate(public,private,basis['state'])
    _,again=load_task(task_id,sources,root)
    integrity=before=={p:file_hash(root/p/(task_id+'.json')) for p in before} and digest(public)==digest(again)
    ok=all(w['success'] for w in witnesses) and all(n['detected'] for n in negatives) and integrity and repeat['success']==basis['success']
    return {'schema':'rr-cpu-qualification-v1','implementation_hashes':implementation_hashes(),'task':task_id,'task_hash':digest(card),
        'status':'cpu_qualified_review_pending' if ok else 'failed','witnesses':witnesses,'negative_controls':negatives,
        'source_integrity':integrity,'reset_repeat_identical':repeat['obligations']==basis['evaluation']['obligations'],
        'variation':variation(public['outlines'],public),'private_visibility':'separate public loader; tested tool interface',
        'runtime_versions':runtime_versions(),'independent_review':'pending','decomposition_reference_eligible':ok and len(witnesses)>=2,
        'model_executed':False,'model_competence':None,'sql_executed':public['family']=='data_product',
        'finite_tests_only':True,'analysis_cpu_seconds':time.process_time()-start}


def inventory(sources,root=ROOT):
    cat=catalog(root);rows=[]
    for c in cat['tasks']:
        reasons=[]
        try:_,p=load_task(c['id'],sources,root);private_task(c['id'],root)
        except Rejected as e:reasons.append(str(e))
        reasons+=['independent_review_pending','clean_model_competence_unmeasured','new_resource_calibration_unmeasured']
        if c['pack']=='energy':reasons.append('underlying_provider_license_review_pending')
        rows.append({**c,'blockers':reasons})
    native=[r for r in rows if r['grounding']!='synthetic_diagnostic']
    return {'schema':'rr-readiness-v1','tasks':rows,'actual_repository_tasks':len(native),
        'source_packs':len({r['pack'] for r in native}),'reviewed_source_packs':0,
        'family_counts':{f:sum(r['family']==f for r in native) for f in ('data_product','api_schema')},
        'non_demo_tasks':sum(r['grounding']=='repo_grounded_authored' for r in native),
        'target':cat['target'],'target_unfilled':True,'splits':split_check(rows),
        'model_executed':False,'full_balanced_gate_applicable':False}


def implementation_hashes():
    base=ROOT.parents[1]
    files=sorted((base/'src'/'reporecourse').glob('*.py'))+sorted((base/'src'/'restricted_artifacts').glob('*.py'))
    return {str(p.relative_to(base)):file_hash(p) for p in files}


def runtime_versions():
    import importlib.metadata,sys
    result={'python':'.'.join(map(str,sys.version_info[:3]))}
    for name in ('sqlglot','jsonschema','referencing'):
        try:result[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:result[name]=None
    return result
