"""One real backend. All GPU imports occur after explicit allocation checks."""

from __future__ import annotations

import importlib.metadata
import os
import subprocess
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
        # cuda:0 is Slurm's process-local device. Never overwrite CUDA_VISIBLE_DEVICES.
        self.model.to(torch.device("cuda:0"))
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
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        with torch.inference_mode():
            outputs = self.model.generate(**inputs, **options)
        end.record()
        torch.cuda.synchronize()
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
        return Generation(text, len(ids), reasoning, start.elapsed_time(end)/1000,
            {"finish_reason": stop, "rendered_input_ids_hash": digest(inputs["input_ids"][0].tolist()),
             "generation_policy": GENERATION_POLICY, "eos_token_id": list(eos),
             "pad_token_id": self.generation_tokens["pad_token_id"],
             "last_generated_token_id": ids[-1] if ids else None,
             "rendered_input_tokens": size, "reasoning_partition_known": reasoning is not None,
             "reasoning_and_answer_share_output_budget": True,
             "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
             "peak_reserved_bytes": torch.cuda.max_memory_reserved(0)})


def preflight(config: ModelConfig, model_lock: Path) -> dict[str, Any]:
    backend = TransformersBackend(config, model_lock)
    torch = backend.torch
    torch.cuda.reset_peak_memory_stats()
    result = backend.generate([{"role": "user", "content": 'Reply exactly with {"ready":true}.'}],
                              config.max_new_tokens if config.thinking else min(64, config.max_new_tokens), 0)
    props = torch.cuda.get_device_properties(0)
    free, total = torch.cuda.mem_get_info(0)
    try:
        driver = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=10, check=True)
        driver_versions = sorted(set(driver.stdout.splitlines()))
    except (OSError, subprocess.SubprocessError):
        driver_versions = None
    return {"status": "smoke_completed_review_output", "hardware": props.name,
            "compute_capability": [props.major, props.minor], "vram_total_bytes": total,
            "vram_free_bytes": free, "torch_cuda": torch.version.cuda,
            "driver_versions": driver_versions,
            "bfloat16_supported": torch.cuda.is_bf16_supported(), "device": "cuda:0",
            "slurm_job_id": os.environ["SLURM_JOB_ID"], "dtype": config.dtype,
            "context_limit": config.context_limit, "generation_limit": config.max_new_tokens,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(0),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(0),
            "settings": plain(config), "runtime": backend.runtime, "generation": plain(result)}
