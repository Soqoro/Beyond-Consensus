"""Six-call diagnostic adapter for the existing approval, journal and registry path."""
from copy import deepcopy
from pathlib import Path
import json,os,re,signal,sys,threading,time
from . import composite_derivation_diagnostic as diagnostic, composite_math as worker, composite_math_launch as base
from .model import digest,Invalid
from .joint_schema import require
from beyond_consensus.experiments import cluster
from beyond_consensus.util import atomic_json
KEY=diagnostic.VERSION
PARENT_SCOPE='bb51d1cb2a3f8914d9f8b0f6e1c4c52f0a21eb273be9b33c9c856c45845c5f37'

def identity():
    root=Path(__file__).resolve().parents[2]
    files=set(base.identity())|{'src/bc_phase2/composite_derivation_diagnostic.py','src/bc_phase2/composite_derivation_launch.py','scripts/composite_derivation_pilot.py','scripts/check_composite_derivation_order.py','experiments/run_composite_derivation.sbatch'}
    return {p:base.previous.local.file_hash(root/p) for p in sorted(files)}

def sources(s):
    p=Path(s['export']['path']);require(base.previous.local.file_hash(p)==s['export']['sha256'],'raw export changed')
    export=json.loads(p.read_bytes());proposal=diagnostic.prepare(export)
    require(proposal==s['proposal'],'proposal changed')
    require(export['binding']['scope']==PARENT_SCOPE,'parent scope')
    return export

def check_cpu(q,proposal):
    require(q['status']=='passed_cpu_checks' and q['proposal_digest']==proposal['proposal_digest'],'CPU proposal binding')
    require(q['model_executed'] is False and q['execution_allowed'] is False and q['xgrammar_version']=='0.1.32','CPU-only evidence')
    require(q['versions']==base.previous.local.VERSIONS,'CPU runtime versions')
    require(len(q['rows'])==6,'six CPU measurements')
    for r,t in zip(q['rows'],proposal['tasks']):
        require((r['source_id'],r['task_id'])==(t['source_id'],t['task_id']),'CPU task order')
        require(r['payload_digest']==t['candidate_request_digest'] and r['schema_digest']==t['candidate_schema_digest'] and r['parent_digest']==t['parent_digest'],'CPU request binding')
        require(type(r['input_tokens']) is int and 0<r['input_tokens']<=13312 and r['reserved_tokens']==r['input_tokens']+3072,'CPU token fit')
        require([o['eos'] for o in r['observations']]==[248046,248044],'EOS coverage')
        for o in r['observations']:
            require(all(o['derivation_first'][k] is True for k in ('string_plus_eos','tokens_plus_eos','roundtrip_exact')),'positive order control')
            require(all(o[v][k] is False for v in ('historical_order','extra_key') for k in ('string_plus_eos','tokens_plus_eos')),'negative order control')
    require(q['total_reservation_tokens']==sum(r['reserved_tokens'] for r in q['rows']),'reservation sum')

def prepare(parent,export_path,q,config):
    require(parent['release_digest']==digest({k:v for k,v in parent.items() if k!='release_digest'}),'parent release digest')
    old=parent['manifest'];require(old['scope_digest']==digest(old['scope'])==PARENT_SCOPE,'exact historical model provenance')
    export_path=Path(export_path).resolve();export=json.loads(export_path.read_bytes());proposal=diagnostic.prepare(export);check_cpu(q,proposal)
    require(q['input_sha256']==base.previous.local.file_hash(export_path),'CPU export bytes')
    dep=base.deployment()
    scope=dict(condition=KEY,parent_scope=PARENT_SCOPE,proposal=proposal,limits=proposal['limits'],
        export={'path':str(export_path),'sha256':base.previous.local.file_hash(export_path)},
        model=deepcopy(old['scope']['model']),cluster=config,deployment=dep,runtime_identity=identity(),cpu_qualification=q,
        continuation='continue after known completed invalid outcome; stop on uncertain usage, integrity or limits',
        monetary_cost='unverified local allocation',D2_D6_campaign_enabled=False)
    blockers=['deployment:'+k for k,v in base.EXPECTED_PACKAGES.items() if dep['packages'].get(k)!=v]
    if not dep['solver_importable']:blockers.append('existing_loader_requires_solver_import')
    m=dict(schema='composite-derivation-manifest-v1',scope=scope,scope_digest=digest(scope),blockers=blockers,execution_allowed=False)
    validate_manifest(m);return m

def validate_manifest(m):
    require(m['schema']=='composite-derivation-manifest-v1' and m['scope_digest']==digest(m['scope']),'manifest integrity')
    s=m['scope'];require(s['condition']==KEY and s['parent_scope']==PARENT_SCOPE and s['runtime_identity']==identity(),'source binding')
    export=sources(s);check_cpu(s['cpu_qualification'],s['proposal'])
    require(s['limits']==s['proposal']['limits'],'limits')
    require(s['cpu_qualification']['input_sha256']==s['export']['sha256'],'qualification export binding')
    model=s['model'];t=export['binding']['transport']
    require(model['checkpoint']==t['checkpoint'] and model['revision']==t['revision'],'model binding')
    require(model['thinking'] is False and model['do_sample'] is False and model['dtype']=='bfloat16' and model['attention']=='sdpa','generation policy')
    require(model['non_thinking_verification']==s['cpu_qualification']['template']==t['template'],'template binding')
    require(digest(base.pilot.lock_for(s))==t['inventory_digest'],'historical inventory binding')
    c=cluster.ClusterConfig(**s['cluster'])
    require(c.partition in ('NA100q','HPCAIq') and c.time=='01:00:00' and c.memory_gb==128 and c.activation_script is None,'allocation limits')
    require(str(Path(c.python).resolve())==s['deployment']['python'],'interpreter binding')
    return s

