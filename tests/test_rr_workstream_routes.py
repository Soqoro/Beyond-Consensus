"""Admission and wrapper boundaries for prepared decoder/catalog workstreams."""
import subprocess
import unittest
from pathlib import Path
from tests.support import ROOT
from beyond_consensus.experiments.runner import run_manifest
from beyond_consensus.util import BCError


class WorkstreamRoutes(unittest.TestCase):
    def test_diagnostic_cannot_enter_task_runner(self):
        with self.assertRaisesRegex(BCError, 'preflight-only'):
            run_manifest({'schema':'rr-decoder-diagnostic-v1'}, Path('/unused'), ROOT)

    def test_cpu_wrapper_separate_modes_no_submission(self):
        script=ROOT/'experiments/qualify_reporecourse.sh'
        for args in (
            ['--decoder-diagnostic-controls','--model-lock','/unused','--dry-run'],
            ['--organization-catalog','--dry-run'],
        ):
            result=subprocess.run(['bash',str(script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('No model weights or GPU jobs',result.stdout)
        for args in (
            ['--decoder-diagnostic-controls','--dry-run'],
            ['--decoder-diagnostic-controls','--organization-catalog','--model-lock','/unused','--dry-run'],
            ['--organization-catalog','--cohort-controls','--dry-run'],
        ):
            result=subprocess.run(['bash',str(script),*args],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
