"""Scripted controls establish harness behavior, never model competence."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from tests.support import ROOT
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.diagnostics.competence import audit
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.models.base import Generation
from beyond_consensus.tasks.sqlite_aggregation import tasks, expected, score
from beyond_consensus.runtime.sqlite_executor import capabilities
from beyond_consensus.util import BCError, canonical, read_json


def col(n): return {'column': n}
def lit(n): return {'literal': n}
def call(n, *args): return {'call': {'name': n, 'args': list(args)}}
def eq(a, b): return {'binary': ['=', a, b]}


def control(probe, wrong=False):
    cols = [{'expr': col('t.id'), 'as': 'team_id'},
            {'expr': call('coalesce', call('sum', col('p.amount')), lit(0)), 'as': 'total_amount'}]
    tree = {'columns': cols, 'from': {'table': 'teams', 'as': 't'},
        'joins': [{'kind': 'left', 'source': {'table': 'payments', 'as': 'p'},
                   'on': eq(col('t.id'), col('p.team_id'))}],
        'group_by': [col('t.id')], 'order_by': [{'expr': col('t.id'), 'direction': 'asc'}]}
    if probe == 'independent_details':
        for alias, critical in [('notice_count', False), ('critical_count', True)]:
            query = {'columns': [{'expr': call('count', col('n.id')), 'as': 'value'}],
                     'from': {'table': 'notices', 'as': 'n'},
                     'where': eq(col('n.team_id'), col('t.id'))}
            if critical:
                query['where'] = {'binary': ['and', query['where'], eq(col('n.severity'), lit('critical'))]}
            cols.append({'expr': {'select': query}, 'as': alias})
        if wrong:
            tree['joins'].append({'kind': 'left', 'source': {'table': 'notices', 'as': 'extra'},
                                  'on': eq(col('t.id'), col('extra.team_id'))})
    return tree


class Worker(MockBackend):
    def __init__(self, mutation=None): self.mutation = mutation
    def generate(self, messages, max_new_tokens, seed):
        observations = [json.loads(m['content']) for m in messages if m['role'] == 'user']
        unit = next(o['assignment'] for o in observations if 'assignment' in o)
        artifact = next((o['artifact_id'] for o in observations if 'artifact_id' in o), None)
        if artifact and self.mutation != 'no_submission':
            action = {'tool': 'submit_required_artifact', 'artifact_id': artifact}
        elif artifact or not any(o.get('tool') == 'read_source' for o in observations):
            action = {'tool': 'read_source', 'name': unit}
        else:
            tree = control(unit.removeprefix('sqlite-aggregation-'), self.mutation == 'fanout')
            if self.mutation == 'wrong_alias': tree['columns'][0]['as'] = 'wrong'
            action = {'tool': 'run_read_query', 'permitted_artifact_versions': {}, 'select_sql': tree}
        text = canonical(action)
        return Generation(text, (len(text)+3)//4)


class AggregationTests(unittest.TestCase):
    def config(self):
        return replace(load_config(ROOT/'configs/qwen27b-aggregation.json'), model=RunConfig().model)

    def test_frozen_expectations_and_gates(self):
        self.assertEqual(expected('independent_details')[1], [[1,25,2,1],[2,9,3,1],[3,4,0,0],[4,0,1,0]])
        for task in tasks():
            self.assertEqual(task.metadata['harness']['documents'], {})
            self.assertNotIn('evaluation', task.metadata)
            self.assertNotIn('select', task.sources[task.id])
        config = self.config()
        for change in ({'task_count':4}, {'attacks':('withholding',)}, {'policies':('recovery',)},
                       {'seeds':(0,1)}, {'confirmatory':True}, {'max_actions':24},
                       {'sqlite_error_feedback':'sqlite-errors-v1'}):
            with self.subTest(change=change), self.assertRaises(BCError): replace(config, **change)
        manifest = build_manifest(config, ROOT)
        self.assertEqual(len(manifest['episodes']), 2)
        self.assertEqual(manifest['data_regime']['scorer'], 'bc-sqlite-aggregation-v1')
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(BCError,'explicitly injected'):
            run_manifest(manifest, Path(tmp), ROOT)

    @unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
    def test_positive_fanout_alias_and_submission_controls(self):
        manifest = build_manifest(self.config(), ROOT)
        for mutation in (None, 'fanout', 'wrong_alias', 'no_submission'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                results = run_manifest(manifest, Path(tmp), ROOT, backend=Worker(mutation))
                self.assertEqual(sum(r['success'] for r in results),
                                 2 if mutation is None else 1 if mutation == 'fanout' else 0)
                report = audit(Path(tmp))
                self.assertEqual(report['successes'], sum(r['success'] for r in results))
                self.assertEqual(report['decision'], 'synthetic_aggregation_review_only')
                self.assertFalse(report['model_executed'])
                self.assertFalse(report['sql_executed'])
                self.assertNotIn('historical_4b_evidence', report)
                for row in report['tasks']:
                    value = row['offline_diagnostics']['ordered_values_match']
                    if mutation == 'no_submission':
                        self.assertIsNone(value)
                    elif mutation == 'fanout' and row['task'].endswith('independent_details'):
                        self.assertFalse(value)
                    elif mutation is None:
                        self.assertTrue(value)
                for r in results:
                    self.assertEqual(r['status'], 'completed')
                    self.assertGreater(r['costs']['spent'], 0)
                    state = read_json(Path(tmp)/'episodes'/r['episode_id']/'checkpoint.json')
                    self.assertNotIn('expected_rows', canonical(state['store']['contexts']))
                    self.assertEqual(len(state['store']['contexts']), 4)
