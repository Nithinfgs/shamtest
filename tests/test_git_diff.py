"""Unit tests for git diff inspection helpers."""

import unittest
from pathlib import Path
from shamtest.git_diff import get_changed_lines_map, get_git_modified_test_files


class TestGitDiff(unittest.TestCase):
    def test_git_modified_test_files_empty_repo_handling(self):
        # When called on empty or non-git directory, returns empty list without crashing
        res = get_git_modified_test_files(cwd=Path("/tmp"))
        self.assertIsInstance(res, list)

    def test_get_changed_lines_map_non_git_dir(self):
        res = get_changed_lines_map("test.py", cwd=Path("/tmp"))
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
