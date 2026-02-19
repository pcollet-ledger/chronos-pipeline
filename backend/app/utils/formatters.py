"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps,
task summaries, execution reports, and workflow dependency trees.
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
        task_result: A dict with ``task_id``, ``status``, and optionally
            ``duration_ms`` and ``error``.

    Returns:
        A summary string like ``"task-1: completed (5ms)"``.
    """
    tid = task_result.get("task_id", "unknown")
    status = task_result.get("status", "unknown")
    duration = task_result.get("duration_ms")
    error = task_result.get("error")

    parts = [f"{tid}: {status}"]
    if duration is not None:
        parts.append(f"({format_duration(duration)})")
    if error:
        parts.append(f"[{error}]")
    return " ".join(parts)


def format_execution_report(execution: Dict[str, Any]) -> str:
    """Format a full execution record into a multi-line report.

    Args:
        execution: A dict with execution fields (``id``, ``status``,
            ``started_at``, ``completed_at``, ``task_results``).

    Returns:
        A multi-line report string.
    """
    lines = [
        f"Execution: {execution.get('id', 'unknown')}",
        f"  Status:  {execution.get('status', 'unknown')}",
        f"  Trigger: {execution.get('trigger', 'unknown')}",
    ]
    started = execution.get("started_at")
    if isinstance(started, datetime):
        lines.append(f"  Started: {format_timestamp(started)}")
    elif isinstance(started, str):
        lines.append(f"  Started: {started}")

    task_results = execution.get("task_results", [])
    if task_results:
        lines.append(f"  Tasks ({len(task_results)}):")
        for tr in task_results:
            lines.append(f"    - {format_task_summary(tr)}")
    return "\n".join(lines)


def format_workflow_tree(
    tasks: List[Dict[str, Any]], indent: int = 2
) -> str:
    """Format a workflow's tasks as an indented dependency tree.

    Tasks with no dependencies appear at the root level; dependent
    tasks are indented under their first dependency.

    Args:
        tasks: List of task dicts with ``id``, ``name``, and ``depends_on``.
        indent: Number of spaces per indentation level.

    Returns:
        A multi-line tree string.
    """
    task_map = {t.get("id", t.get("name", "")): t for t in tasks}
    children: Dict[str, List[str]] = {}
    roots: List[str] = []

    for t in tasks:
        tid = t.get("id", t.get("name", ""))
        deps = t.get("depends_on", [])
        if not deps:
            roots.append(tid)
        else:
            parent = deps[0]
            children.setdefault(parent, []).append(tid)

    lines: List[str] = []

    def _render(tid: str, level: int) -> None:
        task = task_map.get(tid, {})
        prefix = " " * (indent * level)
        name = task.get("name", tid)
        action = task.get("action", "")
        lines.append(f"{prefix}{name} [{action}]")
        for child in children.get(tid, []):
            _render(child, level + 1)

    for root in roots:
        _render(root, 0)

    orphans = set(task_map.keys()) - set(roots) - {
        c for kids in children.values() for c in kids
    }
    for orphan in sorted(orphans):
        _render(orphan, 0)

    return "\n".join(lines)
