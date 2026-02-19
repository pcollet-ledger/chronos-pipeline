"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps, task
summaries, execution reports, and workflow dependency trees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import TaskResult, WorkflowDefinition, WorkflowExecution, WorkflowStatus


def format_duration(ms: Optional[float]) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds, or ``None``.

    Returns:
        A string like ``"120ms"``, ``"3.5s"``, ``"2.1m"``, or ``"1.0h"``.
        Returns ``"—"`` when *ms* is ``None``.
    """
    if ms is None:
        return "—"
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
    """Format a datetime to a string, returning ``"—"`` for ``None``.

    Args:
        dt: The datetime to format.
        fmt: A ``strftime`` format string.

    Returns:
        The formatted timestamp, or ``"—"`` if *dt* is ``None``.
    """
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_task_summary(result: TaskResult) -> str:
    """Produce a one-line summary of a task result.

    Args:
        result: The task result to summarise.

    Returns:
        A string like ``"task-abc: completed (120ms)"`` or
        ``"task-abc: failed — Timeout exceeded"``.
    """
    duration = format_duration(result.duration_ms)
    if result.status == WorkflowStatus.FAILED and result.error:
        return f"{result.task_id}: {result.status.value} — {result.error} ({duration})"
    return f"{result.task_id}: {result.status.value} ({duration})"


def format_execution_report(execution: WorkflowExecution) -> str:
    """Produce a multi-line human-readable execution report.

    Args:
        execution: The execution to report on.

    Returns:
        A formatted string with execution metadata and per-task results.
    """
    lines: List[str] = [
        f"Execution {execution.id}",
        f"  Workflow: {execution.workflow_id}",
        f"  Status:   {execution.status.value}",
        f"  Trigger:  {execution.trigger}",
        f"  Started:  {format_timestamp(execution.started_at)}",
        f"  Ended:    {format_timestamp(execution.completed_at)}",
    ]

    if execution.task_results:
        lines.append(f"  Tasks ({len(execution.task_results)}):")
        for tr in execution.task_results:
            lines.append(f"    - {format_task_summary(tr)}")
    else:
        lines.append("  Tasks: (none)")

    return "\n".join(lines)


def format_workflow_tree(workflow: WorkflowDefinition) -> str:
    """Render a workflow's task dependency graph as an indented tree.

    Root tasks (no dependencies) appear at the top level.  Dependents
    are indented beneath their parents.

    Args:
        workflow: The workflow to render.

    Returns:
        A multi-line string showing the dependency tree.
    """
    task_map: Dict[str, Any] = {t.id: t for t in workflow.tasks}
    children: Dict[str, List[str]] = {t.id: [] for t in workflow.tasks}
    roots: List[str] = []

    for task in workflow.tasks:
        if not task.depends_on:
            roots.append(task.id)
        else:
            for dep_id in task.depends_on:
                if dep_id in children:
                    children[dep_id].append(task.id)

    if not roots:
        roots = [t.id for t in workflow.tasks]

    lines: List[str] = [f"{workflow.name} (v{workflow.version})"]
    visited: set[str] = set()

    def _render(task_id: str, indent: int) -> None:
        if task_id in visited:
            return
        visited.add(task_id)
        task = task_map.get(task_id)
        if task is None:
            return
        prefix = "  " * indent
        lines.append(f"{prefix}├─ {task.name} [{task.action}]")
        for child_id in children.get(task_id, []):
            _render(child_id, indent + 1)

    for root_id in roots:
        _render(root_id, 1)

    return "\n".join(lines)


def format_status_badge(status: WorkflowStatus) -> str:
    """Return a short emoji+label badge for a workflow status.

    Args:
        status: The status to format.

    Returns:
        A string like ``"✓ completed"`` or ``"✗ failed"``.
    """
    badges = {
        WorkflowStatus.COMPLETED: "✓ completed",
        WorkflowStatus.FAILED: "✗ failed",
        WorkflowStatus.RUNNING: "⏳ running",
        WorkflowStatus.PENDING: "○ pending",
        WorkflowStatus.CANCELLED: "⊘ cancelled",
    }
    return badges.get(status, f"? {status.value}")
