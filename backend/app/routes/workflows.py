"""Workflow CRUD and execution endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..models import (
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowImport,
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


@router.post("/import", response_model=WorkflowDefinition, status_code=201)
async def import_workflow(data: WorkflowImport):
    """Import a workflow from an exported JSON definition."""
    return workflow_engine.import_workflow(data)


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str):
    """Get a workflow by ID."""
    wf = workflow_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/{workflow_id}/export")
async def export_workflow(workflow_id: str):
    """Export a workflow definition as a downloadable JSON file."""
    payload = workflow_engine.export_workflow(workflow_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    filename = f"workflow-{workflow_id}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
