"""Utility helpers for Chronos Pipeline backend.

General-purpose functions shared across routes, services, and tests.
Includes pure utility functions (slug generation, pagination, etc.) as
well as thin wrappers around FastAPI primitives for consistent error
responses.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name.

    Args:
        name: The human-readable name to slugify.

    Returns:
        A lowercase, hyphen-separated string safe for use in URLs.
    """
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def compute_checksum(data: str) -> str:
    """Compute a SHA-256 checksum for a given string.

    Args:
        data: The input string to hash.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def paginate(
    items: List[Any],
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """Paginate a list of items.

    Args:
        items: The full list to paginate.
        offset: Zero-based start index.
        limit: Maximum number of items to return.

    Returns:
        A dict with ``items``, ``total``, ``offset``, ``limit``, and
        ``has_more`` keys.
    """
    total = len(items)
    page_items = items[offset : offset + limit]
    return {
        "items": page_items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + limit) < total,
    }


def format_duration(ms: float) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds.

    Returns:
        Human-readable string like ``"500ms"``, ``"5.0s"``, ``"2.0m"``,
        or ``"1.5h"``.
    """
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        data: The root dictionary.
        *keys: Sequence of keys to traverse.
        default: Value returned when any key is missing or ``None``.

    Returns:
        The nested value, or *default* if the path is broken.
    """
    current: Any = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


def timestamp_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime to ISO 8601 string.

    Args:
        dt: A datetime instance, or ``None``.

    Returns:
        ISO 8601 string with trailing ``Z``, or ``None``.
    """
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max.

    Args:
        value: The number to clamp.
        min_val: Lower bound (inclusive).
        max_val: Upper bound (inclusive).

    Returns:
        *value* constrained to ``[min_val, max_val]``.
    """
    return max(min_val, min(value, max_val))


def raise_not_found(resource: str = "Resource") -> None:
    """Raise a 404 ``HTTPException`` with a descriptive detail message.

    Uses a consistent ``"{Resource} not found"`` pattern so that API
    consumers can match on the detail string programmatically.

    Args:
        resource: Name of the missing resource (used in the detail message).

    Raises:
        HTTPException: Always raised with status 404.
    """
    raise HTTPException(status_code=404, detail=f"{resource} not found")


def raise_conflict(message: str) -> None:
    """Raise a 409 ``HTTPException`` with a descriptive detail message.

    Used for business-rule violations where the request is well-formed but
    conflicts with the current state (e.g. retrying a non-failed execution).

    Args:
        message: Human-readable conflict description.

    Raises:
        HTTPException: Always raised with status 409.
    """
    raise HTTPException(status_code=409, detail=message)


def build_error_response(
    status_code: int,
    detail: str,
    code: str,
) -> JSONResponse:
    """Build a ``JSONResponse`` with the standard ``{detail, code}`` body.

    Used by the global exception handlers in ``main.py`` to ensure every
    unhandled-exception response has a machine-readable ``code`` field
    alongside the human-readable ``detail``.

    Args:
        status_code: HTTP status code for the response.
        detail: Human-readable error description.
        code: Machine-readable error code string.

    Returns:
        A ``JSONResponse`` ready to be returned from an exception handler.
    """
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "code": code},
    )
