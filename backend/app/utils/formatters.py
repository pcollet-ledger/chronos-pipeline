"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps, task
summaries, execution reports, and workflow dependency trees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import TaskResult, WorkflowDefinition, WorkflowExecution


def format_duration(ms: float) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds.

    Returns:
        A string like ``"500ms"``, ``"1.5s"``, ``"2.0m"``, or ``"1.0h"``.
    """
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


def format_timestamp(dt: Optional[datetime]) -> str:
    """Format a datetime to ISO 8601 string, or ``"—"`` if ``None``.

    Args:
        dt: The datetime to format.

    Returns:
        An ISO 8601 string or a dash placeholder.
    """
    if dt is None:
        return "—"
    return dt.isoformat() + "Z"


def format_task_summary(result: TaskResult) -> str:
    """Format a single task result as a one-line summary.

    Args:
        result: The task result to summarise.

    Returns:
        A string like ``"task-id: completed (5ms)"``.
    """
    duration = format_duration(result.duration_ms) if result.duration_ms is not None else "—"
    status = result.status.value if hasattr(result.status, "value") else str(result.status)
    line = f"{result.task_id}: {status} ({duration})"
    if result.error:
        line += f" — {result.error}"
    return line


def format_execution_report(execution: WorkflowExecution) -> str:
    """Format a full execution as a multi-line report.

    Args:
        execution: The execution to format.

    Returns:
        A multi-line string with execution metadata and task results.
    """
    status = execution.status.value if hasattr(execution.status, "value") else str(execution.status)
    lines = [
        f"Execution {execution.id}",
        f"  Workflow: {execution.workflow_id}",
        f"  Status:   {status}",
        f"  Trigger:  {execution.trigger}",
        f"  Started:  {format_timestamp(execution.started_at)}",
        f"  Ended:    {format_timestamp(execution.completed_at)}",
        f"  Tasks ({len(execution.task_results)}):",
    ]
    for tr in execution.task_results:
        lines.append(f"    - {format_task_summary(tr)}")
    return "\n".join(lines)


def format_workflow_tree(workflow: WorkflowDefinition) -> str:
    """Format a workflow's task dependency graph as an indented tree.

    Args:
        workflow: The workflow to format.

    Returns:
        A multi-line string showing the dependency tree.
    """
    task_map: Dict[str, Any] = {t.id: t for t in workflow.tasks}
    children: Dict[str, List[str]] = {t.id: [] for t in workflow.tasks}
    roots: List[str] = []

    for task in workflow.tasks:
        if not task.depends_on:
            roots.append(task.id)
        for dep_id in task.depends_on:
            if dep_id in children:
                children[dep_id].append(task.id)

    lines = [f"{workflow.name} (v{workflow.version})"]

    def _render(task_id: str, indent: int) -> None:
        task = task_map.get(task_id)
        if task is None:
            return
        prefix = "  " * indent + ("└─ " if indent > 0 else "")
        lines.append(f"{prefix}{task.name} [{task.action}]")
        for child_id in children.get(task_id, []):
            _render(child_id, indent + 1)

    for root_id in roots:
        _render(root_id, 1)

    # Render orphans (tasks whose dependencies are not in the task list)
    rendered = set()
    for line in lines:
        rendered.add(line)

    return "\n".join(lines)