def approve(m,a):
    validate_manifest(m);require(not m['blockers'],'deployment blockers')
    require(set(a)=={'schema','scope_digest','decision','reviewer','reviewed_at','source_worker_transmission','contract_accepted','gpu_recipe_authorized'},'approval fields')
    require(a['schema']=='composite-derivation-approval-v1' and a['scope_digest']==m['scope_digest'] and a['decision']=='approved','exact approval')
    require(all(a[k] is True for k in ('source_worker_transmission','contract_accepted','gpu_recipe_authorized')),'explicit permissions')
    require(all(type(a[k]) is str and a[k].strip() for k in ('reviewer','reviewed_at')),'review identity')
    v=dict(schema='composite-derivation-release-v1',manifest=m,approval=a);v['release_digest']=digest(v);return v

def validate_release(v):
    require(v==approve(v['manifest'],v['approval']),'release digest');return validate_manifest(v['manifest'])

def source_records(s):return sources(s)
def transport_tasks(s):return [dict(id=r['task_id'],source_id=r['source_id'],fields=r['candidate_fields']) for r in s['proposal']['tasks']]
def arguments(c,snapshot,output):
    a=base.arguments(c,snapshot,output);a[-4]=str(snapshot/'experiments/run_composite_derivation.sbatch');return a

def check_scoped_allocation(record,s):
    fields=dict(re.findall(r'(\w+)=([^\s]+)',record))
    require(fields.get('Partition')==s['cluster']['partition'],'allocated partition')
    base.pilot.check_allocation_record(record.replace('Partition='+s['cluster']['partition'],'Partition=NA100q'))

def open_transport(v):return base.open_transport(v,protocol=sys.modules[__name__])
def submit(root,v,*,dry_run=True):return base.submit(root,v,dry_run=dry_run,protocol=sys.modules[__name__])
def run_allocated(root,out):return base.run_allocated(root,out,protocol=sys.modules[__name__])

class MeasuredTransport:
    """Reject changed rendered requests before journal reservation or generation."""
    def __init__(self,transport,rows):self.transport=transport;self.binding=transport.binding;self.rows={r['payload_digest']:r for r in rows}
    def render(self,request):
        rendered=self.transport.render(request);r=self.rows[request['payload_digest']]
        require(rendered['input_tokens']==r['input_tokens'] and rendered['rendered_ids_digest']==r['rendered_ids_digest'],'rendered request changed')
        return rendered
    def generate(self,rendered):return self.transport.generate(rendered)

def execute(journal,export,out):
    rows=[];out=Path(out)
    for index,(sid,tid) in enumerate(diagnostic.TARGETS):
        g=next(g for g in export['groups'] if (g['source_id'],g['task_id'])==(sid,tid))
        request=diagnostic.candidate_request(g['request'])
        call=journal.invoke(request,'diagnostic/'+str(index),tid)
        require(call is not None,'measured input unexpectedly overflowed')
        obs=call['observation'];row=dict(source_id=sid,task_id=tid,call_id=call['id'],actual_tokens=call['actual_tokens'],status='invalid_response',semantic_validity='unreviewed')
        try:
            require(obs['finish_reason']=='eos' and not obs.get('boundary_error'),'response boundary')
            fields=request['payload']['required_string_fields']
            artifact=worker.parse_artifact(obs['final_text'],{'fields':fields})
            require(list(json.loads(obs['final_text']))==fields,'emission order')
            row.update(status='structurally_valid',artifact=json.loads(artifact))
        except (Invalid,TypeError) as exc:row['error']=str(exc)
        rows.append(row);atomic_json(out/f'case-{index}.json',row)
        atomic_json(out/'progress.json',dict(rows=rows,unrun=[list(x) for x in diagnostic.TARGETS[index+1:]],totals=journal.snapshot()['totals']))
    return dict(status='completed_diagnostic',rows=rows,totals=journal.snapshot()['totals'],model_executed=True,quality='unreviewed',recovery_executed=False)

def dispatch(v,directory):
    s=validate_release(v);out=Path(directory);out.mkdir(exist_ok=False);wall=time.monotonic();cpu=time.process_time();journal=None
    atomic_json(out/'startup.json',dict(scope_digest=digest(s),state='started_no_retry'))
    timer=threading.Timer(s['limits']['wall_seconds'],lambda:os.kill(os.getpid(),signal.SIGKILL));timer.daemon=True;timer.start()
    try:
        export=sources(s);transport=MeasuredTransport(open_transport(v),s['cpu_qualification']['rows'])
        journal=worker.Journal(out/'journal',transport,digest(s),lambda:sources(s),condition=KEY,limits=s['limits'])
        result=execute(journal,export,out)
        result['stage_resources']=dict(cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall)
        atomic_json(out/'result.json',result);return result
    except BaseException as exc:
        atomic_json(out/'failure.json',dict(error_type=type(exc).__name__,error=str(exc),retry_allowed=False,totals=journal.snapshot()['totals'] if journal else None,cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall))
        raise
    finally:timer.cancel()
