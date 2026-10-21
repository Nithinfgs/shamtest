"""Detection of tautological and trivially true assertions (SHAM001, SHAM002)."""

from __future__ import annotations

import ast
from typing import List

from shamtest.models import Issue, Severity
from shamtest.rules.base import Context, Rule


def _is_literal_constant(node: ast.AST) -> bool:
    """Check if node is a literal constant (str, int, float, bool, None)."""
    return isinstance(node, ast.Constant)


def _expressions_match(node1: ast.AST, node2: ast.AST) -> bool:
    """Check if two AST expressions are structurally identical."""
    try:
        return ast.unparse(node1) == ast.unparse(node2)
    except Exception:
        return False


class TautologicalAssertionRule(Rule):
    """SHAM001: Flags assertions that can never fail (tautologies)."""

    rule_id = "SHAM001"
    description = "Tautological assertion that is true by definition"
    severity = Severity.ERROR

    def inspect_node(self, node: ast.AST, context: Context) -> List[Issue]:
        issues: List[Issue] = []

        # 1. Native Python `assert ...`
        if isinstance(node, ast.Assert):
            test = node.test

            # assert True / assert 1 / assert "foo"
            if isinstance(test, ast.Constant) and bool(test.value):
                issue = context.create_issue(
                    rule_id=self.rule_id,
                    message=f"Tautological assert with constant '{test.value}'. This assertion always passes without testing anything.",
                    node=node,
                    severity=self.severity,
                    fix_suggestion="Assert a dynamic condition on the function output instead of a literal constant.",
                )
                if issue:
                    issues.append(issue)

            # assert not False
            elif (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and isinstance(test.operand, ast.Constant)
                and not bool(test.operand.value)
            ):
                issue = context.create_issue(
                    rule_id=self.rule_id,
                    message="Tautological 'assert not False' detected.",
                    node=node,
                    severity=self.severity,
                    fix_suggestion="Replace with an assertion on actual system state.",
                )
                if issue:
                    issues.append(issue)

            # assert x == x or assert 1 == 1 or assert x <= x or assert x >= x
            elif isinstance(test, ast.Compare):
                left = test.left
                for op, right in zip(test.ops, test.comparators):
                    if isinstance(op, (ast.Eq, ast.GtE, ast.LtE, ast.Is)):
                        if _expressions_match(left, right):
                            issue = context.create_issue(
                                rule_id=self.rule_id,
                                message=f"Tautological comparison '{ast.unparse(left)} {type(op).__name__} {ast.unparse(right)}'. Identical left and right operands.",
                                node=node,
                                severity=self.severity,
                                fix_suggestion=f"Compare '{ast.unparse(left)}' against an expected independent value, not itself.",
                            )
                            if issue:
                                issues.append(issue)
                                break
                        elif _is_literal_constant(left) and _is_literal_constant(right):
                            val1 = getattr(left, "value", None)
                            val2 = getattr(right, "value", None)
                            if val1 == val2:
                                issue = context.create_issue(
                                    rule_id=self.rule_id,
                                    message=f"Tautological assert comparing constant '{val1}' == '{val2}'.",
                                    node=node,
                                    severity=self.severity,
                                    fix_suggestion="Assert real output instead of hardcoded literal equality.",
                                )
                                if issue:
                                    issues.append(issue)
                                    break

                    # Membership: assert "a" in "abc" or assert 1 in [1, 2]
                    elif isinstance(op, ast.In):
                        if _is_literal_constant(left) and (
                            _is_literal_constant(right) or isinstance(right, (ast.List, ast.Tuple, ast.Set))
                        ):
                            try:
                                l_val = getattr(left, "value", None)
                                if isinstance(right, ast.Constant) and l_val in right.value:
                                    issue = context.create_issue(
                                        rule_id=self.rule_id,
                                        message=f"Tautological membership check: literal '{l_val}' in literal '{right.value}'.",
                                        node=node,
                                        severity=self.severity,
                                        fix_suggestion="Test container output against expected elements.",
                                    )
                                    if issue:
                                        issues.append(issue)
                                        break
                            except Exception:
                                pass

        # 2. unittest assertions: self.assertEqual(x, x), self.assertTrue(True)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "self":
                method_name = func.attr

                # self.assertTrue(True)
                if method_name in ("assertTrue", "assert_") and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and bool(first_arg.value):
                        issue = context.create_issue(
                            rule_id=self.rule_id,
                            message=f"Tautological 'self.{method_name}({first_arg.value})'. Always passes.",
                            node=node,
                            severity=self.severity,
                            fix_suggestion="Assert dynamic conditions or test results.",
                        )
                        if issue:
                            issues.append(issue)

                # self.assertEqual(x, x)
                elif method_name in ("assertEqual", "assertIs", "assertIsEqual") and len(node.args) >= 2:
                    arg1, arg2 = node.args[0], node.args[1]
                    if _expressions_match(arg1, arg2):
                        issue = context.create_issue(
                            rule_id=self.rule_id,
                            message=f"Tautological 'self.{method_name}' comparing identical expression '{ast.unparse(arg1)}' with itself.",
                            node=node,
                            severity=self.severity,
                            fix_suggestion=f"Compare '{ast.unparse(arg1)}' with an expected reference value.",
                        )
                        if issue:
                            issues.append(issue)
                    elif _is_literal_constant(arg1) and _is_literal_constant(arg2):
                        val1 = getattr(arg1, "value", None)
                        val2 = getattr(arg2, "value", None)
                        if val1 == val2:
                            issue = context.create_issue(
                                rule_id=self.rule_id,
                                message=f"Tautological 'self.{method_name}' comparing constant '{val1}' == '{val2}'.",
                                node=node,
                                severity=self.severity,
                                fix_suggestion="Assert actual behavior instead of constant equality.",
                            )
                            if issue:
                                issues.append(issue)

        return issues


