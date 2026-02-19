"""Workflow CRUD endpoints: create, read, update, delete, bulk-delete, list."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import Response

from ..models import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    WorkflowCreate,
    WorkflowDefinition,
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
        search: Optional case-insensitive name search.
        limit: Maximum number of results (1-1000).
        offset: Pagination offset.

    Returns:
        A list of workflow definitions.
    """
    return workflow_engine.list_workflows(
        tag=tag, search=search, limit=limit, offset=offset,
    )


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_workflows(data: BulkDeleteRequest) -> BulkDeleteResponse:
    """Delete multiple workflows in a single request.

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
