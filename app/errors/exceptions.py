"""Custom exception classes for API errors."""

from typing import Any
from datetime import datetime


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int,
        details: dict[str, Any] | None = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

    def to_response(self) -> dict:
        """Convert to JSON response format."""
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


class InvalidRequestError(APIError):
    """400 Bad Request - Malformed request."""

    def __init__(self, message: str, **details):
        super().__init__(
            message=message,
            code="INVALID_REQUEST",
            status_code=400,
            details=details
        )


class RequestTimeoutError(APIError):
    """408 Request Timeout - Operation timed out."""

    def __init__(self, message: str, **details):
        super().__init__(
            message=message,
            code="REQUEST_TIMEOUT",
            status_code=408,
            details=details
        )


class StateConflictError(APIError):
    """409 Conflict - Invalid state transition."""

    def __init__(self, message: str, **details):
        super().__init__(
            message=message,
            code="STATE_CONFLICT",
            status_code=409,
            details=details
        )


class SemanticError(APIError):
    """422 Unprocessable Entity - Semantic validation failed."""

    def __init__(self, message: str, **details):
        super().__init__(
            message=message,
            code="SEMANTIC_ERROR",
            status_code=422,
            details=details
        )


class ValidationFailedError(APIError):
    """422 Unprocessable Entity - File validation failed."""

    def __init__(self, message: str, **details):
        super().__init__(
            message=message,
            code="VALIDATION_FAILED",
            status_code=422,
            details=details
        )


class ChecksumMismatchError(APIError):
    """422 Unprocessable Entity - Checksum mismatch."""

    def __init__(self, expected: str, computed: str):
        super().__init__(
            message="Computed checksum does not match provided checksum",
            code="CHECKSUM_MISMATCH",
            status_code=422,
            details={
                "expected": expected,
                "computed": computed,
                "suggestion": "File may have been corrupted during transfer. Verify file integrity."
            }
        )


class FileNotFoundError(APIError):
    """404 Not Found - File not found."""

    def __init__(self, file_id: str):
        super().__init__(
            message=f"File not found: {file_id}",
            code="FILE_NOT_FOUND",
            status_code=404,
            details={"file_id": file_id}
        )


class InternalError(APIError):
    """500 Internal Server Error - Server malfunction."""

    def __init__(self, message: str, request_id: str, **details):
        details["request_id"] = request_id
        details["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(
            message=message,
            code="INTERNAL_ERROR",
            status_code=500,
            details=details
        )
