"""ATS extraction failures should be reported without a traceback."""

from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "ats_check", Path(__file__).resolve().parents[1] / "tools" / "ats_check.py"
)
ats_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ats_check)


class ExtractionFailureTests(unittest.TestCase):
    def test_a_missing_poppler_installation_remains_an_optional_skip(self):
        with patch.object(ats_check.shutil, "which", return_value=None):
            code, text, message = ats_check.extract_text(Path('example.pdf'))
        self.assertEqual(code, 3)
        self.assertEqual(text, '')
        self.assertIn('not installed', message)

    def test_a_timeout_returns_a_failed_extraction(self):
        with patch.object(ats_check.shutil, "which", return_value='/tools/pdftotext'), patch.object(
            ats_check.subprocess, 'run', side_effect=subprocess.TimeoutExpired('pdftotext', 30)
        ):
            code, text, message = ats_check.extract_text(Path('example.pdf'))
        self.assertEqual(code, 1)
        self.assertEqual(text, '')
        self.assertIn('timed out', message)

    def test_a_launch_error_returns_a_failed_extraction(self):
        with patch.object(ats_check.shutil, "which", return_value='/tools/pdftotext'), patch.object(
            ats_check.subprocess, 'run', side_effect=PermissionError('not executable')
        ):
            code, _, message = ats_check.extract_text(Path('example.pdf'))
        self.assertEqual(code, 1)
        self.assertIn('Could not run pdftotext', message)

    def test_the_cli_reports_a_timeout_with_a_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf = Path(folder) / 'example.pdf'
            pdf.write_bytes(b'%PDF-1.4\n')
            stderr = io.StringIO()
            with patch.object(sys, 'argv', ['ats_check.py', str(pdf)]), patch.object(
                ats_check.shutil, 'which', return_value='/tools/pdftotext'
            ), patch.object(
                ats_check.subprocess, 'run', side_effect=subprocess.TimeoutExpired('pdftotext', 30)
            ), redirect_stderr(stderr):
                code = ats_check.main()
        self.assertEqual(code, 1)
        self.assertIn('ERROR:', stderr.getvalue())
        self.assertNotIn('Traceback', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
