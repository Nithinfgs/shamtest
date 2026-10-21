"""shamtest: Catch sham, tautological, and mock-poisoned tests before they merge."""

from shamtest.analyzer import Analyzer
from shamtest.config import Config
from shamtest.models import FileReport, Issue, ScanSummary, Severity

__version__ = "0.1.0"

__all__ = [
    "Analyzer",
    "Config",
    "FileReport",
    "Issue",
    "ScanSummary",
    "Severity",
    "__version__",
]
