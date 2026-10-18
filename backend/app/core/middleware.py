"""Custom middleware for resource limits, privacy logging, and error sanitization."""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings
from app.core.logging import logger


class PayloadLimitMiddleware(BaseHTTPMiddleware):
    """Rejects incoming requests exceeding MAX_PAYLOAD_BYTES with HTTP 413."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.MAX_PAYLOAD_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Payload size {length_int} bytes exceeds maximum allowed {settings.MAX_PAYLOAD_BYTES} bytes."
                        },
                    )
            except ValueError:
                pass
        response: Response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs incoming requests and response metadata without exposing sensitive payload bodies."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response: Response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"req_id={request_id} method={request.method} path={request.url.path} "
            f"status={response.status_code} duration={duration_ms:.2f}ms"
        )
        response.headers["X-Request-ID"] = request_id
        return response


def register_exception_handlers(app: FastAPI) -> None:
    """Registers sanitized exception handlers to prevent leaking stack traces (NFR-04)."""

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception(f"Unhandled server error req_id={error_id}: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"An internal server error occurred. Please reference error ID: {error_id}"
            },
        )
