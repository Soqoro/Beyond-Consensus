"""Matched native configuration and read-only comparison, no inference."""
from copy import deepcopy
from collections import Counter
from pathlib import Path
from ..config import from_dict
from ..util import BCError, digest, read_json, atomic_json

BASELINE = '13edf617e4e897fd76a83fc800acc1d51934bff720e02161a5c9f152fa9f5981'
TREE = 'sqlite-json-schema-v1'
TEXT = 'sqlite-sql-text-v1'

# Audited historical worker emits generic restricted-action errors for SQL failures.
# Match the complete provenance tuple, never just a commit or an absent field.
LEGACY_FEEDBACK = {
    (BASELINE,
     '6e650d6468dd3b03ebca19a40c5a08c50a61e8db:d2ad7fc02b2fad1779809dbbfa97d17e64e5da7542185ee391db4a8618e571cd',
     '8f306961f925d8082caf028743201e7c562d773aa487ebf1fdad4b0657d4a93b'): {
        'field': 'sqlite_error_feedback', 'value': 'generic',
        'basis': 'audited_historical_worker_behavior',
        'worker_path': 'src/beyond_consensus/agents/worker.py',
        'worker_sha256': '40f39fd854f9287c8d26fa51ea845f94ec6406a1c86a48969cb9d006c460ad85',
    },
}


def resolve_baseline_config(baseline):
    """Resolve only a reviewed legacy omission; never mutate historical input."""
    config = deepcopy(baseline['config'])
    if digest(config) != baseline.get('config_hash'):
        raise BCError('Historical config hash mismatch')
    if 'sqlite_error_feedback' in config:
        return config, []
    key = tuple(baseline.get(k) for k in ('experiment_id', 'source_revision', 'config_hash'))
    evidence = LEGACY_FEEDBACK.get(key)
    if evidence is None:
        raise BCError('Missing resolved native setting: sqlite_error_feedback; unreviewed historical provenance')
    config['sqlite_error_feedback'] = evidence['value']
    return config, [{**evidence, 'source_revision': key[1], 'historical_config_hash': key[2]}]


def prepare(baseline_path, renewed_data, output):
    from ..tasks.data_manifest import validate_data
    baseline = read_json(baseline_path)
    if baseline.get('experiment_id') != BASELINE or digest(baseline['config']) != baseline.get('config_hash'):
        raise BCError('Supply the actual resolved latest native manifest, with matching config hash')
    config, resolutions = resolve_baseline_config(baseline)
    # Explicit presence: no default budget/feedback/seed inference from summaries.
    for key in ('budget','model','seeds','max_actions','malformed_retries','observation_limit','sqlite_error_feedback'):
        if key not in config:
            raise BCError('Missing resolved native setting: '+key)
    from ..config import ModelConfig, BudgetConfig
    for key, fields in [('model',ModelConfig.__dataclass_fields__), ('budget',BudgetConfig.__dataclass_fields__)]:
        if not isinstance(config[key],dict) or set(fields)-set(config[key]):
            raise BCError('Missing resolved native '+key+' fields; defaults cannot establish a match')
    if (config['model']['action_constraint'] != TREE or config['model']['context_limit'] != 16384
            or config['max_actions'] != 24 or config['task_kind'] != 'sqlite_native'):
        raise BCError('Not the recorded latest native condition')
    tasks = validate_data(Path(renewed_data))
    if {t.id for t in tasks} != {'solar_2','solar_M_3'}:
        raise BCError('Exactly the two renewed individual solar tasks are required')
    old = {t['id']:t for t in baseline['tasks']}
    for task in tasks:
        prior=old.get(task.id,{})
        if prior.get('sources') != task.sources or prior.get('specification') != task.specification or prior.get('required_outputs') != list(task.required_outputs):
            raise BCError('Renewal changed worker task contracts')
        # Runtime approval may change, task/harness/reference contents may not.
        for key in ('harness','evaluation','adaptation','scorer','tool_policy','access_regime','upstream_commit','dataset_revision'):
            if prior['metadata'].get(key) != task.metadata.get(key):
                raise BCError('Renewal changed task/scorer inputs: '+key)
    output=Path(output)
    if output.exists():
        raise BCError('Use a fresh paired-interface directory')
    configs=[]
    for label,mode in [('tree',TREE),('text',TEXT)]:
        c=deepcopy(config);c['name']='native-interface-'+label
        c['model']['action_constraint']=mode
        c['data_manifest']=str(Path(renewed_data).resolve())
        from_dict(c)
        configs.append((label,c))
    output.mkdir(parents=True)
    for label,c in configs:
        atomic_json(output/(label+'.json'),c)
    report={'schema':'bc-interface-plan-v1','baseline_experiment':BASELINE,
        'baseline_manifest_hash':digest(baseline),'planned_episodes':4,'executed':0,
        'arms':['tree','text'],'frozen_settings':config,
        'historical_config_hash':baseline['config_hash'],
        'resolved_config_hash':digest(config),'historical_setting_resolutions':resolutions,
        'treatment_fields':['name','model.action_constraint','necessary query syntax documentation',
                            'decoder schema/qualification','SQL parser CPU allowance charged only when invoked'],
        'shared_changed_field':'renewed data_manifest approval path',
        'feedback':config['sqlite_error_feedback'],'native_group_count':1,
        'historical_control_reused':False,'policy_campaign_enabled':False}
    atomic_json(output/'comparison-plan.json',report)
    return report


