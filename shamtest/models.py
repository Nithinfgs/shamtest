"""Core data models for shamtest."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """Severity of a detected testing issue."""
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Issue:
    """Represents a specific hollow/sham test issue found in code."""
    rule_id: str
    message: str
    file_path: str
    line_number: int
    column: int = 0
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    function_name: Optional[str] = None
    code_snippet: Optional[str] = None
    severity: Severity = Severity.ERROR
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to a serializable dictionary."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "function_name": self.function_name,
            "code_snippet": self.code_snippet,
            "severity": self.severity.value,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class TestFunctionStats:
    """Metrics and statistics for an individual test function."""
    name: str
    line_number: int
    assert_count: int = 0
    mock_count: int = 0
    issues: List[Issue] = field(default_factory=list)

    @property
    def is_hollow(self) -> bool:
        """Return True if any ERROR or WARNING severity issue was flagged."""
        return any(i.severity in (Severity.ERROR, Severity.WARNING) for i in self.issues)


@dataclass
class FileReport:
    """Inspection results for a single test file."""
    file_path: str
    issues: List[Issue] = field(default_factory=list)
    tests: List[TestFunctionStats] = field(default_factory=list)

    @property
    def test_count(self) -> int:
        return len(self.tests)

    @property
    def hollow_test_count(self) -> int:
        return sum(1 for t in self.tests if t.is_hollow)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "test_count": self.test_count,
            "hollow_test_count": self.hollow_test_count,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class ScanSummary:
    """Overall summary of a shamtest scan run."""
    files_scanned: int = 0
    tests_scanned: int = 0
    file_reports: List[FileReport] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def all_issues(self) -> List[Issue]:
        issues: List[Issue] = []
        for r in self.file_reports:
            issues.extend(r.issues)
        return issues

    @property
    def total_issues(self) -> int:
        return len(self.all_issues)

    @property
    def error_count(self) -> int:
        return sum(r.error_count for r in self.file_reports)

    @property
    def warning_count(self) -> int:
        return sum(r.warning_count for r in self.file_reports)

    @property
    def hollow_tests(self) -> int:
        return sum(r.hollow_test_count for r in self.file_reports)

    @property
    def hollow_test_index(self) -> float:
        """Percentage of scanned tests with sham or hollow patterns."""
        if self.tests_scanned == 0:
            return 0.0
        return round((self.hollow_tests / self.tests_scanned) * 100.0, 1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_scanned": self.files_scanned,
            "tests_scanned": self.tests_scanned,
            "hollow_tests": self.hollow_tests,
            "hollow_test_index_pct": self.hollow_test_index,
            "total_issues": self.total_issues,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "duration_ms": round(self.duration_ms, 2),
            "files": [r.to_dict() for r in self.file_reports if r.issues],
        }
