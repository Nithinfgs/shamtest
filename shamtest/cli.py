"""Command-line interface entrypoint for shamtest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set

from shamtest.analyzer import Analyzer
from shamtest.config import Config
from shamtest.formatter import format_json, format_sarif, format_terminal
from shamtest.git_diff import get_changed_lines_map, get_git_modified_test_files
from shamtest.models import Severity

__version__ = "0.1.0"


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="shamtest",
        description="Catch sham, tautological, and mock-poisoned tests before they merge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  shamtest tests/                     Scan tests directory
  shamtest --diff                     Scan only modified test files in git working tree
  shamtest --staged                   Scan staged test files in pre-commit hook
  shamtest --base main                Scan test changes relative to main branch
  shamtest --fail-on warning          Fail on warnings or errors
  shamtest --max-hollow-index 15.0    Fail if hollow test proportion exceeds 15%
  shamtest --json                     Emit JSON report for CI pipelines
  shamtest --sarif > results.sarif    Export GitHub Security Code Scanning SARIF
""",
    )

    parser.add_argument(
        "paths",
        nargs="*",
        default=[],
        help="Test files or directories to scan (default: tests/ or current directory)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Scan only modified test files in git working tree",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Scan only git staged test files (ideal for pre-commit hooks)",
    )
    parser.add_argument(
        "--base",
        metavar="REF",
        help="Compare against git base branch (e.g., 'main' or 'origin/main')",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON report",
    )
    parser.add_argument(
        "--sarif",
        action="store_true",
        help="Output SARIF v2.1.0 format for GitHub Code Scanning integration",
    )
    parser.add_argument(
        "--fail-on",
        choices=["error", "warning", "never"],
        default=None,
        help="Exit with non-zero code on specified severity (default: error)",
    )
    parser.add_argument(
        "--max-hollow-index",
        type=float,
        metavar="PCT",
        help="Maximum allowable Hollow Test Index percentage before failing (e.g., 10.0)",
    )
    parser.add_argument(
        "--ignore",
        metavar="RULES",
        help="Comma-separated list of rule IDs to ignore (e.g., 'SHAM002,SHAM008')",
    )
    parser.add_argument(
        "--min-severity",
        choices=["warning", "error"],
        default=None,
        help="Minimum severity level to report",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose details",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"shamtest {__version__}",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI execution flow."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load configuration
    config = Config.load()

    # CLI flags override config
    if args.ignore:
        cli_ignores = {r.strip().upper() for r in args.ignore.split(",") if r.strip()}
        config.ignore_rules.update(cli_ignores)
    if args.fail_on:
        config.fail_on = args.fail_on.upper()
    if args.min_severity:
        config.min_severity = args.min_severity.upper()
    if args.max_hollow_index is not None:
        config.max_hollow_index = args.max_hollow_index

    analyzer = Analyzer(config=config)

    # Determine files to scan
    diff_lines_map: dict[str, Set[int]] = {}

    if args.diff or args.staged or args.base:
        git_files = get_git_modified_test_files(
            staged=args.staged,
            base_ref=args.base,
        )
        if not git_files:
            if not args.json and not args.sarif:
                print("No modified Python test files detected in git diff.")
            return 0

        target_paths = [Path(f).resolve() for f in git_files]
        # Collect changed line numbers for diff-scoped filtering
        for f in git_files:
            lines = get_changed_lines_map(
                f,
                staged=args.staged,
                base_ref=args.base,
            )
            if lines:
                diff_lines_map[str(Path(f).resolve())] = lines
    else:
        search_paths = args.paths if args.paths else (["tests"] if Path("tests").exists() else ["."])
        target_paths = analyzer.discover_files(search_paths)

    if not target_paths:
        if not args.json and not args.sarif:
            print("No test files found to scan.")
        return 0

    # Execute scan
    summary = analyzer.scan_files(target_paths, diff_lines_map=diff_lines_map)

    # Format output
    if args.json:
        print(format_json(summary))
    elif args.sarif:
        print(format_sarif(summary))
    else:
        print(format_terminal(summary, verbose=args.verbose))

    # Determine exit code
    if config.fail_on == "NEVER":
        return 0

    # Check Hollow Test Index threshold
    if config.max_hollow_index is not None:
        if summary.hollow_test_index > config.max_hollow_index:
            if not args.json and not args.sarif:
                print(
                    f"Failure: Hollow Test Index ({summary.hollow_test_index}%) exceeds "
                    f"configured limit ({config.max_hollow_index}%).",
                    file=sys.stderr,
                )
            return 1

    # Check error/warning counts
    if config.fail_on == "WARNING":
        if summary.error_count > 0 or summary.warning_count > 0:
            return 1
    else:  # ERROR
        if summary.error_count > 0:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
