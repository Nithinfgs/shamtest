"""Integration tests for CLI execution, flags, and exit codes."""

import io
import json
import os
import sys
import tempfile
import unittest
from shamtest.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_file(self, filename: str, content: str) -> str:
        filepath = os.path.join(self.temp_dir.name, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath

    def test_cli_clean_file_exits_zero(self):
        clean_file = self._create_file(
            "test_clean.py",
            """
def test_ok():
    val = 1 + 1
    assert val == 2
""",
        )
        exit_code = main([clean_file])
        self.assertEqual(exit_code, 0)

    def test_cli_bad_file_exits_one(self):
        bad_file = self._create_file(
            "test_bad.py",
            """
def test_bad():
    assert True
""",
        )
        exit_code = main([bad_file])
        self.assertEqual(exit_code, 1)

    def test_cli_fail_on_never_exits_zero(self):
        bad_file = self._create_file(
            "test_bad.py",
            """
def test_bad():
    assert True
""",
        )
        exit_code = main([bad_file, "--fail-on", "never"])
        self.assertEqual(exit_code, 0)

    def test_cli_ignore_rule_suppresses_failure(self):
        bad_file = self._create_file(
            "test_bad.py",
            """
def test_bad():
    assert True
""",
        )
        exit_code = main([bad_file, "--ignore", "SHAM001"])
        self.assertEqual(exit_code, 0)

    def test_cli_json_flag_outputs_valid_json(self):
        bad_file = self._create_file(
            "test_bad.py",
            """
def test_bad():
    assert True
""",
        )
        captured = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured
            main([bad_file, "--json", "--fail-on", "never"])
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        data = json.loads(output)
        self.assertEqual(data["error_count"], 1)

    def test_cli_max_hollow_index_fails_threshold(self):
        bad_file = self._create_file(
            "test_bad.py",
            """
def test_bad():
    assert True
""",
        )
        exit_code = main([bad_file, "--max-hollow-index", "10.0"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
