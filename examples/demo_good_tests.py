"""Demonstration of clean, rigorous, high-signal tests that pass shamtest with zero issues."""

from unittest.mock import Mock
import pytest


def add(a: int, b: int) -> int:
    return a + b


def parse_header(header: str) -> dict:
    if not header:
        raise ValueError("Header cannot be empty")
    k, v = header.split(":", 1)
    return {k.strip(): v.strip()}


def test_add_positive_numbers():
    """Clean test: asserts dynamic function output against independent expected value."""
    result = add(2, 3)
    assert result == 5


def test_add_negative_numbers():
    """Clean test: asserts behavior with edge cases."""
    assert add(-1, -1) == -2
    assert add(0, 0) == 0


def test_parse_header_valid():
    """Clean test: asserts structured dictionary contents."""
    parsed = parse_header("Content-Type: application/json")
    assert parsed == {"Content-Type": "application/json"}
    assert "Content-Type" in parsed
    assert len(parsed) == 1


def test_parse_header_empty_raises_specific_error():
    """Clean test: uses pytest.raises with specific ValueError."""
    with pytest.raises(ValueError, match="Header cannot be empty"):
        parse_header("")


def test_mock_notification_dispatched():
    """Clean test: properly calls mock assertion method with arguments."""
    mock_notifier = Mock()
    mock_notifier.send("welcome_email", user_id=42)

    # Properly invoked assertion with parentheses and argument verification
    mock_notifier.send.assert_called_once_with("welcome_email", user_id=42)
