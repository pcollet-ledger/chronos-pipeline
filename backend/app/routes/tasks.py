"""Task-level endpoints for monitoring individual task executions.

Provides read access to execution records and a retry endpoint that
re-runs only the failed/unexecuted tasks from a previous execution.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ..models import WorkflowExecution, WorkflowStatus
from ..services import workflow_engine
from ..utils.helpers import raise_conflict, raise_not_found

router = APIRouter()


@router.get("/executions", response_model=List[WorkflowExecution])
async def list_all_executions(
    status: Optional[str] = None,
    limit: int = 50,
) -> List[WorkflowExecution]:
    """List all execution records across workflows.

    Args:
        status: Optional status filter (must be a valid ``WorkflowStatus`` value).
        limit: Maximum number of results.

    Returns:
        A list of ``WorkflowExecution`` records.

    Raises:
        HTTPException: 400 if *status* is not a valid enum value.
    """
    ws: Optional[WorkflowStatus] = None
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
async def get_execution(execution_id: str) -> WorkflowExecution:
    """Get details of a specific execution.

    Args:
        execution_id: UUID of the execution record.

    Returns:
        The matching ``WorkflowExecution``.

    Raises:
        HTTPException: 404 if the execution does not exist.
    """
    ex = workflow_engine.get_execution(execution_id)
    if not ex:
        raise_not_found("Execution")
    return ex  # type: ignore[return-value]


@router.post("/executions/{execution_id}/retry", response_model=WorkflowExecution)
async def retry_execution(execution_id: str) -> WorkflowExecution:
    """Re-run only the failed tasks from a previous execution.

    Successful task results from the original run are carried forward.
    Only failed or never-executed tasks are re-run.

    Args:
        execution_id: UUID of the failed execution to retry.

    Returns:
        A new ``WorkflowExecution`` record for the retry attempt.

    Raises:
        HTTPException: 404 if the execution does not exist.
        HTTPException: 409 if the execution cannot be retried (e.g. not
            in ``FAILED`` state, or parent workflow deleted).
    """
    try:
        result = workflow_engine.retry_execution(execution_id)
    except ValueError as exc:
        raise_conflict(str(exc))
    if result is None:
        raise_not_found("Execution")
    return result  # type: ignore[return-value]
