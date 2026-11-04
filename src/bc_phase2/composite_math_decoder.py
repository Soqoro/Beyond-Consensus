"""Opt-in flat task-artifact grammar. Syntax constraints are not mathematical grading."""
import time
from . import composite_math as recipe
from .d1_natural_screen import NaturalTransport
from .model import digest
from .joint_schema import require
from beyond_consensus.models.constrained import load_xgrammar,ReasoningGate
from beyond_consensus.models.action_schema import DECODER_CPU_SECONDS


def schema(task):
    return {'type':'object','properties':{k:{'type':'string','minLength':1} for k in task['fields']},
            'required':list(task['fields']),'additionalProperties':False}


class InjectProcessor:
    """Forward generation unchanged except the approved processor; no retry/fallback."""
    def __init__(self,model,processor):self.model,self.processor=model,processor
    def generate(self,**kwargs):
        require('logits_processor' not in kwargs,'unexpected processor override')
        return self.model.generate(**kwargs,logits_processor=[self.processor])


class TaskTransport(NaturalTransport):
    def __init__(self,tokenizer,model,torch):
        super().__init__(tokenizer,model,torch)
        self.compiled={}
        self.binding.update(decoder='task-fields-xgrammar-v1',xgrammar_version='0.1.32',
                            schema_hashes={t['id']:digest(schema(t)) for t in recipe.TASKS},
                            decoder_cpu_seconds_per_call=DECODER_CPU_SECONDS)
    def render(self,req):
        task=next(t for t in recipe.TASKS if t['id']==req['payload']['task_id'])
        require(req['payload']['required_string_fields']==task['fields'],'task output contract changed')
        rendered=super().render(req);rendered['decoder_task_id']=task['id'];return rendered
    def generate(self,rendered):
        start=time.process_time();task=next(t for t in recipe.TASKS if t['id']==rendered['decoder_task_id'])
        original=self.model
        if task['id'] not in self.compiled:
            xgr,processor_class=load_xgrammar()
            size=original.get_output_embeddings().weight.shape[0]
            info=xgr.TokenizerInfo.from_huggingface(self.tokenizer,vocab_size=size,stop_token_ids=self.tokens['eos_token_id'])
            compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
            grammar=compiler.compile_json_schema(schema(task),any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
            self.compiled[task['id']]=(grammar,processor_class)
        grammar,processor_class=self.compiled[task['id']]
        # New matching state on every physical call, including every replay.
        processor=ReasoningGate(processor_class(grammar),len(rendered['input_ids']),None)
        processor.cpu_seconds=time.process_time()-start
        require(processor.cpu_seconds<DECODER_CPU_SECONDS,'decoder setup CPU limit')
        self.model=InjectProcessor(original,processor)
        try:
            observed=super().generate(rendered)
            observed['decoder']={'schema_hash':digest(schema(task)),'mask_calls':processor.mask_calls,
                                 'cpu_seconds':processor.cpu_seconds,'fresh_matcher':True,'qualification':'unqualified_real_worker_interface'}
            return observed
        finally:self.model=original


def qualify(snapshot):
    """Five fixed CPU grammar controls; local tokenizer only, no weights or statements."""
    import json
    from pathlib import Path
    from . import joint_d1_local as local
    from . import composite_math_launch as launch
    from .d1_natural_screen import verify_non_thinking
    root=Path(snapshot)
    require(all(local.file_hash(root/name)==h for name,h in local.METADATA.items()),'pinned tokenizer/config metadata')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(root),local_files_only=True,trust_remote_code=False)
    template=verify_non_thinking(tokenizer)
    cfg=json.loads((root/'config.json').read_text());size=cfg.get('text_config',cfg)['vocab_size']
    xgr,_=load_xgrammar();eos=[248046,248044]
    start=time.process_time();rows=[]
    info=xgr.TokenizerInfo.from_huggingface(tokenizer,vocab_size=size,stop_token_ids=eos)
    compiler=xgr.GrammarCompiler(info,max_threads=1,cache_enabled=False)
    for task in recipe.TASKS:
        grammar=compiler.compile_json_schema(schema(task),any_whitespace=True,max_whitespace_cnt=2,strict_mode=True)
        text=json.dumps({f:'Synthetic "quoted" text; backslash \\ and newline\nUnicode π.' for f in task['fields']},ensure_ascii=False)
        ids=tokenizer.encode(text,add_special_tokens=False);matcher=xgr.GrammarMatcher(grammar)
        valid=all(matcher.accept_token(t) for t in [*ids,eos[0]])
        bad=json.dumps({f:'x' for f in task['fields']}|{'unexpected':'x'})
        negative=xgr.GrammarMatcher(grammar)
        rejected=not (negative.accept_string(bad) and negative.accept_token(eos[0]))
        malformed='{"'+task['fields'][0]+'":"unescaped "quote""}'
        negative=xgr.GrammarMatcher(grammar)
        malformed_rejected=not (negative.accept_string(malformed) and negative.accept_token(eos[0]))
        recipe.parse_artifact(text,task)
        rows.append(dict(task=task['id'],schema_hash=digest(schema(task)),escaped_text_accepted=valid,
                         extra_key_rejected=rejected,malformed_rejected=malformed_rejected,synthetic_tokens=len(ids)+1))
    return dict(schema='composite-json-cpu-v1',condition=recipe.CONDITION,
        status='passed' if all(r['escaped_text_accepted'] and r['extra_key_rejected'] and r['malformed_rejected'] for r in rows) else 'failed',
        runtime_identity=launch.identity(),metadata=dict(local.METADATA),template=template,xgrammar_version='0.1.32',
        rows=rows,cpu_seconds=time.process_time()-start,model_executed=False,gpu_qualified=False)
