"""Tests for journal_lib.result module."""

import pytest

from journal_lib.result import Result, Success, Failure


class TestResult:
    """Test Result type functionality."""

    def test_success_creation(self):
        """Test Success object creation and methods."""
        success = Success("test value")
        assert success.value == "test value"
        assert success.is_success() == True
        assert success.is_failure() == False

    def test_failure_creation(self):
        """Test Failure object creation and methods."""
        failure = Failure("test error")
        assert failure.error == "test error"
        assert failure.is_success() == False
        assert failure.is_failure() == True

    def test_success_with_different_types(self):
        """Test Success can hold different types."""
        int_success = Success(42)
        assert int_success.value == 42
        assert int_success.is_success() == True

        list_success = Success([1, 2, 3])
        assert list_success.value == [1, 2, 3]
        assert list_success.is_success() == True

        dict_success = Success({"key": "value"})
        assert dict_success.value == {"key": "value"}
        assert dict_success.is_success() == True