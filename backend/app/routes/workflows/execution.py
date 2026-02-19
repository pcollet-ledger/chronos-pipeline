"""Workflow execution and execution-listing endpoints."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, Query

from ...models import WorkflowDefinition, WorkflowExecution
from ...services import workflow_engine

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
    """Execute a workflow and return the execution record."""
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
    """List executions for a specific workflow."""
    return workflow_engine.list_executions(workflow_id=workflow_id, limit=limit)


@router.post("/{workflow_id}/dry-run", response_model=WorkflowExecution)
async def dry_run_workflow(workflow_id: WorkflowIdPath) -> WorkflowExecution:
    """Simulate executing a workflow without running actions."""
    result = workflow_engine.dry_run_workflow(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone a workflow with a new ID and ' (copy)' appended to name."""
    cloned = workflow_engine.clone_workflow(workflow_id)
    if cloned is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return cloned
