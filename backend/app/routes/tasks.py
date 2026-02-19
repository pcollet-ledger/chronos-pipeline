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


@router.get("/executions/compare")
async def compare_executions(
    ids: Annotated[
        str,
        Query(description="Comma-separated pair of execution IDs to compare"),
    ],
) -> Dict[str, Any]:
    """Compare two executions of the same workflow side-by-side."""
    parts = [i.strip() for i in ids.split(",") if i.strip()]
    if len(parts) != 2:
        raise HTTPException(
            status_code=400,
            detail="Exactly two comma-separated execution IDs are required",
        )
    try:
        result = workflow_engine.compare_executions(parts[0], parts[1])
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
    """List all execution records across workflows."""
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
    """Get details of a specific execution."""
    ex = workflow_engine.get_execution(execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex


@router.post("/executions/{execution_id}/retry", response_model=WorkflowExecution)
async def retry_execution(execution_id: ExecutionIdPath) -> WorkflowExecution:
    """Re-run only the failed tasks from a previous execution."""
    try:
        result = workflow_engine.retry_execution(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return result


@router.post("/executions/{execution_id}/cancel", response_model=WorkflowExecution)
async def cancel_execution(execution_id: ExecutionIdPath) -> WorkflowExecution:
    """Cancel a RUNNING or PENDING execution."""
    try:
        result = workflow_engine.cancel_execution(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return result
