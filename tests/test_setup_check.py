"""Regression checks for setups where only python3 is on PATH."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "setup_check", Path(__file__).resolve().parents[1] / "tools" / "setup_check.py"
)
setup_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_check)


class PythonInterpreterChecks(unittest.TestCase):
    def test_running_python_is_detected_without_a_python_alias(self):
        with patch.object(setup_check.shutil, "which", return_value=None):
            found, detail = setup_check.command_version("python")
        self.assertTrue(found)
        self.assertIn(sys.executable, detail)

    def test_pip_is_checked_in_the_active_interpreter(self):
        result = subprocess.CompletedProcess([], 0, stdout="pip 24.2 from active environment\n")
        with patch.object(setup_check.shutil, "which", return_value=None), patch.object(
            setup_check.subprocess, "run", return_value=result
        ) as probe:
            found, detail = setup_check.command_version("pip")
        self.assertTrue(found)
        self.assertIn("pip 24.2", detail)
        self.assertEqual(probe.call_args.args[0], [sys.executable, "-m", "pip", "--version"])

    def test_a_different_pip_on_path_does_not_hide_a_missing_module(self):
        result = subprocess.CompletedProcess([], 1, stdout="No module named pip\n")
        with patch.object(setup_check.shutil, "which", return_value="/other/python/bin/pip"), patch.object(
            setup_check.subprocess, "run", return_value=result
        ):
            found, detail = setup_check.command_version("pip")
        self.assertFalse(found)
        self.assertIn("active Python interpreter", detail)

    def test_a_timed_out_pip_probe_is_reported_as_unavailable(self):
        with patch.object(
            setup_check.subprocess, "run", side_effect=subprocess.TimeoutExpired("pip", 10)
        ):
            found, detail = setup_check.command_version("pip")
        self.assertFalse(found)
        self.assertIn("unavailable", detail)


if __name__ == "__main__":
    unittest.main()
