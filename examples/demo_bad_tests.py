"""Demonstration file containing common AI-generated sham and hollow test anti-patterns."""

from unittest.mock import MagicMock, Mock
import pytest


def test_tautology_literal():
    """SHAM001: Literal tautology asserting True or identical operands."""
    data = {"status": "ok"}
    assert True
    assert 1 == 1
    assert data["status"] == data["status"]


def test_trivial_length_check():
    """SHAM002: Trivially true inequality that can never fail."""
    items = [1, 2, 3]
    # In Python, len() is always >= 0 for any sequence
    assert len(items) >= 0


def test_mock_truthiness_trap():
    """SHAM003: Mock objects in Python are always truthy."""
    mock_service = Mock()
    # bool(Mock()) is ALWAYS True, even if unconfigured or failed
    assert mock_service


def test_uncalled_mock_assertion():
    """SHAM004: Missing call parentheses on mock assertion method."""
    mock_sender = Mock()
    mock_sender.send("payload")
    # Missing ()! Evaluates method object and silently passes without asserting!
    mock_sender.assert_called_once


def test_mock_assertion_typo():
    """SHAM005: Mock dynamically accepts non-existent methods without failing."""
    mock_client = Mock()
    mock_client.fetch()
    # Typo: 'asser_called' is not a real method, but Mock creates it and returns a new Mock!
    mock_client.asser_called()


def test_zero_assertions_blind_run():
    """SHAM006: AI agent ran the function and assumed no crash means passing test."""
    user = {"id": 42, "role": "admin"}
    # Executes code with ZERO assertions on outcome
    formatted = f"User {user['id']}"


def test_swallowed_exception():
    """SHAM007: Try/except pass silently hides failure to throw or wrong exception."""
    try:
        val = 10 / 2  # Doesn't even throw!
    except Exception:
        pass


def test_overly_broad_pytest_raises():
    """SHAM008: Catching generic Exception masks NameError/TypeError bugs."""
    with pytest.raises(Exception):
        raise ValueError("Invalid configuration")


def test_self_validating_mock_loop():
    """SHAM009: Asserts mock return value against itself without testing production code."""
    mock_db = Mock()
    mock_db.query.return_value = {"count": 100}
    res = mock_db.query()
    assert res == {"count": 100}


def test_standalone_mock_condition():
    """SHAM010: Standalone mock condition without assert."""
    mock_worker = Mock()
    mock_worker.run()
    # Evaluates condition as an expression statement, discarding result!
    mock_worker.called
