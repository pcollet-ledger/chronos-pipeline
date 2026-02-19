"""Output formatting helpers for Chronos Pipeline.

Provides human-readable formatting for durations, timestamps,
task summaries, execution reports, and workflow trees.
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
        fmt: The strftime format string.

    Returns:
        The formatted timestamp or ``"—"``.
    """
    if dt is None:
        return "—"
    return dt.strftime(fmt)


def format_task_summary(task_result: Dict[str, Any]) -> str:
    """Produce a one-line summary of a task result.

    Args:
        task_result: A dict with ``task_id``, ``status``, and optional
            ``duration_ms`` keys.

    Returns:
        A summary string like ``"task-abc: completed (150ms)"``.
    """
    task_id = task_result.get("task_id", "unknown")
    status = task_result.get("status", "unknown")
    duration = task_result.get("duration_ms")
    dur_str = f" ({format_duration(duration)})" if duration is not None else ""
    return f"{task_id}: {status}{dur_str}"


def format_execution_report(execution: Dict[str, Any]) -> str:
    """Produce a multi-line report of a workflow execution.

    Args:
        execution: A dict representing a ``WorkflowExecution``.

    Returns:
        A formatted report string.
    """
    lines = [
        f"Execution {execution.get('id', 'N/A')}",
        f"  Status:  {execution.get('status', 'unknown')}",
        f"  Trigger: {execution.get('trigger', 'unknown')}",
        f"  Tasks:   {len(execution.get('task_results', []))}",
    ]
    for tr in execution.get("task_results", []):
        lines.append(f"    - {format_task_summary(tr)}")
    return "\n".join(lines)


def format_workflow_tree(workflow: Dict[str, Any]) -> str:
    """Produce an indented tree representation of a workflow's tasks.

    Tasks with dependencies are indented under their parents.

    Args:
        workflow: A dict representing a ``WorkflowDefinition``.

    Returns:
        A tree-formatted string.
    """
    tasks: List[Dict[str, Any]] = workflow.get("tasks", [])
    if not tasks:
        return f"{workflow.get('name', 'Unnamed')} (no tasks)"

    task_map: Dict[str, Dict[str, Any]] = {}
    for t in tasks:
        tid = t.get("id", t.get("name", ""))
        task_map[tid] = t

    roots = [t for t in tasks if not t.get("depends_on")]
    children_map: Dict[str, List[str]] = {}
    for t in tasks:
        for dep in t.get("depends_on", []):
            children_map.setdefault(dep, []).append(
                t.get("id", t.get("name", ""))
            )

    lines = [workflow.get("name", "Unnamed")]
    visited: set[str] = set()

    def _render(tid: str, depth: int) -> None:
        if tid in visited:
            return
        visited.add(tid)
        t = task_map.get(tid)
        name = t.get("name", tid) if t else tid
        action = t.get("action", "?") if t else "?"
        lines.append(f"{'  ' * (depth + 1)}{name} [{action}]")
        for child_id in children_map.get(tid, []):
            _render(child_id, depth + 1)

    for root in roots:
        rid = root.get("id", root.get("name", ""))
        _render(rid, 0)

    # Render any remaining tasks not reachable from roots
    for t in tasks:
        tid = t.get("id", t.get("name", ""))
        if tid not in visited:
            _render(tid, 0)

    return "\n".join(lines)
