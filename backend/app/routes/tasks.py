"""Task-level endpoints for monitoring individual task executions.

Includes listing, detail retrieval, retry, cancellation, and
comparison of workflow executions.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path, Query

from ..models import WorkflowExecution, WorkflowStatus
from ..services import workflow_engine

router = APIRouter()

ExecutionIdPath = Annotated[
    str,
    Path(description="Unique execution identifier"),
]


@router.get("/executions/compare", response_model=Dict[str, Any])
async def compare_executions(
    ids: Annotated[
        str,
        Query(description="Comma-separated pair of execution IDs to compare"),
    ],
) -> Dict[str, Any]:
    """Compare two executions of the same workflow side-by-side.

    Args:
        ids: Comma-separated execution IDs (exactly 2).

    Returns:
        A comparison dict with task-level diffs and summary.

    Raises:
        HTTPException: 400 if IDs are invalid or belong to different workflows.
        HTTPException: 404 if any execution is not found.
    """
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    try:
        result = workflow_engine.compare_executions(id_list)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="One or both executions not found")
    return result


@router.get("/executions", response_model=List[WorkflowExecution])
async def list_all_executions(
    status: Annotated[
        str | None,
        Query(description="Filter by execution status"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum number of results"),
    ] = 50,
) -> List[WorkflowExecution]:
    """List all execution records across workflows.

    Args:
        status: Optional status filter (must be a valid WorkflowStatus value).
        limit: Maximum number of results (1-1000).

    Returns:
        A list of execution records.

    Raises:
        HTTPException: 400 if the status value is invalid.
    """
    ws = None
    if status:
        try:
            ws = WorkflowStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}. Must be one of: {[s.value for s in WorkflowStatus]}",
            )
    return workflow_engine.list_executions(status=ws, limit=limit)


@router.get("/executions/{execution_id}", response_model=WorkflowExecution)
async def get_execution(execution_id: ExecutionIdPath) -> WorkflowExecution:
    """Get details of a specific execution.

    Args:
        execution_id: The unique execution identifier.

    Returns:
        The execution record.

    Raises:
        HTTPException: 404 if the execution is not found.
    """
    ex = workflow_engine.get_execution(execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex


@router.post("/executions/{execution_id}/retry", response_model=WorkflowExecution)
async def retry_execution(execution_id: ExecutionIdPath) -> WorkflowExecution:
    """Re-run only the failed tasks from a previous execution.

    Args:
        execution_id: The unique execution identifier.

    Returns:
        A new execution record with retried results.

    Raises:
        HTTPException: 404 if the execution is not found.
        HTTPException: 409 if the execution cannot be retried.
    """
    try:
        result = workflow_engine.retry_execution(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return result


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowExecution)
async def cancel_execution(execution_id: ExecutionIdPath) -> WorkflowExecution:
    """Cancel a RUNNING or PENDING execution.

    Args:
        execution_id: The unique execution identifier.

    Returns:
        The updated execution record with CANCELLED status.

    Raises:
        HTTPException: 404 if the execution is not found.
        HTTPException: 409 if the execution is not in a cancellable state.
    """
    try:
        result = workflow_engine.cancel_execution(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return result
