"""Workflow cloning endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ...models import WorkflowDefinition
from ...services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone an existing workflow with a new ID.

    Args:
        workflow_id: The ID of the workflow to clone.

    Returns:
        The newly created clone.

    Raises:
        HTTPException: 404 if the source workflow is not found.
    """
    clone = workflow_engine.clone_workflow(workflow_id)
    if clone is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return clone
