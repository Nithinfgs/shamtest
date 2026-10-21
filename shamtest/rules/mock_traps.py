"""Detection of mock-related traps and deceptive assertions (SHAM003, SHAM004, SHAM005, SHAM010)."""

from __future__ import annotations

import ast
from typing import List, Set

from shamtest.models import Issue, Severity
from shamtest.rules.base import Context, Rule

VALID_MOCK_ASSERT_METHODS = {
    "assert_called",
    "assert_called_once",
    "assert_called_with",
    "assert_called_once_with",
    "assert_any_call",
    "assert_has_calls",
    "assert_not_called",
}

COMMON_MOCK_NAMES = {
    "Mock",
    "MagicMock",
    "AsyncMock",
    "NonCallableMock",
    "PropertyMock",
    "create_autospec",
}


def _is_mock_constructor(node: ast.AST) -> bool:
    """Check if an AST node is a call constructing a mock object."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in COMMON_MOCK_NAMES
    if isinstance(func, ast.Attribute):
        return func.attr in COMMON_MOCK_NAMES
    return False


class MockTrapsRule(Rule):
    """Detects mock traps including uninvoked assertions, method typos, and bare conditions."""

    rule_id = "SHAM004"
    description = "Mock assertion traps (uncalled assertions, typos, truthiness traps)"
    severity = Severity.ERROR

    def inspect_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, context: Context
    ) -> List[Issue]:
        issues: List[Issue] = []
        mock_vars: Set[str] = set()

        # Step 1: Detect mock variables assigned in this function
        for stmt in ast.walk(func_node):
            if isinstance(stmt, ast.Assign):
                if _is_mock_constructor(stmt.value):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            mock_vars.add(target.id)
            elif isinstance(stmt, ast.AnnAssign) and stmt.value:
                if _is_mock_constructor(stmt.value) and isinstance(stmt.target, ast.Name):
                    mock_vars.add(stmt.target.id)

        # Detect mock arguments from @patch or fixtures (arguments named *mock or *patch)
        for arg in func_node.args.args:
            name_lower = arg.arg.lower()
            if "mock" in name_lower or "patch" in name_lower or name_lower.startswith("m_"):
                mock_vars.add(arg.arg)

        # Step 2: Traverse statements in function looking for mock traps
        for node in ast.walk(func_node):
            # Trait A: SHAM004 - Mock assertion missing call ()
            # e.g., `mock_service.assert_called_once` as an ast.Expr statement
            if isinstance(node, ast.Expr):
                val = node.value
                if isinstance(val, ast.Attribute) and val.attr in VALID_MOCK_ASSERT_METHODS:
                    issue = context.create_issue(
                        rule_id="SHAM004",
                        message=(
                            f"Uncalled mock assertion '{ast.unparse(val)}'. Missing '()' parentheses. "
                            "This attribute reference evaluates to a bound method and silently passes without executing an assertion."
                        ),
                        node=node,
                        severity=Severity.ERROR,
                        fix_suggestion=f"Add parentheses: '{ast.unparse(val)}()'.",
                    )
                    if issue:
                        issues.append(issue)

                # Trait D: SHAM010 - Standalone mock condition without assert
                # e.g., `mock_obj.called` or `mock.call_count == 1` as a statement
                elif isinstance(val, ast.Attribute) and val.attr in ("called", "call_count"):
                    obj_name = ast.unparse(val.value)
                    if obj_name in mock_vars or "mock" in obj_name.lower():
                        issue = context.create_issue(
                            rule_id="SHAM010",
                            message=(
                                f"Standalone mock attribute '{ast.unparse(val)}' as a statement. "
                                "This condition is never asserted and will silently pass."
                            ),
                            node=node,
                            severity=Severity.ERROR,
                            fix_suggestion=f"Wrap in assert: 'assert {ast.unparse(val)}'.",
                        )
                        if issue:
                            issues.append(issue)

                elif isinstance(val, ast.Compare):
                    # e.g., `mock.call_count == 1` as standalone statement
                    left_str = ast.unparse(val.left)
                    if any(m in left_str for m in ("called", "call_count")):
                        issue = context.create_issue(
                            rule_id="SHAM010",
                            message=(
                                f"Comparison '{ast.unparse(val)}' used as a statement without assert. "
                                "Expression evaluates and discards result, never failing."
                            ),
                            node=node,
                            severity=Severity.ERROR,
                            fix_suggestion=f"Prefix with assert: 'assert {ast.unparse(val)}'.",
                        )
                        if issue:
                            issues.append(issue)

            # Trait B: SHAM005 - Mock assertion method typo
            # e.g., `mock.asser_called()` or `mock.assert_called_once_with_args()`
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    attr = func.attr
                    # Check if attribute looks like an assertion typo
                    if (
                        attr.startswith("assert_")
                        or attr.startswith("asser_")
                        or attr.startswith("asserts_")
                    ) and attr not in VALID_MOCK_ASSERT_METHODS:
                        # Make sure it's on a mock object, not self (unittest)
                        base_str = ast.unparse(func.value)
                        if base_str != "self":
                            issue = context.create_issue(
                                rule_id="SHAM005",
                                message=(
                                    f"Non-existent mock assertion method '{attr}()' called on '{base_str}'. "
                                    "Python's Mock dynamically accepts undefined methods, so this call silently returns a new Mock and NEVER asserts!"
                                ),
                                node=node,
                                severity=Severity.ERROR,
                                fix_suggestion=f"Replace with a valid mock assertion method, such as: {', '.join(sorted(VALID_MOCK_ASSERT_METHODS))}.",
                            )
                            if issue:
                                issues.append(issue)

            # Trait C: SHAM003 - Truthiness check on Mock object
            # e.g., `assert mock_obj` or `self.assertTrue(mock_obj)`
            elif isinstance(node, ast.Assert):
                test = node.test
                if isinstance(test, ast.Name) and test.id in mock_vars:
                    issue = context.create_issue(
                        rule_id="SHAM003",
                        message=(
                            f"Truthiness assertion 'assert {test.id}' on Mock object. "
                            "In Python, bool(Mock()) is always True, so this assertion passes even if the function failed or returned an empty mock!"
                        ),
                        node=node,
                        severity=Severity.ERROR,
                        fix_suggestion=f"Assert specific properties or call history: 'assert {test.id}.called' or '{test.id}.assert_called_once()'.",
                    )
                    if issue:
                        issues.append(issue)

        return issues
