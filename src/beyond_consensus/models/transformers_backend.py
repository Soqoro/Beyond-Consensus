"""One real backend. All GPU imports occur after explicit allocation checks."""

from __future__ import annotations

import importlib.metadata
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from ..config import ModelConfig
from ..util import BCError, file_hash, plain, read_json, digest
from .base import Generation
from .staging import resolve_model_config

GENERATION_POLICY = "tokenizer-turn-eos-v1"


def generation_tokens(tokenizer, generation_config):
    """Preserve model stop IDs and also stop at the staged tokenizer's turn end."""
    def valid(value):
        return type(value) is int and value >= 0

    turn_token = tokenizer.eos_token
    turn_id = tokenizer.eos_token_id
    if (not isinstance(turn_token, str) or not turn_token or not valid(turn_id)
            or turn_id == getattr(tokenizer, "unk_token_id", None)
            or tokenizer.convert_tokens_to_ids(turn_token) != turn_id
            or not isinstance(tokenizer.chat_template, str)
            or turn_token not in tokenizer.chat_template):
        raise BCError("Cannot verify tokenizer turn-end token against the staged chat template")
    configured = generation_config.eos_token_id
    eos = [] if configured is None else list(configured) if isinstance(configured, (list, tuple)) else [configured]
    if any(not valid(value) for value in eos):
        raise BCError("Invalid model generation EOS token IDs")
    eos = list(dict.fromkeys([*eos, turn_id]))
    pad = generation_config.pad_token_id
    if pad is None:
        pad = tokenizer.pad_token_id
    if pad is None:
        pad = turn_id
    if not valid(pad):
        raise BCError("Invalid generation padding token ID")
    return {"eos_token_id": eos, "pad_token_id": pad}


def require_allocation() -> None:
    if not os.environ.get("SLURM_JOB_ID"):
        raise BCError("Real inference/preflight requires a Slurm GPU allocation; no login-node model loading")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if not visible or visible in ("-1", "NoDevFiles"):
        raise BCError("Slurm did not assign CUDA_VISIBLE_DEVICES; request exactly one GPU")


def dependencies() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in
            ("torch", "transformers", "tokenizers", "huggingface-hub", "safetensors")}


def verify_thinking_template(tokenizer, enabled):
    """Validate the staged template, not an assumed model-family capability."""
    template = tokenizer.chat_template
    result = {"template_hash": digest(template), "reasoning_requested": enabled, "reasoning_support_verified": False}
    if not enabled:
        return result
    if not isinstance(template, str) or "enable_thinking" not in template:
        raise BCError("Reasoning mode unsupported: staged chat template has no enable_thinking switch")
    messages = [{"role": "user", "content": "Template capability probe"}]
    off = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    on = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=True)
    closing = tokenizer.convert_tokens_to_ids("</think>")
    if off == on or "<think>" not in on or closing is None or closing == getattr(tokenizer, "unk_token_id", None):
        raise BCError("Reasoning mode unsupported: template switch or reasoning delimiter could not be verified")
    result.update(reasoning_support_verified=True, probe_off_hash=digest(off), probe_on_hash=digest(on))
    return result


def stopping_reason(ids, eos, cap):
    eos_ids = eos if isinstance(eos, list) else [eos]
    return "eos" if ids and ids[-1] in eos_ids else "length_limit" if len(ids) >= cap else "other_or_unknown"


