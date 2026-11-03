"""Exact approved D1 release and shared-registry Slurm adapter; no general unlock."""
from copy import deepcopy
from datetime import datetime, timezone
import getpass
import os
from pathlib import Path
import re

from .model import digest
from .joint_schema import require
from . import joint_d1_release as release
from . import joint_d1_local as local
from beyond_consensus.experiments import cluster
from beyond_consensus.experiments.snapshot import create_snapshot, verify_snapshot, environment_inventory
from beyond_consensus.experiments.manifest import source_revision
from beyond_consensus.util import atomic_json, directory_lock, plain, read_json

APPROVED_SCOPE = '057793e3479c14cfa4f6ec3d5add628a53ce8fbfe8629bef17815d68079ca6ad'
PARENT_RUNTIME = {
  "src/bc_phase2/joint_d1_qwen.py": "2e4938f9ad13c557ba2a3963d1e82e7126efdfe9aaa3e0e50ae010c2b7576a89",
  "src/bc_phase2/joint_d1_readiness.py": "bc9441eacc78f8410c563b3ae034586b23815a0a58141dcbf4aed2ea1089f2f4",
  "src/bc_phase2/joint_pipeline_contracts.py": "4e845fbdffaba91b13d0cfebe7938ae6396d64e9dbda450dd099977ca5a1a246",
  "src/bc_phase2/joint_schema.py": "46b5e34ef858babd0f7723fcde46a55648ace3b273c0d2c6d5ffba6e300d040b",
  "src/bc_phase2/joint_core.py": "6924f669af73257f656de25881794852b395181b4ac62df9c53f544dfa3a82a3",
  "src/bc_phase2/model.py": "4268a30bd27c4b0d0781d7aade933d834b33a7bde1b2181a32c18cf61e21515d",
  "src/bc_phase2/planner_qwen.py": "9f8214d37f6e91d6c4f2439bc0082cace2ea8ceb2512ca76303735e118206d1a",
  "src/bc_phase2/planner_ledger.py": "a35c5d84dae80c779726344dcd6ac74ba937788ab5627762ea355d378df21ef7",
  "src/bc_phase2/joint_d1_local.py": "53f336c59dee6d26de26a40c7b3d67dec151668d7f7329ddb5d662b0837cfe23",
  "src/beyond_consensus/models/transformers_backend.py": "4fc3da401a23c7e45c0d0a40cf5cbd4bf9ac860a8c8f464acdbf9e38995362cd",
  "src/bc_phase2/joint_d1_release.py": "c6c6ee2708d75727008c9e86616649c06129d7abff7ad5ada924c1703ead4af5",
  "scripts/freeze_joint_d1_scope.py": "3dfff1b473b53daf609f4e6e280810e17aac20daeac0c1fd803db9d3bdca7f6f"
}

# Explicit, reviewed integration delta only. Scientific and token-rendering
# dependencies remain identical. The release envelope binds ALL current files.
CHANGED_PARENT_FILES = {'src/bc_phase2/joint_d1_release.py','src/bc_phase2/planner_qwen.py'}


def validate_parent_runtime(root, manifest):
    require(manifest.get('scope_digest') == APPROVED_SCOPE and
            digest(manifest.get('scope')) == APPROVED_SCOPE, 'unapproved parent scope')
    old = manifest['scope'].get('runtime_implementation')
    require(old == PARENT_RUNTIME, 'parent runtime differs from reviewed release')
    current = release.runtime_identity(root)
    require(all(current.get(p) == h for p,h in old.items() if p not in CHANGED_PARENT_FILES),
            'unreviewed parent dependency change')


