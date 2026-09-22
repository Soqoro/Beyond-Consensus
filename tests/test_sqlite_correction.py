"""Supplied-draft correction controls, not model competence measurements."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from tests.support import ROOT
from tests.test_sqlite_compatibility import controls
from beyond_consensus.config import RunConfig, load_config
from beyond_consensus.experiments.manifest import build_manifest
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.models.mock import MockBackend
from beyond_consensus.models.base import Generation
from beyond_consensus.runtime.sqlite_executor import capabilities
from beyond_consensus.tasks.sqlite_correction import tasks
from beyond_consensus.diagnostics.sqlite_correction import compare
from beyond_consensus.util import BCError, canonical, read_json


def config(mode):
    name = 'generic' if mode == 'generic' else 'categorized'
    return replace(load_config(ROOT/f'configs/qwen27b-sql-correction-{name}.json'), model=RunConfig().model)


class ScriptedCorrection(MockBackend):
    def __init__(self, repeat=False):
        self.repeat = repeat
        self.first_messages = []

    def generate(self, messages, max_new_tokens, seed):
        observations = [json.loads(m['content']) for m in messages if m['role']=='user']
        assignment = next(o for o in observations if 'assignment' in o)['assignment']
        draft = next(o['action'] for o in observations if o.get('diagnostic_input')=='supplied_invalid_draft')
        if not any(m['role']=='assistant' for m in messages):
            self.first_messages.append(copy.deepcopy(messages))
        created = next((o for o in observations if 'artifact_id' in o), None)
        if self.repeat:
            action = draft
        elif created:
            action = {'tool':'submit_required_artifact', 'artifact_id':created['artifact_id']}
        elif not any(o.get('tool')=='read_source' for o in observations):
            action = {'tool':'read_source', 'name':assignment}
        else:
            tree = controls()['aggregate' if assignment.endswith('0') else 'join']
            action = {'tool':'run_read_query','select_sql':tree,'permitted_artifact_versions':{}}
        text = canonical(action)
        return Generation(text, (len(text)+3)//4)


class CorrectionTests(unittest.TestCase):
    def test_matched_tasks_and_bounded_config(self):
        a, b = build_manifest(config('generic'), ROOT), build_manifest(config('sqlite-errors-v1'), ROOT)
        self.assertEqual(a['tasks'], b['tasks'])
        self.assertNotEqual(a['experiment_id'], b['experiment_id'])
        self.assertEqual(a['planned_episodes'], 2)
        self.assertEqual(a['data_regime']['adaptation'], 'bc_sqlite_tool_correction_v1')
        for change in ({'task_count':4}, {'max_actions':24}, {'malformed_retries':3},
                       {'shards':2}, {'policies':('recovery',)}, {'seeds':(1,)}):
            with self.subTest(change=change), self.assertRaises(BCError):
                replace(config('generic'), **change)
        self.assertTrue(all('expected' not in canonical(t.sources) for t in tasks()))

    @unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
    def test_paired_execution_charges_seed_and_separates_model_history(self):
        with tempfile.TemporaryDirectory() as temp:
            roots = [Path(temp)/'generic', Path(temp)/'feedback']
            first_histories = []
            for mode, root in zip(('generic','sqlite-errors-v1'), roots):
                backend = ScriptedCorrection()
                manifest = build_manifest(config(mode), ROOT)
                results = run_manifest(manifest, root, ROOT, backend=backend)
                self.assertEqual([r['success'] for r in results], [True,True])
                first_histories.append(backend.first_messages)
                resume_backend = ScriptedCorrection(True)
                resumed = run_manifest(manifest, root, ROOT, backend=resume_backend)
                self.assertEqual([r["costs"] for r in resumed], [r["costs"] for r in results])
                self.assertEqual(resume_backend.first_messages, [])
                for result in results:
                    self.assertEqual(result['metrics']['tool_rejections'], 1)
                    entries = result['costs']['entries']
                    self.assertEqual(len([e for e in entries if e['kind']=='model']), 3)
                    self.assertEqual(len([e for e in entries if e['kind']=='tool']), 4)
                    sql = [e for e in entries if e['kind']=='sql_execution' and e['stage']=='primary']
                    self.assertEqual([e['work'] for e in sql], [30,30])
                    self.assertEqual([e['status'] for e in sql], ['semantic_error','ok'])
                    state=read_json(root/'episodes'/result['episode_id']/'checkpoint.json')
                    events=state['store']['events']
                    self.assertEqual(sum(e['type']=='diagnostic_seed_action' for e in events),1)
                    self.assertEqual(sum(e['type']=='generation_metadata' for e in events),3)
            for generic, feedback in zip(*first_histories):
                self.assertEqual(generic[:-1], feedback[:-1])
                self.assertNotEqual(generic[-1], feedback[-1])
                self.assertTrue(all(m['role']!='assistant' for m in generic))
            report=compare(*roots)
            self.assertTrue(report['complete_diagnostic'])
            self.assertTrue(all(t['same_seed_action'] for t in report['paired_tasks']))
            self.assertTrue(all(t['feedback_path_observed'] for t in report['conditions'][1]['tasks']))
            self.assertFalse(any(t['feedback_path_observed'] for t in report['conditions'][0]['tasks']))
            with self.assertRaises(BCError): compare(roots[1],roots[0])

    @unittest.skipUnless(capabilities()['defensive'], 'SQLite defensive controls required')
    def test_seed_consumes_retry_and_failures_remain_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg=config('sqlite-errors-v1')
            result=run_manifest(build_manifest(cfg,ROOT),Path(temp),ROOT,backend=ScriptedCorrection(True))
            for r in result:
                self.assertFalse(r['success'])
                self.assertEqual(r['status'],'completed')
                self.assertEqual(r['metrics']['tool_rejections'],3)
                self.assertEqual(len([e for e in r['costs']['entries'] if e['kind']=='model']),2)
                self.assertEqual(sum(e['work'] for e in r['costs']['entries']),r['costs']['spent'])
