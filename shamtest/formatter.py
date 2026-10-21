"""Output formatters for terminal, JSON, and GitHub SARIF reporting."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

from shamtest.models import Issue, ScanSummary, Severity


class Colors:
    """Terminal ANSI colors with automatic NO_COLOR and tty detection."""
    RED = "\033[91m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def enabled(cls) -> bool:
        """Color is disabled if NO_COLOR is set or output is redirected."""
        if "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb":
            return False
        return sys.stdout.isatty()


def c(text: str, color_code: str) -> str:
    """Wrap text in ANSI color if enabled."""
    if Colors.enabled():
        return f"{color_code}{text}{Colors.RESET}"
    return text


def format_terminal(summary: ScanSummary, verbose: bool = False) -> str:
    """Render human-readable terminal report with code pointers and metrics."""
    lines: List[str] = []

    # Header banner
    lines.append("")
    lines.append(c("shamtest", Colors.BOLD + Colors.CYAN) + c(" — Automated Sham & Hollow Test Detection", Colors.DIM))
    lines.append(c("=" * 64, Colors.DIM))

    if not summary.file_reports or summary.total_issues == 0:
        lines.append("")
        lines.append(f"{c('✓ No sham test patterns detected!', Colors.BOLD + Colors.GREEN)}")
        lines.append(
            c(f"Scanned {summary.tests_scanned} tests across {summary.files_scanned} files in {summary.duration_ms:.1f}ms.", Colors.DIM)
        )
        lines.append("")
        return "\n".join(lines)

    # Group issues by file
    for report in summary.file_reports:
        if not report.issues:
            continue

        lines.append("")
        lines.append(f"{c('File:', Colors.BOLD)} {c(report.file_path, Colors.BOLD + Colors.BLUE)}")

        for issue in report.issues:
            # Severity tag
            if issue.severity == Severity.ERROR:
                tag = c("[ERROR]", Colors.BOLD + Colors.RED)
            elif issue.severity == Severity.WARNING:
                tag = c("[WARNING]", Colors.BOLD + Colors.YELLOW)
            else:
                tag = c("[INFO]", Colors.CYAN)

            loc = f"{issue.line_number}:{issue.column + 1}"
            rule_str = c(issue.rule_id, Colors.BOLD + Colors.MAGENTA)
            func_str = f" in {c(issue.function_name + '()', Colors.CYAN)}" if issue.function_name else ""

            lines.append(f"  {tag} {loc} {rule_str}{func_str}: {issue.message}")

            # Source snippet with pointer
            if issue.code_snippet:
                lines.append(f"    {c('│', Colors.DIM)} {issue.code_snippet}")
                if issue.column > 0:
                    pad = " " * (issue.column + 2)
                    lines.append(f"    {c('│', Colors.DIM)} {pad}{c('^', Colors.BOLD + Colors.RED)}")

            if issue.fix_suggestion:
                lines.append(f"    {c('↳ Fix:', Colors.BOLD + Colors.GREEN)} {c(issue.fix_suggestion, Colors.DIM)}")

    # Footer metrics summary
    lines.append("")
    lines.append(c("-" * 64, Colors.DIM))
    lines.append(c("Inspection Summary:", Colors.BOLD))
    lines.append(f"  Files Scanned:        {summary.files_scanned}")
    lines.append(f"  Total Tests:          {summary.tests_scanned}")
    lines.append(
        f"  Hollow Tests:         {c(str(summary.hollow_tests), Colors.BOLD + Colors.RED if summary.hollow_tests > 0 else Colors.GREEN)}"
    )

    # Hollow test index percentage indicator
    index_str = f"{summary.hollow_test_index:.1f}%"
    if summary.hollow_test_index == 0.0:
        colored_index = c(index_str, Colors.BOLD + Colors.GREEN)
    elif summary.hollow_test_index < 20.0:
        colored_index = c(index_str, Colors.BOLD + Colors.YELLOW)
    else:
        colored_index = c(index_str, Colors.BOLD + Colors.RED)

    lines.append(f"  Hollow Test Index:    {colored_index} (proportion of low-signal / vacuous tests)")
    lines.append(f"  Total Issues:         {summary.total_issues} ({summary.error_count} errors, {summary.warning_count} warnings)")
    lines.append(f"  Scan Duration:        {summary.duration_ms:.1f}ms")
    lines.append("")

    return "\n".join(lines)


def format_json(summary: ScanSummary) -> str:
    """Render machine-readable JSON output."""
    return json.dumps(summary.to_dict(), indent=2)


def format_sarif(summary: ScanSummary) -> str:
    """Render SARIF v2.1.0 JSON format for GitHub Security Code Scanning."""
    sarif: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "shamtest",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/Nithinfgs/shamtest",
                        "rules": [
                            {
                                "id": "SHAM001",
                                "name": "TautologicalAssertion",
                                "shortDescription": {"text": "Tautological assertion that is always true"},
                            },
                            {
                                "id": "SHAM002",
                                "name": "TriviallyTrueAssertion",
                                "shortDescription": {"text": "Trivially true comparison such as len(x) >= 0"},
                            },
                            {
                                "id": "SHAM003",
                                "name": "MockTruthinessTrap",
                                "shortDescription": {"text": "Asserting truthiness of a Mock object"},
                            },
                            {
                                "id": "SHAM004",
                                "name": "UncalledMockAssertion",
                                "shortDescription": {"text": "Mock assertion method missing call parentheses"},
                            },
                            {
                                "id": "SHAM005",
                                "name": "MockMethodTypo",
                                "shortDescription": {"text": "Calling non-existent assertion method on a Mock"},
                            },
                            {
                                "id": "SHAM006",
                                "name": "ZeroAssertionTest",
                                "shortDescription": {"text": "Test function containing zero assertions"},
                            },
                            {
                                "id": "SHAM007",
                                "name": "SwallowedExceptionTest",
                                "shortDescription": {"text": "Swallowed exception via try/except pass in test"},
                            },
                            {
                                "id": "SHAM008",
                                "name": "OverlyBroadExceptionCapture",
                                "shortDescription": {"text": "Overly broad exception capture in test"},
                            },
                            {
                                "id": "SHAM009",
                                "name": "SelfValidatingMockLoop",
                                "shortDescription": {"text": "Asserting mock return value directly against itself"},
                            },
                            {
                                "id": "SHAM010",
                                "name": "StandaloneMockCondition",
                                "shortDescription": {"text": "Mock assertion property evaluated as bare statement"},
                            },
                        ],
                    }
                },
                "results": [
                    {
                        "ruleId": issue.rule_id,
                        "level": "error" if issue.severity == Severity.ERROR else "warning",
                        "message": {"text": issue.message},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": issue.file_path},
                                    "region": {
                                        "startLine": issue.line_number,
                                        "startColumn": issue.column + 1,
                                        "endLine": issue.end_line or issue.line_number,
                                        "endColumn": (issue.end_column or issue.column) + 1,
                                    },
                                }
                            }
                        ],
                    }
                    for issue in summary.all_issues
                ],
            }
        ],
    }
    return json.dumps(sarif, indent=2)
