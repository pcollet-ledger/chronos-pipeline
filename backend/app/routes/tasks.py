"""Task-level endpoints for monitoring individual task executions."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException

from ..models import WorkflowExecution, WorkflowStatus
from ..services import workflow_engine

router = APIRouter()


@router.get("/executions", response_model=List[WorkflowExecution])
async def list_all_executions(
    status: Optional[str] = None,
    limit: int = 50,
):
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
async def get_execution(execution_id: str):
    """Get details of a specific execution."""
    ex = workflow_engine.get_execution(execution_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex
