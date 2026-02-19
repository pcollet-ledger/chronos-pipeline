"""Extended workflow endpoints: clone, versioning, tagging, dry-run."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, HTTPException, Path

from ..models import TagsRequest, WorkflowDefinition, WorkflowExecution
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone an existing workflow with a new ID.

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


@router.get("/{workflow_id}/history", response_model=List[Dict[str, Any]])
async def get_workflow_history(workflow_id: WorkflowIdPath) -> List[Dict[str, Any]]:
    """Get all previous versions of a workflow.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A list of version snapshots sorted newest first.

    Raises:
        HTTPException: 404 if the workflow was never found.
    """
    history = workflow_engine.get_workflow_history(workflow_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return history


@router.get("/{workflow_id}/history/{version}")
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(description="Version number to retrieve", ge=1)],
) -> Dict[str, Any]:
    """Get a specific version snapshot of a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        version: The version number.

    Returns:
        The version snapshot.

    Raises:
        HTTPException: 404 if the workflow or version is not found.
    """
    wf = workflow_engine.get_workflow(workflow_id)
    if wf is None and workflow_engine.get_workflow_history(workflow_id) is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    snapshot = workflow_engine.get_workflow_version(workflow_id, version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return snapshot


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_tags(
    workflow_id: WorkflowIdPath, data: TagsRequest
) -> WorkflowDefinition:
    """Add tags to a workflow (idempotent for duplicates).

    Args:
        workflow_id: The unique workflow identifier.
        data: The tags to add.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    wf = workflow_engine.add_tags(workflow_id, data.tags)
    if wf is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_tag(
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
    """
    result = workflow_engine.remove_tag(workflow_id, tag)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if result is False:
        raise HTTPException(status_code=404, detail="Tag not found")
    wf = workflow_engine.get_workflow(workflow_id)
    return wf


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
    execution = workflow_engine.dry_run_workflow(workflow_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return execution
