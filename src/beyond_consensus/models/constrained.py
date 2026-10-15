"""Optional XGrammar adapter; importing this module needs only the stdlib.

Reasoning is unrestricted. One fresh matcher constrains the final action after
its verified closing token. No forced reasoning terminator, repair or fallback.
"""
from __future__ import annotations

import importlib.metadata
import time
import sys

from .action_schema import decoder_schema, contract, XGRAMMAR_VERSION, DECODER_CPU_SECONDS
from ..util import BCError


class ReasoningGate:
    """Single-sequence HF processor with a generated-suffix-only boundary."""
    def __init__(self, inner, prompt_length, closing_id, *, clock=time.process_time):
        self.inner, self.prompt_length, self.closing_id = inner, prompt_length, closing_id
        self.cursor = prompt_length
        self.next_length = prompt_length
        self.active = closing_id is None
        self.clock = clock
        self.cpu_seconds = 0.0
        self.mask_calls = 0

    def __call__(self, input_ids, scores):
        start = self.clock()
        try:
            if input_ids.shape[0] != 1 or input_ids.shape[1] != self.next_length:
                raise BCError("Constrained decoding requires one append-only sequence")
            self.next_length += 1
            if self.cpu_seconds >= DECODER_CPU_SECONDS:
                raise BCError("Constrained decoder CPU allowance exhausted")
            if not self.active:
                new = input_ids[0, self.cursor:].tolist()
                self.active = self.closing_id in new
                self.cursor = input_ids.shape[1]
            if self.active:
                self.mask_calls += 1
                return self.inner(input_ids, scores)
            return scores
        finally:
            self.cpu_seconds += max(0.0, self.clock()-start)
            if self.cpu_seconds > DECODER_CPU_SECONDS and sys.exc_info()[0] is None:
                raise BCError("Constrained decoder CPU allowance exhausted")


def load_xgrammar():
    try:
        version = importlib.metadata.version("xgrammar")
        if version != XGRAMMAR_VERSION:
            raise BCError(f"Constrained decoding requires xgrammar=={XGRAMMAR_VERSION}")
        import xgrammar as xgr
        from xgrammar.contrib.hf import LogitsProcessor
    except (ImportError, importlib.metadata.PackageNotFoundError) as exc:
        raise BCError(f"Install optional xgrammar=={XGRAMMAR_VERSION}; unconstrained fallback is forbidden") from exc
    return xgr, LogitsProcessor


class ActionConstraint:
    def __init__(self, tokenizer, vocab_size, eos_ids, mode="sqlite-json-schema-v1", *, public_task=None, terminal_ids=None):
        start = time.process_time()
        self.xgr, self.processor_class = load_xgrammar()
        info = self.xgr.TokenizerInfo.from_huggingface(tokenizer, vocab_size=vocab_size,
                                                      stop_token_ids=eos_ids)
        compiler = self.xgr.GrammarCompiler(info, max_threads=1, cache_enabled=False)
        # Declared envelope order does not guarantee arbitrary nested-key uniqueness.
        schema=decoder_schema(mode)
        if terminal_ids is not None:
            from reporecourse.action_schema import schema_v2, RELIABLE_MODES
            if mode not in RELIABLE_MODES or '-plan-' not in mode or not public_task:raise BCError('Invalid public grammar binding')
            schema=schema_v2(mode,terminal_ids)
        from .unique_keys import MODE as UNIQUE_MODE
        self.unique_vocab = info.decoded_vocab if mode == UNIQUE_MODE else None
        if mode == UNIQUE_MODE and info.add_prefix_space:
            raise BCError('Unique-key decoding requires no implicit prefix space')
        self.stop_ids = eos_ids
        self.compiled = compiler.compile_json_schema(schema, any_whitespace=True,
                                                     max_whitespace_cnt=2, strict_mode=True)
        self.runtime = {**contract(mode), "vocab_size": vocab_size, "stop_token_ids": list(eos_ids),
                        "static_setup_cpu_seconds": time.process_time()-start}

        if terminal_ids is not None:
            from ..util import digest
            self.runtime['public_grammar_binding']=dict(task_id=public_task,terminal_ids=list(terminal_ids),schema_sha256=digest(schema),cache_key=digest([mode,public_task,list(terminal_ids),schema]))

    def processor(self, prompt_length, closing_id, trace=None):
        inner = self.processor_class(self.compiled)
        if trace is not None:
            from .decoder_trace import ObservedProcessor
            inner = ObservedProcessor(inner,trace,self.runtime['vocab_size'],stop_ids=self.stop_ids)
        if self.unique_vocab is not None:
            from .unique_keys import UniqueKeyProcessor
            inner = UniqueKeyProcessor(inner, self.unique_vocab, self.stop_ids, trace=trace)
        return ReasoningGate(inner, prompt_length, closing_id)
