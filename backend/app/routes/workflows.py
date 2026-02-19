"""Workflow CRUD, execution, cloning, versioning, tagging, search, and dry-run endpoints.

All endpoints return Pydantic models directly; FastAPI handles
serialisation.  ``None`` from services maps to 404, ``ValueError``
maps to 409.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from ..models import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowUpdate,
)
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


class TagsRequest(BaseModel):
    """Request body for adding tags to a workflow."""
    tags: List[str] = Field(..., min_length=1, description="Tags to add")


@router.post("/", response_model=WorkflowDefinition, status_code=201)
async def create_workflow(data: WorkflowCreate) -> WorkflowDefinition:
    """Create a new workflow definition."""
    return workflow_engine.create_workflow(data)


@router.get("/", response_model=List[WorkflowDefinition])
async def list_workflows(
    tag: Annotated[
        str | None,
        Query(description="Filter workflows by tag"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Filter workflows by name substring (case-insensitive)"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip"),
    ] = 0,
) -> List[WorkflowDefinition]:
    """List all workflow definitions with optional filters."""
    return workflow_engine.list_workflows(tag=tag, search=search, limit=limit, offset=offset)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_workflows(data: BulkDeleteRequest) -> BulkDeleteResponse:
    """Delete multiple workflows in a single request."""
    return workflow_engine.bulk_delete_workflows(data.ids)


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Get a workflow by ID."""
    wf = workflow_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(
    workflow_id: WorkflowIdPath, data: WorkflowUpdate
) -> WorkflowDefinition:
    """Update an existing workflow."""
    wf = workflow_engine.update_workflow(workflow_id, data)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}", status_code=204, response_class=Response)
async def delete_workflow(workflow_id: WorkflowIdPath) -> Response:
    """Delete a workflow."""
    if not workflow_engine.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return Response(status_code=204)


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


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone a workflow with a new ID and ' (copy)' appended to the name."""
    clone = workflow_engine.clone_workflow(workflow_id)
    if clone is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return clone


@router.get("/{workflow_id}/history")
async def get_workflow_history(workflow_id: WorkflowIdPath) -> List[Dict[str, Any]]:
    """Get version history for a workflow, newest first."""
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}")
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> Dict[str, Any]:
    """Get a specific version snapshot of a workflow."""
    snapshot = workflow_engine.get_workflow_version(workflow_id, version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snapshot


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_tags(workflow_id: WorkflowIdPath, data: TagsRequest) -> WorkflowDefinition:
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
    """Remove a tag from a workflow."""
    result = workflow_engine.remove_tag(workflow_id, tag)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if result is False:
        raise HTTPException(status_code=404, detail=f"Tag '{tag}' not found on workflow")
    wf = workflow_engine.get_workflow(workflow_id)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.post("/{workflow_id}/dry-run", response_model=WorkflowExecution)
async def dry_run_workflow(workflow_id: WorkflowIdPath) -> WorkflowExecution:
    """Simulate executing a workflow without running actions."""
    execution = workflow_engine.dry_run_workflow(workflow_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return execution
