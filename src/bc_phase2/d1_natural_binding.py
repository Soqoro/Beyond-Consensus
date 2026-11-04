"""Read-only scope binding for the natural screen; never approves or dispatches."""
from copy import deepcopy
import hashlib
from pathlib import Path
import re

from . import d1_natural_screen as pilot
from . import joint_d1_local as local
from .model import digest
from .joint_schema import require


def sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def bind(verification, inventory_report, cluster_config, partition_record):
    """Bind existing receipts, not source text. Historical inventory is rechecked at load."""
    v = verification
    require(v.get('status') == 'three_statement_requests_tokenized_no_model', 'three-source tokenization required')
    require(v.get('model_executed') is False and v.get('execution_allowed') is False, 'offline evidence required')
    require(v.get('checkpoint') == pilot.CHECKPOINT and v.get('revision') == pilot.REVISION, 'pinned model')
    require(v.get('interface_implementation') == pilot.implementation(), 'screen implementation changed')
    require(v.get('prompt_hash') == digest(pilot.PROMPT) and v.get('schema_hash') == digest(pilot.response_schema()), 'prompt/schema changed')
    require(v.get('statements_file_sha256') == local.STATEMENTS_HASH, 'statement file hash')
    statement_path = Path(v.get('statements_file', ''))
    require(statement_path.is_absolute() and statement_path.parent == Path(pilot.disabled_manifest()['scope']['source_package']['path']), 'extracted source location')
    require(all(v.get('files', {}).get(name, {}).get('sha256') == local.METADATA[name]
                for name in ('config.json', 'tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja')), 'metadata hashes')
    template = v.get('template_check', {})
    switch = template.get('on_off_switch', {})
    require(template.get('enable_thinking') is False and template.get('template_hash') == local.TEMPLATE_HASH
            and switch.get('reasoning_support_verified') is True
            and sha(switch.get('probe_on_hash')) and sha(switch.get('probe_off_hash'))
            and switch['probe_on_hash'] != switch['probe_off_hash'], 'non-thinking support')
    rows = v.get('real_source_counts')
    require(type(rows) is list and [r.get('source_id') for r in rows] == list(pilot.SMOKE), 'exact ordered sources')
    for row in rows:
        count = row.get('input_tokens')
        require(type(count) is int and 0 < count <= pilot.CONTEXT-pilot.OUTPUT, 'input fit')
        require(row.get('reserved_tokens') == count+pilot.OUTPUT and v.get('output_reservation_tokens') == pilot.OUTPUT, 'output ceiling')
        require(row.get('statement_sha256') == local.STATEMENT_HASHES[row['source_id']]
                and sha(row.get('payload_digest')) and sha(row.get('rendered_ids_digest')), 'request binding')
    old = inventory_report
    require(old.get('schema') == 'joint-d1-local-verification-v1'
            and old.get('checkpoint') == pilot.CHECKPOINT and old.get('revision') == pilot.REVISION, 'existing inventory model')
    require(old.get('source_ids') == list(pilot.SMOKE) and old.get('statements_file_sha256') == local.STATEMENTS_HASH, 'inventory source binding')
    inventory = old.get('inventory', {})
    files = inventory.get('files', {})
    require(type(files) is dict and files and all(Path(k).name == k and sha(h) for k,h in files.items()), 'inventory hashes')
    require(all(files.get(k) == h for k,h in local.METADATA.items()), 'inventory metadata')
    shards = inventory.get('weight_shards')
    require(type(shards) is list and len(shards) == 11 and len(set(shards)) == 11
            and all(s.endswith('.safetensors') and s in files for s in shards), 'eleven pinned weight shards')
    require(Path(old.get('local_path', '')).is_absolute() and Path(old['local_path']).name == pilot.REVISION, 'snapshot path')
    require(old.get('generation_tokens') == {'eos_token_id':[248046,248044], 'pad_token_id':248044}, 'stop tokens')
    from beyond_consensus.experiments.cluster import ClusterConfig, seconds
    require(type(cluster_config) is dict, 'cluster object')
    config = ClusterConfig(**cluster_config)
    require(config.partition == 'NA100q' and seconds(config.time) == 3600 and config.memory_gb == 128
            and config.activation_script is None, 'reviewed NA100q one-hour/128GB resources only')
    require(type(partition_record) is str, 'partition evidence')
    fields = dict(re.findall(r'(\w+)=([^\s]+)', partition_record))
    require(fields.get('PartitionName') == config.partition and fields.get('State') == 'UP'
            and fields.get('Nodes') == 'node01', 'partition/node evidence')
    manifest = pilot.disabled_manifest()
    scope = manifest['scope']
    scope['source_package'].update(path=str(statement_path), hash_evidence='verified_statement_only_receipt')
    scope['model'].update(current_inventory=deepcopy(inventory), local_path=old['local_path'],
                          generation_tokens=deepcopy(old['generation_tokens']),
                          non_thinking_verification=deepcopy(template))
    scope['initial_token_counts'] = {r['source_id']:r['input_tokens'] for r in rows}
    scope['rendered_request_hashes'] = {r['source_id']:r['rendered_ids_digest'] for r in rows}
    scope['verified_requests'] = deepcopy(rows)
    scope['resources']['partition'] = config.partition
    scope['cluster'] = deepcopy(cluster_config)
    scope['evidence'] = {'verification_digest':digest(v), 'historical_inventory_digest':digest(old),
                         'partition_record':partition_record, 'inventory_recheck_before_load':True,
                         'gpu_vram_check_before_load':True, 'scheduler_allocation_tested':False}
    scope['binding_implementation'] = identity()
    manifest.update(schema='d1-natural-screen-bound-disabled-v1', scope_digest=digest(scope),
                    scope_complete=True, approval=None, execution_allowed=False,
                    launch_bridge='explicit_receipt_required',
                    binding_inputs={'verification':deepcopy(v), 'inventory_report':deepcopy(old),
                                    'cluster_config':deepcopy(cluster_config), 'partition_record':partition_record})
    return manifest


