"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps,
task summaries, execution reports, and workflow dependency trees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from ..models import TaskDefinition, TaskResult, WorkflowDefinition, WorkflowExecution, WorkflowStatus


def format_duration(ms: Optional[float]) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Automatically selects the most appropriate unit (ms, s, m, h).

    Args:
        ms: Duration in milliseconds, or ``None``.

    Returns:
        A formatted string like ``"42ms"``, ``"1.5s"``, ``"3.2m"``, or
        ``"1.1h"``.  Returns ``"N/A"`` when *ms* is ``None``.
    """
    if ms is None:
        return "N/A"
    if ms < 0:
        return "0ms"
    if ms < 1000:
        return f"{ms:.0f}ms"
    seconds = ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    return f"{hours:.1f}h"


def format_timestamp(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime to a human-readable string.

    Args:
        dt: The datetime to format, or ``None``.
        fmt: ``strftime`` format string.

    Returns:
        The formatted timestamp, or ``"N/A"`` when *dt* is ``None``.
    """
    if dt is None:
        return "N/A"
    return dt.strftime(fmt)


def format_task_summary(task: TaskDefinition) -> str:
    """Produce a one-line summary of a task definition.

    Includes the task name, action, priority, and dependency count.

    Args:
        task: The task definition to summarise.

    Returns:
        A string like ``"Log Step [log] (priority=high, deps=2)"``.
    """
    dep_count = len(task.depends_on)
    parts = [
        f"{task.name} [{task.action}]",
        f"(priority={task.priority.value}, deps={dep_count})",
    ]
    if task.pre_hook:
        parts.append(f"pre_hook={task.pre_hook}")
    if task.post_hook:
        parts.append(f"post_hook={task.post_hook}")
    return " ".join(parts)


def format_task_result_line(result: TaskResult) -> str:
    """Format a single task result as a status line.

    Args:
        result: The task result to format.

    Returns:
        A string like ``"[COMPLETED] task-id (42ms)"`` or
        ``"[FAILED] task-id: error message"``.
    """
    status_label = result.status.value.upper()
    duration_str = format_duration(result.duration_ms)
    if result.status == WorkflowStatus.FAILED and result.error:
        return f"[{status_label}] {result.task_id} ({duration_str}): {result.error}"
    return f"[{status_label}] {result.task_id} ({duration_str})"


def format_execution_report(execution: WorkflowExecution) -> str:
    """Generate a multi-line execution report.

    Includes execution metadata, overall status, and per-task results.

    Args:
        execution: The execution to report on.

    Returns:
        A multi-line string suitable for logging or display.
    """
    lines: List[str] = [
        f"Execution Report: {execution.id}",
        f"  Workflow:  {execution.workflow_id}",
        f"  Status:    {execution.status.value}",
        f"  Trigger:   {execution.trigger}",
        f"  Started:   {format_timestamp(execution.started_at)}",
        f"  Completed: {format_timestamp(execution.completed_at)}",
    ]

    if execution.cancelled_at:
        lines.append(f"  Cancelled: {format_timestamp(execution.cancelled_at)}")

    if execution.started_at and execution.completed_at:
        dur_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000
        lines.append(f"  Duration:  {format_duration(dur_ms)}")

    if execution.task_results:
        lines.append(f"  Tasks ({len(execution.task_results)}):")
        for tr in execution.task_results:
            lines.append(f"    {format_task_result_line(tr)}")
    else:
        lines.append("  Tasks: (none)")

    if execution.metadata:
        lines.append(f"  Metadata:  {execution.metadata}")

    return "\n".join(lines)


def format_workflow_tree(workflow: WorkflowDefinition) -> str:
    """Render a workflow's task dependency structure as an ASCII tree.

    Root tasks (no dependencies) are listed first, followed by their
    dependents indented with tree-drawing characters.

    Args:
        workflow: The workflow to render.

    Returns:
        A multi-line ASCII tree string.
    """
    if not workflow.tasks:
        return f"{workflow.name} (no tasks)"

    task_map: Dict[str, TaskDefinition] = {t.id: t for t in workflow.tasks}
    children: Dict[str, List[str]] = {t.id: [] for t in workflow.tasks}
    roots: List[str] = []

    for task in workflow.tasks:
        if not task.depends_on:
            roots.append(task.id)
        for dep_id in task.depends_on:
            if dep_id in children:
                children[dep_id].append(task.id)

    if not roots:
        roots = [workflow.tasks[0].id]

    lines: List[str] = [f"{workflow.name} (v{workflow.version})"]
    visited: set[str] = set()

    def _render(task_id: str, prefix: str, is_last: bool) -> None:
        if task_id in visited or task_id not in task_map:
            return
        visited.add(task_id)

        connector = "└── " if is_last else "├── "
        task = task_map[task_id]
        lines.append(f"{prefix}{connector}{task.name} [{task.action}]")

        child_prefix = prefix + ("    " if is_last else "│   ")
        child_ids = children.get(task_id, [])
        for i, child_id in enumerate(child_ids):
            _render(child_id, child_prefix, i == len(child_ids) - 1)

    for i, root_id in enumerate(roots):
        _render(root_id, "", i == len(roots) - 1)

    return "\n".join(lines)
