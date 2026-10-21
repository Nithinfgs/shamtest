"""Rule registry for shamtest."""

from __future__ import annotations

from typing import List, Type

from shamtest.rules.base import Rule
from shamtest.rules.exceptions import ExceptionHandlingRules
from shamtest.rules.mock_loops import SelfValidatingMockLoopRule
from shamtest.rules.mock_traps import MockTrapsRule
from shamtest.rules.tautology import TautologicalAssertionRule, TriviallyTrueAssertionRule
from shamtest.rules.zero_assert import ZeroAssertionRule

ALL_RULES: List[Type[Rule]] = [
    TautologicalAssertionRule,      # SHAM001
    TriviallyTrueAssertionRule,     # SHAM002
    MockTrapsRule,                  # SHAM003, SHAM004, SHAM005, SHAM010
    ZeroAssertionRule,              # SHAM006
    ExceptionHandlingRules,         # SHAM007, SHAM008
    SelfValidatingMockLoopRule,     # SHAM009
]

__all__ = [
    "ALL_RULES",
    "Rule",
    "TautologicalAssertionRule",
    "TriviallyTrueAssertionRule",
    "MockTrapsRule",
    "ZeroAssertionRule",
    "ExceptionHandlingRules",
    "SelfValidatingMockLoopRule",
]
