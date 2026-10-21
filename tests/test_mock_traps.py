"""Unit tests for mock-related assertion traps (SHAM003, SHAM004, SHAM005, SHAM010)."""

import unittest
from shamtest.analyzer import Analyzer
from shamtest.models import Severity


class TestMockTraps(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_mock_truthiness_assertion(self):
        code = """
from unittest.mock import Mock

def test_truthiness():
    m = Mock()
    assert m
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM003", rules)

    def test_uncalled_mock_assertion_missing_parens(self):
        code = """
from unittest.mock import Mock

def test_uncalled():
    m = Mock()
    m.do_something()
    m.assert_called_once
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM004", rules)

    def test_mock_assertion_method_typo(self):
        code = """
from unittest.mock import Mock

def test_typo():
    client_mock = Mock()
    client_mock.call()
    client_mock.asser_called()
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM005", rules)

    def test_standalone_mock_called_property(self):
        code = """
from unittest.mock import Mock

def test_standalone():
    worker_mock = Mock()
    worker_mock.run()
    worker_mock.called
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM010", rules)

    def test_proper_mock_assertions_pass(self):
        code = """
from unittest.mock import Mock

def test_proper():
    m = Mock()
    m.perform(123)
    m.perform.assert_called_once_with(123)
    assert m.called is True
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)


if __name__ == "__main__":
    unittest.main()
