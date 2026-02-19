"""Workflow versioning endpoints (history, specific version)."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path

from ...models import WorkflowDefinition
from ...services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.get("/{workflow_id}/history", response_model=List[WorkflowDefinition])
async def get_workflow_history(workflow_id: WorkflowIdPath) -> List[WorkflowDefinition]:
    """Get all previous versions of a workflow, newest first.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A list of version snapshots.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    result = workflow_engine.get_workflow_history(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/{workflow_id}/history/{version}", response_model=WorkflowDefinition)
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> WorkflowDefinition:
    """Get a specific version snapshot of a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        version: The version number.

    Returns:
        The version snapshot.

    Raises:
        HTTPException: 404 if the workflow or version is not found.
    """
    if workflow_engine.get_workflow(workflow_id) is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    result = workflow_engine.get_workflow_version(workflow_id, version)
    if result is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return result
