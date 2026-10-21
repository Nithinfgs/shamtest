"""Detection of self-validating mock loops (SHAM009)."""

from __future__ import annotations

import ast
from typing import Dict, List, Set

from shamtest.models import Issue, Severity
from shamtest.rules.base import Context, Rule


def _ast_to_code(node: ast.AST) -> str:
    """Normalize AST node to string."""
    try:
        return ast.unparse(node).strip()
    except Exception:
        return ""


class SelfValidatingMockLoopRule(Rule):
    """SHAM009: Flags tests that only test unittest.mock against itself."""

    rule_id = "SHAM009"
    description = "Self-validating mock loop testing mock against mock return value"
    severity = Severity.ERROR

    def inspect_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, context: Context
    ) -> List[Issue]:
        issues: List[Issue] = []

        # Map of mock target expression -> configured return value code
        mock_returns: Dict[str, str] = {}
        # Variables that store return value of mock calls
        assigned_from_mock: Dict[str, str] = {}

        # Scan for `.return_value = ...` assignments
        for stmt in func_node.body:
            if isinstance(stmt, ast.Assign):
                # target.return_value = value
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "return_value":
                        mock_obj_str = _ast_to_code(target.value)
                        val_str = _ast_to_code(stmt.value)
                        mock_returns[mock_obj_str] = val_str

                # var = mock(...)
                if isinstance(stmt.value, ast.Call):
                    call_func_str = _ast_to_code(stmt.value.func)
                    if call_func_str in mock_returns:
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                assigned_from_mock[target.id] = mock_returns[call_func_str]

        # Scan for asserts comparing assigned variable against configured return value
        for node in ast.walk(func_node):
            if isinstance(node, ast.Assert):
                test = node.test
                if isinstance(test, ast.Compare):
                    left_str = _ast_to_code(test.left)
                    for op, right in zip(test.ops, test.comparators):
                        if isinstance(op, ast.Eq):
                            right_str = _ast_to_code(right)
                            # Case 1: assert result == expected_val (where result was from mock return)
                            if left_str in assigned_from_mock and assigned_from_mock[left_str] == right_str:
                                issue = context.create_issue(
                                    rule_id=self.rule_id,
                                    message=(
                                        f"Self-validating mock loop: variable '{left_str}' is assigned from mock, "
                                        f"and asserted directly against the mock's configured return value '{right_str}'. "
                                        "This tests Python's mock library, not your application code."
                                    ),
                                    node=node,
                                    severity=self.severity,
                                    fix_suggestion="Pass the mock into your real application component and assert the component's output or side-effects.",
                                )
                                if issue:
                                    issues.append(issue)

                            # Case 2: assert mock_func() == expected_val
                            elif left_str.endswith("()") and left_str[:-2] in mock_returns:
                                if mock_returns[left_str[:-2]] == right_str:
                                    issue = context.create_issue(
                                        rule_id=self.rule_id,
                                        message=(
                                            f"Direct mock loop: calling '{left_str}' and asserting against its own "
                                            f"configured return_value '{right_str}'. No production code is executed."
                                        ),
                                        node=node,
                                        severity=self.severity,
                                        fix_suggestion="Exercise actual application logic with the mock as a dependency.",
                                    )
                                    if issue:
                                        issues.append(issue)

        return issues
