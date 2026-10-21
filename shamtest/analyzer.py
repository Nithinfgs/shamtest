"""Core AST static analyzer engine for shamtest."""

from __future__ import annotations

import ast
import fnmatch
import time
from pathlib import Path
from typing import List, Optional, Set

from shamtest.config import Config
from shamtest.models import FileReport, Issue, ScanSummary, Severity, TestFunctionStats
from shamtest.rules import ALL_RULES, Rule
from shamtest.rules.base import Context


class Analyzer:
    """Orchestrates parsing and rule execution across test files."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.rules: List[Rule] = [rule_cls() for rule_cls in ALL_RULES]

    def is_excluded(self, path: Path) -> bool:
        """Check if path matches any exclusion pattern."""
        path_str = str(path)
        for pat in self.config.exclude_patterns:
            if fnmatch.fnmatch(path_str, f"*{pat}*") or pat in path.parts:
                return True
        return False

    def discover_files(self, paths: List[str]) -> List[Path]:
        """Find Python test files matching paths, directories, or globs."""
        found: List[Path] = []
        for p_str in paths:
            p = Path(p_str)
            if p.is_file():
                if p.suffix == ".py" and not self.is_excluded(p):
                    found.append(p.resolve())
            elif p.is_dir():
                for sub in p.rglob("*.py"):
                    if not self.is_excluded(sub):
                        name_lower = sub.name.lower()
                        if (
                            name_lower.startswith("test_")
                            or name_lower.endswith("_test.py")
                            or "tests" in sub.parts
                        ):
                            found.append(sub.resolve())
        return sorted(list(set(found)))

    def scan_source(
        self,
        source_code: str,
        file_path: str = "<stdin>",
        changed_lines: Optional[Set[int]] = None,
    ) -> FileReport:
        """Analyze Python source code string for sham test patterns."""
        report = FileReport(file_path=file_path)

        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            report.issues.append(
                Issue(
                    rule_id="SHAM000",
                    message=f"SyntaxError parsing test file: {e.msg}",
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    column=e.offset or 0,
                    severity=Severity.ERROR,
                )
            )
            return report

        context = Context(file_path=file_path, source_code=source_code)

        # Traverse the AST, tracking function scope
        for top_node in ast.iter_child_nodes(tree):
            # Check module-level statements
            if isinstance(top_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._inspect_function_def(top_node, context, report, changed_lines)
            elif isinstance(top_node, ast.ClassDef):
                # Inspect test classes (e.g., unittest.TestCase)
                for class_child in ast.iter_child_nodes(top_node):
                    if isinstance(class_child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self._inspect_function_def(class_child, context, report, changed_lines)
                    else:
                        self._inspect_node_recursive(class_child, context, report, changed_lines)
            else:
                self._inspect_node_recursive(top_node, context, report, changed_lines)

        return report

    def _inspect_function_def(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        context: Context,
        report: FileReport,
        changed_lines: Optional[Set[int]],
    ) -> None:
        """Inspect a function definition and its children in its own scope."""
        old_func = context.current_function
        old_node = context.current_function_node

        context.current_function = func_node.name
        context.current_function_node = func_node

        func_stats: Optional[TestFunctionStats] = None
        is_test = func_node.name.startswith("test_") or func_node.name.startswith("test")
        if is_test:
            func_stats = TestFunctionStats(
                name=func_node.name,
                line_number=func_node.lineno,
            )
            report.tests.append(func_stats)

        # 1. Run function-level rules
        for rule in self.rules:
            issues = rule.inspect_function(func_node, context)
            for issue in issues:
                if self._should_include_issue(issue, changed_lines):
                    report.issues.append(issue)
                    if func_stats and issue not in func_stats.issues:
                        func_stats.issues.append(issue)

        # 2. Run node-level rules recursively inside this function
        for child in ast.walk(func_node):
            if child is func_node:
                continue
            for rule in self.rules:
                issues = rule.inspect_node(child, context)
                for issue in issues:
                    if self._should_include_issue(issue, changed_lines):
                        report.issues.append(issue)
                        if func_stats and issue not in func_stats.issues:
                            func_stats.issues.append(issue)

        context.current_function = old_func
        context.current_function_node = old_node

    def _inspect_node_recursive(
        self,
        node: ast.AST,
        context: Context,
        report: FileReport,
        changed_lines: Optional[Set[int]],
    ) -> None:
        """Inspect module-level non-function AST nodes."""
        for child in ast.walk(node):
            for rule in self.rules:
                issues = rule.inspect_node(child, context)
                for issue in issues:
                    if self._should_include_issue(issue, changed_lines):
                        report.issues.append(issue)

    def _should_include_issue(
        self, issue: Issue, changed_lines: Optional[Set[int]] = None
    ) -> bool:
        """Determine if issue passes ignore rules, changed-lines filter, and min severity."""
        if issue.rule_id in self.config.ignore_rules:
            return False

        if self.config.min_severity == "ERROR" and issue.severity != Severity.ERROR:
            return False

        if changed_lines is not None:
            if issue.line_number not in changed_lines:
                return False

        return True

    def scan_files(
        self,
        file_paths: List[Path],
        diff_lines_map: Optional[dict[str, Set[int]]] = None,
    ) -> ScanSummary:
        """Scan a list of files and produce a summary report."""
        start_time = time.perf_counter()
        summary = ScanSummary(files_scanned=len(file_paths))

        for path in file_paths:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                changed_lines = diff_lines_map.get(str(path)) if diff_lines_map else None
                file_report = self.scan_source(
                    content,
                    file_path=str(path),
                    changed_lines=changed_lines,
                )
                summary.tests_scanned += file_report.test_count
                summary.file_reports.append(file_report)
            except Exception as e:
                summary.file_reports.append(
                    FileReport(
                        file_path=str(path),
                        issues=[
                            Issue(
                                rule_id="SHAM000",
                                message=f"Failed to read file: {e}",
                                file_path=str(path),
                                line_number=1,
                                severity=Severity.ERROR,
                            )
                        ],
                    )
                )

        summary.duration_ms = (time.perf_counter() - start_time) * 1000.0
        return summary
