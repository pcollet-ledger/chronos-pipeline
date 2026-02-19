"""Workflow dry-run endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from ...models import WorkflowExecution
from ...services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/dry-run", response_model=WorkflowExecution)
async def dry_run_workflow(workflow_id: WorkflowIdPath) -> WorkflowExecution:
    """Simulate executing a workflow without running actions.

    The dry-run is NOT stored in the executions registry.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A simulated execution record.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    result = workflow_engine.dry_run_workflow(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result
