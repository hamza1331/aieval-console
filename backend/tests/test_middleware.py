"""Tests for request resource-limit middleware."""

import asyncio

from starlette.types import Message, Scope

from app.core.config import settings
from app.core.middleware import PayloadLimitMiddleware


def test_payload_limit_rejects_chunked_body_without_content_length(monkeypatch) -> None:
    monkeypatch.setattr(settings, "MAX_PAYLOAD_BYTES", 5)
    messages: list[Message] = [
        {"type": "http.request", "body": b"123", "more_body": True},
        {"type": "http.request", "body": b"456", "more_body": False},
    ]
    sent: list[Message] = []
    app_called = False

    async def receive() -> Message:
        return messages.pop(0)

    async def send(message: Message) -> None:
        sent.append(message)

    async def app(scope: Scope, receive, send) -> None:
        nonlocal app_called
        app_called = True

    scope: Scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/evaluations",
        "raw_path": b"/api/v1/evaluations",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("test", 1234),
        "server": ("test", 8000),
    }

    asyncio.run(PayloadLimitMiddleware(app)(scope, receive, send))

    assert not app_called
    assert sent[0]["status"] == 413

