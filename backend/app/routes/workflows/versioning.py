"""Workflow version history endpoints."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path

from ...services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.get("/{workflow_id}/history", response_model=List[Dict[str, Any]])
async def get_workflow_history(
    workflow_id: WorkflowIdPath,
) -> List[Dict[str, Any]]:
    """Return all previous version snapshots, newest first."""
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}")
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> Dict[str, Any]:
    """Return a specific version snapshot."""
    snap = workflow_engine.get_workflow_version(workflow_id, version)
    if snap is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snap
