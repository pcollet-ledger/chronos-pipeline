"""Extended workflow endpoints: cloning, versioning, and tagging."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from ..models import WorkflowDefinition
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


class TagsPayload(BaseModel):
    """Request body for adding tags to a workflow."""
    tags: List[str] = Field(..., min_length=1)


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone a workflow with a new ID and ' (copy)' appended to the name."""
    clone = workflow_engine.clone_workflow(workflow_id)
    if not clone:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return clone


@router.get("/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: WorkflowIdPath,
) -> List[Dict[str, Any]]:
    """Return all version snapshots for a workflow, newest first."""
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}")
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number (1-based)")],
) -> Dict[str, Any]:
    """Return a specific version snapshot of a workflow."""
    snapshot = workflow_engine.get_workflow_version(workflow_id, version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snapshot


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_tags(
    workflow_id: WorkflowIdPath, data: TagsPayload
) -> WorkflowDefinition:
    """Add tags to a workflow (idempotent)."""
    wf = workflow_engine.add_tags(workflow_id, data.tags)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_tag(
    workflow_id: WorkflowIdPath,
    tag: Annotated[str, Path(description="Tag to remove")],
) -> WorkflowDefinition:
    """Remove a tag from a workflow."""
    try:
        wf = workflow_engine.remove_tag(workflow_id, tag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf
