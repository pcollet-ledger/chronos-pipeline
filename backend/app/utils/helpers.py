"""Utility helpers for Chronos Pipeline backend."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a name."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def compute_checksum(data: str) -> str:
    """Compute a SHA-256 checksum for a given string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def paginate(
    items: List[Any],
    offset: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """Paginate a list of items."""
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
    """Format a duration in milliseconds to a human-readable string."""
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
    """Safely get a nested value from a dictionary."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return default
        if current is None:
            return default
    return current


def timestamp_to_iso(dt: Optional[datetime]) -> Optional[str]:
    """Convert a datetime to ISO 8601 string."""
    if dt is None:
        return None
    return dt.isoformat() + "Z"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(value, max_val))
