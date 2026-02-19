"""Workflow tag management endpoints."""

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
    """Add tags to a workflow (idempotent for duplicates)."""
    wf = workflow_engine.add_tags(workflow_id, data.tags)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_tag(
    workflow_id: WorkflowIdPath,
    tag: Annotated[str, Path(description="Tag to remove")],
) -> WorkflowDefinition:
    """Remove a specific tag from a workflow."""
    result = workflow_engine.remove_tag(workflow_id, tag)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Tag not found on workflow")
    wf = workflow_engine.get_workflow(workflow_id)
    return wf