def prepare(root, manifest, *, reviewer):
    """Record the user's explicit approval; never select or expand a new scope."""
    validate_parent_runtime(root, manifest)
    release.validate_frozen(root, manifest)
    require(manifest['approval'] is None, 'preserve previously recorded approval')
    require(type(reviewer) is str and bool(reviewer.strip()), 'reviewer required')
    approved = deepcopy(manifest)
    approved['approval'] = {'schema':'joint-d1-frozen-approval-v1','stage':'D1',
        'decision':'approved','scope_digest':APPROVED_SCOPE,'reviewer':reviewer,
        'reviewed_at':datetime.now(timezone.utc).isoformat(),
        'statement_transmission_authorized':True}
    value = {'schema':'joint-d1-scoped-release-v1','manifest':approved,
             'runtime_implementation':release.runtime_identity(root),
             'authorization_basis':'explicit_user_proceed_after_exact_D1_scope_review',
             'later_stages_enabled':False}
    value['release_digest'] = digest(value)
    validate_authorization(root,value)
    return value


def validate_authorization(root, value):
    require(type(value) is dict and set(value)=={'schema','manifest','runtime_implementation',
        'authorization_basis','later_stages_enabled','release_digest'}, 'release fields')
    require(value['schema']=='joint-d1-scoped-release-v1' and value['later_stages_enabled'] is False,
            'D1-only release')
    require(value['authorization_basis']=='explicit_user_proceed_after_exact_D1_scope_review','approval basis')
    require(value['release_digest']==digest({k:v for k,v in value.items() if k!='release_digest'}),
            'release digest changed')
    validate_parent_runtime(root,value['manifest'])
    require(value['runtime_implementation']==release.runtime_identity(root),'release runtime changed')
    require(release.approval_matches(root,value['manifest'],value['manifest']['approval']),
            'exact execution/transmission approval required')
    return value['manifest']['scope']


def summary(root, value):
    scope=validate_authorization(root,value)
    return {'status':'D1_SCOPED_RELEASE_PREPARED','scope_digest':APPROVED_SCOPE,
            'release_digest':value['release_digest'],'source_ids':scope['source_ids'],
            'limits':scope['limits'],'model':scope['model'],
            'approval_matches':True,'submitted':False,'model_executed':False,
            'D2_D6_enabled':False,'scheduler_and_allocation_checks_pending':True}


def arguments(config, snapshot, output):
    require(cluster.seconds(config.time)==3600 and config.memory_gb==128,'D1 allocation must be 1h/128GB')
    require(config.activation_script is None,'D1 uses explicit Python; activation script unsupported')
    argv=cluster.sbatch_arguments(config,snapshot,output,[0],1,mode='preflight')
    argv[-6:]=[str(snapshot/'experiments/run_joint_d1.sbatch'),str(snapshot),str(output),config.python]
    return argv


