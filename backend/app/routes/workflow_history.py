"""Workflow versioning/history endpoints: list history, get specific version, clone."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path

from ..models import WorkflowDefinition
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.get("/{workflow_id}/history", response_model=List[WorkflowDefinition])
async def get_workflow_history(workflow_id: WorkflowIdPath) -> List[WorkflowDefinition]:
    """Get the version history of a workflow (newest first)."""
    result = workflow_engine.get_workflow_history(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/{workflow_id}/history/{version}", response_model=WorkflowDefinition)
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="1-based version number")],
) -> WorkflowDefinition:
    """Get a specific historical version of a workflow."""
    result = workflow_engine.get_workflow_version(workflow_id, version)
    if result is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return result


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Create a deep copy of a workflow with a new ID."""
    result = workflow_engine.clone_workflow(workflow_id)
    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result