class TransformersBackend:
    def __init__(self, config: ModelConfig, lock_path: Path | None) -> None:
        require_allocation()
        if lock_path is None:
            raise BCError("Pass --model-lock from the explicit model staging step")
        locked = resolve_model_config(config, lock_path)
        if config != locked:
            raise BCError("Resolve checkpoint/tokenizer revisions into the experiment manifest before inference")
        lock = read_json(lock_path)
        for relative, expected in lock["metadata_hashes"].items():
            if file_hash(Path(lock["model_path"]) / relative) != expected:
                raise BCError("Staged model metadata changed")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            import torch
            from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
        except ImportError as exc:
            raise BCError("Pinned GPU dependencies are missing; install them once during setup") from exc
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise BCError("Expected exactly one process-visible CUDA device; no CPU or multi-GPU fallback")
        if config.dtype == "bfloat16" and not torch.cuda.is_bf16_supported():
            raise BCError("Assigned device does not support requested bfloat16; configure a new run explicitly")
        if not config.checkpoint.startswith("Qwen/Qwen3.5-"):
            raise BCError("Gemma-3 is a documented later validation target; its loader is not yet GPU validated")
        if importlib.metadata.version("transformers") != "5.3.0":
            raise BCError("Use reviewed transformers==5.3.0; a dependency change requires new validation")
        architecture = read_json(Path(lock["model_path"]) / "config.json").get("architectures")
        if architecture != ["Qwen3_5ForConditionalGeneration"]:
            raise BCError(f"Unexpected checkpoint architecture {architecture}; loader review required")
        if config.action_constraint == "sqlite-sql-text-v1":
            from ..runtime.sql_text import require_qualification as require_frontend
            require_frontend(lock)
            from ..runtime.sql_text import VERSION as parser_version
            if importlib.metadata.version("sqlglot") != parser_version:
                raise BCError("Pinned SQL parser missing or changed before model loading")
        from .competence import CHECKPOINT, hardware, require_qualification, versions
        candidate = config.checkpoint == CHECKPOINT
        hardware_before = hardware(torch) if candidate else None
        if candidate:
            require_qualification(lock, versions(), config.context_limit, config.action_constraint)
            if read_json(Path(lock['model_path'])/'config.json').get('quantization_config'):
                raise BCError('Quantized model metadata is not this BF16 condition')
            try:
                driver = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=10, check=True)
                hardware_before['driver_versions'] = sorted(set(driver.stdout.splitlines()))
            except (OSError, subprocess.SubprocessError):
                hardware_before['driver_versions'] = None
            for name, expected in lock['weight_hashes'].items():
                if file_hash(Path(lock['model_path'])/name) != expected:
                    raise BCError('27B staged weight integrity failed')
        load_start = time.monotonic()
        self.config, self.torch = config, torch
        self.tokenizer = AutoTokenizer.from_pretrained(lock["tokenizer_path"], local_files_only=True,
                                                       trust_remote_code=False)
        if not self.tokenizer.chat_template:
            raise BCError("Staged tokenizer has no official chat template")
        template_check = verify_thinking_template(self.tokenizer, config.thinking)
        self.model = Qwen3_5ForConditionalGeneration.from_pretrained(
            lock["model_path"], dtype=getattr(torch, config.dtype), local_files_only=True,
            trust_remote_code=False, attn_implementation="sdpa")
        self.generation_tokens = generation_tokens(self.tokenizer, self.model.generation_config)
        if candidate:
            qualified = lock['decoder_qualification']
            if (self.generation_tokens != qualified.get('effective_generation_tokens') or
                    template_check['template_hash'] != qualified.get('thinking_template', {}).get('template_hash')):
                raise BCError('Loaded tokenizer/template/stop configuration differs from CPU qualification')
        self.constraint = None
        if config.action_constraint != "none":
            from .constrained import ActionConstraint
            self.constraint = ActionConstraint(self.tokenizer, self.model.get_output_embeddings().weight.shape[0],
                                               self.generation_tokens["eos_token_id"], config.action_constraint)
        # cuda:0 is Slurm's process-local device. Never overwrite CUDA_VISIBLE_DEVICES.
        try:
            self.model.to(torch.device("cuda:0"))
        except torch.cuda.OutOfMemoryError as exc:
            raise BCError('GPU OOM loading model; no offload/quantization/cap fallback. '+str(hardware_before)) from exc
        self.model.eval()
        self.model.requires_grad_(False)
        self.runtime = {"dependencies": dependencies(), "checkpoint_revision": config.revision,
                        "tokenizer_revision": config.tokenizer_revision, "loader": type(self.model).__name__,
                        "model_path": lock["model_path"], "import_path": __file__,
                        "chat_template": template_check, "settings": plain(config),
                        "generation_tokens": {"policy": GENERATION_POLICY,
                            "configured_eos_token_id": self.model.generation_config.eos_token_id,
                            "tokenizer_eos_token_id": self.tokenizer.eos_token_id,
                            **self.generation_tokens},
                        "model_lock_hash": digest(lock), "slurm_job_id": os.environ["SLURM_JOB_ID"],
                        "model_lock": {k: lock.get(k) for k in ("schema", "checkpoint", "revision", "tokenizer_revision", "metadata_hashes", "status")},
                        "slurm_array_job_id": os.environ.get("SLURM_ARRAY_JOB_ID"),
                        "slurm_array_task_id": os.environ.get("SLURM_ARRAY_TASK_ID"),
                        "hardware": torch.cuda.get_device_name(0),
                        "compute_capability": list(torch.cuda.get_device_capability(0)),
                        "vram_total_bytes": torch.cuda.get_device_properties(0).total_memory,
                        "torch_cuda": torch.version.cuda,
                        "snapshot_id": Path(__file__).resolve().parents[3].name if (Path(__file__).resolve().parents[3]/"snapshot.json").exists() else None}
        if candidate:
            from .competence import placement
            self.runtime.update(hardware_before_load=hardware_before, placement=placement(self.model),
                load_wall_seconds=time.monotonic()-load_start, load_device_seconds=None,
                load_peak_allocated_bytes=torch.cuda.max_memory_allocated(0),
                load_peak_reserved_bytes=torch.cuda.max_memory_reserved(0),
                qualification_key=lock['decoder_qualification']['qualification_key'])
            if self.model.get_output_embeddings().weight.shape[0] != lock['decoder_qualification']['vocab_size']:
                raise BCError('Qualified vocabulary differs from loaded logits dimension')
        if self.constraint is not None:
            self.runtime["action_constraint"] = self.constraint.runtime

    def encode(self, messages: list[dict[str, str]]) -> Any:
        return self.tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
            return_tensors="pt", return_dict=True, enable_thinking=self.config.thinking)

    def count_input(self, messages: list[dict[str, str]]) -> int:
        return int(self.encode(messages)["input_ids"].shape[-1])

    def generate(self, messages: list[dict[str, str]], max_new_tokens: int, seed: int) -> Generation:
        torch = self.torch
        inputs = self.encode(messages).to(torch.device("cuda:0"))
        size = int(inputs["input_ids"].shape[-1])
        if size + max_new_tokens > self.config.context_limit:
            raise BCError("Context/generation limits exceeded; no implicit truncation")
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        options: dict[str, Any] = {"max_new_tokens": max_new_tokens, "do_sample": self.config.do_sample,
                                  "use_cache": True, **self.generation_tokens}
        if self.config.do_sample:
            options.update(temperature=self.config.temperature, top_p=self.config.top_p, top_k=self.config.top_k)
        processor = None
        setup_cpu = 0.0
        if self.config.action_constraint != "none":
            start_cpu = time.process_time()
            closing_id = self.tokenizer.convert_tokens_to_ids("</think>") if self.config.thinking else None
            processor = self.constraint.processor(size, closing_id)
            options["logits_processor"] = [processor]
            setup_cpu = time.process_time()-start_cpu
        wall_start = time.monotonic()
        candidate = self.config.checkpoint == "Qwen/Qwen3.5-27B"
        if candidate:
            options['return_dict_in_generate'] = True
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        with torch.inference_mode():
            try:
                outputs = self.model.generate(**inputs, **options)
            except torch.cuda.OutOfMemoryError as exc:
                raise BCError('GPU OOM during generation; no automatic cap/precision/device fallback; '
                    f'input={size}, cap={max_new_tokens}, allocated={torch.cuda.max_memory_allocated(0)}, '
                    f'reserved={torch.cuda.max_memory_reserved(0)}') from exc
        end.record()
        torch.cuda.synchronize()
        cache_details = {}
        if candidate:
            cache = getattr(outputs, 'past_key_values', None)
            try:
                cache_length = int(cache.get_seq_length()) if cache is not None else None
            except (AttributeError, TypeError, ValueError):
                cache_length = None
            cache_details = {'observed_cache_sequence_length': cache_length,
                             'state_dtypes': cache_dtypes(cache), 'prefill_seconds': None}
            outputs = outputs.sequences
        ids = outputs[0, size:].tolist()
        # All generated tokens (including reasoning, delimiters and EOS) remain charged.
        reasoning: int | None = 0
        answer_ids = ids
        if self.config.thinking:
            closing = self.tokenizer.convert_tokens_to_ids("</think>")
            if closing in ids:
                boundary = ids.index(closing) + 1
                reasoning, answer_ids = boundary, ids[boundary:]
            else:
                reasoning = None
        text = self.tokenizer.decode(answer_ids, skip_special_tokens=True).strip()
        eos = self.generation_tokens["eos_token_id"]
        stop = stopping_reason(ids, eos, max_new_tokens)
        constraint_details = {}
        if processor is not None:
            from .action_schema import validate_action, contract
            start_cpu = time.process_time()
            try:
                validate_action(text, self.config.action_constraint)
                complete = reasoning is not None
            except BCError:
                complete = False
            constraint_details = {"action_constraint": contract(self.config.action_constraint), "constraint_complete": complete,
                "constraint_mask_calls": processor.mask_calls,
                "constraint_cpu_seconds": setup_cpu+processor.cpu_seconds+time.process_time()-start_cpu}
        return Generation(text, len(ids), reasoning, start.elapsed_time(end)/1000,
            {**constraint_details, **cache_details, "generation_wall_seconds": time.monotonic()-wall_start,
             "finish_reason": stop, "rendered_input_ids_hash": digest(inputs["input_ids"][0].tolist()),
             "generation_policy": GENERATION_POLICY, "eos_token_id": list(eos),
             "pad_token_id": self.generation_tokens["pad_token_id"],
             "last_generated_token_id": ids[-1] if ids else None,
             "rendered_input_tokens": size, "reasoning_partition_known": reasoning is not None,
             "reasoning_and_answer_share_output_budget": True,
             "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
             "peak_reserved_bytes": torch.cuda.max_memory_reserved(0)})