class TriviallyTrueAssertionRule(Rule):
    """SHAM002: Flags assertions that check invariants that can never be false."""

    rule_id = "SHAM002"
    description = "Trivially true check (e.g., len(x) >= 0 or status_code != 500)"
    severity = Severity.WARNING

    def inspect_node(self, node: ast.AST, context: Context) -> List[Issue]:
        issues: List[Issue] = []

        # Check `assert len(...) >= 0` or `assert len(...) > -1`
        if isinstance(node, ast.Assert):
            test = node.test
            if isinstance(test, ast.Compare):
                left = test.left
                for op, right in zip(test.ops, test.comparators):
                    # Check if left is `len(...)`
                    if (
                        isinstance(left, ast.Call)
                        and isinstance(left.func, ast.Name)
                        and left.func.id == "len"
                    ):
                        if (
                            isinstance(op, ast.GtE)
                            and isinstance(right, ast.Constant)
                            and right.value == 0
                        ):
                            issue = context.create_issue(
                                rule_id=self.rule_id,
                                message="Trivially true check 'len(...) >= 0'. The length of any sequence in Python is always >= 0.",
                                node=node,
                                severity=self.severity,
                                fix_suggestion="Assert an exact expected length (e.g., len(...) == 3) or assert non-empty (len(...) > 0).",
                            )
                            if issue:
                                issues.append(issue)

                        elif (
                            isinstance(op, ast.Gt)
                            and isinstance(right, ast.Constant)
                            and right.value == -1
                        ):
                            issue = context.create_issue(
                                rule_id=self.rule_id,
                                message="Trivially true check 'len(...) > -1'. Length is always non-negative.",
                                node=node,
                                severity=self.severity,
                                fix_suggestion="Assert specific expected count or elements.",
                            )
                            if issue:
                                issues.append(issue)

                    # Check status_code != 500
                    if (
                        isinstance(left, ast.Attribute)
                        and left.attr in ("status_code", "status")
                        and isinstance(op, ast.NotEq)
                        and isinstance(right, ast.Constant)
                        and right.value == 500
                    ):
                        issue = context.create_issue(
                            rule_id=self.rule_id,
                            message=f"Vacuous status check '{ast.unparse(left)} != 500'. Silently passes 400, 401, 403, 404, and other error statuses.",
                            node=node,
                            severity=self.severity,
                            fix_suggestion="Assert the specific expected HTTP status code (e.g., status_code == 200).",
                        )
                        if issue:
                            issues.append(issue)

        # Also check unittest: self.assertGreaterEqual(len(x), 0)
        elif isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
                and func.attr in ("assertGreaterEqual", "assert_greater_equal")
                and len(node.args) >= 2
            ):
                first_arg, second_arg = node.args[0], node.args[1]
                if (
                    isinstance(first_arg, ast.Call)
                    and isinstance(first_arg.func, ast.Name)
                    and first_arg.func.id == "len"
                    and isinstance(second_arg, ast.Constant)
                    and second_arg.value == 0
                ):
                    issue = context.create_issue(
                        rule_id=self.rule_id,
                        message="Trivially true 'self.assertGreaterEqual(len(...), 0)'. Sequence length is always >= 0.",
                        node=node,
                        severity=self.severity,
                        fix_suggestion="Assert an exact count or non-empty sequence.",
                    )
                    if issue:
                        issues.append(issue)

        return issues
