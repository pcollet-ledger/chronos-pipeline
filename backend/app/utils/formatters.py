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
        A string like '500ms', '2.5s', '3.2m', or '1.5h'.
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
    """Format a datetime to a string, returning '—' for None.

    Args:
        dt: The datetime to format.
        fmt: The strftime format string.

    Returns:
        A formatted timestamp string or '—'.
    """
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_task_summary(task_result: Dict[str, Any]) -> str:
    """Format a single task result into a one-line summary.

    Args:
        task_result: A dict with task_id, status, and optional duration_ms.

    Returns:
        A string like 'task-abc: completed (12ms)'.
    """
    task_id = task_result.get("task_id", "unknown")
    status = task_result.get("status", "unknown")
    duration = task_result.get("duration_ms")
    dur_str = f" ({format_duration(duration)})" if duration is not None else ""
    return f"{task_id}: {status}{dur_str}"


def format_execution_report(execution: Dict[str, Any]) -> str:
    """Format a full execution record into a multi-line report.

    Args:
        execution: A dict with id, status, started_at, completed_at, task_results.

    Returns:
        A multi-line string report.
    """
    lines: List[str] = []
    exec_id = execution.get("id", "unknown")
    status = execution.get("status", "unknown")
    lines.append(f"Execution {exec_id} [{status}]")

    started = execution.get("started_at")
    completed = execution.get("completed_at")
    if started:
        lines.append(f"  Started:   {started}")
    if completed:
        lines.append(f"  Completed: {completed}")

    task_results = execution.get("task_results", [])
    if task_results:
        lines.append(f"  Tasks ({len(task_results)}):")
        for tr in task_results:
            lines.append(f"    - {format_task_summary(tr)}")

    return "\n".join(lines)


def format_workflow_tree(
    tasks: List[Dict[str, Any]],
    indent: str = "  ",
) -> str:
    """Format a workflow's task list as an indented dependency tree.

    Tasks with no dependencies appear at the root level; tasks that
    depend on others are indented beneath their first dependency.

    Args:
        tasks: A list of task dicts with 'id', 'name', and 'depends_on'.
        indent: The indentation string per level.

    Returns:
        A multi-line tree representation.
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
        task = task_map.get(tid)
        name = task.get("name", tid) if task else tid
        action = task.get("action", "") if task else ""
        prefix = indent * level
        lines.append(f"{prefix}{name} [{action}]" if action else f"{prefix}{name}")
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
