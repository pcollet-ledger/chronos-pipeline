"""Analytics service for workflow execution metrics.

Includes a simple TTL-based cache to avoid recomputing expensive
aggregations on every request.  The cache is invalidated when new
executions are created and can be cleared manually for test isolation.
"""

from __future__ import annotations

import threading
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..models import AnalyticsSummary, WorkflowExecution, WorkflowStatus
from ..utils.formatters import format_duration
from . import workflow_engine

# Default cache TTL in seconds
DEFAULT_CACHE_TTL: float = 30.0

_cache_lock = threading.Lock()
_cache: Dict[str, Tuple[float, Any]] = {}
_cache_ttl: float = DEFAULT_CACHE_TTL


def set_cache_ttl(ttl: float) -> None:
    """Configure the cache TTL.

    Args:
        ttl: Time-to-live in seconds for cached entries.
    """
    global _cache_ttl
    _cache_ttl = ttl


def get_cache_ttl() -> float:
    """Return the current cache TTL in seconds.

    Returns:
        The TTL value.
    """
    return _cache_ttl


def clear_cache() -> None:
    """Invalidate all cached analytics results."""
    with _cache_lock:
        _cache.clear()


def invalidate_cache() -> None:
    """Invalidate the analytics cache.

    Should be called whenever new executions are created so that
    subsequent analytics queries return fresh data.
    """
    clear_cache()


def _get_cached(key: str) -> Optional[Any]:
    """Return a cached value if it exists and has not expired.

    Args:
        key: The cache key.

    Returns:
        The cached value, or ``None`` if missing or expired.
    """
    with _cache_lock:
        entry = _cache.get(key)
        if entry is None:
            return None
        ts, value = entry
        if (time.monotonic() - ts) > _cache_ttl:
            del _cache[key]
            return None
        return value


def _set_cached(key: str, value: Any) -> None:
    """Store a value in the cache with the current timestamp.

    Args:
        key: The cache key.
        value: The value to cache.
    """
    with _cache_lock:
        _cache[key] = (time.monotonic(), value)


def get_summary(days: int = 30) -> AnalyticsSummary:
    """Generate an analytics summary for the given time window.

    Args:
        days: Number of days to look back.

    Returns:
        An ``AnalyticsSummary`` with aggregated metrics.
    """
    cache_key = f"summary:{days}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    cutoff = datetime.utcnow() - timedelta(days=days)
    all_executions = workflow_engine.list_executions(limit=10000)
    recent = [
        e for e in all_executions
        if e.started_at and e.started_at >= cutoff
    ]

    total = len(recent)
    completed = sum(1 for e in recent if e.status == WorkflowStatus.COMPLETED)
    success_rate = (completed / total * 100) if total > 0 else 0.0

    durations: List[float] = []
    for ex in recent:
        if ex.started_at and ex.completed_at:
            d = (ex.completed_at - ex.started_at).total_seconds() * 1000
            durations.append(d)
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    status_counts: Counter[str] = Counter()
    for ex in recent:
        status_counts[ex.status.value] += 1

    failing = _top_failing_workflows(recent)

    result = AnalyticsSummary(
        total_workflows=len(workflow_engine.list_workflows(limit=100000)),
        total_executions=total,
        success_rate=round(success_rate, 2),
        avg_duration_ms=round(avg_duration, 2),
        executions_by_status=dict(status_counts),
        recent_executions=recent[:10],
        top_failing_workflows=failing,
    )
    _set_cached(cache_key, result)
    return result


def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
    """Get detailed stats for a specific workflow.

    Args:
        workflow_id: The workflow to compute stats for.

    Returns:
        A dict with execution counts, rates, and duration statistics.
    """
    cache_key = f"workflow_stats:{workflow_id}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

    executions = workflow_engine.list_executions(workflow_id=workflow_id, limit=1000)
    total = len(executions)
    completed = sum(1 for e in executions if e.status == WorkflowStatus.COMPLETED)
    failed = sum(1 for e in executions if e.status == WorkflowStatus.FAILED)

    durations: List[float] = []
    for ex in executions:
        if ex.started_at and ex.completed_at:
            d = (ex.completed_at - ex.started_at).total_seconds() * 1000
            durations.append(d)

    avg_dur = round(sum(durations) / len(durations) if durations else 0, 2)
    min_dur = round(min(durations) if durations else 0, 2)
    max_dur = round(max(durations) if durations else 0, 2)

    result = {
        "workflow_id": workflow_id,
        "total_executions": total,
        "completed": completed,
        "failed": failed,
        "success_rate": round((completed / total * 100) if total else 0, 2),
        "avg_duration_ms": avg_dur,
        "min_duration_ms": min_dur,
        "max_duration_ms": max_dur,
        "avg_duration_formatted": format_duration(avg_dur),
        "min_duration_formatted": format_duration(min_dur),
        "max_duration_formatted": format_duration(max_dur),
    }
    _set_cached(cache_key, result)
    return result


def get_execution_timeline(
    hours: int = 24,
    bucket_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """Get execution counts bucketed by time for charting.

    Args:
        hours: How many hours of history to include.
        bucket_minutes: Width of each time bucket in minutes.

    Returns:
        A list of dicts with ``time``, ``total``, ``completed``, and ``failed`` keys.
    """
    cache_key = f"timeline:{hours}:{bucket_minutes}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return cached

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

    result = [{"time": k, **v} for k, v in sorted(buckets.items())]
    _set_cached(cache_key, result)
    return result


def _top_failing_workflows(
    executions: List[WorkflowExecution], limit: int = 5
) -> List[Dict[str, Any]]:
    """Identify workflows with the highest failure rates.

    Args:
        executions: The list of executions to analyse.
        limit: Maximum number of workflows to return.

    Returns:
        A list of dicts with failure counts and rates.
    """
    failure_counts: Counter[str] = Counter()
    total_counts: Counter[str] = Counter()

    for ex in executions:
        total_counts[ex.workflow_id] += 1
        if ex.status == WorkflowStatus.FAILED:
            failure_counts[ex.workflow_id] += 1

    results: List[Dict[str, Any]] = []
    for wf_id, failures in failure_counts.most_common(limit):
        total = total_counts[wf_id]
        results.append({
            "workflow_id": wf_id,
            "failures": failures,
            "total": total,
            "failure_rate": round(failures / total * 100, 2) if total else 0,
        })
    return results
