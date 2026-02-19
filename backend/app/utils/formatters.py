"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps, task
summaries, execution reports, and workflow dependency trees.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def format_duration(ms: float) -> str:
    """Format a duration in milliseconds to a human-readable string.

    Args:
        ms: Duration in milliseconds.

    Returns:
        A string like ``"500ms"``, ``"2.5s"``, ``"3.2m"``, or ``"1.5h"``.
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


def format_timestamp(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime to a string, returning ``"—"`` for ``None``.

    Args:
        dt: The datetime to format.
        fmt: strftime format string.

    Returns:
        The formatted string or ``"—"``.
    """
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_task_summary(task_result: Dict[str, Any]) -> str:
    """Format a single task result into a one-line summary.

    Args:
        task_result: A dict with ``task_id``, ``status``, and optional ``duration_ms``.

    Returns:
        A summary string like ``"task-abc: completed (12ms)"``.
    """
    task_id = task_result.get("task_id", "unknown")
    status = task_result.get("status", "unknown")
    duration = task_result.get("duration_ms")
    dur_str = f" ({format_duration(duration)})" if duration is not None else ""
    return f"{task_id}: {status}{dur_str}"


def format_execution_report(execution: Dict[str, Any]) -> str:
    """Format a workflow execution into a multi-line report.

    Args:
        execution: A dict with execution fields.

    Returns:
        A multi-line report string.
    """
    lines = [
        f"Execution {execution.get('id', 'unknown')}",
        f"  Status:  {execution.get('status', 'unknown')}",
        f"  Trigger: {execution.get('trigger', 'unknown')}",
    ]
    task_results = execution.get("task_results", [])
    if task_results:
        lines.append(f"  Tasks ({len(task_results)}):")
        for tr in task_results:
            lines.append(f"    - {format_task_summary(tr)}")
    return "\n".join(lines)


def format_workflow_tree(
    workflow_name: str,
    tasks: List[Dict[str, Any]],
) -> str:
    """Format a workflow's task dependency graph as an indented tree.

    Args:
        workflow_name: The workflow name.
        tasks: List of task dicts with ``name`` and ``depends_on``.

    Returns:
        A multi-line tree string.
    """
    lines = [workflow_name]
    task_map = {t.get("id", t.get("name", "")): t for t in tasks}
    roots = [t for t in tasks if not t.get("depends_on")]
    dependents: Dict[str, List[str]] = {}
    for t in tasks:
        for dep in t.get("depends_on", []):
            dependents.setdefault(dep, []).append(
                t.get("id", t.get("name", ""))
            )

    def _render(task_id: str, indent: int) -> None:
        task = task_map.get(task_id, {})
        name = task.get("name", task_id)
        prefix = "  " * indent + ("├─ " if indent > 0 else "  ")
        lines.append(f"{prefix}{name}")
        for child_id in dependents.get(task_id, []):
            _render(child_id, indent + 1)

    for root in roots:
        rid = root.get("id", root.get("name", ""))
        _render(rid, 1)

    return "\n".join(lines)
