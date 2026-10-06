"""Optional bridge to the existing frozen backend; no model loading on import."""
from dataclasses import asdict
from pathlib import Path
from ..config import ModelConfig
from ..util import file_hash, read_json, BCError
from .staging import resolve_model_config


def binding(config_path, lock_path, pool, execution_contract="adaptive_legacy"):
    """Resolve existing staged metadata, never download or infer a revision."""
    data=read_json(Path(config_path));settings=data.get('model',data)
    config=resolve_model_config(ModelConfig(**settings),Path(lock_path))
    grammar=(f'reporecourse-plan-scoped-v1-pool-{pool}' if execution_contract=='plan_scoped_v1' else f'reporecourse-plan-v2-pool-{pool}')
    if (config.checkpoint!='Qwen/Qwen3.5-27B' or config.dtype!='bfloat16'
            or config.action_constraint!=grammar):
        raise BCError('Use a pool-bound Qwen3.5-27B BF16 planner configuration and qualified lock')
    return {'adapter':'existing-transformers-backend','settings':asdict(config),
            'model_lock_sha256':file_hash(Path(lock_path))}


def generate(request, public, config_path, lock_path):
    """User-triggered allocation only. Task execution has separate v2 gates."""
    from reporecourse.v2 import PromptedPlanner, verify_record
    verify_record(request,'request_id')
    resolved=binding(config_path,lock_path,request['config']['pool_size'],request['config'].get('execution_contract','adaptive_legacy'))
    if resolved!=request['model_binding']:raise BCError('Planner binding changed after request freezing')
    if request['config'].get('protocol')=='rr-open-planning-v1':
        raise BCError('Open planning backend binding prepared; shared-registry GPU qualification and explicit engineering approval pending')
    from .transformers_backend import TransformersBackend
    config=ModelConfig(**resolved['settings'])
    # Enforces Slurm, exactly one visible GPU, 80-GB-class hardware, local pinned
    # weights, tokenizer, pool-specific grammar approval, no offload/fallback.
    backend=TransformersBackend(config,Path(lock_path))
    return PromptedPlanner(backend,config.max_new_tokens).run(request,public)
