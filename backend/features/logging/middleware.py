"""
Logging middleware for FastAPI.

Captures all requests, responses, and exceptions.
"""
import time
import traceback
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from features.logging.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response for every API call.

        Logs:
        - Request: method, path, client IP
        - Response: status code, processing time
        - Errors: Full traceback for 5xx errors
        """
        # Generate request ID for tracking
        request_id = id(request)

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} | "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log response
            log_level = "info" if response.status_code < 400 else "warning"
            if response.status_code >= 500:
                log_level = "error"

            getattr(logger, log_level)(
                f"[{request_id}] {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.3f}s"
            )

            return response

        except Exception as exc:
            # Log exception with full traceback
            process_time = time.time() - start_time

            logger.error(
                f"[{request_id}] {request.method} {request.url.path} | "
                f"EXCEPTION: {type(exc).__name__}: {str(exc)} | "
                f"Time: {process_time:.3f}s\n"
                f"{traceback.format_exc()}"
            )

            # Re-raise to let FastAPI's exception handlers deal with it
            raise


class ExceptionLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch and log unhandled exceptions.

    This should be the outermost middleware to catch everything.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Catch any unhandled exceptions and log them."""
        try:
            return await call_next(request)
        except Exception as exc:
            # Log critical unhandled exception
            logger.critical(
                f"UNHANDLED EXCEPTION: {type(exc).__name__}: {str(exc)}\n"
                f"Request: {request.method} {request.url.path}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )

            # Return generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred. Please contact support."
                    }
                }
            )
