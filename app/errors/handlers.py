"""Global exception handlers for FastAPI."""

from fastapi import Request
from fastapi.responses import JSONResponse
import uuid
import logging

from app.errors.exceptions import APIError

logger = logging.getLogger(__name__)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response()
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError as 400 Bad Request."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_REQUEST",
                "message": str(exc),
                "details": {}
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Log error for debugging
    logger.error(
        f"Unhandled exception: {exc}",
        extra={"request_id": request_id},
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {
                    "request_id": request_id
                }
            }
        }
    )
