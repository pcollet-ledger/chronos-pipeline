"""Workflow execution engine with dependency resolution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from .action_registry import run_action as _run_action
from ..models import (
    TaskDefinition,
    TaskResult,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowImport,
    WorkflowStatus,
    WorkflowUpdate,
)


# In-memory storage (replace with database in production)
_workflows: Dict[str, WorkflowDefinition] = {}
_executions: Dict[str, WorkflowExecution] = {}


def create_workflow(data: WorkflowCreate) -> WorkflowDefinition:
    """Create a new workflow definition."""
    workflow = WorkflowDefinition(
        name=data.name,
        description=data.description,
        tasks=data.tasks,
        schedule=data.schedule,
        tags=data.tags,
    )
    _workflows[workflow.id] = workflow
    return workflow


def get_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Retrieve a workflow by ID."""
    return _workflows.get(workflow_id)


def list_workflows(
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[WorkflowDefinition]:
    """List workflows with optional tag filtering."""
    results = list(_workflows.values())
    if tag:
        results = [w for w in results if tag in w.tags]
    results.sort(key=lambda w: w.updated_at, reverse=True)
    return results[offset : offset + limit]


def update_workflow(
    workflow_id: str, data: WorkflowUpdate
) -> Optional[WorkflowDefinition]:
    """Update an existing workflow."""
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workflow, key, value)
    workflow.updated_at = datetime.utcnow()
    _workflows[workflow_id] = workflow
    return workflow


def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow by ID."""
    if workflow_id in _workflows:
        del _workflows[workflow_id]
        return True
    return False


def execute_workflow(workflow_id: str, trigger: str = "manual") -> Optional[WorkflowExecution]:
    """Execute a workflow and return the execution record."""
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status=WorkflowStatus.RUNNING,
        started_at=datetime.utcnow(),
        trigger=trigger,
    )

    # Resolve execution order via topological sort
    ordered_tasks = _topological_sort(workflow.tasks)

    for task in ordered_tasks:
        result = _execute_task(task)
        execution.task_results.append(result)
        if result.status == WorkflowStatus.FAILED:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            _executions[execution.id] = execution
            return execution

    execution.status = WorkflowStatus.COMPLETED
    execution.completed_at = datetime.utcnow()
    _executions[execution.id] = execution
    return execution


def get_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """Retrieve an execution record by ID."""
    return _executions.get(execution_id)


def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[WorkflowStatus] = None,
    limit: int = 50,
) -> List[WorkflowExecution]:
    """List execution records with optional filters."""
    results = list(_executions.values())
    if workflow_id:
        results = [e for e in results if e.workflow_id == workflow_id]
    if status:
        results = [e for e in results if e.status == status]
    results.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
    return results[:limit]


def export_workflow(workflow_id: str) -> Optional[Dict[str, Any]]:
    """Export a workflow definition as a portable dictionary.

    The exported payload omits internal fields (``id``, ``created_at``,
    ``updated_at``) so it can be re-imported into any instance.
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None
    data = workflow.model_dump()
    for key in ("id", "created_at", "updated_at"):
        data.pop(key, None)
    for task in data.get("tasks", []):
        task.pop("id", None)
    data["version"] = "1.0"
    return data


def import_workflow(data: WorkflowImport) -> WorkflowDefinition:
    """Import a workflow from an exported definition, assigning fresh IDs."""
    workflow = WorkflowDefinition(
        name=data.name,
        description=data.description,
        tasks=data.tasks,
        schedule=data.schedule,
        tags=data.tags,
    )
    _workflows[workflow.id] = workflow
    return workflow


def _topological_sort(tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    """Sort tasks respecting dependency order."""
    task_map = {t.id: t for t in tasks}
    visited: set = set()
    order: List[TaskDefinition] = []

    def visit(task_id: str) -> None:
        if task_id in visited:
            return
        visited.add(task_id)
        task = task_map.get(task_id)
        if task:
            for dep_id in task.depends_on:
                visit(dep_id)
            order.append(task)

    for task in tasks:
        visit(task.id)
    return order


def _execute_task(task: TaskDefinition) -> TaskResult:
    """Execute a single task and return its result."""
    started = datetime.utcnow()
    try:
        output = _run_action(task.action, task.parameters)
        completed = datetime.utcnow()
        duration = int((completed - started).total_seconds() * 1000)
        return TaskResult(
            task_id=task.id,
            status=WorkflowStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            output=output,
            duration_ms=duration,
        )
    except Exception as exc:
        completed = datetime.utcnow()
        duration = int((completed - started).total_seconds() * 1000)
        return TaskResult(
            task_id=task.id,
            status=WorkflowStatus.FAILED,
            started_at=started,
            completed_at=completed,
            error=str(exc),
            duration_ms=duration,
        )


def clear_all() -> None:
    """Clear all workflows and executions (for testing)."""
    _workflows.clear()
    _executions.clear()
