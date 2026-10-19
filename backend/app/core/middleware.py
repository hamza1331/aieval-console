"""Custom middleware for resource limits, privacy logging, and error sanitization."""

import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings
from app.core.logging import logger


class PayloadLimitMiddleware:
    """Rejects incoming requests exceeding MAX_PAYLOAD_BYTES with HTTP 413."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for key, value in scope["headers"] if key.lower() == b"content-length"),
            None,
        )
        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.MAX_PAYLOAD_BYTES:
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Payload size {length_int} bytes exceeds maximum allowed {settings.MAX_PAYLOAD_BYTES} bytes."
                        },
                    )
                    await response(scope, receive, send)
                    return
            except ValueError:
                pass

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > settings.MAX_PAYLOAD_BYTES:
                response = JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Payload size exceeds maximum allowed {settings.MAX_PAYLOAD_BYTES} bytes."
                    },
                )
                await response(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        body_sent = False

        async def receive_body() -> Message:
            nonlocal body_sent
            if body_sent:
                return await receive()
            body_sent = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, receive_body, send)


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
