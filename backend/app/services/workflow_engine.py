"""Workflow execution engine with dependency resolution.

Provides CRUD operations for workflow definitions, execution with
topological ordering, retry of failed executions, cancellation,
cloning, tagging, versioning, dry-run, search, and secondary indexes
for efficient filtered queries.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, TypedDict, Union

from ..models import (
    BulkDeleteResponse,
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


# ---------------------------------------------------------------------------
# In-memory storage
# ---------------------------------------------------------------------------
_workflows: Dict[str, WorkflowDefinition] = {}
_executions: Dict[str, WorkflowExecution] = {}

# Secondary indexes for efficient filtered queries
_workflow_tag_index: Dict[str, Set[str]] = defaultdict(set)
_execution_status_index: Dict[WorkflowStatus, Set[str]] = defaultdict(set)
_execution_workflow_index: Dict[str, Set[str]] = defaultdict(set)

# Version history: workflow_id -> list of (version_number, snapshot)
_workflow_versions: Dict[str, List[WorkflowDefinition]] = {}


# ---------------------------------------------------------------------------
# Index maintenance helpers
# ---------------------------------------------------------------------------

def _index_workflow(workflow: WorkflowDefinition) -> None:
    """Add a workflow to all secondary indexes.

    Args:
        workflow: The workflow to index.
    """
    for tag in workflow.tags:
        _workflow_tag_index[tag].add(workflow.id)


def _unindex_workflow(workflow: WorkflowDefinition) -> None:
    """Remove a workflow from all secondary indexes.

    Args:
        workflow: The workflow to remove from indexes.
    """
    for tag in workflow.tags:
        _workflow_tag_index[tag].discard(workflow.id)
        if not _workflow_tag_index[tag]:
            del _workflow_tag_index[tag]


def _index_execution(execution: WorkflowExecution) -> None:
    """Add an execution to all secondary indexes.

    Args:
        execution: The execution to index.
    """
    _execution_status_index[execution.status].add(execution.id)
    _execution_workflow_index[execution.workflow_id].add(execution.id)


def _unindex_execution_status(execution: WorkflowExecution, old_status: WorkflowStatus) -> None:
    """Remove an execution from the status index for *old_status*.

    Args:
        execution: The execution whose status changed.
        old_status: The previous status to remove from the index.
    """
    _execution_status_index[old_status].discard(execution.id)
    if not _execution_status_index[old_status]:
        del _execution_status_index[old_status]


def _rebuild_indexes() -> None:
    """Rebuild all secondary indexes from the primary stores.

    Useful for recovery after inconsistencies or for testing.
    """
    _workflow_tag_index.clear()
    _execution_status_index.clear()
    _execution_workflow_index.clear()

    for wf in _workflows.values():
        _index_workflow(wf)
    for ex in _executions.values():
        _index_execution(ex)


# ---------------------------------------------------------------------------
# Workflow CRUD
# ---------------------------------------------------------------------------

def create_workflow(data: WorkflowCreate) -> WorkflowDefinition:
    """Create a new workflow definition.

    Args:
        data: The workflow creation payload.

    Returns:
        The newly created workflow definition.
    """
    workflow = WorkflowDefinition(
        name=data.name,
        description=data.description,
        tasks=data.tasks,
        schedule=data.schedule,
        tags=data.tags,
    )
    _workflows[workflow.id] = workflow
    _index_workflow(workflow)
    return workflow


def get_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Retrieve a workflow by ID.

    Args:
        workflow_id: The unique workflow identifier.

    Returns:
        The workflow if found, otherwise ``None``.
    """
    return _workflows.get(workflow_id)


