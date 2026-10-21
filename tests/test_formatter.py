"""Unit tests for report formatters (terminal, JSON, SARIF)."""

import json
import unittest
from shamtest.formatter import format_json, format_sarif, format_terminal
from shamtest.models import FileReport, Issue, ScanSummary, Severity


class TestFormatter(unittest.TestCase):
    def setUp(self):
        self.issue = Issue(
            rule_id="SHAM001",
            message="Tautological assertion",
            file_path="tests/test_foo.py",
            line_number=10,
            column=4,
            end_line=10,
            end_column=15,
            function_name="test_foo",
            code_snippet="assert True",
            severity=Severity.ERROR,
            fix_suggestion="Assert actual state.",
        )
        self.report = FileReport(file_path="tests/test_foo.py", issues=[self.issue])
        self.summary = ScanSummary(
            files_scanned=1,
            tests_scanned=2,
            file_reports=[self.report],
            duration_ms=4.2,
        )

    def test_terminal_formatter_contains_rule_and_fix(self):
        output = format_terminal(self.summary)
        self.assertIn("SHAM001", output)
        self.assertIn("test_foo", output)
        self.assertIn("Tautological assertion", output)
        self.assertIn("Fix:", output)
        self.assertIn("Hollow Test Index:", output)

    def test_json_formatter_valid_structure(self):
        json_str = format_json(self.summary)
        data = json.loads(json_str)
        self.assertEqual(data["files_scanned"], 1)
        self.assertEqual(data["tests_scanned"], 2)
        self.assertEqual(data["error_count"], 1)
        self.assertEqual(len(data["files"]), 1)
        self.assertEqual(data["files"][0]["issues"][0]["rule_id"], "SHAM001")

    def test_sarif_formatter_valid_schema(self):
        sarif_str = format_sarif(self.summary)
        data = json.loads(sarif_str)
        self.assertEqual(data["version"], "2.1.0")
        self.assertEqual(data["runs"][0]["tool"]["driver"]["name"], "shamtest")
        self.assertEqual(len(data["runs"][0]["results"]), 1)
        self.assertEqual(data["runs"][0]["results"][0]["ruleId"], "SHAM001")


if __name__ == "__main__":
    unittest.main()
