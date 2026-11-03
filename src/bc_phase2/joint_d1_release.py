"""Frozen D1 scope binding; only a separately validated exact release may dispatch."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import time
import os
import signal
import threading

from .model import Invalid,digest
from .joint_schema import require
from . import joint_d1_local as local
from .joint_d1_qwen import configuration,settings,limits,implementation,JointQwenSession
from .joint_d1_readiness import NEUTRAL_PROMPT,PROMPT_VERSION,SMOKE
from .joint_pipeline_contracts import planner_payload
from .planner_qwen import QwenTransport,open_local,CHECKPOINT,REVISION

LIVE_RELEASED=False
# Exact source of the already completed tokenizer/inventory verification. The only
# changed shared file is joint_d1_qwen.py (session integration, not token rendering).
VERIFIED_BASE_IMPLEMENTATION = {'src/bc_phase2/joint_d1_qwen.py': '3161822377c9c788d26c5eb064566eafb0698ed18479688c2a575cafbbee58a9', 'src/bc_phase2/joint_d1_readiness.py': 'bc9441eacc78f8410c563b3ae034586b23815a0a58141dcbf4aed2ea1089f2f4', 'src/bc_phase2/joint_pipeline_contracts.py': '4e845fbdffaba91b13d0cfebe7938ae6396d64e9dbda450dd099977ca5a1a246', 'src/bc_phase2/joint_schema.py': '46b5e34ef858babd0f7723fcde46a55648ace3b273c0d2c6d5ffba6e300d040b', 'src/bc_phase2/joint_core.py': '6924f669af73257f656de25881794852b395181b4ac62df9c53f544dfa3a82a3', 'src/bc_phase2/model.py': '4268a30bd27c4b0d0781d7aade933d834b33a7bde1b2181a32c18cf61e21515d', 'src/bc_phase2/planner_qwen.py': '9f8214d37f6e91d6c4f2439bc0082cace2ea8ceb2512ca76303735e118206d1a', 'src/bc_phase2/planner_ledger.py': 'a35c5d84dae80c779726344dcd6ac74ba937788ab5627762ea355d378df21ef7', 'src/bc_phase2/joint_d1_local.py': '53f336c59dee6d26de26a40c7b3d67dec151668d7f7329ddb5d662b0837cfe23', 'src/beyond_consensus/models/transformers_backend.py': '4fc3da401a23c7e45c0d0a40cf5cbd4bf9ac860a8c8f464acdbf9e38995362cd'}


def read_evidence(path,cap=2*1024*1024):
    """Saved evidence has finite measured times; blueprint JSON remains strict."""
    with Path(path).open('rb') as handle:raw=handle.read(cap+1)
    require(len(raw)<=cap,'evidence size')
    def pairs(rows):
        value={}
        for k,v in rows:
            require(k not in value,'duplicate evidence key');value[k]=v
        return value
    def reject(value):raise Invalid('nonfinite evidence')
    try:
        value=json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=reject)
        json.dumps(value,allow_nan=False)
    except (ValueError,UnicodeError,RecursionError) as exc:raise Invalid('invalid evidence JSON') from exc
    require(type(value) is dict,'evidence object')
    return value


def _hash(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None


def _request(record):
    require(type(record) is dict and set(record)=={'id','problem'},'statement-only record')
    payload=planner_payload(record,4,2);payload.update(prompt=NEUTRAL_PROMPT,prompt_version=PROMPT_VERSION)
    return {'payload':payload,'payload_digest':digest(payload)}


def runtime_identity(root):
    result=implementation(root)
    for p in ('src/bc_phase2/joint_d1_release.py','scripts/freeze_joint_d1_scope.py',
              'src/bc_phase2/joint_d1_launch.py','scripts/launch_joint_d1.py',
              'experiments/run_joint_d1.sbatch',
              'src/beyond_consensus/experiments/cluster.py',
              'src/beyond_consensus/experiments/snapshot.py',
              'src/beyond_consensus/experiments/manifest.py',
              'src/beyond_consensus/util.py',
              'src/bc_phase1/core.py', 'src/bc_phase2/planner_first.py',
              'src/bc_phase2/response_boundary.py','src/bc_phase2/joint_pipeline_sources.py'):
        result[p]=local.file_hash(Path(root)/p)
    return result


def validate_verification(root,receipt,report):
    local.validate_receipt(receipt)
    expected={'schema','status','receipt_digest','source_ids','statements_file_sha256','statement_hashes',
              'implementation','accounting','local_path','checkpoint','revision','inventory','template',
              'generation_tokens','packages','initial_requests','correction_fit','model_executed',
              'execution_allowed','gpu_used','worst_case_fit_established'}
    require(type(report) is dict and set(report)==expected,'full verification report required')
    require(report['schema']=='joint-d1-local-verification-v1' and
            report['status']=='local_inventory_and_initial_tokenization_observed','verification status')
    require(report['receipt_digest']==digest(receipt),'verification/receipt mismatch')
    require(report['source_ids']==list(SMOKE) and report['statement_hashes']==local.STATEMENT_HASHES
            and report['statements_file_sha256']==local.STATEMENTS_HASH,'source verification mismatch')
    require(report['checkpoint']==CHECKPOINT and report['revision']==REVISION and
            report['local_path']==receipt['model_path'],'verified model mismatch')
    require(report['packages']==local.VERSIONS,'verified environment mismatch')
    require(all(report[k] is False for k in ('model_executed','execution_allowed','gpu_used','worst_case_fit_established')),
            'verification cannot authorize execution')
    require(report['correction_fit']=='checked_at_dispatch_not_worst_case_qualified','correction policy')
    current=implementation(root)
    recorded=report['implementation']
    require(recorded==VERIFIED_BASE_IMPLEMENTATION or recorded==current,'unreviewed verification implementation')
    # No broad compatibility waiver: all verifier/parser/rendering dependencies must still match.
    require(all(current[p]==h for p,h in recorded.items()
                if p not in ('src/bc_phase2/joint_d1_qwen.py','src/bc_phase2/planner_qwen.py')),
            'verification dependency changed; new review needed')
    require(recorded['src/bc_phase2/planner_qwen.py'] in
            (VERIFIED_BASE_IMPLEMENTATION['src/bc_phase2/planner_qwen.py'],current['src/bc_phase2/planner_qwen.py']),
            'unreviewed loader verification')
    accounting=report['accounting']
    require(type(accounting) is dict and set(accounting)=={'ledger','cpu_seconds','wall_seconds'}
            and accounting['ledger']=='offline_preparation_not_model_usage','preparation accounting')
    require(all(type(accounting[k]) in (int,float) and math.isfinite(accounting[k]) and accounting[k]>=0
                for k in ('cpu_seconds','wall_seconds')),'invalid preparation usage')
    inv=report['inventory']
    require(type(inv) is dict and set(inv)=={'files','weight_shards','weight_bytes','weight_hashes_observed','trusted_weight_reference_compared'},'inventory fields')
    require(inv['weight_hashes_observed'] is True and inv['trusted_weight_reference_compared'] is False,'observed inventory provenance')
    files=inv['files'];require(type(files) is dict and bool(files),'inventory files')
    require(all(type(n) is str and Path(n).name==n and n not in ('.','..') and _hash(h) for n,h in files.items()),'inventory names/hashes')
    require(all(files.get(n)==h for n,h in local.METADATA.items()),'metadata binding mismatch')
    shards=inv['weight_shards']
    require(type(shards) is list and len(shards)==11 and all(type(n) is str for n in shards)
            and len(set(shards))==11 and all(n in files and n.endswith('.safetensors') for n in shards),'eleven bound shards')
    require(type(inv['weight_bytes']) is int and inv['weight_bytes']>0,'weight size')
    template=report['template']
    require(type(template) is dict and set(template)=={'template_hash','reasoning_requested','reasoning_support_verified','probe_off_hash','probe_on_hash'},'template fields')
    require(template['template_hash']==local.TEMPLATE_HASH and template['reasoning_requested'] is True
            and template['reasoning_support_verified'] is True,'thinking template binding')
    require(all(_hash(template[k]) for k in ('probe_off_hash','probe_on_hash')),'template probe hashes')
    require(report['generation_tokens']=={'eos_token_id':[248046,248044],'pad_token_id':248044},'stop tokens')
    calls=report['initial_requests']
    require(type(calls) is list and len(calls)==3,'three initial request observations')
    for source,row in zip(SMOKE,calls):
        require(type(row) is dict and set(row)=={'source_id','payload_digest','rendered_ids_digest','input_tokens','output_reservation_tokens'},'initial request fields')
        require(row['source_id']==source and all(_hash(row[k]) for k in ('payload_digest','rendered_ids_digest')),'initial request binding')
        require(type(row['input_tokens']) is int and 0<row['input_tokens']<=10240
                and type(row['output_reservation_tokens']) is int and row['output_reservation_tokens']==6144,'request caps')
    return report


def freeze(root,receipt,report,statements_path):
    validate_verification(root,receipt,report)
    records=local.statement_records(statements_path,SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
    requests=[_request(row) for row in records]
    require([r['payload_digest'] for r in requests]==[r['payload_digest'] for r in report['initial_requests']],
            'verified payload differs from current statement/prompt')
    scope={'stage':'D1','source_ids':list(SMOKE),'pilot':configuration(root)['scope']['pilot'],
           'identities':configuration(root)['scope']['identities'],'runtime_implementation':runtime_identity(root),
           'model':settings(),'limits':limits(),'settings_accepted':True,'limits_accepted':True,
           'receipt':deepcopy(receipt),'verification':deepcopy(report),
           'source_access_permission':dict(local.SOURCE_PERMISSION),
           'statement_file_sha256':local.STATEMENTS_HASH,
           'policy':{'initial_per_source':1,'structural_corrections_per_source':1,'semantic_retries':0,
                     'transport_retries':0,'cache':'no_response_reuse','tools':[],
                     'dispatch_order':'frozen_source_order_initial_then_eligible_correction',
                     'ambiguous_attempt':'halt_entire_campaign','later_stages_enabled':False},
           'approval_scope':'D1_only_including_transmission_of_bound_statement_views'}
    return {'schema':'joint-d1-frozen-scope-v1','enabled':False,'scope':scope,'scope_digest':digest(scope),'approval':None}


def validate_frozen(root,manifest):
    require(type(manifest) is dict and set(manifest)=={'schema','enabled','scope','scope_digest','approval'},'frozen fields')
    require(manifest['schema']=='joint-d1-frozen-scope-v1' and manifest['enabled'] is False,'frozen disabled manifest')
    scope=manifest['scope'];require(type(scope) is dict,'scope object')
    require(manifest['scope_digest']==digest(scope),'scope hash changed')
    require(scope.get('stage')=='D1' and scope.get('source_ids')==list(SMOKE),'D1 source/stage binding')
    if scope.get('runtime_implementation')!=runtime_identity(root):
        from .joint_d1_launch import validate_parent_runtime
        validate_parent_runtime(root,manifest)
    base=configuration(root)['scope']
    require(scope.get('model')==settings() and scope.get('limits')==limits() and
            scope.get('pilot')==base['pilot'] and scope.get('identities')==base['identities'],'settings/prompt/capacity binding')
    validate_verification(root,scope['receipt'],scope['verification'])
    require(scope.get('settings_accepted') is True and scope.get('limits_accepted') is True,'confirmed choices required')
    require(scope.get('source_access_permission')==local.SOURCE_PERMISSION and
            scope.get('statement_file_sha256')==local.STATEMENTS_HASH,'source permission/hash')
    expected_policy={'initial_per_source':1,'structural_corrections_per_source':1,'semantic_retries':0,
                     'transport_retries':0,'cache':'no_response_reuse','tools':[],
                     'dispatch_order':'frozen_source_order_initial_then_eligible_correction',
                     'ambiguous_attempt':'halt_entire_campaign','later_stages_enabled':False}
    require(scope.get('policy')==expected_policy and scope.get('approval_scope')=='D1_only_including_transmission_of_bound_statement_views','dispatch/approval scope')
    require(set(scope)=={'stage','source_ids','pilot','identities','runtime_implementation','model','limits',
        'settings_accepted','limits_accepted','receipt','verification','source_access_permission',
        'statement_file_sha256','policy','approval_scope'},'scope fields')
    return scope


def approval_matches(root,manifest,receipt):
    validate_frozen(root,manifest)
    if type(receipt) is not dict or set(receipt)!={'schema','stage','decision','scope_digest','reviewer','reviewed_at','statement_transmission_authorized'}:return False
    return (receipt['schema']=='joint-d1-frozen-approval-v1' and receipt['stage']=='D1'
            and receipt['decision']=='approved' and receipt['scope_digest']==manifest['scope_digest']
            and receipt['statement_transmission_authorized'] is True
            and all(type(receipt[k]) is str and bool(receipt[k].strip()) for k in ('reviewer','reviewed_at')))


def review(root,manifest):
    scope=validate_frozen(root,manifest)
    approved=approval_matches(root,manifest,manifest['approval'])
    return {'status':'frozen_for_review_execution_disabled','scope_digest':manifest['scope_digest'],
            'source_ids':scope['source_ids'],'initial_requests':scope['verification']['initial_requests'],
            'model':scope['model'],'limits':scope['limits'],
            'approval_matches':approved,'blockers':([] if approved else ['exact_D1_execution_and_transmission_approval_pending'])+['live_dispatch_release_disabled'],
            'limitations':['observed_fit_only','weight_hashes_not_independently_authenticated','local_deployment_cost_not_measured'],
            'model_executed':False,'execution_allowed':False,'next_stage_authorized':False}


class BoundD1Session(JointQwenSession):
    """Durable dispatch: synthetic doubles or the exact approved D1 release."""
    def __init__(self,directory,scope,records,transport,*,manifest=None,root=None,started_at=None,authorization=None):
        require(type(transport) is QwenTransport,'Qwen transport required')
        self._authorized_live=False
        if authorization is not None:
            from .joint_d1_launch import validate_authorization
            require(validate_authorization(root,authorization)==scope,'authorized session scope')
            require(authorization['manifest']==manifest,'authorized session manifest')
            self._authorized_live=True
        if transport.evidence=='injected_offline_double':
            require(all(type(r) is dict and type(r.get('id')) is str and r['id'].startswith('mock:') for r in records),
                    'offline bound session requires synthetic source IDs')
        else:
            require((LIVE_RELEASED or self._authorized_live) and transport.evidence=='local_runtime_unqualified','bound session live transport disabled')
            require(manifest is not None and approval_matches(root,manifest,manifest['approval']),'exact live approval required')
            require(scope==manifest['scope'],'live scope binding')
            require(all(hashlib.sha256(r['problem'].encode('utf8')).hexdigest()==local.STATEMENT_HASHES[r['id']] for r in records),'live statement hashes')
        require([r['id'] for r in records]==scope['source_ids'] and len(records)==3,'scope source order')
        require(scope['model']==settings() and scope['limits']==limits(),'bound session settings/limits')
        requests=[_request(r) for r in records]
        self._initialize(directory,requests,transport,scope_binding=scope,started_at=started_at)
        self._check_transport()

    def _check_transport(self):
        require(type(self.transport) is QwenTransport and self.transport.binding==self.binding['transport'],'transport changed')
        require(self.transport.evidence=='injected_offline_double' or
                ((LIVE_RELEASED or self._authorized_live) and self.transport.evidence=='local_runtime_unqualified'),'live release disabled')
        for k,v in {'checkpoint':CHECKPOINT,'revision':REVISION,'context_limit':16384,
                    'output_cap':6144,'thinking':True,'do_sample':False}.items():
            require(self.transport.binding.get(k)==v,'bound model/settings mismatch')

    def _model_executed(self):
        return self.transport.evidence!='injected_offline_double'

    def _render_request(self,request):
        result=super()._render_request(request)
        if 'correction_prompt' not in request['payload']:
            source=request['payload']['source']['id']
            expected=next(r for r in self.binding['execution_scope']['verification']['initial_requests'] if r['source_id']==source)
            require(expected['payload_digest']==request['payload_digest'] and
                    expected['rendered_ids_digest']==digest(result['input_ids']) and
                    expected['input_tokens']==result['input_tokens'],'initial tokenization changed')
        return result

    def _totals(self,state):
        return {'actual_tokens':sum(a['actual_tokens'] or 0 for a in state['attempts']),
                'reserved_tokens':sum(a['reservation_tokens'] for a in state['attempts'] if a['actual_tokens'] is None),
                'attempts':len(state['attempts']),
                'model_calls_observed':sum('observation' in a for a in state['attempts']) if self._model_executed() else 0,
                'evidence':self.transport.evidence}

    def advance(self,source_id):
        state=self.snapshot()
        for earlier in self.binding['execution_scope']['source_ids']:
            if earlier==source_id:break
            previous=[a for a in state['attempts'] if a['source_id']==earlier]
            require(previous and (len(previous)==2 or previous[-1].get('review',{}).get('status')!='invalid'),
                    'frozen dispatch order')
        return super().advance(source_id)


def drive_session(session):
    """No automatic resume/retry or new backend creation. Report unrun rows too."""
    require(type(session) is BoundD1Session,'prepared bound session required')
    summaries=[];halted=False
    for source in session.binding['execution_scope']['source_ids']:
        if halted:
            summaries.append({'source_id':source,'status':'unrun'});continue
        try:
            first=session.advance(source)
            if first['state']!='completed':
                summaries.append({'source_id':source,'status':first['state']});halted=True;continue
            last=first
            if first['review']['status']=='invalid':last=session.advance(source)
            summaries.append({'source_id':source,'status':last['review']['status'] if last['state']=='completed' else last['state'],
                              'request_count':last['attempt']+1,'admitted':False})
            halted=last['state']!='completed'
        except Exception as exc:
            summaries.append({'source_id':source,'status':'stopped','error_type':type(exc).__name__})
            halted=True
    return {'schema':'joint-d1-prepared-orchestration-v1','sources':summaries,'halted':halted,
            'ledger':session.snapshot(),'model_executed':session.snapshot()['model_executed'],
            'execution_allowed':False,'next_stage_authorized':False}


def dispatch_live(root,manifest,statements_path,directory,*,authorization=None):
    """Allocated-job body; a generic approval receipt cannot open the code gates.

    The explicit authorization path validates the separate exact-scope release.
    The startup record forbids automatic repeat even when loading was interrupted.
    """
    if authorization is not None:
        from .joint_d1_launch import validate_authorization
        validate_authorization(root,authorization)
        require(authorization['manifest']==manifest,'dispatch authorization mismatch')
    else:
        require(LIVE_RELEASED,'D1 live dispatch release disabled; exact scope approval and release review required')
    scope=validate_frozen(root,manifest)
    require(approval_matches(root,manifest,manifest['approval']),'exact D1 approval required')
    from beyond_consensus.models.transformers_backend import require_allocation
    require_allocation()
    records=local.statement_records(statements_path,SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    startup=directory/'startup.json'
    started=time.time();cpu_start=time.process_time();wall_start=time.monotonic()
    with startup.open('x') as handle:
        json.dump({'scope_digest':manifest['scope_digest'],'started_at':started,
                   'state':'started_no_automatic_retry','allocation_wall_reservation_seconds':3600},handle)
        handle.flush();os.fsync(handle.fileno())
    fd=os.open(directory,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    # Hard process watchdog includes inventory recheck, loading and all generation.
    # A killed process leaves startup/reservations intact; never catch and replay it.
    watchdog=threading.Timer(scope['limits']['campaign_wall_seconds'],lambda:os.kill(os.getpid(),signal.SIGKILL))
    watchdog.daemon=True;watchdog.start()
    session=None
    try:
        report=scope['verification']
        lock={'checkpoint':CHECKPOINT,'revision':REVISION,'local_path':report['local_path'],
              'files':report['inventory']['files']}
        transport=open_local(lock,authorization=authorization) if authorization is not None else open_local(lock)
        require(transport.template==report['template'] and transport.tokens==report['generation_tokens'],
                'loaded template/stops differ from frozen verification')
        props=transport.torch.cuda.get_device_properties(0)
        require(props.total_memory>=80_000_000_000,'80GB-class GPU required')
        session=BoundD1Session(directory/'requests',scope,records,transport,
                               manifest=manifest,root=root,started_at=started,authorization=authorization)
        result=drive_session(session)
        result['stage_resources']={'cpu_seconds':time.process_time()-cpu_start,
                                   'wall_seconds':time.monotonic()-wall_start,
                                   'includes_inventory_loading_dispatch_and_validation':True}
        with (directory/'result.json').open('x') as handle:
            json.dump(result,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
        return result
    except Exception as exc:
        failure={'status':'dispatch_failed_no_retry','error_type':type(exc).__name__,
                 'scope_digest':manifest['scope_digest'],
                 'model_executed':False if session is None else session.snapshot()['model_executed'],
                 'sources':[{'source_id':s,'status':'unrun'} for s in scope['source_ids']] if session is None else None,
                 'ledger':session.snapshot() if session is not None else None,
                 'cpu_seconds':time.process_time()-cpu_start,'wall_seconds':time.monotonic()-wall_start,
                 'next_stage_authorized':False}
        with (directory/'failure.json').open('x') as handle:
            json.dump(failure,handle,indent=2);handle.write('\n');handle.flush();os.fsync(handle.fileno())
        raise
    finally:watchdog.cancel()
