"""Workflow version history endpoints."""

from __future__ import annotations

from typing import Annotated, Any, List

from fastapi import APIRouter, HTTPException, Path

from ...models import WorkflowVersionSnapshot
from ...services import workflow_engine
from .params import WorkflowIdPath

router = APIRouter()


@router.get("/{workflow_id}/history", response_model=List[WorkflowVersionSnapshot])
async def get_workflow_history(
    workflow_id: WorkflowIdPath,
) -> List[dict[str, Any]]:
    """Return all previous version snapshots, newest first."""
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}", response_model=WorkflowVersionSnapshot)
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> dict[str, Any]:
    """Return a specific version snapshot."""
    snap = workflow_engine.get_workflow_version(workflow_id, version)
    if snap is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snap
