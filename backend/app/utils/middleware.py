"""Request/response middleware for timing and tracing.

Adds the following to every HTTP response:
- ``X-Request-ID``: a unique UUID identifying the request.
- ``X-Response-Time``: wall-clock duration in milliseconds.

Also logs method, path, status code, and duration for observability.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("chronos.middleware")


class TimingAndTracingMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns a request ID and measures response time.

    Attributes:
        None — all state is per-request.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process a single request through the middleware chain.

        Args:
            request: The incoming HTTP request.
            call_next: Callable that forwards the request to the next handler.

        Returns:
            The HTTP response with tracing headers attached.
        """
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        logger.info(
            "%s %s -> %s (%.2fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