def list_workflows(
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[WorkflowDefinition]:
    """List workflows with optional tag and name-search filtering.

    Uses secondary indexes when a tag filter is provided for O(1) lookup
    instead of scanning all workflows.

    Args:
        tag: Optional tag to filter by.
        search: Optional case-insensitive name substring filter.
        limit: Maximum number of results.
        offset: Number of results to skip.

    Returns:
        A list of matching workflow definitions.
    """
    if tag:
        wf_ids = _workflow_tag_index.get(tag, set())
        results = [_workflows[wid] for wid in wf_ids if wid in _workflows]
    else:
        results = list(_workflows.values())
    if search:
        needle = search.lower()
        results = [w for w in results if needle in w.name.lower()]
    results.sort(key=lambda w: w.updated_at, reverse=True)
    return results[offset: offset + limit]


def update_workflow(
    workflow_id: str, data: WorkflowUpdate
) -> Optional[WorkflowDefinition]:
    """Update an existing workflow and store a version snapshot.

    The ``version`` field on the workflow is auto-incremented on each
    update.  A deep-copy snapshot of the pre-update state is stored
    in ``_workflow_versions``.

    Args:
        workflow_id: The ID of the workflow to update.
        data: The partial update payload.

    Returns:
        The updated workflow, or ``None`` if not found.
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None

    # Store a snapshot of the current state before mutating
    snapshot = workflow.model_copy(deep=True)
    if workflow_id not in _workflow_versions:
        _workflow_versions[workflow_id] = []
    _workflow_versions[workflow_id].append(snapshot)

    _unindex_workflow(workflow)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workflow, key, value)
    workflow.updated_at = datetime.utcnow()
    workflow.version = snapshot.version + 1
    _workflows[workflow_id] = workflow
    _index_workflow(workflow)
    return workflow


def delete_workflow(workflow_id: str) -> bool:
    """Delete a workflow by ID.

    Args:
        workflow_id: The ID of the workflow to delete.

    Returns:
        ``True`` if the workflow was deleted, ``False`` if not found.
    """
    workflow = _workflows.get(workflow_id)
    if workflow:
        _unindex_workflow(workflow)
        del _workflows[workflow_id]
        return True
    return False


def bulk_delete_workflows(workflow_ids: List[str]) -> BulkDeleteResponse:
    """Delete multiple workflows in one operation.

    Duplicate IDs in the input are deduplicated so that each unique ID is
    processed exactly once.  IDs that do not match an existing workflow are
    tracked in ``not_found_ids`` rather than raising an error, allowing
    callers to treat the operation as idempotent.

    Args:
        workflow_ids: List of workflow IDs to delete.

    Returns:
        A ``BulkDeleteResponse`` summarising results.
    """
    seen: set[str] = set()
    unique_ids: List[str] = []
    for wid in workflow_ids:
        if wid not in seen:
            seen.add(wid)
            unique_ids.append(wid)

    deleted_ids: List[str] = []
    not_found_ids: List[str] = []

    for wid in unique_ids:
        if delete_workflow(wid):
            deleted_ids.append(wid)
        else:
            not_found_ids.append(wid)

    return BulkDeleteResponse(
        deleted=len(deleted_ids),
        not_found=len(not_found_ids),
        deleted_ids=deleted_ids,
        not_found_ids=not_found_ids,
    )


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def execute_workflow(workflow_id: str, trigger: str = "manual") -> Optional[WorkflowExecution]:
    """Execute a workflow and return the execution record.

    Tasks are executed in topological order.  Execution halts at the
    first task failure.

    Args:
        workflow_id: The ID of the workflow to execute.
        trigger: How the execution was triggered (e.g. ``"manual"``, ``"scheduled"``).

    Returns:
        The execution record, or ``None`` if the workflow was not found.
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status=WorkflowStatus.RUNNING,
        started_at=datetime.utcnow(),
        trigger=trigger,
    )

    ordered_tasks = _topological_sort(workflow.tasks)

    for task in ordered_tasks:
        result = _execute_task(task)
        execution.task_results.append(result)
        if result.status == WorkflowStatus.FAILED:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.utcnow()
            _executions[execution.id] = execution
            _index_execution(execution)
            return execution

    execution.status = WorkflowStatus.COMPLETED
    execution.completed_at = datetime.utcnow()
    _executions[execution.id] = execution
    _index_execution(execution)
    return execution


def get_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """Retrieve an execution record by ID.

    Args:
        execution_id: The unique execution identifier.

    Returns:
        The execution if found, otherwise ``None``.
    """
    return _executions.get(execution_id)


