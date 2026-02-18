"""Analytics service for workflow execution metrics."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..models import AnalyticsSummary, WorkflowExecution, WorkflowStatus
from . import workflow_engine


def get_summary(days: int = 30) -> AnalyticsSummary:
    """Generate an analytics summary for the given time window."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    all_executions = workflow_engine.list_executions(limit=10000)
    recent = [
        e for e in all_executions
        if e.started_at and e.started_at >= cutoff
    ]

    total = len(recent)
    completed = sum(1 for e in recent if e.status == WorkflowStatus.COMPLETED)
    success_rate = (completed / total * 100) if total > 0 else 0.0

    durations = []
    for ex in recent:
        if ex.started_at and ex.completed_at:
            d = (ex.completed_at - ex.started_at).total_seconds() * 1000
            durations.append(d)
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    status_counts: Counter = Counter()
    for ex in recent:
        status_counts[ex.status.value] += 1

    failing = _top_failing_workflows(recent)

    return AnalyticsSummary(
        total_workflows=len(workflow_engine.list_workflows()),
        total_executions=total,
        success_rate=round(success_rate, 2),
        avg_duration_ms=round(avg_duration, 2),
        executions_by_status=dict(status_counts),
        recent_executions=recent[:10],
        top_failing_workflows=failing,
    )


def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
    """Get detailed stats for a specific workflow."""
    executions = workflow_engine.list_executions(workflow_id=workflow_id, limit=1000)
    total = len(executions)
    completed = sum(1 for e in executions if e.status == WorkflowStatus.COMPLETED)
    failed = sum(1 for e in executions if e.status == WorkflowStatus.FAILED)

    durations = []
    for ex in executions:
        if ex.started_at and ex.completed_at:
            d = (ex.completed_at - ex.started_at).total_seconds() * 1000
            durations.append(d)

    return {
        "workflow_id": workflow_id,
        "total_executions": total,
        "completed": completed,
        "failed": failed,
        "success_rate": round((completed / total * 100) if total else 0, 2),
        "avg_duration_ms": round(sum(durations) / len(durations) if durations else 0, 2),
        "min_duration_ms": round(min(durations) if durations else 0, 2),
        "max_duration_ms": round(max(durations) if durations else 0, 2),
    }


def get_execution_timeline(
    hours: int = 24,
    bucket_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """Get execution counts bucketed by time for charting."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=hours)
    executions = workflow_engine.list_executions(limit=10000)
    recent = [
        e for e in executions
        if e.started_at and e.started_at >= cutoff
    ]

    buckets: Dict[str, Dict[str, int]] = {}
    current = cutoff
    while current <= now:
        key = current.strftime("%Y-%m-%dT%H:%M")
        buckets[key] = {"total": 0, "completed": 0, "failed": 0}
        current += timedelta(minutes=bucket_minutes)

    for ex in recent:
        if not ex.started_at:
            continue
        bucket_time = ex.started_at.replace(
            minute=(ex.started_at.minute // bucket_minutes) * bucket_minutes,
            second=0, microsecond=0
        )
        key = bucket_time.strftime("%Y-%m-%dT%H:%M")
        if key in buckets:
            buckets[key]["total"] += 1
            if ex.status == WorkflowStatus.COMPLETED:
                buckets[key]["completed"] += 1
            elif ex.status == WorkflowStatus.FAILED:
                buckets[key]["failed"] += 1

    return [{"time": k, **v} for k, v in sorted(buckets.items())]


def _top_failing_workflows(
    executions: List[WorkflowExecution], limit: int = 5
) -> List[Dict[str, Any]]:
    """Identify workflows with the highest failure rates."""
    failure_counts: Counter = Counter()
    total_counts: Counter = Counter()

    for ex in executions:
        total_counts[ex.workflow_id] += 1
        if ex.status == WorkflowStatus.FAILED:
            failure_counts[ex.workflow_id] += 1

    results = []
    for wf_id, failures in failure_counts.most_common(limit):
        total = total_counts[wf_id]
        results.append({
            "workflow_id": wf_id,
            "failures": failures,
            "total": total,
            "failure_rate": round(failures / total * 100, 2) if total else 0,
        })
    return results
