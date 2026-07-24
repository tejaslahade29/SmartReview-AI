import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for application-raised errors that map to an HTTP response."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "app_error"

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class ValidationFailedError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "validation_failed"


class UnsupportedFileTypeError(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    error_code = "unsupported_file_type"


class FileTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    error_code = "file_too_large"


class CorruptDocumentError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "corrupt_document"


class ClaudeServiceError(AppError):
    """Raised when the Claude API is unreachable or fails after retries."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "claude_service_error"


class ClaudeRefusalError(AppError):
    """Raised when Claude declines to review the document."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "claude_refused"


class ClaudeResponseInvalidError(AppError):
    """Raised when Claude's response cannot be parsed as the expected structured findings."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "claude_response_invalid"


class AIServiceError(AppError):
    """Provider-neutral equivalent of ClaudeServiceError, for non-Anthropic providers."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "ai_service_error"


class AIRefusalError(AppError):
    """Provider-neutral equivalent of ClaudeRefusalError."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "ai_refused"


class AIResponseInvalidError(AppError):
    """Provider-neutral equivalent of ClaudeResponseInvalidError."""

    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "ai_response_invalid"


def _error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": error_code, "message": message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError on %s %s: %s", request.method, request.url.path, exc.message)
        return _error_response(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info("Request validation failed on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_failed",
            "Request validation failed.",
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_server_error",
            "An unexpected error occurred.",
        )
