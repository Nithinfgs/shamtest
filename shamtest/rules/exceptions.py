"""Detection of swallowed exceptions and overly broad error handling in tests (SHAM007, SHAM008)."""

from __future__ import annotations

import ast
from typing import List

from shamtest.models import Issue, Severity
from shamtest.rules.base import Context, Rule


class ExceptionHandlingRules(Rule):
    """Detects swallowed exceptions and overly broad exception captures in tests."""

    rule_id = "SHAM007"
    description = "Swallowed exceptions and overly broad error tests"
    severity = Severity.ERROR

    def inspect_function(
        self, func_node: ast.FunctionDef | ast.AsyncFunctionDef, context: Context
    ) -> List[Issue]:
        issues: List[Issue] = []

        for node in ast.walk(func_node):
            # 1. SHAM007: `try: ... except: pass` in tests
            if isinstance(node, ast.Try):
                for handler in node.handlers:
                    body = [
                        stmt for stmt in handler.body
                        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
                    ]
                    # If body is just `pass` or empty
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        # Check if try block had a pytest.fail() or self.fail()
                        has_fail = any(
                            isinstance(sub, ast.Call)
                            and (
                                (isinstance(sub.func, ast.Attribute) and sub.func.attr == "fail")
                                or (isinstance(sub.func, ast.Name) and sub.func.id == "fail")
                            )
                            for sub in ast.walk(node)
                        )
                        if not has_fail:
                            exc_name = ast.unparse(handler.type) if handler.type else "all exceptions"
                            issue = context.create_issue(
                                rule_id="SHAM007",
                                message=(
                                    f"Swallowed exception: 'try ... except {exc_name}: pass' in test. "
                                    "If the code does not raise an exception, the test will falsely pass anyway."
                                ),
                                node=handler,
                                severity=Severity.ERROR,
                                fix_suggestion="Use 'pytest.raises(SpecificException)' or 'self.assertRaises(SpecificException)' instead of swallowing in try/except.",
                            )
                            if issue:
                                issues.append(issue)

            # 2. SHAM008: Overly broad exception capture like `pytest.raises(Exception)`
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    expr = item.context_expr
                    if isinstance(expr, ast.Call):
                        func = expr.func
                        is_raises = False
                        if isinstance(func, ast.Attribute) and func.attr in ("raises", "assertRaises"):
                            is_raises = True
                        elif isinstance(func, ast.Name) and func.id in ("raises", "assertRaises"):
                            is_raises = True

                        if is_raises and expr.args:
                            first_arg = expr.args[0]
                            arg_str = ast.unparse(first_arg).strip()
                            if arg_str in ("Exception", "BaseException"):
                                issue = context.create_issue(
                                    rule_id="SHAM008",
                                    message=(
                                        f"Overly broad '{ast.unparse(expr)}'. Catching '{arg_str}' masks fundamental "
                                        "programming bugs (such as NameError, TypeError, AttributeError, or broken imports)."
                                    ),
                                    node=expr,
                                    severity=Severity.WARNING,
                                    fix_suggestion=f"Catch a specific exception class (e.g. ValueError, KeyError) instead of '{arg_str}'.",
                                )
                                if issue:
                                    issues.append(issue)

        return issues
