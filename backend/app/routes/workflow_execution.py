"""Workflow execution endpoints: execute, list executions, dry-run."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, Query

from ..models import WorkflowDefinition, WorkflowExecution
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_workflow(
    workflow_id: WorkflowIdPath,
    trigger: Annotated[
        str,
        Query(description="How the execution was triggered"),
    ] = "manual",
) -> WorkflowExecution:
    """Execute a workflow and return the execution record.

    Args:
        workflow_id: The unique workflow identifier.
        trigger: Trigger source label.

    Returns:
        The execution record.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    execution = workflow_engine.execute_workflow(workflow_id, trigger=trigger)
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return execution


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def list_workflow_executions(
    workflow_id: WorkflowIdPath,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 50,
) -> List[WorkflowExecution]:
    """List executions for a specific workflow.

    Args:
        workflow_id: The unique workflow identifier.
        limit: Maximum number of results (1-1000).

    Returns:
        A list of execution records.
    """
    return workflow_engine.list_executions(workflow_id=workflow_id, limit=limit)


@router.post("/{workflow_id}/dry-run", response_model=WorkflowExecution)
async def dry_run_workflow(workflow_id: WorkflowIdPath) -> WorkflowExecution:
    """Simulate executing a workflow without running actions.

    Validates the DAG and returns the execution order with
    ``output={'dry_run': True}`` for each task.  The execution is
    **not** stored in the executions registry.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A synthetic execution record.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    result = workflow_engine.dry_run_workflow(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result
