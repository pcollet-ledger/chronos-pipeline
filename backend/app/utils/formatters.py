"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps, task
summaries, execution reports, and workflow dependency trees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def format_duration(ms: Optional[float]) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds, or ``None``.

    Returns:
        A formatted string like ``"150ms"``, ``"2.3s"``, ``"1.5m"``, or ``"—"``
        when the input is ``None``.
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
        fmt: strftime format string.

    Returns:
        Formatted timestamp or ``"—"``.
    """
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_task_summary(task_result: Dict[str, Any]) -> str:
    """Produce a one-line summary of a task result.

    Args:
        task_result: A dict with at least ``task_id``, ``status``, and
            optionally ``duration_ms`` and ``error``.

    Returns:
        A summary string like ``"task-abc: completed (12ms)"``.
    """
    tid = task_result.get("task_id", "unknown")
    status = task_result.get("status", "unknown")
    duration = format_duration(task_result.get("duration_ms"))
    error = task_result.get("error")
    base = f"{tid}: {status} ({duration})"
    if error:
        base += f" — {error}"
    return base


def format_execution_report(execution: Dict[str, Any]) -> str:
    """Format a full execution record as a multi-line report.

    Args:
        execution: A dict representing a ``WorkflowExecution``.

    Returns:
        A multi-line human-readable report.
    """
    lines: List[str] = [
        f"Execution {execution.get('id', 'N/A')}",
        f"  Workflow: {execution.get('workflow_id', 'N/A')}",
        f"  Status:   {execution.get('status', 'N/A')}",
        f"  Trigger:  {execution.get('trigger', 'N/A')}",
        f"  Started:  {execution.get('started_at', '—')}",
        f"  Finished: {execution.get('completed_at', '—')}",
    ]
    task_results = execution.get("task_results", [])
    if task_results:
        lines.append(f"  Tasks ({len(task_results)}):")
        for tr in task_results:
            lines.append(f"    - {format_task_summary(tr)}")
    return "\n".join(lines)


def format_workflow_tree(
    tasks: List[Dict[str, Any]], indent: int = 2
) -> str:
    """Render a workflow's tasks as an indented dependency tree.

    Tasks without dependencies appear at the root level.  Dependents
    are indented beneath their parents.

    Args:
        tasks: List of task dicts with ``id``, ``name``, and ``depends_on``.
        indent: Number of spaces per indentation level.

    Returns:
        A multi-line string representing the task tree.
    """
    task_map: Dict[str, Dict[str, Any]] = {t["id"]: t for t in tasks}
    children: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
    roots: List[str] = []

    for t in tasks:
        deps = t.get("depends_on", [])
        if not deps:
            roots.append(t["id"])
        else:
            for dep_id in deps:
                if dep_id in children:
                    children[dep_id].append(t["id"])

    lines: List[str] = []

    def _render(task_id: str, level: int) -> None:
        task = task_map.get(task_id)
        if not task:
            return
        prefix = " " * (indent * level)
        lines.append(f"{prefix}{task.get('name', task_id)} [{task.get('action', '?')}]")
        for child_id in children.get(task_id, []):
            _render(child_id, level + 1)

    for root_id in roots:
        _render(root_id, 0)

    return "\n".join(lines)
