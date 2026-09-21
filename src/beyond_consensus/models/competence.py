"""Fail-closed opt-in 27B prerequisites; no GPU imports or model execution."""
from pathlib import Path
import importlib.metadata
import sys
from ..util import BCError, digest, file_hash
from .action_schema import contract

CHECKPOINT = 'Qwen/Qwen3.5-27B'
REVISION = 'fc05daec18b0a78c049392ed2e771dde82bdf654'
# Nominal 80 GB devices may report less than 80 GiB. Reject 40/48 GB and MIG.
MIN_TOTAL_BYTES = 75 * 1024**3
MIN_FREE_BYTES = 70 * 1024**3
PACKAGES = ('torch', 'transformers', 'tokenizers', 'huggingface-hub', 'safetensors', 'xgrammar')


def hardware(torch):
    count = torch.cuda.device_count()
    if not torch.cuda.is_available() or count != 1:
        raise BCError('27B requires exactly one visible CUDA device; no fallback')
    name = torch.cuda.get_device_name(0)
    free, total = torch.cuda.mem_get_info(0)
    result = dict(visible_devices=count, name=name, total_bytes=total, free_bytes=free,
                  bf16=torch.cuda.is_bf16_supported(), cuda_runtime=torch.version.cuda,
                  minimum_total_bytes=MIN_TOTAL_BYTES, minimum_free_bytes=MIN_FREE_BYTES)
    if ('MIG' in name.upper() or not any(n in name.upper() for n in ('A100', 'H100'))
            or total < MIN_TOTAL_BYTES or free < MIN_FREE_BYTES or not result['bf16']):
        raise BCError('27B hardware blocked before loading; require full A100/H100 80-GB-class allocation: '+str(result))
    return result


def versions():
    return {p: importlib.metadata.version(p) for p in PACKAGES}


def qualification_key(lock, packages, context_limit=8192):
    if context_limit not in (8192, 16384):
        raise BCError("Unsupported qualification context")
    root = Path(__file__).resolve().parents[3]
    return digest({'checkpoint': lock['checkpoint'], 'revision': lock['revision'],
        'tokenizer_revision': lock['tokenizer_revision'], 'metadata': lock['metadata_hashes'],
        'packages': packages, 'python': list(sys.version_info[:3]), 'contract': contract(),
        'settings': {'thinking': True, 'output': 2048, 'total_context': context_limit},
        'implementation': {name: file_hash(root/name) for name in (
            'scripts/check_action_constraints.py',
            'src/beyond_consensus/models/constrained.py',
            'src/beyond_consensus/models/action_schema.py', 'src/beyond_consensus/models/transformers_backend.py')}})


def require_qualification(lock, packages, context_limit=8192):
    report = lock.get('decoder_qualification', {})
    if (report.get('status') != 'passed' or report.get('qualification_key') != qualification_key(lock, packages, context_limit)
            or report.get('model_executed') is not False or report.get('sql_executed') is not False):
        raise BCError('27B requires a current model-specific CPU qualification bound into a NEW model lock')
    return report


def placement(model):
    if getattr(model, 'is_quantized', False) or getattr(model, 'hf_device_map', None):
        raise BCError('27B quantization/device-map/offload is not this condition')
    counts = {}
    for _, value in list(model.named_parameters()) + list(model.named_buffers()):
        if str(value.device) != 'cuda:0':
            raise BCError('27B parameter/buffer is not on process-local cuda:0')
        dtype = str(value.dtype)
        counts[dtype] = counts.get(dtype, 0) + value.numel()
        if value.is_floating_point() and dtype not in ('torch.bfloat16', 'torch.float32'):
            raise BCError('Unexpected 27B floating dtype; no precision fallback')
    if not counts.get('torch.bfloat16'):
        raise BCError('No BF16 weights observed in requested BF16 condition')
    return {'parameter_and_buffer_elements_by_dtype': counts, 'device': 'cuda:0',
            'accumulation_dtype': 'not instrumented; native operator behavior retained'}
