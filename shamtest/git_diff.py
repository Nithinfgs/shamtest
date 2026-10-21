"""Git diff inspection utilities for shamtest."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set


def get_git_modified_test_files(
    staged: bool = False,
    base_ref: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> List[str]:
    """Retrieve list of modified Python test files from git."""
    work_dir = str(cwd or Path.cwd())

    cmd = ["git", "diff", "--name-only", "--diff-filter=d"]
    if staged:
        cmd.append("--cached")
    elif base_ref:
        cmd.extend([f"{base_ref}...HEAD"])

    try:
        res = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        files = res.stdout.splitlines()
    except (subprocess.SubprocessError, FileNotFoundError):
        return []

    # Also capture untracked test files if running working-tree diff
    if not staged and not base_ref:
        try:
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            for line in status_res.stdout.splitlines():
                if line.startswith("?? "):
                    files.append(line[3:].strip())
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    test_files: List[str] = []
    for f in files:
        f_norm = f.strip()
        if f_norm.endswith(".py") and ("test" in f_norm.lower()):
            test_files.append(f_norm)

    return sorted(list(set(test_files)))


def get_changed_lines_map(
    file_path: str,
    staged: bool = False,
    base_ref: Optional[str] = None,
    cwd: Optional[Path] = None,
) -> Optional[Set[int]]:
    """Parse unified diff to get changed line numbers in file_path."""
    work_dir = str(cwd or Path.cwd())
    cmd = ["git", "diff", "-U0"]
    if staged:
        cmd.append("--cached")
    elif base_ref:
        cmd.extend([f"{base_ref}...HEAD"])
    cmd.extend(["--", file_path])

    try:
        res = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

    changed_lines: Set[int] = set()
    # Parse @@ -a,b +c,d @@ hunk headers
    hunk_pattern = re.compile(r"^@@\s+-\d+(?:,\d+)?\s+\+(\d+)(?:,(\d+))?\s+@@")

    for line in res.stdout.splitlines():
        match = hunk_pattern.match(line)
        if match:
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) else 1
            for l in range(start, start + count):
                changed_lines.add(l)

    return changed_lines if changed_lines else None
