"""Unit tests for tautological and trivially true assertion rules (SHAM001, SHAM002)."""

import unittest
from shamtest.analyzer import Analyzer
from shamtest.models import Severity


class TestTautologyRules(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_assert_constant_true(self):
        code = """
def test_foo():
    assert True
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM001")
        self.assertEqual(report.issues[0].severity, Severity.ERROR)

    def test_assert_identical_variable_comparison(self):
        code = """
def test_bar():
    x = 42
    assert x == x
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM001")
        self.assertIn("Identical left and right operands", report.issues[0].message)

    def test_assert_identical_attribute_comparison(self):
        code = """
def test_obj():
    assert resp.status == resp.status
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM001")

    def test_assert_literal_constant_equality(self):
        code = """
def test_literals():
    assert "abc" == "abc"
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM001")

    def test_unittest_assert_equal_self_tautology(self):
        code = """
class MyTestCase(unittest.TestCase):
    def test_case(self):
        val = 10
        self.assertEqual(val, val)
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM001")

    def test_trivially_true_length_non_negative(self):
        code = """
def test_len():
    items = []
    assert len(items) >= 0
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM002")
        self.assertEqual(report.issues[0].severity, Severity.WARNING)

    def test_vacuous_status_code_check(self):
        code = """
def test_http():
    res = client.get("/")
    assert res.status_code != 500
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 1)
        self.assertEqual(report.issues[0].rule_id, "SHAM002")

    def test_valid_assertions_pass_cleanly(self):
        code = """
def test_valid():
    x = calculate(2)
    assert x == 4
    assert len(x.items) == 2
    assert x.status_code == 200
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)

    def test_inline_suppression(self):
        code = """
def test_suppressed():
    assert True  # shamtest: disable=SHAM001
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)


if __name__ == "__main__":
    unittest.main()
