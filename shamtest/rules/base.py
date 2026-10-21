"""Base classes for shamtest inspection rules."""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set

from shamtest.models import Issue, Severity


class Context:
    """Carries contextual metadata and file source during AST traversal."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.current_function: Optional[str] = None
        self.current_function_node: Optional[ast.FunctionDef | ast.AsyncFunctionDef] = None
        self.mock_variables: Set[str] = set()
        self.mock_return_values: Dict[str, ast.AST] = {}
        self.suppressions: Dict[int, Set[str]] = self._parse_suppressions()

    def _parse_suppressions(self) -> Dict[int, Set[str]]:
        """Parse inline suppression comments like `# shamtest: disable=SHAM001,SHAM002`."""
        suppressions: Dict[int, Set[str]] = {}
        for line_idx, line in enumerate(self.source_lines, start=1):
            line_str = line.strip()
            if "#" not in line_str:
                continue
            comment_part = line_str.split("#", 1)[1].strip()
            # Support # shamtest: disable=RULE1,RULE2 or # shamtest: ignore or # noqa: shamtest
            if "shamtest: disable=" in comment_part:
                rules_str = comment_part.split("shamtest: disable=", 1)[1].split()[0]
                rules = {r.strip().upper() for r in rules_str.split(",") if r.strip()}
                suppressions[line_idx] = rules
            elif "shamtest: ignore" in comment_part or "noqa: shamtest" in comment_part or comment_part == "noqa":
                suppressions[line_idx] = {"ALL"}
        return suppressions

    def is_suppressed(self, rule_id: str, line_number: int) -> bool:
        """Check if a rule is suppressed on the given line."""
        rules = self.suppressions.get(line_number)
        if not rules:
            # Also check the previous line (comment above)
            rules = self.suppressions.get(line_number - 1)
        if not rules:
            return False
        return "ALL" in rules or rule_id.upper() in rules

    def get_source_line(self, line_number: int) -> Optional[str]:
        """Retrieve the raw source line safely."""
        if 1 <= line_number <= len(self.source_lines):
            return self.source_lines[line_number - 1]
        return None

    def create_issue(
        self,
        rule_id: str,
        message: str,
        node: ast.AST,
        severity: Severity = Severity.ERROR,
        fix_suggestion: Optional[str] = None,
    ) -> Optional[Issue]:
        """Helper to create an issue if not suppressed."""
        line = getattr(node, "lineno", 1)
        col = getattr(node, "col_offset", 0)
        end_line = getattr(node, "end_lineno", line)
        end_col = getattr(node, "end_col_offset", col)

        if self.is_suppressed(rule_id, line):
            return None

        snippet = self.get_source_line(line)
        if snippet:
            snippet = snippet.strip()

        return Issue(
            rule_id=rule_id,
            message=message,
            file_path=self.file_path,
            line_number=line,
            column=col,
            end_line=end_line,
            end_column=end_col,
            function_name=self.current_function,
            code_snippet=snippet,
            severity=severity,
            fix_suggestion=fix_suggestion,
        )


class Rule(ABC):
    """Abstract base class for all detection rules."""
    rule_id: str = "SHAM000"
    description: str = "Base rule"
    severity: Severity = Severity.ERROR

    def inspect_node(self, node: ast.AST, context: Context) -> List[Issue]:
        """Inspect a single AST node. Default returns empty."""
        return []

    def inspect_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, context: Context
    ) -> List[Issue]:
        """Inspect an entire test function body. Default returns empty."""
        return []
