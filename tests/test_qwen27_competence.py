"""CPU doubles only: these checks do not establish 27B fit or competence."""
import copy
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from tests.support import ROOT
from beyond_consensus.config import load_config, ModelConfig
from beyond_consensus.models.competence import hardware, placement, qualification_key, require_qualification
from beyond_consensus.models.staging import resolve_model_config
from beyond_consensus.models.action_schema import validate_action
from beyond_consensus.runtime.budget import BudgetLedger
from beyond_consensus.diagnostics.competence import compatibility, output_diagnostics, audit
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.util import BCError
from tests.test_sqlite_compatibility import controls, ScriptedWorker

class CompetenceTests(unittest.TestCase):
    def config(self): return load_config(ROOT/'configs/qwen27b-sql-competence.json')

    def test_opt_in_and_frozen_probe_condition(self):
        c = self.config()
        old = load_config(ROOT/'configs/sqlite-tool-compatibility-constrained.json')
        self.assertEqual(ModelConfig().checkpoint, 'Qwen/Qwen3.5-4B')
        a, b = build_manifest(c, ROOT), build_manifest(old, ROOT)
        self.assertEqual(a['tasks'], b['tasks'])
        self.assertEqual(len(a['episodes']),4)
        self.assertEqual({e['seed'] for e in a['episodes']},{0})
        for change in ({'revision':None},{'tokenizer_revision':old.model.revision},
                       {'dtype':'float16'},{'max_new_tokens':4096}):
            with self.assertRaises(BCError): replace(c.model, **change)
        for change in ({'task_count':8},{'shards':4},{'policies':('recovery',)}):
            with self.assertRaises(BCError): replace(c, **change)
        self.assertEqual(compatibility(a)['status'],'unmatched_competence_screen')
        diff=compatibility(a,b)
        self.assertTrue(diff['invariants']['tasks']['equal'])
        self.assertTrue(diff['invariants']['execution_config']['equal'])
        self.assertEqual(diff['status'],'unmatched_competence_screen')

    def test_hardware_mock_rejects_before_loader(self):
        def device(name='NVIDIA A100-SXM4-80GB',size=80,count=1):
            return SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:True,device_count=lambda:count,
                get_device_name=lambda i:name,mem_get_info=lambda i:(size*1024**3,size*1024**3),
                is_bf16_supported=lambda:True),version=SimpleNamespace(cuda='12.6'))
        self.assertEqual(hardware(device())['visible_devices'],1)
        for args in ({'size':40},{'size':48},{'name':'MIG A100','size':80},{'count':2},{'name':'RTX 6000'}):
            with self.assertRaises(BCError):hardware(device(**args))
        for model in (SimpleNamespace(is_quantized=True),SimpleNamespace(hf_device_map={'a':'cpu'})):
            with self.assertRaises(BCError):placement(model)

    def test_lock_and_model_specific_qualification(self):
        lock={'checkpoint':self.config().model.checkpoint,'revision':self.config().model.revision,
              'tokenizer_revision':self.config().model.revision,'metadata_hashes':{'config.json':'x'}}
        key=qualification_key(lock,{'xgrammar':'0.1.32'})
        lock['decoder_qualification']={'status':'passed','qualification_key':key,'model_executed':False,'sql_executed':False}
        require_qualification(lock,{'xgrammar':'0.1.32'})
        for update in ({'revision':'0'*40},{'metadata_hashes':{}},{'checkpoint':'Qwen/Qwen3.5-4B'}):
            with self.assertRaises(BCError):require_qualification(lock|update,{'xgrammar':'0.1.32'})
        with self.assertRaises(BCError):require_qualification(lock,{'xgrammar':'0.1.33'})
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'lock.json';path.write_text(json.dumps(lock|{'schema':'bc-model-lock-v1'}))
            with self.assertRaises(BCError):resolve_model_config(self.config().model,path)

    def test_correct_actions_expressible_and_wrong_case_not_regraded(self):
        for probe,tree in controls().items():
            action={'tool':'submit_view_definition' if probe=='view' else 'run_read_query',
                    'select_sql':tree,'permitted_artifact_versions':{}}
            if probe=='view':action['artifact_name']='entry_adjusted'
            validate_action(json.dumps(action))
        from beyond_consensus.tasks.sqlite_compatibility import expected, score
        columns,rows=expected('case');tree=copy.deepcopy(controls()['case']);tree['columns'][-1].pop('as')
        d=output_diagnostics('case',{'select':tree,'rows':rows})
        self.assertTrue(d['ordered_values_match']);self.assertFalse(d['column_contract_match'])
        self.assertFalse(score('case',{'columns':['id','expression'],'rows':rows}))
        tree=copy.deepcopy(controls()['aggregate']);tree['columns'][1]['expr']={'literal':0}
        validate_action(json.dumps({'tool':'run_read_query','select_sql':tree,'permitted_artifact_versions':{}}))

    def test_ledger_release_and_interruption_exact(self):
        b=BudgetLedger(10000);k=b.reserve_work('primary',300,'constrained_decoding');b.reconcile_work(k,20)
        self.assertEqual(b.entries[-1]['released_work'],280)
        k=b.reserve_work('primary',300,'constrained_decoding');b.uncertain_inflight()
        self.assertEqual(b.entries[-1]['released_work'],0);self.assertTrue(b.entries[-1]['uncertain'])
        k=b.reserve_call('primary',100,2048);b.reconcile(k,output_tokens=2048,reasoning_tokens=None)
        self.assertIsNone(b.entries[-1]['reasoning_tokens'])
        self.assertEqual(b.spent,sum(e['work'] for e in b.entries))

    def test_audit_real_cpu_journal_sanitized_no_rescore(self):
        c=replace(load_config(ROOT/'configs/sqlite-tool-compatibility.json'),model=ModelConfig())
        m=build_manifest(c,ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);run_manifest(m,path,ROOT,backend=ScriptedWorker('wrong_alias'))
            report=audit(path)
            self.assertEqual(report['planned'],4);self.assertEqual(report['successes'],0)
            self.assertTrue(all(r['ledger_residual']==0 for r in report['tasks']))
            self.assertFalse(report['sql_executed'])
            self.assertNotIn('contexts',json.dumps(report))

    def test_backend_rejects_40gb_before_weight_loader(self):
        from unittest.mock import Mock
        from beyond_consensus.models.transformers_backend import TransformersBackend
        torch=SimpleNamespace(cuda=SimpleNamespace(is_available=lambda:True, device_count=lambda:1,
            is_bf16_supported=lambda:True, get_device_name=lambda i:'NVIDIA A100-SXM4-40GB',
            mem_get_info=lambda i:(40*1024**3,40*1024**3)),version=SimpleNamespace(cuda='12.6'))
        loader=Mock()
        transformers=SimpleNamespace(AutoTokenizer=Mock(),Qwen3_5ForConditionalGeneration=loader)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config.json').write_text(json.dumps({'architectures':['Qwen3_5ForConditionalGeneration']}))
            lock=root/'lock.json';lock.write_text(json.dumps({'model_path':tmp,'metadata_hashes':{}}))
            with patch.dict('sys.modules',{'torch':torch,'transformers':transformers}), \
                 patch('beyond_consensus.models.transformers_backend.require_allocation'), \
                 patch('beyond_consensus.models.transformers_backend.resolve_model_config',return_value=self.config().model), \
                 patch('importlib.metadata.version',return_value='5.3.0'), self.assertRaisesRegex(BCError,'hardware blocked'):
                TransformersBackend(self.config().model,lock)
            loader.from_pretrained.assert_not_called()

    def test_synthetic_long_history_reserves_output_without_truncation(self):
        from beyond_consensus.models.transformers_backend import long_history
        backend=SimpleNamespace(config=self.config().model,
            count_input=lambda messages:sum(len(m['content'])//4 for m in messages)+32)
        messages=long_history(backend)
        size=backend.count_input(messages)
        self.assertLessEqual(size+2048,8192);self.assertGreaterEqual(size,6112)
        self.assertEqual(messages[-2]['role'],'assistant')
        self.assertEqual(json.loads(messages[-1]['content'])['tool'],'inspect_schema')

    def test_stale_native_runtime_still_blocks(self):
        from beyond_consensus.tasks.sqlite_compatibility import tasks
        c=load_config(ROOT/'configs/validation/qwen35-27b-sql-competence.json')
        native=[]
        for task,name in zip(tasks(),('solar_2','solar_M_3')):
            native.append(replace(task,id=name,kind='sqlite_native', metadata={**task.metadata,
                'readiness':'reference_validated','validation_hash':'recorded',
                'validated_sqlite_runtime':{'stale':True}}))
        with self.assertRaisesRegex(BCError,'runtime changed'):
            build_manifest(c,ROOT,native)

    def test_staging_dry_run_and_quota_never_download(self):
        from unittest.mock import Mock
        from beyond_consensus.models.staging import stage_model
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=stage_model(self.config().model,root,dry_run=True)
            self.assertFalse(result['downloaded']);self.assertEqual(list(root.iterdir()),[])
            download=Mock()
            info=SimpleNamespace(sha=self.config().model.revision,
                siblings=[SimpleNamespace(size=54_000_000_000,rfilename='model-00001.safetensors')])
            hub=SimpleNamespace(HfApi=lambda:SimpleNamespace(model_info=lambda *a,**kw:info),snapshot_download=download)
            with patch.dict('sys.modules',{'huggingface_hub':hub}), self.assertRaisesRegex(BCError,'quota'):
                stage_model(self.config().model,root,quota_bytes=1)
            download.assert_not_called()

    def test_cpu_probe_controls_are_same_known_trees(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('offline_checker',ROOT/'scripts/check_action_constraints.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.synthetic_probe_trees(),controls())
