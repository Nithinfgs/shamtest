"""Unit tests for zero-assertion test function detection (SHAM006)."""

import unittest
from shamtest.analyzer import Analyzer


class TestZeroAssertion(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_blind_function_call_zero_assertions(self):
        code = """
def test_blind_execution():
    val = process_data("payload")
    print(val)
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM006", rules)

    def test_empty_stub_test_function(self):
        code = """
def test_placeholder():
    pass
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM006", rules)

    def test_non_test_helper_function_ignored(self):
        code = """
def helper_setup():
    return {"user": "admin"}

def test_actual():
    data = helper_setup()
    assert data["user"] == "admin"
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)

    def test_pytest_raises_counts_as_assertion(self):
        code = """
import pytest

def test_with_raises():
    with pytest.raises(ValueError):
        raise ValueError("Invalid")
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertNotIn("SHAM006", rules)


if __name__ == "__main__":
    unittest.main()
