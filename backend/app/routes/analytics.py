"""Analytics endpoints for dashboard metrics.

All analytics computations are cached with a configurable TTL to avoid
recomputation on every request.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List

from fastapi import APIRouter, Path, Query

from ..models import AnalyticsSummary
from ..services import analytics_service

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    days: Annotated[
        int,
        Query(ge=0, le=99999, description="Number of days to look back"),
    ] = 30,
) -> AnalyticsSummary:
    """Get analytics summary for the dashboard.

    Args:
        days: How many days of history to include.

    Returns:
        An analytics summary with aggregated metrics.
    """
    return analytics_service.get_summary(days=days)


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(
    workflow_id: Annotated[
        str,
        Path(description="Unique workflow identifier"),
    ],
) -> Dict[str, Any]:
    """Get detailed stats for a specific workflow.

    Args:
        workflow_id: The workflow to compute stats for.

    Returns:
        A dict with execution counts, rates, and duration statistics.
    """
    return analytics_service.get_workflow_stats(workflow_id)


@router.get("/timeline")
async def get_timeline(
    hours: Annotated[
        int,
        Query(ge=0, le=8760, description="Hours of history to include"),
    ] = 24,
    bucket_minutes: Annotated[
        int,
        Query(ge=1, le=1440, description="Width of each time bucket in minutes"),
    ] = 60,
) -> List[Dict[str, Any]]:
    """Get execution timeline data for charting.

    Args:
        hours: How many hours of history to include.
        bucket_minutes: Width of each time bucket in minutes.

    Returns:
        A list of time-bucketed execution counts.
    """
    return analytics_service.get_execution_timeline(hours=hours, bucket_minutes=bucket_minutes)