def compare(tree_root,text_root):
    from ..experiments.manifest import validate_manifest
    from ..evaluation.aggregate import aggregate
    from .competence import audit
    roots=[Path(tree_root),Path(text_root)]
    manifests=[read_json(p/'manifest.json') for p in roots]
    normalized=[]
    for m,mode in zip(manifests,(TREE,TEXT)):
        cfg=validate_manifest(m)
        if cfg.task_kind!='sqlite_native' or cfg.model.action_constraint!=mode or cfg.max_actions!=24 or cfg.model.context_limit!=16384:
            raise BCError('Expected matched native tree/text conditions')
        c=deepcopy(m['config']);c.pop('name');c['model'].pop('action_constraint');normalized.append(c)
    if normalized[0]!=normalized[1] or any(manifests[0][k]!=manifests[1][k] for k in ('tasks','source_revision','data_regime')):
        raise BCError('Unmatched native interface conditions')
    reports=[]
    for root,m in zip(roots,manifests):
        summary=aggregate(m,root)
        details=audit(root)
        compiler=[]
        for ep in m['episodes']:
            path=root/'episodes'/ep['episode_id']/'checkpoint.json'
            state=read_json(path) if path.exists() else {}
            events=state.get('store',{}).get('events',[])
            entries=state.get('ledger',{}).get('entries',[])
            compiler.append({'task':ep['task_id'],
                'compiler_statuses':dict(Counter(e['status'] for e in events if e.get('type')=='sql_compilation')),
                'compiler_charged_work':sum(e.get('work',0) for e in entries if e.get('kind')=='sql_compilation'),
                'compiler_calls':sum(e.get('type')=='sql_compilation' for e in events),
                'semantic_formula_or_join_diagnosis':'unknown_without_separate_private_offline_review'})
        reports.append({'experiment_id':m['experiment_id'],'aggregate':summary,'competence':details,'compiler':compiler})
    return {'schema':'bc-interface-comparison-v1','model_executed':False,'sql_executed':False,
            'reports':reports,'matched_recorded_fields':True,'confirmatory':False,
            'interpretation':'Two repeatedly inspected tasks in one database; reviewed native adaptation only.'}


def reference_frontend(data_path):
    """Evaluator-side representability only; no reference text in the report."""
    from ..tasks.data_manifest import validate_data
    from ..runtime.sqlite_executor import compile_select
    from ..runtime.sql_text import lower, contract
    tasks=validate_data(Path(data_path))
    reports=[]
    for task in tasks:
        evaluations = task.metadata.get('evaluation', {})
        if not isinstance(evaluations, dict) or set(evaluations) != set(task.required_outputs) or not task.required_outputs:
            reports.append({'task': task.id, 'unit': None, 'status': 'blocked_reference_coverage'})
            continue
        for unit in task.required_outputs:
            evaluation = evaluations[unit]
            if not isinstance(evaluation, dict):
                reports.append({'task': task.id, 'unit': unit, 'status': 'blocked_reference_shape'})
                continue
            artifact=evaluation.get('artifact',{})
            try:
                objects=set(task.metadata['harness']['tables']) | set(artifact.get('bindings',{}))
                text,_=compile_select(artifact['select'],objects)
                lowered=lower(text,objects)
                equivalent=(lowered['status']=='ok' and compile_select(lowered['tree'],objects)[0]==text)
                status='representable' if equivalent else 'blocked_expressivity_or_serialization'
            except (BCError,ValueError,KeyError,TypeError):
                status='blocked_reference_shape'
            reports.append({'task':task.id,'unit':unit,'status':status})
    return {'schema':'bc-reference-frontend-v1','status':'passed' if reports and all(r['status']=='representable' for r in reports) else 'blocked',
        'data_manifest_hash':digest(read_json(data_path)), 'compiler':contract(), 'reports':reports,
        'model_executed':False,'sql_executed':False,'reference_text_exported':False,
        'meaning':'Exact existing-IR SQL serialization round trip; not worker competence or upstream scorer parity.'}
