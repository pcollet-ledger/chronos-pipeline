"""Analytics endpoints for dashboard metrics.

Provides aggregated statistics, per-workflow breakdowns, and time-bucketed
execution timelines for charting.
"""

from typing import Any, Dict, List

from fastapi import APIRouter

from ..models import AnalyticsSummary
from ..services import analytics_service

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(days: int = 30) -> AnalyticsSummary:
    """Get analytics summary for the dashboard.

    Args:
        days: Number of days to include in the summary window.

    Returns:
        An ``AnalyticsSummary`` with totals, rates, and recent executions.
    """
    return analytics_service.get_summary(days=days)


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
    """Get detailed stats for a specific workflow.

    Args:
        workflow_id: UUID of the workflow.

    Returns:
        A dict with execution counts, success rate, and duration stats.
    """
    return analytics_service.get_workflow_stats(workflow_id)


@router.get("/timeline")
async def get_timeline(
    hours: int = 24,
    bucket_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """Get execution timeline data for charting.

    Args:
        hours: Number of hours to look back.
        bucket_minutes: Size of each time bucket in minutes.

    Returns:
        A list of time-bucketed dicts with ``time``, ``total``,
        ``completed``, and ``failed`` counts.
    """
    return analytics_service.get_execution_timeline(
        hours=hours, bucket_minutes=bucket_minutes
    )
