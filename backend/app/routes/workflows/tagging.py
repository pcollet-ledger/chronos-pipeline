"""Workflow tagging endpoints (add/remove tags)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ...models import TagsRequest, WorkflowDefinition
from ...services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_tags(
    workflow_id: WorkflowIdPath, data: TagsRequest
) -> WorkflowDefinition:
    """Add one or more tags to a workflow (idempotent).

    Args:
        workflow_id: The unique workflow identifier.
        data: The tags to add.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    result = workflow_engine.add_tags(workflow_id, data.tags)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_tag(
    workflow_id: WorkflowIdPath,
    tag: Annotated[str, Path(description="Tag to remove")],
) -> WorkflowDefinition:
    """Remove a specific tag from a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        tag: The tag to remove.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow or tag is not found.
    """
    try:
        result = workflow_engine.remove_tag(workflow_id, tag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result
