"""Tests for Error handling."""


from src.shared.errors import (
    AppError,
    BusinessRuleViolationError,
    ConflictError,
    ErrorCode,
    NotFoundError,
    ValidationError,
)


class TestErrorHierarchy:
    """Tests for error hierarchy."""

    def test_app_error_base(self) -> None:
        """Test base AppError."""
        error = AppError(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Test error",
            status_code=500,
        )
        assert error.error_code == ErrorCode.INTERNAL_ERROR
        assert error.message == "Test error"
        assert error.status_code == 500
        assert str(error) == "Test error"

    def test_validation_error(self) -> None:
        """Test ValidationError."""
        error = ValidationError(message="Invalid input", details={"field": "email"})
        assert error.error_code == ErrorCode.VALIDATION_ERROR
        assert error.status_code == 422
        assert "Invalid input" in error.message

    def test_not_found_error(self) -> None:
        """Test NotFoundError."""
        error = NotFoundError(resource_type="Task", resource_id="123")
        assert error.error_code == ErrorCode.NOT_FOUND
        assert error.status_code == 404
        assert "Task" in error.message
        assert "123" in error.message

    def test_business_rule_violation_error(self) -> None:
        """Test BusinessRuleViolationError."""
        error = BusinessRuleViolationError(
            message="Cannot delete active task",
            rule_name="TASK_STATUS_RULE",
        )
        assert error.error_code == ErrorCode.BUSINESS_RULE_VIOLATION
        assert error.status_code == 400
        assert error.details["rule_name"] == "TASK_STATUS_RULE"

    def test_conflict_error(self) -> None:
        """Test ConflictError."""
        error = ConflictError(
            resource_type="Staff",
            message="Email already exists",
        )
        assert error.error_code == ErrorCode.CONFLICT
        assert error.status_code == 409
        assert error.details["resource_type"] == "Staff"

    def test_error_to_dict(self) -> None:
        """Test error serialization."""
        error = ValidationError(
            message="Invalid field",
            details={"field": "name"},
        )
        error_dict = error.to_dict()
        assert error_dict["error_code"] == ErrorCode.VALIDATION_ERROR
        assert error_dict["message"] == "Invalid field"
        assert error_dict["details"]["field"] == "name"

    def test_error_inheritance(self) -> None:
        """Test that all errors inherit from AppError."""
        errors = [
            ValidationError("test"),
            NotFoundError("Type", "id"),
            BusinessRuleViolationError("test"),
            ConflictError("Type", "test"),
        ]
        for error in errors:
            assert isinstance(error, AppError)
