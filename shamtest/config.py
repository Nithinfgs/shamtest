"""Configuration loading for shamtest."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None  # type: ignore


@dataclass
class Config:
    """Runtime configuration for shamtest scans."""
    ignore_rules: Set[str] = field(default_factory=set)
    exclude_patterns: List[str] = field(default_factory=lambda: [
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
    ])
    fail_on: str = "ERROR"  # "ERROR" or "WARNING"
    min_severity: str = "WARNING"
    max_hollow_index: Optional[float] = None  # Max allowed Hollow Test Index %

    @classmethod
    def load(cls, search_dir: Optional[Path] = None) -> Config:
        """Find and load configuration from .shamtest.toml or pyproject.toml."""
        target_dir = search_dir or Path.cwd()

        # Check .shamtest.toml
        dot_conf = target_dir / ".shamtest.toml"
        if dot_conf.exists() and tomllib:
            try:
                with open(dot_conf, "rb") as f:
                    data = tomllib.load(f)
                return cls._from_dict(data)
            except Exception:
                pass

        # Check pyproject.toml
        pyproject = target_dir / "pyproject.toml"
        if pyproject.exists() and tomllib:
            try:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                tool_data = data.get("tool", {}).get("shamtest", {})
                if tool_data:
                    return cls._from_dict(tool_data)
            except Exception:
                pass

        return cls()

    @classmethod
    def _from_dict(cls, data: dict) -> Config:
        ignore = set(data.get("ignore", []))
        exclude = data.get("exclude", [
            ".git",
            ".venv",
            "venv",
            "__pycache__",
            ".pytest_cache",
        ])
        fail_on = data.get("fail_on", "ERROR").upper()
        min_severity = data.get("min_severity", "WARNING").upper()
        max_hollow_index = data.get("max_hollow_index")

        return cls(
            ignore_rules=ignore,
            exclude_patterns=exclude,
            fail_on=fail_on,
            min_severity=min_severity,
            max_hollow_index=float(max_hollow_index) if max_hollow_index is not None else None,
        )
