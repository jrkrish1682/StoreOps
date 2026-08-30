"""
Shared error hierarchy for StoreOps API.

All errors in services must raise AppError or its subclasses.
Never raise raw Exception, RuntimeError, or ValueError.
"""

from enum import StrEnum
from typing import Any


class ErrorCode(StrEnum):
    """Standard error codes."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    CONFLICT = "CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        error_code: ErrorCode | str,
        message: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize AppError.

        Args:
            error_code: Machine-readable error code
            message: Human-readable error message
            status_code: HTTP status code
            details: Optional additional error details
        """
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AppError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ValidationError."""
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details,
        )


class NotFoundError(AppError):
    """Raised when a resource is not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str | int,
    ) -> None:
        """Initialize NotFoundError."""
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": str(resource_id)},
        )


class BusinessRuleViolationError(AppError):
    """Raised when business rule is violated."""

    def __init__(
        self,
        message: str,
        rule_name: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize BusinessRuleViolationError."""
        error_details = details or {}
        if rule_name:
            error_details["rule_name"] = rule_name
        super().__init__(
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            message=message,
            status_code=400,
            details=error_details,
        )


class ConflictError(AppError):
    """Raised when resource already exists."""

    def __init__(
        self,
        resource_type: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ConflictError."""
        super().__init__(
            error_code=ErrorCode.CONFLICT,
            message=message,
            status_code=409,
            details={**(details or {}), "resource_type": resource_type},
        )
