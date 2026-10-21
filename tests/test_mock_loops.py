"""Unit tests for self-validating mock loops (SHAM009)."""

import unittest
from shamtest.analyzer import Analyzer


class TestMockLoops(unittest.TestCase):
    def setUp(self):
        self.analyzer = Analyzer()

    def test_direct_mock_loop(self):
        code = """
from unittest.mock import Mock

def test_loop():
    mock_api = Mock()
    mock_api.fetch.return_value = 42
    res = mock_api.fetch()
    assert res == 42
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        rules = [i.rule_id for i in report.issues]
        self.assertIn("SHAM009", rules)

    def test_mock_passed_to_real_service_passes_clean(self):
        code = """
from unittest.mock import Mock

def test_real_integration():
    mock_repo = Mock()
    mock_repo.get_user.return_value = {"id": 1, "role": "admin"}
    service = UserService(repo=mock_repo)
    is_admin = service.check_admin(1)
    assert is_admin is True
"""
        report = self.analyzer.scan_source(code, "test_file.py")
        self.assertEqual(len(report.issues), 0)


if __name__ == "__main__":
    unittest.main()
