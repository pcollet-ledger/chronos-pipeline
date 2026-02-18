"""Task scheduling service with cron expression support."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence


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
    current_time: datetime = now or datetime.utcnow()
    due: List[ScheduleEntry] = []
    for entry in _schedule_registry.values():
        if entry.enabled and entry.next_run and entry.next_run <= current_time:
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

    Fields: minute (0-59), hour (0-23), day-of-month (1-31),
    month (1-12), day-of-week (0-6).
    """
    parts: List[str] = expression.strip().split()
    if len(parts) != 5:
        return False

    _FIELD_RANGES: Sequence[tuple[int, int]] = (
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day of month
        (1, 12),   # month
        (0, 6),    # day of week
    )

    for part, (lo, hi) in zip(parts, _FIELD_RANGES):
        if not _validate_cron_field(part, lo, hi):
            return False
    return True


def _validate_cron_field(field: str, lo: int, hi: int) -> bool:
    """Validate a single cron field against its allowed range."""
    pattern: str = r"^(\*|[0-9]{1,2}(-[0-9]{1,2})?(,[0-9]{1,2})*)(/[0-9]{1,2})?$"
    if not re.match(pattern, field):
        return False

    step_parts: List[str] = field.split("/")
    base: str = step_parts[0]

    if len(step_parts) == 2:
        step_val: int = int(step_parts[1])
        if step_val < 1 or step_val > hi:
            return False

    if base == "*":
        return True

    for token in base.split(","):
        range_parts: List[str] = token.split("-")
        for num_str in range_parts:
            val: int = int(num_str)
            if val < lo or val > hi:
                return False
        if len(range_parts) == 2 and int(range_parts[0]) > int(range_parts[1]):
            return False

    return True


def compute_next_run(cron_expression: str, from_time: Optional[datetime] = None) -> datetime:
    """Compute the next run time from a cron expression (simplified)."""
    base: datetime = from_time or datetime.utcnow()
    parts: List[str] = cron_expression.strip().split()
    minute_spec: str = parts[0]
    hour_spec: str = parts[1]

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
