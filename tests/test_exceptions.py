"""Unit tests for exception handling rules (SHAM007, SHAM008)."""

import unittest
from shamtest.analyzer import Analyzer


class TestExceptionRules(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_swallowed_exception_pass(self):
        code = """
def test_swallowed():
    try:
        divide(10, 0)
    except Exception:
        pass
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM007", rules)

    def test_overly_broad_pytest_raises_exception(self):
        code = """
import pytest

def test_broad():
    with pytest.raises(Exception):
        do_work()
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM008", rules)

    def test_specific_pytest_raises_is_clean(self):
        code = """
import pytest

def test_specific():
    with pytest.raises(KeyError):
        lookup("missing_key")
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)


if __name__ == "__main__":
    unittest.main()
