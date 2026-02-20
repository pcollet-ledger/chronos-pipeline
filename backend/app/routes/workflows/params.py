"""Shared parameter type aliases for workflow route handlers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Path

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]