def cache_dtypes(cache):
    """Bounded metadata-only traversal; never serialize tensor contents."""
    found, seen = set(), set()
    def visit(value, depth=0):
        if depth > 5 or id(value) in seen:
            return
        seen.add(id(value))
        if hasattr(value, 'dtype') and hasattr(value, 'shape'):
            found.add(str(value.dtype))
        elif isinstance(value, (list, tuple)):
            for item in value: visit(item, depth+1)
        elif isinstance(value, dict):
            for item in value.values(): visit(item, depth+1)
        elif value is not None and hasattr(value, '__dict__'):
            visit(vars(value), depth+1)
    visit(cache)
    return sorted(found) or None


def long_history(backend):
    """Public synthetic history; retain 2048 output slots under TOTAL 8192 cap."""
    messages = [{'role': 'system', 'content': 'Use exactly one JSON tool action per turn, no Markdown.'},
        {'role': 'user', 'content': 'Synthetic preflight. Inspect database fixture.'},
        {'role': 'assistant', 'content': '{"tool":"inspect_schema","database_id":"fixture"}'},
        {'role': 'user', 'content': ''}]
    suffix = '\nSynthetic tool result complete. Reply with one inspect_schema action for fixture.'
    low, high = 0, 16384
    limit = backend.config.context_limit-backend.config.max_new_tokens
    while low < high:
        mid = (low+high+1)//2
        messages[-1]['content'] = json.dumps({'tool': 'inspect_schema', 'result': {'synthetic_padding': 'synthetic datum ' * mid}, 'instruction': suffix})
        if backend.count_input(messages) <= limit: low = mid
        else: high = mid-1
    messages[-1]['content'] = json.dumps({'tool': 'inspect_schema', 'result': {'synthetic_padding': 'synthetic datum ' * low}, 'instruction': suffix})
    if not limit-32 <= backend.count_input(messages) <= limit:
        raise BCError('Synthetic long-context input did not reach the configured allowance')
    return messages


