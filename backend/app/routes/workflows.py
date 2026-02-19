"""Workflow CRUD and execution endpoints.

All endpoints return Pydantic models directly; FastAPI handles
serialisation.  ``None`` from services maps to 404, ``ValueError``
maps to 409.
"""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

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


@router.post("/", response_model=WorkflowDefinition, status_code=201)
async def create_workflow(data: WorkflowCreate) -> WorkflowDefinition:
    """Create a new workflow definition.

    Args:
        data: The workflow creation payload.

    Returns:
        The newly created workflow definition.
    """
    return workflow_engine.create_workflow(data)


@router.get("/", response_model=List[WorkflowDefinition])
async def list_workflows(
    tag: Annotated[
        str | None,
        Query(description="Filter workflows by tag"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Case-insensitive substring search on workflow name"),
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
    """List all workflow definitions.

    Args:
        tag: Optional tag filter.
        search: Optional name substring filter.
        limit: Maximum number of results (1-1000).
        offset: Pagination offset.

    Returns:
        A list of workflow definitions.
    """
    return workflow_engine.list_workflows(tag=tag, search=search, limit=limit, offset=offset)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_workflows(data: BulkDeleteRequest) -> BulkDeleteResponse:
    """Delete multiple workflows in a single request.

    Accepts a JSON body with a list of workflow IDs.  IDs that do not
    match an existing workflow are reported as ``not_found`` rather than
    causing an error, making the operation safe to retry.

    Args:
        data: The bulk delete request payload.

    Returns:
        A summary of deleted and not-found IDs.
    """
    return workflow_engine.bulk_delete_workflows(data.ids)


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Get a workflow by ID.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        The workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    wf = workflow_engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.patch("/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(
    workflow_id: WorkflowIdPath, data: WorkflowUpdate
) -> WorkflowDefinition:
    """Update an existing workflow.

    Args:
        workflow_id: The unique workflow identifier.
        data: The partial update payload.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    wf = workflow_engine.update_workflow(workflow_id, data)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}", status_code=204, response_class=Response)
async def delete_workflow(workflow_id: WorkflowIdPath) -> Response:
    """Delete a workflow.

    Args:
        workflow_id: The unique workflow identifier.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
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


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone an existing workflow with a new ID and ' (copy)' appended to the name.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        The cloned workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    clone = workflow_engine.clone_workflow(workflow_id)
    if clone is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return clone


@router.post("/{workflow_id}/dry-run", response_model=WorkflowExecution)
async def dry_run_workflow(workflow_id: WorkflowIdPath) -> WorkflowExecution:
    """Simulate executing a workflow without running actions.

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


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_workflow_tags(
    workflow_id: WorkflowIdPath,
    data: dict,
) -> WorkflowDefinition:
    """Add tags to a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        data: A dict with a ``tags`` key containing a list of strings.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    tags = data.get("tags", [])
    wf = workflow_engine.add_tags(workflow_id, tags)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_workflow_tag(
    workflow_id: WorkflowIdPath,
    tag: Annotated[str, Path(description="Tag to remove")],
) -> WorkflowDefinition:
    """Remove a tag from a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        tag: The tag to remove.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow or tag is not found.
        HTTPException: 409 if the tag does not exist on the workflow.
    """
    try:
        wf = workflow_engine.remove_tag(workflow_id, tag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.get("/{workflow_id}/history")
async def get_workflow_history(
    workflow_id: WorkflowIdPath,
) -> List[dict]:
    """Return all version snapshots for a workflow, newest first.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A list of version snapshots.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}")
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> dict:
    """Return a specific version snapshot.

    Args:
        workflow_id: The unique workflow identifier.
        version: The version number.

    Returns:
        The version snapshot.

    Raises:
        HTTPException: 404 if the workflow or version is not found.
    """
    snapshot = workflow_engine.get_workflow_version(workflow_id, version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snapshot
