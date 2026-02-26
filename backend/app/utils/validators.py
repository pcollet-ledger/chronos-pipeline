"""Reusable validation functions for Chronos Pipeline.

Centralises input validation logic so that routes, services, and tests
can share the same rules without duplication.
"""

from __future__ import annotations

import re
from typing import List, Optional

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

VALID_ACTIONS = frozenset({"log", "transform", "validate", "notify", "aggregate"})

MAX_WORKFLOW_NAME_LENGTH = 200
MAX_TAG_LENGTH = 50
MAX_TAGS_COUNT = 100
MIN_LIMIT = 1
MAX_LIMIT = 1000
MIN_OFFSET = 0


def validate_workflow_name(name: str) -> Optional[str]:
    """Return an error message if *name* is invalid, else ``None``.

    Args:
        name: The workflow name to validate.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if not name or not name.strip():
        return "Workflow name must not be empty or whitespace-only"
    if len(name) > MAX_WORKFLOW_NAME_LENGTH:
        return f"Workflow name must not exceed {MAX_WORKFLOW_NAME_LENGTH} characters"
    return None


def validate_action_name(action: str) -> Optional[str]:
    """Return an error message if *action* is not a known action name.

    Args:
        action: The action name to validate.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if action not in VALID_ACTIONS:
        return f"Unknown action '{action}'. Valid actions: {sorted(VALID_ACTIONS)}"
    return None


def validate_tags(tags: List[str]) -> Optional[str]:
    """Return an error message if the tag list is invalid.

    Args:
        tags: List of tag strings to validate.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if len(tags) > MAX_TAGS_COUNT:
        return f"Too many tags (max {MAX_TAGS_COUNT})"
    for tag in tags:
        if len(tag) > MAX_TAG_LENGTH:
            return f"Tag '{tag[:20]}...' exceeds {MAX_TAG_LENGTH} characters"
    return None


def validate_limit(limit: int) -> Optional[str]:
    """Return an error message if *limit* is out of range.

    Args:
        limit: The pagination limit to validate.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if limit < MIN_LIMIT:
        return f"limit must be >= {MIN_LIMIT}"
    if limit > MAX_LIMIT:
        return f"limit must be <= {MAX_LIMIT}"
    return None


def validate_offset(offset: int) -> Optional[str]:
    """Return an error message if *offset* is negative.

    Args:
        offset: The pagination offset to validate.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if offset < MIN_OFFSET:
        return f"offset must be >= {MIN_OFFSET}"
    return None


def validate_non_negative_int(value: int, name: str) -> Optional[str]:
    """Return an error message if *value* is negative.

    Args:
        value: The integer to validate.
        name: The parameter name for the error message.

    Returns:
        An error string if validation fails, otherwise ``None``.
    """
    if value < 0:
        return f"{name} must be >= 0"
    return None


# Backward-compatible alias
validate_positive_int = validate_non_negative_int


def is_valid_uuid(value: str) -> bool:
    """Check whether *value* looks like a UUID v4 string.

    Args:
        value: The string to check.

    Returns:
        ``True`` if the string matches UUID format.
    """
    return bool(_UUID_RE.match(value))


def is_valid_slug(value: str) -> bool:
    """Check whether *value* is a valid URL slug.

    Args:
        value: The string to check.

    Returns:
        ``True`` if the string is a valid slug.
    """
    return bool(_SLUG_RE.match(value))
