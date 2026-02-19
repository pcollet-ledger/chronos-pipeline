"""Chronos Pipeline Backend - FastAPI Application Entry Point.

Configures the FastAPI application, CORS middleware, router mounts, and
global exception handlers.  Exception handlers ensure that *every*
unhandled error response uses a consistent ``{detail, code}`` JSON shape
so that clients can rely on a stable contract for programmatic error
handling.

Note: ``HTTPException`` raised inside route handlers is *not* caught by
these global handlers — FastAPI's built-in handler takes precedence.
"""

import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import analytics, tasks, workflows
from .utils.helpers import build_error_response

logger = logging.getLogger("chronos_pipeline")

app = FastAPI(
    title="Chronos Pipeline",
    description="Data pipeline orchestration and scheduling platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ``ValueError`` as a 400 Bad Request.

    Service functions raise ``ValueError`` for business-rule violations
    (e.g. invalid cron expressions, unknown action names).  Surfacing these
    as 400 gives clients actionable feedback without exposing internals.

    Args:
        request: The incoming HTTP request that triggered the error.
        exc: The ``ValueError`` instance.

    Returns:
        A 400 JSON response with ``{detail, code}``.
    """
    logger.warning(
        "ValueError on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return build_error_response(
        status_code=400,
        detail=str(exc),
        code="bad_request",
    )


@app.exception_handler(KeyError)
async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
    """Handle ``KeyError`` as a 404 Not Found.

    A ``KeyError`` typically means a lookup into an in-memory store failed.
    Mapping it to 404 keeps the API semantics clean for consumers.

    Args:
        request: The incoming HTTP request that triggered the error.
        exc: The ``KeyError`` instance.

    Returns:
        A 404 JSON response with ``{detail, code}``.
    """
    logger.warning(
        "KeyError on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    key_name: Union[str, int] = exc.args[0] if exc.args else "unknown"
    return build_error_response(
        status_code=404,
        detail=f"Resource not found: {key_name}",
        code="not_found",
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    """Handle ``PermissionError`` as a 403 Forbidden.

    Although the current in-memory backend has no auth layer, this handler
    future-proofs the API so that permission checks added later surface as
    proper 403 responses instead of 500s.

    Args:
        request: The incoming HTTP request that triggered the error.
        exc: The ``PermissionError`` instance.

    Returns:
        A 403 JSON response with ``{detail, code}``.
    """
    logger.warning(
        "PermissionError on %s %s: %s\n%s",
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return build_error_response(
        status_code=403,
        detail=str(exc) if str(exc) else "Permission denied",
        code="forbidden",
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for any exception not handled by a more specific handler.

    Logs the full traceback at ERROR level so operators can diagnose the
    issue, but returns a generic message to the client to avoid leaking
    implementation details.

    Args:
        request: The incoming HTTP request that triggered the error.
        exc: The unhandled exception.

    Returns:
        A 500 JSON response with ``{detail, code}``.
    """
    logger.error(
        "Unhandled %s on %s %s: %s\n%s",
        type(exc).__name__,
        request.method,
        request.url.path,
        exc,
        traceback.format_exc(),
    )
    return build_error_response(
        status_code=500,
        detail="Internal server error",
        code="internal_server_error",
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        A dict with ``status`` and ``service`` keys.
    """
    return {"status": "healthy", "service": "chronos-pipeline-backend"}
