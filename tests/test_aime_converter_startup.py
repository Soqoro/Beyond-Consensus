"""Converter startup regression; no Arrow install, dataset reads or model calls."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aime_converter',ROOT/'scripts/convert_prospective_aime_parquet.py')
converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)

class ConverterStartup(unittest.TestCase):
    def test_approved_path_checks_version_before_source_access(self):
        # Reproduces the reported main() path; pre-fix code raises UnboundLocalError.
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/'output'
            argv=['converter','--repo',str(ROOT),'--output',str(output),'--approved-isolated-conversion']
            with patch.object(converter.sys,'argv',argv),patch.object(converter.signal,'signal'),patch.object(converter.signal,'alarm'),patch.object(converter.importlib.metadata,'version',return_value='wrong') as version:
                with self.assertRaisesRegex(RuntimeError,'pinned parser version'):converter.main()
                version.assert_called_once_with('pyarrow')
            self.assertFalse(output.exists())

    def test_unapproved_path_does_not_check_or_import_parser(self):
        with tempfile.TemporaryDirectory() as td:
            argv=['converter','--repo',str(ROOT),'--output',str(Path(td)/'out')]
            with patch.object(converter.sys,'argv',argv),patch.object(converter.importlib.metadata,'version') as version:
                with self.assertRaisesRegex(SystemExit,'exception not recorded'):converter.main()
                version.assert_not_called()

if __name__=='__main__':unittest.main()