def identity():
    root = Path(__file__).resolve().parents[2]
    names = ['src/bc_phase2/d1_natural_binding.py', 'scripts/bind_d1_natural_screen.py',
             'src/bc_phase2/joint_d1_local.py', 'src/beyond_consensus/experiments/cluster.py',
             'src/bc_phase2/d1_natural_launch.py', 'scripts/launch_d1_natural.py',
             'experiments/run_d1_natural.sbatch', 'src/beyond_consensus/experiments/snapshot.py',
             'src/beyond_consensus/util.py']
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in names}


def review(manifest):
    require(manifest.get('schema') == 'd1-natural-screen-bound-disabled-v1'
            and manifest.get('scope_digest') == digest(manifest.get('scope')), 'bound manifest digest')
    require(manifest.get('approval') is None and manifest.get('execution_allowed') is False, 'disabled only')
    scope = manifest['scope']
    require(scope.get('implementation') == pilot.implementation() and scope.get('binding_implementation') == identity(), 'source changed')
    return {'status':'bound_for_review_not_dispatchable', 'scope_digest':manifest['scope_digest'],
            'initial_requests':scope['verified_requests'], 'resources':scope['resources'],
            'observed_total_reservation_tokens':sum(r['reserved_tokens'] for r in scope['verified_requests']),
            'remaining':['exact_source_transmission_and_GPU_approval'],
            'runtime_checks':['full_inventory_recheck','source_and_rendered_request_recheck',
                              'one_visible_GPU_at_least_80000000000_bytes_before_loading',
                              'shared_registry_and_allocated_scheduler_checks'],
            'approval_template':{'schema':'D1-natural-screen-v1-approval', 'decision':'pending',
                                 'scope_digest':manifest['scope_digest'], 'reviewer':None, 'reviewed_at':None,
                                 'statement_transmission_authorized':False, 'GPU_spending_authorized':False},
            'model_executed':False,'execution_allowed':False,'D2_D6_enabled':False}