def cancel_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """Cancel a RUNNING or PENDING execution.

    Args:
        execution_id: The ID of the execution to cancel.

    Returns:
        The updated execution record, or ``None`` if not found.

    Raises:
        ValueError: If the execution is not in a cancellable state
            (i.e. not RUNNING or PENDING).
    """
    execution = _executions.get(execution_id)
    if execution is None:
        return None

    cancellable = {WorkflowStatus.RUNNING, WorkflowStatus.PENDING}
    if execution.status not in cancellable:
        raise ValueError(
            f"Only running or pending executions can be cancelled. "
            f"Current status: {execution.status.value}"
        )

    old_status = execution.status
    execution.status = WorkflowStatus.CANCELLED
    execution.cancelled_at = datetime.utcnow()
    execution.completed_at = execution.cancelled_at

    _unindex_execution_status(execution, old_status)
    _execution_status_index[WorkflowStatus.CANCELLED].add(execution.id)

    return execution


def retry_execution(execution_id: str) -> Optional[WorkflowExecution]:
    """Re-run only the failed/unexecuted tasks from a previous execution.

    Returns ``None`` if the *execution_id* is not found.

    Args:
        execution_id: The ID of the execution to retry.

    Returns:
        A new execution record with retried results, or ``None`` if not found.

    Raises:
        ValueError: If the execution is not in a ``FAILED`` state or if
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

    succeeded_task_ids = {
        tr.task_id
        for tr in original.task_results
        if tr.status == WorkflowStatus.COMPLETED
    }

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
            prev_result = next(
                tr for tr in original.task_results if tr.task_id == task.id
            )
            new_execution.task_results.append(prev_result)
        else:
            result = _execute_task(task)
            new_execution.task_results.append(result)
            if result.status == WorkflowStatus.FAILED:
                new_execution.status = WorkflowStatus.FAILED
                new_execution.completed_at = datetime.utcnow()
                _executions[new_execution.id] = new_execution
                _index_execution(new_execution)
                return new_execution

    new_execution.status = WorkflowStatus.COMPLETED
    new_execution.completed_at = datetime.utcnow()
    _executions[new_execution.id] = new_execution
    _index_execution(new_execution)
    return new_execution


def list_executions(
    workflow_id: Optional[str] = None,
    status: Optional[WorkflowStatus] = None,
    limit: int = 50,
) -> List[WorkflowExecution]:
    """List execution records with optional filters.

    Uses secondary indexes when filters are provided.

    Args:
        workflow_id: Optional workflow ID to filter by.
        status: Optional status to filter by.
        limit: Maximum number of results.

    Returns:
        A list of matching execution records, sorted newest first.
    """
    if workflow_id and status:
        wf_ids = _execution_workflow_index.get(workflow_id, set())
        st_ids = _execution_status_index.get(status, set())
        result_ids = wf_ids & st_ids
        results = [_executions[eid] for eid in result_ids if eid in _executions]
    elif workflow_id:
        ex_ids = _execution_workflow_index.get(workflow_id, set())
        results = [_executions[eid] for eid in ex_ids if eid in _executions]
    elif status:
        ex_ids = _execution_status_index.get(status, set())
        results = [_executions[eid] for eid in ex_ids if eid in _executions]
    else:
        results = list(_executions.values())

    results.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _topological_sort(tasks: List[TaskDefinition]) -> List[TaskDefinition]:
    """Sort tasks respecting dependency order.

    Args:
        tasks: The list of task definitions to sort.

    Returns:
        Tasks ordered so that dependencies come before dependents.
    """
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


def _run_hook(hook_name: str, parameters: Dict[str, Any]) -> ActionOutput:
    """Execute a single hook action.

    Hooks share the same action registry as regular task actions.

    Args:
        hook_name: The action name to execute as a hook.
        parameters: Parameters to pass to the hook action.

    Returns:
        The action output.

    Raises:
        ValueError: If *hook_name* is not a recognised action.
    """
    return _run_action(hook_name, parameters)


def _execute_task(task: TaskDefinition) -> TaskResult:
    """Execute a single task, including optional pre/post hooks.

    Execution order:
      1. Run ``pre_hook`` (if set).  A failure here aborts immediately.
      2. Run the main ``action``.
      3. Run ``post_hook`` (if set).  A failure here marks the task failed.

    Args:
        task: The task definition to execute.

    Returns:
        A ``TaskResult`` with status, output, and timing information.
    """
    started = datetime.utcnow()
    try:
        combined_output: Dict[str, Any] = {}

        if task.pre_hook is not None:
            pre_result = _run_hook(task.pre_hook, task.parameters)
            combined_output["pre_hook_output"] = dict(pre_result)

        main_result = _run_action(task.action, task.parameters)
        combined_output.update(main_result)

        if task.post_hook is not None:
            post_result = _run_hook(task.post_hook, task.parameters)
            combined_output["post_hook_output"] = dict(post_result)

        completed = datetime.utcnow()
        duration = int((completed - started).total_seconds() * 1000)
        return TaskResult(
            task_id=task.id,
            status=WorkflowStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            output=combined_output,
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

    Args:
        action: The action name to execute.
        parameters: Parameters to pass to the action handler.

    Returns:
        The action output.

    Raises:
        ValueError: If *action* is not a recognised action name.
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


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

def clone_workflow(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Deep-copy a workflow with a new ID and ' (copy)' appended to the name.

    Args:
        workflow_id: The ID of the workflow to clone.

    Returns:
        The newly created clone, or ``None`` if the source was not found.
    """
    original = _workflows.get(workflow_id)
    if original is None:
        return None

    cloned = original.model_copy(deep=True)
    cloned.id = str(__import__("uuid").uuid4())
    cloned.name = f"{original.name} (copy)"
    cloned.version = 1
    cloned.created_at = datetime.utcnow()
    cloned.updated_at = datetime.utcnow()

    for task in cloned.tasks:
        task.id = str(__import__("uuid").uuid4())

    _workflows[cloned.id] = cloned
    _index_workflow(cloned)
    return cloned