def preflight(config: ModelConfig, model_lock: Path) -> dict[str, Any]:
    if config.action_constraint == "sqlite-sql-text-v1":
        import importlib.metadata
        from ..runtime.sql_text import VERSION
        if importlib.metadata.version("sqlglot") != VERSION:
            raise BCError("Pinned SQL parser required before model loading")
    backend = TransformersBackend(config, model_lock)
    torch = backend.torch
    torch.cuda.reset_peak_memory_stats()
    prompt = ('Reply with one JSON action to inspect database fixture: tool inspect_schema, database_id fixture.'
              if config.action_constraint != "none" else 'Reply exactly with {"ready":true}.')
    result = backend.generate([{"role": "user", "content": prompt}],
                              config.max_new_tokens if config.thinking else min(64, config.max_new_tokens), 0)
    extra = {}
    if config.checkpoint == "Qwen/Qwen3.5-27B":
        extended = backend.generate(long_history(backend), config.max_new_tokens, 0)
        extra = {'long_context_generation': plain(extended), 'worst_case_fit_established': False,
                 'footprint_note': 'Actual reached input/output/cache lengths only; early EOS does not test full cap.'}
        def valid_probe(generation):
            try:
                action = json.loads(generation.text)
                return generation.diagnostics.get('constraint_complete') and action == {
                    'tool': 'inspect_schema', 'database_id': 'fixture'}
            except (ValueError, TypeError):
                return False
        extra['command_failed'] = not (valid_probe(result) and valid_probe(extended))
    if config.action_constraint == "sqlite-sql-text-v1":
        from ..runtime.sql_text import lower
        from ..runtime.sqlite_executor import execute
        from ..tasks.sqlite_compatibility import database
        import tempfile
        query_probe = backend.generate([{"role":"user", "content":
            'Synthetic qualification only. Return one JSON action: tool run_read_query, permitted_artifact_versions {}, select_sql a SQL string selecting id from entries ordered by id.'}], config.max_new_tokens, 0)
        try:
            action = json.loads(query_probe.text)
            if set(action) != {"tool","permitted_artifact_versions","select_sql"} or action["tool"] != "run_read_query" or action["permitted_artifact_versions"] != {}:
                raise ValueError("Invalid probe envelope")
            compiled = lower(action["select_sql"], ["entries","departments"])
            with tempfile.TemporaryDirectory(prefix="bc-sql-preflight-") as tmp:
                checked = execute(database(Path(tmp)/"synthetic.sqlite"), ["entries","departments"], [], [compiled["tree"]]) if compiled["status"] == "ok" else {"status":"not_executed"}
            passed = checked["status"] == "ok" and checked["outputs"][0]["columns"] == ["id"] and checked["outputs"][0]["rows"] == [[i] for i in range(1,6)]
            extra["sql_frontend_probe"] = {"generation":plain(query_probe), "compiler":{k:v for k,v in compiled.items() if k!="tree"}, "passed":passed}
        except (ValueError,KeyError,TypeError):
            passed = False
            extra["sql_frontend_probe"] = {"passed":False}
        extra["command_failed"] = extra.get("command_failed",False) or not passed
    props = torch.cuda.get_device_properties(0)
    free, total = torch.cuda.mem_get_info(0)
    try:
        driver = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=10, check=True)
        driver_versions = sorted(set(driver.stdout.splitlines()))
    except (OSError, subprocess.SubprocessError):
        driver_versions = None
    return {**extra, "status": "smoke_completed_review_output", "hardware": props.name,
            "compute_capability": [props.major, props.minor], "vram_total_bytes": total,
            "vram_free_bytes": free, "torch_cuda": torch.version.cuda,
            "driver_versions": driver_versions,
            "bfloat16_supported": torch.cuda.is_bf16_supported(), "device": "cuda:0",
            "slurm_job_id": os.environ["SLURM_JOB_ID"], "dtype": config.dtype,
            "context_limit": config.context_limit, "generation_limit": config.max_new_tokens,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(0),
            "settings": plain(config), "runtime": backend.runtime, "generation": plain(result)}
