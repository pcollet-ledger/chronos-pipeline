"""Workflow CRUD and execution endpoints."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ..models import (
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowUpdate,
)
from ..services import workflow_engine

router = APIRouter()


@router.post("/", response_model=WorkflowDefinition, status_code=201)
async def create_workflow(data: WorkflowCreate):
    """Create a new workflow definition."""
    return workflow_engine.create_workflow(data)


@router.get("/", response_model=List[WorkflowDefinition])
async def list_workflows(tag: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List all workflow definitions."""
    return workflow_engine.list_workflows(tag=tag, limit=limit, offset=offset)


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str):
    """Get a workflow by ID."""
    wf = workflow_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(workflow_id: str, data: WorkflowUpdate):
    """Update an existing workflow."""
    wf = workflow_engine.update_workflow(workflow_id, data)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    if not workflow_engine.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_workflow(workflow_id: str, trigger: str = "manual"):
    """Execute a workflow and return the execution record."""
    execution = workflow_engine.execute_workflow(workflow_id, trigger=trigger)
    if not execution:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return execution


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def list_workflow_executions(workflow_id: str, limit: int = 50):
    """List executions for a specific workflow."""
    return workflow_engine.list_executions(workflow_id=workflow_id, limit=limit)