# ---------------------------------------------------------------------------
# Tagging
# ---------------------------------------------------------------------------

def add_tags(workflow_id: str, tags: List[str]) -> Optional[WorkflowDefinition]:
    """Add tags to a workflow (idempotent for duplicates).

    Args:
        workflow_id: The workflow to tag.
        tags: Tags to add.

    Returns:
        The updated workflow, or ``None`` if not found.
    """
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        return None

    _unindex_workflow(workflow)
    existing = set(workflow.tags)
    for tag in tags:
        if tag not in existing:
            workflow.tags.append(tag)
            existing.add(tag)
    workflow.updated_at = datetime.utcnow()
    _index_workflow(workflow)
    return workflow


def remove_tag(workflow_id: str, tag: str) -> Optional[WorkflowDefinition]:
    """Remove a specific tag from a workflow.

    Args:
        workflow_id: The workflow to modify.
        tag: The tag to remove.

    Returns:
        The updated workflow, or ``None`` if the workflow is not found.

    Raises:
        ValueError: If the tag does not exist on the workflow.
    """
    workflow = _workflows.get(workflow_id)
    if workflow is None:
        return None

    if tag not in workflow.tags:
        raise ValueError(f"Tag '{tag}' not found on workflow")

    _unindex_workflow(workflow)
    workflow.tags = [t for t in workflow.tags if t != tag]
    workflow.updated_at = datetime.utcnow()
    _index_workflow(workflow)
    return workflow


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

def get_workflow_history(workflow_id: str) -> Optional[List[WorkflowDefinition]]:
    """Return all previous version snapshots, newest first.

    Args:
        workflow_id: The workflow to get history for.

    Returns:
        A list of version snapshots (empty if no updates), or ``None``
        if the workflow does not exist.
    """
    if workflow_id not in _workflows:
        return None
    versions = _workflow_versions.get(workflow_id, [])
    return list(reversed(versions))


