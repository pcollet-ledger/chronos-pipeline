"""Integration tests for analytics accuracy and consistency.

Verifies that analytics summaries, workflow stats, timeline data, and
top-failing-workflows all reflect the actual execution state accurately.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import WorkflowCreate
from app.services.analytics_service import clear_cache, get_summary, get_workflow_stats
from app.services.workflow_engine import (
    clear_all,
    create_workflow,
    execute_workflow,
    retry_execution,
)


@pytest.fixture(autouse=True)
def cleanup():
    clear_all()
    clear_cache()
    yield
    clear_all()
    clear_cache()


@pytest.fixture
def client():
    return TestClient(app)


def _good_wf(name: str = "Good"):
    return create_workflow(WorkflowCreate(
        name=name,
        tasks=[{"name": "Log", "action": "log", "parameters": {"message": "ok"}}],
    ))


def _bad_wf(name: str = "Bad"):
    return create_workflow(WorkflowCreate(
        name=name,
        tasks=[{"name": "Fail", "action": "unknown_action", "parameters": {}}],
    ))


class TestSummaryAccuracy:
    """Verify analytics summary numbers match actual execution state."""

    def test_counts_match_after_mixed_executions(self):
        good = _good_wf()
        bad = _bad_wf()
        execute_workflow(good.id)
        execute_workflow(good.id)
        execute_workflow(bad.id)
        clear_cache()

        summary = get_summary(days=30)
        assert summary.total_executions == 3
        assert summary.executions_by_status.get("completed", 0) == 2
        assert summary.executions_by_status.get("failed", 0) == 1
        assert summary.success_rate == pytest.approx(66.67, abs=0.01)

    def test_total_workflows_reflects_current_state(self):
        _good_wf("A")
        _good_wf("B")
        clear_cache()
        summary = get_summary()
        assert summary.total_workflows == 2

    def test_avg_duration_is_positive_for_completed(self):
        wf = _good_wf()
        execute_workflow(wf.id)
        clear_cache()
        summary = get_summary()
        assert summary.avg_duration_ms >= 0

    def test_recent_executions_ordered_newest_first(self):
        wf = _good_wf()
        ids = []
        for _ in range(3):
            ex = execute_workflow(wf.id)
            ids.append(ex.id)
        clear_cache()
        summary = get_summary()
        recent_ids = [e.id for e in summary.recent_executions]
        assert recent_ids == list(reversed(ids))

    def test_summary_after_retry_includes_retry(self):
        bad = _bad_wf()
        ex = execute_workflow(bad.id)
        retry_execution(ex.id)
        clear_cache()
        summary = get_summary()
        assert summary.total_executions == 2

    def test_summary_empty_when_no_executions(self):
        _good_wf()
        clear_cache()
        summary = get_summary()
        assert summary.total_executions == 0
        assert summary.success_rate == 0.0


class TestTopFailingWorkflows:
    """Verify the top-failing-workflows list is accurate."""

    def test_top_failing_identifies_correct_workflow(self):
        good = _good_wf("Reliable")
        bad = _bad_wf("Flaky")
        execute_workflow(good.id)
        execute_workflow(good.id)
        for _ in range(3):
            execute_workflow(bad.id)
        clear_cache()
        summary = get_summary()
        assert len(summary.top_failing_workflows) >= 1
        top = summary.top_failing_workflows[0]
        assert top["workflow_id"] == bad.id
        assert top["failures"] == 3
        assert top["failure_rate"] == 100.0

    def test_top_failing_empty_when_all_succeed(self):
        wf = _good_wf()
        execute_workflow(wf.id)
        clear_cache()
        summary = get_summary()
        assert summary.top_failing_workflows == []

    def test_top_failing_respects_limit(self):
        for i in range(10):
            bad = _bad_wf(f"Bad-{i}")
            execute_workflow(bad.id)
        clear_cache()
        summary = get_summary()
        assert len(summary.top_failing_workflows) <= 5


class TestWorkflowStatsAccuracy:
    """Verify per-workflow stats match actual execution counts."""

    def test_stats_counts(self):
        wf = _good_wf()
        for _ in range(5):
            execute_workflow(wf.id)
        clear_cache()
        stats = get_workflow_stats(wf.id)
        assert stats["total_executions"] == 5
        assert stats["completed"] == 5
        assert stats["failed"] == 0
        assert stats["success_rate"] == 100.0

    def test_stats_with_failures(self):
        bad = _bad_wf()
        for _ in range(3):
            execute_workflow(bad.id)
        clear_cache()
        stats = get_workflow_stats(bad.id)
        assert stats["total_executions"] == 3
        assert stats["failed"] == 3
        assert stats["success_rate"] == 0.0

    def test_stats_duration_bounds(self):
        wf = _good_wf()
        execute_workflow(wf.id)
        execute_workflow(wf.id)
        clear_cache()
        stats = get_workflow_stats(wf.id)
        assert stats["min_duration_ms"] <= stats["avg_duration_ms"]
        assert stats["avg_duration_ms"] <= stats["max_duration_ms"]

    def test_stats_nonexistent_workflow(self):
        clear_cache()
        stats = get_workflow_stats("nonexistent")
        assert stats["total_executions"] == 0


class TestTimelineAccuracy:
    """Verify timeline bucketing is correct."""

    def test_timeline_has_buckets(self):
        from app.services.analytics_service import get_execution_timeline

        wf = _good_wf()
        execute_workflow(wf.id)
        clear_cache()
        data = get_execution_timeline(hours=1, bucket_minutes=1)
        assert isinstance(data, list)
        assert len(data) > 0
        total = sum(b["total"] for b in data)
        assert total >= 1

    def test_timeline_completed_count(self):
        from app.services.analytics_service import get_execution_timeline

        wf = _good_wf()
        execute_workflow(wf.id)
        execute_workflow(wf.id)
        clear_cache()
        data = get_execution_timeline(hours=1, bucket_minutes=1)
        completed = sum(b["completed"] for b in data)
        assert completed >= 2

    def test_timeline_failed_count(self):
        from app.services.analytics_service import get_execution_timeline

        bad = _bad_wf()
        execute_workflow(bad.id)
        clear_cache()
        data = get_execution_timeline(hours=1, bucket_minutes=1)
        failed = sum(b["failed"] for b in data)
        assert failed >= 1

    def test_timeline_empty(self, client):
        clear_cache()
        resp = client.get("/api/analytics/timeline", params={"hours": 1, "bucket_minutes": 15})
        data = resp.json()
        assert all(b["total"] == 0 for b in data)

    def test_timeline_bucket_structure(self, client):
        clear_cache()
        resp = client.get("/api/analytics/timeline", params={"hours": 2, "bucket_minutes": 30})
        data = resp.json()
        for bucket in data:
            assert "time" in bucket
            assert "total" in bucket
            assert "completed" in bucket
            assert "failed" in bucket


class TestAnalyticsCacheIntegration:
    """Verify cache invalidation works correctly with analytics."""

    def test_cache_returns_stale_without_invalidation(self):
        wf = _good_wf()
        execute_workflow(wf.id)
        summary1 = get_summary()
        execute_workflow(wf.id)
        summary2 = get_summary()
        assert summary1.total_executions == summary2.total_executions

    def test_cache_returns_fresh_after_invalidation(self):
        wf = _good_wf()
        execute_workflow(wf.id)
        summary1 = get_summary()
        execute_workflow(wf.id)
        clear_cache()
        summary2 = get_summary()
        assert summary2.total_executions == summary1.total_executions + 1

    def test_api_summary_uses_cache(self, client):
        wf = _good_wf()
        execute_workflow(wf.id)
        resp1 = client.get("/api/analytics/summary")
        execute_workflow(wf.id)
        resp2 = client.get("/api/analytics/summary")
        assert resp1.json()["total_executions"] == resp2.json()["total_executions"]
