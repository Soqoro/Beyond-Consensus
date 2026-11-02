"""Statement and snapshot fixtures only; never actual model/data bytes."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock

from bc_phase2 import joint_d1_local as local
from bc_phase2.joint_d1_qwen import preflight,open_live
from bc_phase2.model import Invalid,digest
from test_phase2_planner_qwen import Tokenizer

ROOT=Path(__file__).resolve().parents[1]


def receipt():
    # Report metadata only; no benchmark question text.
    return dict(status='statement_extraction_and_metadata_inspection_complete',
        source_ids=list(local.SMOKE),dataset_sha256=local.DATASET_HASH,
        statements_file_sha256=local.STATEMENTS_HASH,statement_hashes=dict(local.STATEMENT_HASHES),
        checkpoint=local.CHECKPOINT,revision=local.REVISION,
        model_path='/unavailable/'+local.REVISION,directory='/unavailable/statements',
        metadata={k:{'sha256':v} for k,v in local.METADATA.items()},packages=dict(local.VERSIONS),
        execution_allowed=False,model_executed=False)


class LocalD1(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_binding_recognizes_confirmed_choices_without_approval(self):
        cfg=local.bind_receipt(ROOT,receipt());scope=cfg['scope']
        self.assertTrue(scope['settings_accepted']);self.assertTrue(scope['limits_accepted'])
        self.assertEqual(scope['source_ids'],list(local.SMOKE))
        result=preflight(cfg,ROOT)
        self.assertNotIn('pending:limits_accepted',result['blockers'])
        self.assertNotIn('unverified:source_access_permission',result['blockers'])
        self.assertIn('unverified:source_receipts',result['blockers'])
        self.assertFalse(result['execution_allowed']);self.assertIsNone(cfg['approval'])
        self.assertIsNone(scope['statement_transmission_permission'])
        with self.assertRaises(Invalid):open_live(cfg)

    def test_receipt_changed_ids_hash_model_metadata_or_packages_rejected(self):
        for key,value in [('source_ids',list(reversed(local.SMOKE))),('dataset_sha256','bad'),
            ('statements_file_sha256','bad'),('statement_hashes',{}),('revision','bad'),
            ('checkpoint','other'),('metadata',{}),('packages',{}),('execution_allowed',True)]:
            r=receipt();r[key]=value
            with self.subTest(key=key),self.assertRaises(Invalid):local.bind_receipt(ROOT,r)

    def test_statement_file_order_protected_fields_and_mutation(self):
        path=self.root/'statements.json';rows=[{'id':'mock:0','problem':'synthetic'}]
        def write(value):
            path.write_text(json.dumps(value));return local.file_hash(path)
        hashes={'mock:0':hashlib.sha256(b'synthetic').hexdigest()}
        expected=write(rows)
        self.assertEqual(local.statement_records(path,['mock:0'],expected,hashes),rows)
        path.write_text('changed')
        with self.assertRaises(Invalid):local.statement_records(path,['mock:0'],expected,hashes)
        bad=[dict(rows[0],answer='DO_NOT_DELIVER')]
        with self.assertRaises(Invalid):local.statement_records(path,['mock:0'],write(bad),hashes)
        with self.assertRaises(Invalid):local.statement_records(path,['mock:1'],write(rows),hashes)
        with self.assertRaises(Invalid):local.statement_records(path,['mock:0'],write(rows),{'mock:0':'bad'})

    def test_shared_rendering_and_context_limit(self):
        tokenizer=Tokenizer();rows=[dict(id='mock:0',problem='synthetic only')]
        rendered=local.render_statements(tokenizer,rows,digest(tokenizer.chat_template))
        self.assertEqual(rendered[0]['input_tokens'],5)
        self.assertNotIn('problem',json.dumps(rendered))
        self.assertEqual(rendered[0]['output_reservation_tokens'],6144)
        tokenizer.input_length=10241
        with self.assertRaises(Invalid):local.render_statements(tokenizer,rows,digest(tokenizer.chat_template))

    def test_inventory_hashes_shards_without_deserializing(self):
        (self.root/'fixture.safetensors').write_bytes(b'artificial-not-model-weights')
        (self.root/'config.json').write_text('{}')
        (self.root/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'x':'fixture.safetensors'}}))
        meta={'config.json':local.file_hash(self.root/'config.json')}
        r=local.snapshot_inventory(self.root,meta)
        self.assertTrue(r['weight_hashes_observed']);self.assertFalse(r['trusted_weight_reference_compared'])
        self.assertEqual(r['weight_shards'],['fixture.safetensors'])
        (self.root/'config.json').write_text('{"changed":true}')
        with self.assertRaises(Invalid):local.snapshot_inventory(self.root,meta)

    def test_inventory_missing_shard_nested_template_and_code_rejected(self):
        index=self.root/'model.safetensors.index.json'
        index.write_text(json.dumps({'weight_map':{'x':'../bad.safetensors'}}))
        with self.assertRaises(Invalid):local.snapshot_inventory(self.root,{})
        (self.root/'remote.py').write_text('raise AssertionError("must not execute")')
        with self.assertRaises(Invalid):local.snapshot_inventory(self.root,{})
        (self.root/'remote.py').unlink();(self.root/'chat_templates').mkdir()
        with self.assertRaises(Invalid):local.snapshot_inventory(self.root,{})

    def test_complete_local_verification_with_artificial_files_and_tokenizer(self):
        model_root=self.root/local.REVISION;model_root.mkdir()
        (model_root/'fixture.safetensors').write_bytes(b'artificial-weight-bytes')
        (model_root/'model.safetensors.index.json').write_text(json.dumps({'weight_map':{'x':'fixture.safetensors'}}))
        (model_root/'generation_config.json').write_text(json.dumps({'eos_token_id':[248046,248044],'pad_token_id':248044}))
        meta={p.name:local.file_hash(p) for p in model_root.iterdir() if p.suffix=='.json'}
        statements=self.root/'statements.json'
        statements.write_text(json.dumps([{'id':'mock:only','problem':'synthetic'}]))
        tokenizer=Tokenizer();tokenizer.eos_token_id=248046;tokenizer.pad_token_id=248044
        original=tokenizer.convert_tokens_to_ids
        tokenizer.convert_tokens_to_ids=lambda x:248046 if x=='<eos>' else original(x)
        loader=Mock(return_value=tokenizer)
        with patch.object(local,'SMOKE',('mock:only',)),patch.object(local,'METADATA',meta),\
             patch.object(local,'STATEMENTS_HASH',local.file_hash(statements)),\
             patch.object(local,'STATEMENT_HASHES',{'mock:only':hashlib.sha256(b'synthetic').hexdigest()}),\
             patch.object(local,'TEMPLATE_HASH',digest(tokenizer.chat_template)),\
             patch.object(local.importlib.metadata,'version',side_effect=lambda n:local.VERSIONS[n]):
            r=receipt();r['model_path']=str(model_root)
            report=local.verify_local(r,statements,loader)
        loader.assert_called_once_with(str(model_root),local_files_only=True,trust_remote_code=False)
        self.assertEqual(report['initial_requests'][0]['input_tokens'],5)
        self.assertFalse(report['model_executed']);self.assertFalse(report['execution_allowed'])
        self.assertFalse(report['inventory']['trusted_weight_reference_compared'])
        self.assertNotIn('synthetic',json.dumps(report))

    def test_prepared_loader_uses_existing_single_device_pattern_with_doubles(self):
        # Temporarily exercise unreachable branch with fully injected modules, no real import.
        from bc_phase2 import planner_qwen as q
        model=Mock();model_class=Mock();model_class.from_pretrained.return_value=model
        token_class=Mock();token_class.from_pretrained.return_value=object()
        torch=SimpleNamespace(cuda=SimpleNamespace(device_count=lambda:1),bfloat16='fake_bf16',device=lambda x:x)
        transformers=SimpleNamespace(AutoTokenizer=token_class,Qwen3_5ForConditionalGeneration=model_class)
        with patch.object(q,'_REAL_EXECUTION_RELEASED',True),patch.object(q,'verify_local_inventory',return_value=self.root),\
             patch('beyond_consensus.models.transformers_backend.require_allocation'),\
             patch.dict(sys.modules,torch=torch,transformers=transformers),patch.object(q,'QwenTransport'):
            q.open_local({})
        options=model_class.from_pretrained.call_args.kwargs
        self.assertNotIn('device_map',options);self.assertTrue(options['local_files_only'])
        self.assertFalse(options['trust_remote_code']);model.to.assert_called_once_with('cuda:0')
        model.requires_grad_.assert_called_once_with(False)
        self.assertFalse(q._REAL_EXECUTION_RELEASED)
        with self.assertRaises(Invalid):q.open_local({})

if __name__=='__main__':unittest.main()
