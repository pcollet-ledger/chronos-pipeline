"""Workflow extra endpoints: clone, tags, versioning history."""

from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, HTTPException, Path

from ..models import WorkflowDefinition
from ..services import workflow_engine

router = APIRouter()

WorkflowIdPath = Annotated[
    str,
    Path(description="Unique workflow identifier"),
]


@router.post("/{workflow_id}/clone", response_model=WorkflowDefinition, status_code=201)
async def clone_workflow(workflow_id: WorkflowIdPath) -> WorkflowDefinition:
    """Clone an existing workflow with a new ID and ' (copy)' appended to the name.

    Args:
        workflow_id: The ID of the workflow to clone.

    Returns:
        The newly created clone.

    Raises:
        HTTPException: 404 if the source workflow is not found.
    """
    clone = workflow_engine.clone_workflow(workflow_id)
    if clone is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return clone


@router.post("/{workflow_id}/tags", response_model=WorkflowDefinition)
async def add_tags(
    workflow_id: WorkflowIdPath,
    body: dict,
) -> WorkflowDefinition:
    """Add one or more tags to a workflow.

    Expects ``{"tags": ["tag1", "tag2"]}``.  Adding duplicate tags is
    idempotent.

    Args:
        workflow_id: The unique workflow identifier.
        body: Request body containing a ``tags`` list.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    tags = body.get("tags", [])
    result = workflow_engine.add_tags(workflow_id, tags)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.delete("/{workflow_id}/tags/{tag}", response_model=WorkflowDefinition)
async def remove_tag(
    workflow_id: WorkflowIdPath,
    tag: Annotated[str, Path(description="Tag to remove")],
) -> WorkflowDefinition:
    """Remove a specific tag from a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        tag: The tag string to remove.

    Returns:
        The updated workflow definition.

    Raises:
        HTTPException: 404 if the workflow or tag is not found.
    """
    try:
        result = workflow_engine.remove_tag(workflow_id, tag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/{workflow_id}/history", response_model=List[WorkflowDefinition])
async def get_workflow_history(workflow_id: WorkflowIdPath) -> List[WorkflowDefinition]:
    """Return all previous versions of a workflow, newest first.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        A list of version snapshots.

    Raises:
        HTTPException: 404 if the workflow is not found.
    """
    result = workflow_engine.get_workflow_history(workflow_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return result


@router.get("/{workflow_id}/history/{version}", response_model=WorkflowDefinition)
async def get_workflow_version(
    workflow_id: WorkflowIdPath,
    version: Annotated[int, Path(ge=1, description="Version number")],
) -> WorkflowDefinition:
    """Return a specific version snapshot of a workflow.

    Args:
        workflow_id: The unique workflow identifier.
        version: The version number to retrieve.

    Returns:
        The version snapshot.

    Raises:
        HTTPException: 404 if the workflow or version is not found.
    """
    result = workflow_engine.get_workflow_version(workflow_id, version)
    if result is None:
        raise HTTPException(status_code=404, detail="Workflow or version not found")
    return result
