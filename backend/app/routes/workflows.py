"""Workflow CRUD and execution endpoints.

All endpoints return Pydantic models directly — FastAPI handles
serialisation.  ``None`` from service functions maps to 404, and
``ValueError`` maps to 409 (business-rule conflict).
"""

from typing import List, Optional

from fastapi import APIRouter

from ..models import (
    BulkDeleteRequest,
    BulkDeleteResponse,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowUpdate,
)
from ..services import workflow_engine
from ..utils.helpers import raise_conflict, raise_not_found

router = APIRouter()


@router.post("/", response_model=WorkflowDefinition, status_code=201)
async def create_workflow(data: WorkflowCreate) -> WorkflowDefinition:
    """Create a new workflow definition.

    Args:
        data: Workflow creation payload.

    Returns:
        The newly created ``WorkflowDefinition``.
    """
    return workflow_engine.create_workflow(data)


@router.get("/", response_model=List[WorkflowDefinition])
async def list_workflows(
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[WorkflowDefinition]:
    """List all workflow definitions with optional filtering.

    Args:
        tag: If provided, only workflows containing this tag are returned.
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        A list of ``WorkflowDefinition`` objects.
    """
    return workflow_engine.list_workflows(tag=tag, limit=limit, offset=offset)


@router.post("/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_workflows(data: BulkDeleteRequest) -> BulkDeleteResponse:
    """Delete multiple workflows in a single request.

    Accepts a JSON body with a list of workflow IDs.  IDs that do not
    match an existing workflow are reported as ``not_found`` rather than
    causing an error, making the operation safe to retry.

    Args:
        data: Request body containing the list of IDs.

    Returns:
        A ``BulkDeleteResponse`` summarising deleted vs. not-found counts.
    """
    return workflow_engine.bulk_delete_workflows(data.ids)


@router.get("/{workflow_id}", response_model=WorkflowDefinition)
async def get_workflow(workflow_id: str) -> WorkflowDefinition:
    """Get a workflow by ID.

    Args:
        workflow_id: UUID of the workflow.

    Returns:
        The matching ``WorkflowDefinition``.

    Raises:
        HTTPException: 404 if the workflow does not exist.
    """
    wf = workflow_engine.get_workflow(workflow_id)
    if not wf:
        raise_not_found("Workflow")
    return wf  # type: ignore[return-value]


@router.patch("/{workflow_id}", response_model=WorkflowDefinition)
async def update_workflow(
    workflow_id: str,
    data: WorkflowUpdate,
) -> WorkflowDefinition:
    """Update an existing workflow.

    Args:
        workflow_id: UUID of the workflow to update.
        data: Partial update payload.

    Returns:
        The updated ``WorkflowDefinition``.

    Raises:
        HTTPException: 404 if the workflow does not exist.
    """
    wf = workflow_engine.update_workflow(workflow_id, data)
    if not wf:
        raise_not_found("Workflow")
    return wf  # type: ignore[return-value]


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(workflow_id: str) -> None:
    """Delete a workflow.

    Args:
        workflow_id: UUID of the workflow to delete.

    Raises:
        HTTPException: 404 if the workflow does not exist.
    """
    if not workflow_engine.delete_workflow(workflow_id):
        raise_not_found("Workflow")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecution)
async def execute_workflow(
    workflow_id: str,
    trigger: str = "manual",
) -> WorkflowExecution:
    """Execute a workflow and return the execution record.

    Args:
        workflow_id: UUID of the workflow to execute.
        trigger: Label for what triggered the execution (default ``"manual"``).

    Returns:
        The ``WorkflowExecution`` record.

    Raises:
        HTTPException: 404 if the workflow does not exist.
    """
    execution = workflow_engine.execute_workflow(workflow_id, trigger=trigger)
    if not execution:
        raise_not_found("Workflow")
    return execution  # type: ignore[return-value]


@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecution])
async def list_workflow_executions(
    workflow_id: str,
    limit: int = 50,
) -> List[WorkflowExecution]:
    """List executions for a specific workflow.

    Args:
        workflow_id: UUID of the workflow.
        limit: Maximum number of results.

    Returns:
        A list of ``WorkflowExecution`` records.
    """
    return workflow_engine.list_executions(workflow_id=workflow_id, limit=limit)
