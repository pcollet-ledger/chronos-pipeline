"""Workflow execution engine with dependency resolution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypedDict, Union

from ..models import (
    TaskDefinition,
    TaskResult,
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStatus,
    WorkflowUpdate,
)


class LogOutput(TypedDict):
    message: str


class TransformOutput(TypedDict):
    transformed: bool
    input_keys: List[str]


class ValidateOutput(TypedDict):
    valid: bool


class NotifyOutput(TypedDict):
    notified: bool
    channel: str


class AggregateOutput(TypedDict):
    count: int
    keys: List[str]


ActionOutput = Union[LogOutput, TransformOutput, ValidateOutput, NotifyOutput, AggregateOutput]

_ActionHandler = Callable[[Dict[str, Any]], ActionOutput]


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


def retry_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """Re-run only the failed/unexecuted tasks from a previous execution.

    Returns ``None`` if the *execution_id* is not found.
    Raises ``ValueError`` if the execution is not in a ``FAILED`` state or if
    the parent workflow no longer exists.
    """
    original = _executions.get(execution_id)
    if original is None:
        return None

    if original.status != WorkflowStatus.FAILED:
        raise ValueError(
            f"Only failed executions can be retried. Current status: {original.status.value}"
        )

    workflow = _workflows.get(original.workflow_id)
    if workflow is None:
        raise ValueError("Parent workflow no longer exists")

    # Determine which task IDs completed successfully in the original run
    succeeded_task_ids = {
        tr.task_id
        for tr in original.task_results
        if tr.status == WorkflowStatus.COMPLETED
    }

    # Build a new execution, preserving successful results
    new_execution = WorkflowExecution(
        workflow_id=original.workflow_id,
        status=WorkflowStatus.RUNNING,
        started_at=datetime.utcnow(),
        trigger="retry",
        metadata={"retried_from": execution_id},
    )

    ordered_tasks = _topological_sort(workflow.tasks)

    for task in ordered_tasks:
        if task.id in succeeded_task_ids:
            # Carry forward the original successful result
            prev_result = next(
                tr for tr in original.task_results if tr.task_id == task.id
            )
            new_execution.task_results.append(prev_result)
        else:
            # Re-execute this task
            result = _execute_task(task)
            new_execution.task_results.append(result)
            if result.status == WorkflowStatus.FAILED:
                new_execution.status = WorkflowStatus.FAILED
                new_execution.completed_at = datetime.utcnow()
                _executions[new_execution.id] = new_execution
                return new_execution

    new_execution.status = WorkflowStatus.COMPLETED
    new_execution.completed_at = datetime.utcnow()
    _executions[new_execution.id] = new_execution
    return new_execution


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


def _topological_sort(tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    """Sort tasks respecting dependency order."""
    task_map: Dict[str, TaskDefinition] = {t.id: t for t in tasks}
    visited: set[str] = set()
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


def _run_action(action: str, parameters: Dict[str, Any]) -> ActionOutput:
    """Dispatch and run a task action.

    Raises ``ValueError`` if *action* is not a recognised action name.
    """
    actions: Dict[str, _ActionHandler] = {
        "log": lambda p: LogOutput(message=p.get("message", "logged")),
        "transform": lambda p: TransformOutput(transformed=True, input_keys=list(p.keys())),
        "validate": lambda p: ValidateOutput(valid=bool(p)),
        "notify": lambda p: NotifyOutput(notified=True, channel=p.get("channel", "default")),
        "aggregate": lambda p: AggregateOutput(count=len(p), keys=list(p.keys())),
    }
    handler = actions.get(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")
    return handler(parameters)


def clear_all() -> None:
    """Clear all workflows and executions (for testing)."""
    _workflows.clear()
    _executions.clear()
