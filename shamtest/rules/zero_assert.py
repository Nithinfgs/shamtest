"""Detection of test functions containing zero assertions (SHAM006)."""

from __future__ import annotations

import ast
from typing import List

from shamtest.models import Issue, Severity
from shamtest.rules.base import Context, Rule


def _is_test_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Determine whether a function is considered a test."""
    name = node.name.lower()
    return name.startswith("test_") or name.startswith("test")


def _contains_assertion(node: ast.AST) -> bool:
    """Check if AST subtree contains any assert statement or testing assertion call."""
    for sub in ast.walk(node):
        # 1. Native `assert ...`
        if isinstance(sub, ast.Assert):
            return True

        # 2. Call to self.assert* or mock.assert_* or pytest.fail / self.fail
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Attribute):
                attr = func.attr
                if attr.startswith("assert_") or attr.startswith("assert"):
                    return True
                if attr == "fail":  # self.fail() or pytest.fail()
                    return True
            elif isinstance(func, ast.Name):
                if func.id in ("assert_that", "verify", "check"):
                    return True

        # 3. Context manager like `with pytest.raises(...)` or `with self.assertRaises(...)`
        if isinstance(sub, (ast.With, ast.AsyncWith)):
            for item in sub.items:
                ctx_expr = item.context_expr
                if isinstance(ctx_expr, ast.Call):
                    func = ctx_expr.func
                    if isinstance(func, ast.Attribute) and func.attr in ("raises", "warns", "assertRaises"):
                        return True
                    if isinstance(func, ast.Name) and func.id in ("raises", "assertRaises"):
                        return True

    return False


class ZeroAssertionRule(Rule):
    """SHAM006: Flags test functions that contain zero assertions or expectations."""

    rule_id = "SHAM006"
    description = "Test function contains zero assertions"
    severity = Severity.ERROR

    def inspect_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, context: Context
    ) -> List[Issue]:
        issues: List[Issue] = []

        if not _is_test_function(func_node):
            return issues

        # Skip empty functions or stub functions with only `pass` or `...`
        body = [stmt for stmt in func_node.body if not (
            isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)  # docstring
        )]
        if not body or (len(body) == 1 and isinstance(body[0], ast.Pass)):
            # Trivial stub/placeholder test
            issue = context.create_issue(
                rule_id=self.rule_id,
                message=f"Empty/stub test function '{func_node.name}()' contains only 'pass' or docstring.",
                node=func_node,
                severity=Severity.WARNING,
                fix_suggestion="Implement real test logic or remove placeholder test.",
            )
            if issue:
                issues.append(issue)
            return issues

        # Check for assertions in the function body
        has_assert = any(_contains_assertion(stmt) for stmt in body)
        if not has_assert:
            issue = context.create_issue(
                rule_id=self.rule_id,
                message=(
                    f"Test function '{func_node.name}()' executes code but contains ZERO assertions. "
                    "This test will pass even if the code returns incorrect results or fails silently."
                ),
                node=func_node,
                severity=self.severity,
                fix_suggestion="Add explicit assertions on the return value, state change, or mock invocations.",
            )
            if issue:
                issues.append(issue)

        return issues
