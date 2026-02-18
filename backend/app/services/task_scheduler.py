"""Task scheduling service with cron expression support."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional


@dataclass
class ScheduleEntry:
    """A scheduled workflow entry."""
    workflow_id: str
    cron_expression: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    tags: List[str] = field(default_factory=list)


# In-memory schedule registry
_schedule_registry: Dict[str, ScheduleEntry] = {}


def register_schedule(workflow_id: str, cron_expression: str, tags: Optional[List[str]] = None) -> ScheduleEntry:
    """Register a workflow for scheduled execution."""
    if not validate_cron(cron_expression):
        raise ValueError(f"Invalid cron expression: {cron_expression}")

    entry = ScheduleEntry(
        workflow_id=workflow_id,
        cron_expression=cron_expression,
        next_run=compute_next_run(cron_expression),
        tags=tags or [],
    )
    _schedule_registry[workflow_id] = entry
    return entry


def unregister_schedule(workflow_id: str) -> bool:
    """Remove a workflow from the schedule."""
    if workflow_id in _schedule_registry:
        del _schedule_registry[workflow_id]
        return True
    return False


def get_schedule(workflow_id: str) -> Optional[ScheduleEntry]:
    """Get schedule entry for a workflow."""
    return _schedule_registry.get(workflow_id)


def list_schedules(enabled_only: bool = False) -> List[ScheduleEntry]:
    """List all scheduled entries."""
    entries = list(_schedule_registry.values())
    if enabled_only:
        entries = [e for e in entries if e.enabled]
    return sorted(entries, key=lambda e: e.next_run or datetime.max)


def get_due_schedules(now: Optional[datetime] = None) -> List[ScheduleEntry]:
    """Get all schedules that are due for execution."""
    now = now or datetime.utcnow()
    due = []
    for entry in _schedule_registry.values():
        if entry.enabled and entry.next_run and entry.next_run <= now:
            due.append(entry)
    return due


def mark_executed(workflow_id: str) -> Optional[ScheduleEntry]:
    """Mark a schedule as executed and compute next run."""
    entry = _schedule_registry.get(workflow_id)
    if not entry:
        return None
    entry.last_run = datetime.utcnow()
    entry.run_count += 1
    entry.next_run = compute_next_run(entry.cron_expression)
    return entry


def toggle_schedule(workflow_id: str, enabled: bool) -> Optional[ScheduleEntry]:
    """Enable or disable a scheduled workflow."""
    entry = _schedule_registry.get(workflow_id)
    if not entry:
        return None
    entry.enabled = enabled
    return entry


def validate_cron(expression: str) -> bool:
    """Validate a cron expression (simplified 5-field format).

    Delegates to the shared implementation in ``app.models`` to keep
    validation consistent across the scheduler and the API layer.
    """
    from ..models import validate_cron_expression

    return validate_cron_expression(expression)


def compute_next_run(cron_expression: str, from_time: Optional[datetime] = None) -> datetime:
    """Compute the next run time from a cron expression (simplified)."""
    base = from_time or datetime.utcnow()
    parts = cron_expression.strip().split()
    minute_spec = parts[0]
    hour_spec = parts[1]

    if minute_spec == "*" and hour_spec == "*":
        return base + timedelta(minutes=1)

    target_minute = int(minute_spec) if minute_spec != "*" else base.minute
    target_hour = int(hour_spec) if hour_spec != "*" else base.hour

    candidate = base.replace(minute=target_minute, second=0, microsecond=0)
    if hour_spec != "*":
        candidate = candidate.replace(hour=target_hour)

    if candidate <= base:
        if hour_spec == "*":
            candidate += timedelta(hours=1)
        else:
            candidate += timedelta(days=1)

    return candidate


def clear_schedules() -> None:
    """Clear all schedules (for testing)."""
    _schedule_registry.clear()