def submit(root, value, statements, config, *, dry_run=True):
    """Only a browser-terminal explicit submit calls Slurm; never called here."""
    require(not os.environ.get('SLURM_JOB_ID'),'no batch self-submission')
    validate_authorization(root,value)
    local.statement_records(statements,release.SMOKE,local.STATEMENTS_HASH,local.STATEMENT_HASHES)
    statements=Path(statements).resolve()
    output=Path(config.output_root)/('d1-'+APPROVED_SCOPE)
    registry=cluster.registry_root();state_path=registry/'registry.json'
    def action():
        state=read_json(state_path) if state_path.exists() else {'jobs':[]}
        cluster.guard(state)
        require(APPROVED_SCOPE not in state.get('d1_scopes',{}),'D1 scope already submitted/uncertain; no automatic repeat')
        require(not output.exists(),'D1 output exists; preserve evidence and reconcile before any action')
        cluster.validate_site(config)
        snapshot=Path(config.snapshot_root)/'SNAPSHOT_CREATED_AT_SUBMISSION'
        argv=arguments(config,snapshot,output)
        if dry_run:
            return {'dry_run':True,'argv':argv,'output':str(output),'registry':str(state_path),
                    'scope_digest':APPROVED_SCOPE,'submitted':False}
        require(Path(config.python).is_file(),'configured Python missing')
        manifest={'schema':'joint-d1-slurm-v1','source_revision':source_revision(root),
                  'release':value,'statement_path':str(statements)}
        report=value['manifest']['scope']['verification']
        lock={'checkpoint':release.CHECKPOINT,'revision':release.REVISION,
              'local_path':report['local_path'],'files':report['inventory']['files']}
        snapshot=create_snapshot(root,Path(config.snapshot_root),manifest,plain(config),lock)
        # Validate the committed archive, not merely the mutable checkout.
        validate_authorization(snapshot,value)
        (output/'logs').mkdir(parents=True,exist_ok=False)
        atomic_json(output/'manifest.json',manifest)
        argv=arguments(config,snapshot,output)
        cluster.command([argv[0],'--test-only',*argv[1:]])
        state['completed_jobs']=(state.get('completed_jobs',[])+state.get('jobs',[]))[-100:]
        state['jobs']=[]
        reservation={'scope_digest':APPROVED_SCOPE,'release_digest':value['release_digest'],
                     'snapshot':str(snapshot),'output':str(output),'state':'submission_uncertain'}
        state.setdefault('d1_scopes',{})[APPROVED_SCOPE]=reservation
        state['uncertain_submission']=dict(reservation)
        atomic_json(state_path,state)
        response=cluster.command(argv)
        job=response.split(';',1)[0]
        require(re.fullmatch(r'[0-9]+',job) is not None,'unknown job ID; preserve uncertain registry')
        reservation.update(job_id=job,state='submitted_no_retry')
        state['uncertain_submission']=None
        state['jobs'].append({'job_id':job,'manifest_hash':digest(manifest),'snapshot':str(snapshot),
            'output':str(output),'concurrency':1,'physical_gpus_per_job':1,'reserved_physical_gpus':1,'mode':'D1'})
        atomic_json(state_path,state)
        return {'job_id':job,'snapshot':str(snapshot),'output':str(output),
                'scope_digest':APPROVED_SCOPE,'release_digest':value['release_digest'],'submitted':True}
    if dry_run:return action()
    with directory_lock(registry/'.submission.lock'):return action()


def run_allocated(root, output):
    """Snapshot-only job entry; registry and environment verified before loading."""
    require(os.environ.get('SLURM_JOB_ID'),'allocated job required')
    marker=verify_snapshot(root)
    manifest=release.read_evidence(Path(root)/'resolved/manifest.json')
    require(manifest.get('schema')=='joint-d1-slurm-v1','D1 snapshot required')
    value=manifest['release'];validate_authorization(root,value)
    config=cluster.load_cluster(Path(root)/'resolved/cluster.json')
    expected=Path(config.output_root)/('d1-'+APPROVED_SCOPE)
    require(Path(output).resolve()==expected.resolve(),'job output binding')
    require(read_json(Path(output)/'manifest.json')==manifest,'output manifest changed')
    require(marker['manifest_hash']==digest(manifest),'snapshot manifest binding')
    job=os.environ.get('SLURM_ARRAY_JOB_ID',os.environ['SLURM_JOB_ID'])
    require(os.environ.get('SLURM_ARRAY_TASK_ID','0')=='0','only one array task')
    # Submission publishes the receipt under the same lock. A very fast job
    # must not read the transient uncertain record before sbatch returns.
    with directory_lock(cluster.registry_root()/'.submission.lock'):
        state=read_json(cluster.registry_root()/'registry.json')
    record=state.get('d1_scopes',{}).get(APPROVED_SCOPE,{})
    require(record.get('job_id')==job and record.get('state')=='submitted_no_retry' and
            record.get('release_digest')==value['release_digest'] and
            Path(record.get('snapshot','')).resolve()==Path(root).resolve() and
            Path(record.get('output','')).resolve()==Path(output).resolve(),'registered D1 job required')
    active=cluster.active_gpu_jobs()
    require(bool(active) and all(j.split('_')[0]==job and n==1 for j,n in active.items()),
            'exclusive one-GPU campaign required')
    require(environment_inventory(config.python)==read_json(Path(root)/'resolved/environment.json'),
            'allocated environment differs from snapshot')
    result=release.dispatch_live(root,value['manifest'],manifest['statement_path'],Path(output)/'execution',authorization=value)
    return {'output':str(output),'scope_digest':APPROVED_SCOPE,'halted':result['halted'],
            'sources':result['sources'],'model_executed':result['model_executed'],'D2_D6_enabled':False}
