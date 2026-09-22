"""No historical native artifacts are fabricated: all inputs below are mocks."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.support import ROOT
from beyond_consensus.config import load_config
from beyond_consensus.diagnostics.sql_interface import prepare, BASELINE, TREE, TEXT
from beyond_consensus.schemas import TaskInstance
from beyond_consensus.util import plain, digest, atomic_json, read_json, BCError


class MatchedPlanTests(unittest.TestCase):
    def test_resolved_fields_required_and_only_representation_changes(self):
        cfg=replace(load_config(ROOT/'configs/qwen27b-sql-competence.json'), task_kind='sqlite_native',task_count=2,
                    sqlite_fixture_suite='arithmetic_v1',development_profile='qwen35-27b-native-context16k-actions24',
                    max_actions=24,model=replace(load_config(ROOT/'configs/qwen27b-sql-competence.json').model,context_limit=16384))
        tasks=[TaskInstance(k,'sqlite_native','synthetic-group','Synthetic placeholder', {k:{'kind':'query','requirement':'synthetic'}},(k,),(),{}) for k in ('solar_2','solar_M_3')]
        baseline={'experiment_id':BASELINE,'config':plain(cfg),'config_hash':digest(cfg),'tasks':plain(tasks)}
        with tempfile.TemporaryDirectory() as temp, patch('beyond_consensus.tasks.data_manifest.validate_data',return_value=tasks):
            root=Path(temp);path=root/'mock-baseline.json';atomic_json(path,baseline)
            report=prepare(path,root/'mock-renewed.json',root/'pair')
            self.assertEqual(report['planned_episodes'],4)
            a,b=[read_json(root/'pair'/(k+'.json')) for k in ('tree','text')]
            self.assertEqual(a['model'].pop('action_constraint'),TREE)
            self.assertEqual(b['model'].pop('action_constraint'),TEXT)
            a.pop('name');b.pop('name');self.assertEqual(a,b)
            for field in ('sqlite_error_feedback','budget','seeds'):
                missing=deepcopy(baseline);missing['config'].pop(field);missing['config_hash']=digest(missing['config'])
                atomic_json(path,missing)
                with self.assertRaises(BCError):prepare(path,root/'mock-renewed.json',root/field)

            missing=deepcopy(baseline);missing['config']['model'].pop('do_sample');missing['config_hash']=digest(missing['config'])
            atomic_json(path,missing)
            with self.assertRaises(BCError):prepare(path,root/'mock-renewed.json',root/'missing-model-field')


class ReferenceCoverageTests(unittest.TestCase):
    def test_every_required_output_must_have_a_reference(self):
        from beyond_consensus.diagnostics.sql_interface import reference_frontend
        task = TaskInstance('synthetic', 'sqlite_native', 'synthetic-group',
                            'Synthetic coverage check', {}, ('a', 'b'), (), {})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'mock-data.json'
            atomic_json(path, {})
            for evaluations in ({}, {'a': {}}, {'a': {}, 'b': {}, 'extra': {}}, None):
                candidate = replace(task, metadata={'evaluation': evaluations})
                with patch('beyond_consensus.tasks.data_manifest.validate_data', return_value=[candidate]), \
                     patch('beyond_consensus.runtime.sql_text.lower') as lower:
                    report = reference_frontend(path)
                self.assertEqual(report['status'], 'blocked')
                self.assertEqual(report['reports'][0]['status'], 'blocked_reference_coverage')
                lower.assert_not_called()


class LegacyFeedbackTests(unittest.TestCase):
    def test_only_reviewed_provenance_resolves_without_mutation(self):
        from beyond_consensus.diagnostics.sql_interface import resolve_baseline_config
        baseline = {'experiment_id': 'synthetic', 'source_revision': 'synthetic-source',
                    'config': {'max_actions': 24}}
        baseline['config_hash'] = digest(baseline['config'])
        original = deepcopy(baseline)
        key = ('synthetic', 'synthetic-source', baseline['config_hash'])
        evidence = {'field': 'sqlite_error_feedback', 'value': 'generic', 'basis': 'mock-only'}
        with patch('beyond_consensus.diagnostics.sql_interface.LEGACY_FEEDBACK', {key: evidence}):
            config, resolutions = resolve_baseline_config(baseline)
            self.assertEqual(config['sqlite_error_feedback'], 'generic')
            self.assertEqual(resolutions[0]['historical_config_hash'], baseline['config_hash'])
            self.assertEqual(baseline, original)
            for field in ('experiment_id', 'source_revision', 'config_hash'):
                changed = deepcopy(baseline); changed[field] = 'different'
                with self.assertRaises(BCError): resolve_baseline_config(changed)
            changed = deepcopy(baseline); changed['config']['max_actions'] = 25
            changed['config_hash'] = digest(changed['config'])
            with self.assertRaises(BCError): resolve_baseline_config(changed)

    def test_explicit_setting_is_preserved_and_unknown_omission_blocks(self):
        from beyond_consensus.diagnostics.sql_interface import resolve_baseline_config
        config = {'sqlite_error_feedback': 'sqlite-errors-v1'}
        resolved, evidence = resolve_baseline_config({'config': config, 'config_hash': digest(config)})
        self.assertEqual(resolved, config)
        self.assertEqual(evidence, [])
        with self.assertRaises(BCError):
            resolve_baseline_config({'config': {}, 'config_hash': digest({})})
