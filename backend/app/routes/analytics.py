"""Analytics endpoints for dashboard metrics."""

from typing import Any, Dict, List

from fastapi import APIRouter

from ..models import AnalyticsSummary
from ..services import analytics_service

router = APIRouter()


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(days: int = 30):
    """Get analytics summary for the dashboard."""
    return analytics_service.get_summary(days=days)


@router.get("/workflows/{workflow_id}/stats")
async def get_workflow_stats(workflow_id: str) -> Dict[str, Any]:
    """Get detailed stats for a specific workflow."""
    return analytics_service.get_workflow_stats(workflow_id)


@router.get("/timeline")
async def get_timeline(hours: int = 24, bucket_minutes: int = 60) -> List[Dict[str, Any]]:
    """Get execution timeline data for charting."""
    return analytics_service.get_execution_timeline(hours=hours, bucket_minutes=bucket_minutes)
