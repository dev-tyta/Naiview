"""Request middleware — logging, request IDs, error handling.

14 of INTERNAL_ARCHITECTURE.md.
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject a unique request_id into every request for structured logging."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.info(
            "request_started",
            method=request.method,
            path=str(request.url.path),
        )

        response = await call_next(request)

        logger.info(
            "request_completed",
            status_code=response.status_code,
        )

        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.unbind_contextvars("request_id")
        return response