def get_workflow_version(
    workflow_id: str, version: int
) -> Optional[WorkflowDefinition]:
    """Return a specific version snapshot.

    Args:
        workflow_id: The workflow to query.
        version: The version number (1-based).

    Returns:
        The snapshot, or ``None`` if not found.
    """
    if workflow_id not in _workflows:
        return None
    versions = _workflow_versions.get(workflow_id, [])
    for v in versions:
        if v.version == version:
            return v
    # Also check current version
    current = _workflows.get(workflow_id)
    if current and current.version == version:
        return current
    return None


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------

def dry_run_workflow(workflow_id: str) -> Optional[WorkflowExecution]:
    """Simulate executing a workflow without running actions.

    The execution is **not** stored in the registry.

    Args:
        workflow_id: The workflow to dry-run.

    Returns:
        A synthetic execution record, or ``None`` if the workflow is not found.
    """
    workflow = _workflows.get(workflow_id)
    if not workflow:
        return None

    started = datetime.utcnow()
    ordered_tasks = _topological_sort(workflow.tasks)

    task_results: List[TaskResult] = []
    for task in ordered_tasks:
        task_results.append(TaskResult(
            task_id=task.id,
            status=WorkflowStatus.COMPLETED,
            started_at=started,
            completed_at=started,
            output={"dry_run": True},
            duration_ms=0,
        ))

    return WorkflowExecution(
        workflow_id=workflow_id,
        status=WorkflowStatus.COMPLETED,
        started_at=started,
        completed_at=started,
        task_results=task_results,
        trigger="dry-run",
    )


# ---------------------------------------------------------------------------
# Execution comparison
# ---------------------------------------------------------------------------

def compare_executions(
    execution_ids: List[str],
) -> Optional[Dict[str, Any]]:
    """Compare two executions of the same workflow side-by-side.

    Args:
        execution_ids: Exactly two execution IDs to compare.

    Returns:
        A comparison dict, or ``None`` if any execution is not found.

    Raises:
        ValueError: If the executions belong to different workflows or
            if the number of IDs is not exactly 2.
    """
    if len(execution_ids) != 2:
        raise ValueError("Exactly two execution IDs are required")

    exec_a = _executions.get(execution_ids[0])
    exec_b = _executions.get(execution_ids[1])

    if exec_a is None or exec_b is None:
        return None

    if exec_a.workflow_id != exec_b.workflow_id:
        raise ValueError("Executions belong to different workflows")

    task_comparison: List[Dict[str, Any]] = []
    results_a = {tr.task_id: tr for tr in exec_a.task_results}
    results_b = {tr.task_id: tr for tr in exec_b.task_results}
    all_task_ids = list(dict.fromkeys(
        list(results_a.keys()) + list(results_b.keys())
    ))

    improved = 0
    regressed = 0
    unchanged = 0

    for tid in all_task_ids:
        ra = results_a.get(tid)
        rb = results_b.get(tid)
        status_a = ra.status.value if ra else "missing"
        status_b = rb.status.value if rb else "missing"
        dur_a = ra.duration_ms if ra and ra.duration_ms else 0
        dur_b = rb.duration_ms if rb and rb.duration_ms else 0

        if status_a == status_b:
            unchanged += 1
        elif status_b == "completed" and status_a != "completed":
            improved += 1
        elif status_a == "completed" and status_b != "completed":
            regressed += 1
        else:
            unchanged += 1

        task_comparison.append({
            "task_id": tid,
            "status_a": status_a,
            "status_b": status_b,
            "duration_diff_ms": dur_b - dur_a,
        })

    return {
        "workflow_id": exec_a.workflow_id,
        "executions": [exec_a, exec_b],
        "task_comparison": task_comparison,
        "summary": {
            "improved_count": improved,
            "regressed_count": regressed,
            "unchanged_count": unchanged,
        },
    }


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def clear_all() -> None:
    """Clear all workflows, executions, indexes, and version history (for testing)."""
    _workflows.clear()
    _executions.clear()
    _workflow_tag_index.clear()
    _execution_status_index.clear()
    _execution_workflow_index.clear()
    _workflow_versions.clear()
