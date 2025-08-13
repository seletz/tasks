"""
Simple result type for error handling.

This module provides a basic Result type pattern for handling success and failure
cases in a more explicit way than exceptions. It helps distinguish between empty
data and error conditions, making the code more maintainable and debuggable.

Example usage:
    from journal_lib.result import Result, Success, Failure

    def some_operation() -> Result[str]:
        if success_condition:
            return Success("operation result")
        else:
            return Failure("error message")

    result = some_operation()
    if result.is_success():
        print(f"Got: {result.value}")
    else:
        print(f"Error: {result.error}")
"""

from typing import TypeVar

T = TypeVar("T")


class Success[T]:
    """Represents a successful operation with a value."""

    def __init__(self, value: T):
        self.value = value

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False


class Failure:
    """Represents a failed operation with an error message."""

    def __init__(self, error: str):
        self.error = error

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True


Result = Success[T] | Failure
